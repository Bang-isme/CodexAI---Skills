#!/usr/bin/env python3
"""Mechanical visual quality gate with optional local Node detector."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any


SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".next",
    ".venv",
    "venv",
    ".codex",
    ".idea",
    ".vscode",
}
UI_EXTENSIONS = {".jsx", ".tsx", ".vue", ".html", ".css", ".scss"}
DEFAULT_FONT_RE = re.compile(
    r"(font-family\s*:|fontFamily\s*[:=])[^;\n]{0,80}\b(Arial|Helvetica|sans-serif|system-ui|Inter|Roboto)\b",
    re.IGNORECASE,
)
GRADIENT_CLICHE_RE = re.compile(
    r"linear-gradient\([^)]*(#(?:007bff|2196F3|3B82F6|6C63FF|7C3AED)|blue|purple)",
    re.IGNORECASE,
)
SPACING_RE = re.compile(r"(?:padding|margin|gap|border-radius)\s*:\s*(\d+(?:\.\d+)?)px", re.IGNORECASE)
CTA_RE = re.compile(r"(btn-primary|button[^>]*primary|variant=['\"]primary['\"])", re.IGNORECASE)
CARD_RE = re.compile(r"\b(card|rounded-xl|rounded-2xl)\b", re.IGNORECASE)
HIERARCHY_HINT_RE = re.compile(r"<(h1|h2|h3|h4)\b", re.IGNORECASE)
RESPONSIVE_RE = re.compile(r"@media|sm:|md:|lg:|xl:|max-w-|container-type", re.IGNORECASE)
REDUCED_MOTION_RE = re.compile(r"prefers-reduced-motion", re.IGNORECASE)
STATE_RE = re.compile(r"\b(disabled|aria-busy|loading|isLoading|empty|error)\b", re.IGNORECASE)

DEFAULT_VIEWPORTS: list[dict[str, Any]] = [
    {"id": "desktop-laptop", "width": 1280, "height": 800, "deviceScaleFactor": 1, "class": "desktop", "orientation": "landscape"},
    {"id": "desktop-standard", "width": 1440, "height": 900, "deviceScaleFactor": 1, "class": "desktop", "orientation": "landscape"},
    {"id": "desktop-wide", "width": 1920, "height": 1080, "deviceScaleFactor": 1, "class": "desktop", "orientation": "landscape"},
    {"id": "tablet-portrait", "width": 768, "height": 1024, "deviceScaleFactor": 1, "class": "tablet", "orientation": "portrait", "mobile": True, "touch": True},
    {"id": "tablet-landscape", "width": 1024, "height": 768, "deviceScaleFactor": 1, "class": "tablet", "orientation": "landscape", "mobile": True, "touch": True},
    {"id": "mobile-portrait", "width": 390, "height": 844, "deviceScaleFactor": 1, "class": "mobile", "orientation": "portrait", "mobile": True, "touch": True},
    {"id": "mobile-landscape", "width": 844, "height": 390, "deviceScaleFactor": 1, "class": "mobile", "orientation": "landscape", "mobile": True, "touch": True},
]
RESPONSIVE_MIN_WIDTH = 320
RESPONSIVE_MAX_WIDTH = 2560
RESPONSIVE_WIDTH_STEP = 64
RESPONSIVE_SCAN_HEIGHT = 900


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run mechanical visual checks on UI source. Dry-run by default; never installs Node packages."
    )
    parser.add_argument("--project-root", required=True, help="Project root to confine scans and writes")
    parser.add_argument("--files", default="", help="Optional comma-separated relative files; default is a UI scan")
    parser.add_argument("--apply", action="store_true", help="Write review JSON under .codex/design/reviews")
    parser.add_argument("--allow-network", action="store_true", help="Unused; detector never installs or fetches packages")
    parser.add_argument("--capture-manifest", default="", help="Optional responsive capture evidence manifest, relative to project root")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--max-rounds", type=int, default=2, help="Documented inspect/fix round limit")
    return parser.parse_args()


def confined(project_root: Path, relative: str | Path) -> Path:
    root = project_root.expanduser().resolve()
    target = (root / Path(str(relative))).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"path escapes project root: {relative}")
    return target


def expected_responsive_widths(
    breakpoints: list[int],
    min_width: int = RESPONSIVE_MIN_WIDTH,
    max_width: int = RESPONSIVE_MAX_WIDTH,
    step: int = RESPONSIVE_WIDTH_STEP,
) -> list[int]:
    if min_width < 1 or max_width < min_width or step < 1:
        raise ValueError("invalid responsive width range")
    widths = set(range(min_width, max_width + 1, step))
    widths.add(max_width)
    for breakpoint in breakpoints:
        if isinstance(breakpoint, bool) or not isinstance(breakpoint, int):
            raise ValueError("breakpoints must be integer CSS pixel widths")
        for candidate in (breakpoint - 1, breakpoint, breakpoint + 1):
            if min_width <= candidate <= max_width:
                widths.add(candidate)
    return sorted(widths)


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("not a readable PNG")
    return struct.unpack(">II", header[16:24])


def validate_capture_evidence(project_root: Path, manifest_path: str | Path | None) -> dict[str, Any]:
    """Validate responsive capture coverage and its on-disk PNG evidence."""
    if not manifest_path:
        return {"status": "DEGRADED", "reason": "capture manifest missing", "issues": ["capture manifest missing"]}
    try:
        manifest_file = confined(project_root, manifest_path)
    except (OSError, ValueError) as exc:
        return {"status": "fail", "reason": str(exc), "issues": [str(exc)]}
    if not manifest_file.is_file():
        return {"status": "DEGRADED", "reason": "capture manifest not found", "issues": ["capture manifest not found"]}
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "fail", "reason": f"invalid capture manifest: {exc}", "issues": [str(exc)]}
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1:
        return {"status": "fail", "reason": "unsupported capture manifest schema", "issues": ["unsupported capture manifest schema"]}

    if manifest.get("status") == "DEGRADED" and not manifest.get("captures"):
        reason = str(manifest.get("reason") or "capture runtime unavailable")
        return {"status": "DEGRADED", "reason": reason, "issues": [reason], "route_count": len(manifest.get("routes", []))}

    issues: list[str] = []
    degraded: list[str] = []
    routes = manifest.get("routes")
    states = manifest.get("states")
    breakpoints = manifest.get("breakpoints")
    captures = manifest.get("captures")
    if not isinstance(routes, list) or not routes or not isinstance(states, list) or not states:
        return {"status": "fail", "reason": "manifest needs routes and states", "issues": ["manifest needs routes and states"]}
    if not isinstance(breakpoints, list) or not isinstance(captures, list):
        return {"status": "fail", "reason": "manifest needs breakpoints and captures", "issues": ["manifest needs breakpoints and captures"]}
    try:
        widths = expected_responsive_widths(breakpoints)
    except ValueError as exc:
        return {"status": "fail", "reason": str(exc), "issues": [str(exc)]}
    breakpoint_sources = manifest.get("breakpointSources", [])
    if not isinstance(breakpoint_sources, list) or any(not isinstance(source, str) or not source.strip() for source in breakpoint_sources):
        return {"status": "fail", "reason": "breakpointSources must be a list of source references", "issues": ["invalid breakpointSources"]}
    if breakpoints and not breakpoint_sources:
        degraded.append("breakpoint values have no recorded source references")

    route_ids = [route.get("id") for route in routes if isinstance(route, dict)]
    if len(route_ids) != len(routes) or any(not isinstance(item, str) or not item for item in route_ids) or len(set(route_ids)) != len(route_ids):
        return {"status": "fail", "reason": "route IDs must be unique non-empty strings", "issues": ["invalid route IDs"]}
    default_viewports = {item["id"]: item for item in DEFAULT_VIEWPORTS}
    targets: dict[str, tuple[int, int]] = {}
    for route_id in route_ids:
        for viewport in DEFAULT_VIEWPORTS:
            key = f"{route_id}|default|{viewport['id']}"
            targets[key] = (viewport["width"], viewport["height"])
        for breakpoint in breakpoints:
            for width in (breakpoint - 1, breakpoint, breakpoint + 1):
                if RESPONSIVE_MIN_WIDTH <= width <= RESPONSIVE_MAX_WIDTH:
                    key = f"{route_id}|default|width-{width}"
                    targets[key] = (width, 900)

    default_states: set[str] = set()
    route_state_keys: set[str] = set()
    for state in states:
        if not isinstance(state, dict):
            issues.append("state entry is not an object")
            continue
        state_id, route_id = state.get("id"), state.get("routeId")
        viewport_ids = state.get("viewportIds", [])
        if not isinstance(state_id, str) or not state_id or route_id not in route_ids:
            issues.append("state has invalid id or routeId")
            continue
        route_state_keys.add(f"{route_id}|{state_id}")
        if state_id == "default":
            default_states.add(route_id)
            continue
        if not isinstance(viewport_ids, list) or not viewport_ids:
            issues.append(f"state {state_id} has no required viewportIds")
            continue
        for viewport_id in viewport_ids:
            viewport = default_viewports.get(viewport_id)
            if viewport is None:
                issues.append(f"state {state_id} names unknown viewport {viewport_id}")
                continue
            targets[f"{route_id}|{state_id}|{viewport_id}"] = (viewport["width"], viewport["height"])
    for route_id in route_ids:
        if route_id not in default_states:
            issues.append(f"route {route_id} has no default state")

    early_scan = manifest.get("responsiveScan", {})
    early_scan_routes = early_scan.get("routes", []) if isinstance(early_scan, dict) else []
    if isinstance(early_scan_routes, list):
        for route_scan in early_scan_routes:
            if not isinstance(route_scan, dict) or route_scan.get("routeId") not in route_ids:
                continue
            samples = route_scan.get("widths", [])
            if not isinstance(samples, list):
                continue
            for sample in samples:
                if not isinstance(sample, dict) or not isinstance(sample.get("width"), int):
                    continue
                width = sample["width"]
                if not RESPONSIVE_MIN_WIDTH <= width <= RESPONSIVE_MAX_WIDTH:
                    continue
                has_capture_signal = bool(sample.get("horizontalOverflow") or sample.get("consoleErrors") or sample.get("clippedControls"))
                if has_capture_signal:
                    targets[f"{route_scan['routeId']}|default|width-{width}"] = (width, RESPONSIVE_SCAN_HEIGHT)

    capture_by_key: dict[str, dict[str, Any]] = {}
    for capture in captures:
        if not isinstance(capture, dict) or not isinstance(capture.get("key"), str):
            issues.append("capture entry has no key")
            continue
        key = capture["key"]
        if key in capture_by_key:
            issues.append(f"duplicate capture key {key}")
        capture_by_key[key] = capture
    for key, dimensions in targets.items():
        capture = capture_by_key.get(key)
        if capture is None:
            issues.append(f"missing capture {key}")
            continue
        if capture.get("status") == "DEGRADED":
            degraded.append(f"capture unavailable for {key}")
            continue
        if capture.get("status") != "captured":
            issues.append(f"capture failed for {key}")
            continue
        actual_viewport = capture.get("viewport", {})
        expected_width, expected_height = dimensions
        if (actual_viewport.get("width"), actual_viewport.get("height"), actual_viewport.get("deviceScaleFactor")) != (expected_width, expected_height, 1):
            issues.append(f"capture viewport dimensions mismatch for {key}")
        document_height = capture.get("documentHeight")
        if not isinstance(document_height, int) or document_height < expected_height:
            issues.append(f"invalid document height for {key}")
            continue
        stitched_path = capture.get("stitchedPath")
        try:
            stitched_file = confined(project_root, stitched_path)
            stitched_dimensions = _png_dimensions(stitched_file)
        except (OSError, TypeError, ValueError) as exc:
            issues.append(f"stitched image missing or invalid for {key}: {exc}")
            stitched_dimensions = (0, 0)
        if stitched_dimensions != (expected_width, document_height):
            issues.append(f"stitched image dimensions mismatch for {key}")

        segments = capture.get("segments")
        if not isinstance(segments, list) or not segments:
            issues.append(f"capture has no viewport segments for {key}")
            continue
        covered_end = 0
        previous_scroll: int | None = None
        previous_height: int | None = None
        for index, segment in enumerate(segments):
            if not isinstance(segment, dict):
                issues.append(f"invalid segment in {key}")
                continue
            try:
                segment_file = confined(project_root, segment.get("path", ""))
                segment_dimensions = _png_dimensions(segment_file)
            except (OSError, TypeError, ValueError) as exc:
                issues.append(f"segment missing or invalid for {key}: {exc}")
                continue
            scroll_y = segment.get("sourceScrollY")
            source_height = segment.get("sourceViewportHeight")
            start_y = segment.get("coveredStartY")
            end_y = segment.get("coveredEndY")
            if segment_dimensions != (expected_width, expected_height):
                issues.append(f"segment dimensions mismatch for {key}")
            if not all(isinstance(value, int) for value in (scroll_y, source_height, start_y, end_y)):
                issues.append(f"segment coordinates invalid for {key}")
                continue
            if start_y != covered_end:
                issues.append(f"segment coverage gap or overlap for {key} at y={start_y}")
            if end_y <= start_y or start_y < scroll_y or end_y > scroll_y + source_height:
                issues.append(f"segment coverage outside source viewport for {key}")
            if previous_scroll is not None and previous_height is not None and scroll_y >= previous_scroll + previous_height:
                issues.append(f"viewport slices do not overlap for {key}")
            covered_end = end_y
            previous_scroll, previous_height = scroll_y, source_height
        if covered_end != document_height:
            issues.append(f"segment coverage ends at {covered_end}, expected {document_height} for {key}")

    scan = manifest.get("responsiveScan", {})
    if not isinstance(scan, dict):
        issues.append("responsiveScan must be an object")
        scan = {}
    if (scan.get("minWidth"), scan.get("maxWidth"), scan.get("step")) != (RESPONSIVE_MIN_WIDTH, RESPONSIVE_MAX_WIDTH, RESPONSIVE_WIDTH_STEP):
        issues.append("responsive scan range must be 320–2560px in 64px steps")
    scan_routes = scan.get("routes", [])
    scan_by_route = {item.get("routeId"): item for item in scan_routes if isinstance(item, dict)}
    for route_id in route_ids:
        route_scan = scan_by_route.get(route_id)
        if not route_scan or route_scan.get("stateId") != "default":
            issues.append(f"missing default responsive scan for route {route_id}")
            continue
        samples = route_scan.get("widths", [])
        observed: dict[int, dict[str, Any]] = {}
        for sample in samples:
            if not isinstance(sample, dict) or not isinstance(sample.get("width"), int):
                issues.append(f"invalid responsive width sample for route {route_id}")
                continue
            width = sample["width"]
            if width in observed:
                issues.append(f"duplicate responsive width {width} for route {route_id}")
            observed[width] = sample
            client_width = sample.get("clientWidth")
            scroll_width = sample.get("scrollWidth")
            if not isinstance(client_width, int) or not isinstance(scroll_width, int):
                issues.append(f"responsive width sample lacks dimensions at {width}px for route {route_id}")
            elif sample.get("horizontalOverflow") or scroll_width > client_width:
                issues.append(f"horizontal overflow at {width}px for route {route_id}")
            if sample.get("clippedControls") and f"{route_id}|default|width-{width}" not in capture_by_key:
                issues.append(f"missing clipping-signal capture at {width}px for route {route_id}")
            if sample.get("consoleErrors"):
                issues.append(f"browser errors at {width}px for route {route_id}")
        missing_widths = sorted(set(widths) - set(observed))
        if missing_widths:
            issues.append(f"responsive scan missing widths for route {route_id}: {missing_widths[:8]}")

    if manifest.get("errors"):
        issues.append("capture reported browser or runtime errors")

    flows = manifest.get("flows")
    expected_flow_ids: set[str] = set()
    if not isinstance(flows, list) or not flows:
        degraded.append("UX contract flow review is missing")
    else:
        flow_covered_routes: set[str] = set()
        for flow in flows:
            if not isinstance(flow, dict) or not isinstance(flow.get("id"), str) or not flow.get("id"):
                issues.append("flow entry needs a non-empty id")
                continue
            flow_id = flow["id"]
            if flow_id in expected_flow_ids:
                issues.append(f"duplicate flow id {flow_id}")
            expected_flow_ids.add(flow_id)
            flow_routes = flow.get("routeIds")
            if not isinstance(flow_routes, list) or not flow_routes or any(route_id not in route_ids for route_id in flow_routes):
                issues.append(f"flow {flow_id} must reference known routes")
            else:
                flow_covered_routes.update(flow_routes)
        uncovered_routes = sorted(set(route_ids) - flow_covered_routes)
        if uncovered_routes:
            degraded.append(f"UX contract flows do not cover routes: {uncovered_routes}")

    functional_review = manifest.get("functionalReview")
    if not isinstance(functional_review, dict):
        degraded.append("functional and accessibility review is missing")
    else:
        checked_flow_ids = functional_review.get("checkedFlowIds", [])
        checked_route_state_keys = functional_review.get("checkedRouteStateKeys", [])
        if not isinstance(checked_flow_ids, list):
            checked_flow_ids = []
        if not isinstance(checked_route_state_keys, list):
            checked_route_state_keys = []
        if not expected_flow_ids.issubset({item for item in checked_flow_ids if isinstance(item, str)}):
            degraded.append("functional review has not exercised every required UX flow")
        if not route_state_keys.issubset({item for item in checked_route_state_keys if isinstance(item, str)}):
            degraded.append("functional review has not checked every declared route/state")
        if functional_review.get("status") != "complete" or functional_review.get("mainFlowStatus") != "pass" or functional_review.get("accessibilityStatus") != "pass":
            if functional_review.get("mainFlowStatus") == "fail" or functional_review.get("accessibilityStatus") == "fail":
                issues.append("main flow or accessibility review failed")
            else:
                degraded.append("functional or accessibility review is incomplete")
        functional_findings = functional_review.get("findings", [])
        if isinstance(functional_findings, list):
            for finding in functional_findings:
                if not isinstance(finding, dict):
                    issues.append("functional review finding is not an object")
                    continue
                if not finding.get("description") or not finding.get("evidence"):
                    issues.append("functional review finding needs a description and test/capture evidence")
                if isinstance(finding, dict) and (finding.get("blocking") or finding.get("severity") in {"P0", "P1"}):
                    resolution = finding.get("resolution", {})
                    if not isinstance(resolution, dict) or resolution.get("status") not in {"fixed", "product-justified"}:
                        issues.append("functional review has unresolved blocking findings")
                        break
                    if resolution.get("status") == "product-justified" and not resolution.get("rationale"):
                        issues.append("product-justified functional finding lacks a rationale")
                        break
        else:
            issues.append("functional review findings must be a list")

    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict) or not provenance.get("appRevision") or not isinstance(provenance.get("references"), list):
        degraded.append("capture provenance is incomplete (appRevision and references are required)")

    review = manifest.get("visualReview", {})
    expected_review_keys = set(targets)
    checked_keys = review.get("checkedCaptureKeys", []) if isinstance(review, dict) else []
    if not isinstance(checked_keys, list):
        checked_keys = []
    reviewed_keys = set(key for key in checked_keys if isinstance(key, str))
    if (
        not isinstance(review, dict)
        or review.get("status") != "complete"
        or not review.get("reviewer")
        or not review.get("summary")
        or not expected_review_keys.issubset(reviewed_keys)
    ):
        degraded.append("visual review incomplete for one or more required captures")
    if isinstance(review, dict):
        review_findings = review.get("findings", [])
        if not isinstance(review_findings, list):
            issues.append("visual review findings must be a list")
            review_findings = []
        for finding in review_findings:
            if not isinstance(finding, dict):
                issues.append("visual review finding is not an object")
                continue
            evidence_key = finding.get("captureKey")
            if evidence_key not in expected_review_keys:
                issues.append("visual review finding lacks a valid captureKey")
            if not all(finding.get(field) for field in ("routeId", "stateId", "viewportId", "description", "severity")):
                issues.append("visual review finding lacks route/state/viewport, description, or severity")
            resolution = finding.get("resolution", {})
            resolution_status = resolution.get("status") if isinstance(resolution, dict) else None
            resolved = resolution_status in {"fixed", "product-justified"}
            if resolution_status == "product-justified" and not resolution.get("rationale"):
                issues.append("product-justified finding lacks a rationale")
            if (finding.get("blocking") or finding.get("severity") in {"P0", "P1"}) and not resolved:
                issues.append("visual review has unresolved blocking findings")
    if manifest.get("status") == "DEGRADED":
        degraded.append(str(manifest.get("reason") or "capture runtime degraded"))
    elif manifest.get("status") not in {"captured", "complete"}:
        issues.append("manifest capture status is not captured")

    status = "fail" if issues else "DEGRADED" if degraded else "pass"
    report: dict[str, Any] = {
        "status": status,
        "issues": issues + degraded,
        "route_count": len(route_ids),
        "flow_count": len(expected_flow_ids),
        "capture_count": len(capture_by_key),
        "responsive_width_count": len(widths),
        "breakpoints": breakpoints,
        "required_viewports": DEFAULT_VIEWPORTS,
    }
    if degraded:
        report["reason"] = "; ".join(degraded)
    return report


def iter_ui_files(project_root: Path, explicit: list[str]) -> list[Path]:
    if explicit:
        return [confined(project_root, item) for item in explicit if item.strip()]
    files: list[Path] = []
    root = project_root.resolve()
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in UI_EXTENSIONS:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        files.append(path)
        if len(files) >= 200:
            break
    return files


def add_finding(
    findings: list[dict[str, Any]],
    *,
    check: str,
    severity: str,
    path: Path,
    project_root: Path,
    message: str,
    blocking: bool,
) -> None:
    findings.append(
        {
            "check": check,
            "severity": severity,
            "blocking": blocking,
            "file": path.relative_to(project_root.resolve()).as_posix(),
            "message": message,
            "kind": "mechanical",
        }
    )


def scan_file(path: Path, project_root: Path, findings: list[dict[str, Any]]) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    if DEFAULT_FONT_RE.search(text):
        add_finding(
            findings,
            check="default_font",
            severity="warning",
            path=path,
            project_root=project_root,
            message="Generic font-family token matched; verify it fits the local type contract and rendered surface.",
            blocking=False,
        )
    if GRADIENT_CLICHE_RE.search(text):
        add_finding(
            findings,
            check="gradient_cliche",
            severity="warning",
            path=path,
            project_root=project_root,
            message="A familiar blue/purple gradient pattern matched; inspect its product role in the rendered composition.",
            blocking=False,
        )
    spacing_values = SPACING_RE.findall(text)
    unique_spacing = {value for value in spacing_values}
    if len(unique_spacing) >= 8:
        add_finding(
            findings,
            check="arbitrary_spacing_radius",
            severity="warning",
            path=path,
            project_root=project_root,
            message=f"{len(unique_spacing)} distinct px spacing/radius values; verify whether the local token scale is intentional.",
            blocking=False,
        )
    if len(CTA_RE.findall(text)) >= 2:
        add_finding(
            findings,
            check="competing_ctas",
            severity="warning",
            path=path,
            project_root=project_root,
            message="Several primary-action markers occur in one file; inspect one rendered region before judging hierarchy.",
            blocking=False,
        )
    if len(CARD_RE.findall(text)) >= 6:
        add_finding(
            findings,
            check="card_repetition",
            severity="warning",
            path=path,
            project_root=project_root,
            message="Repeated card markers matched; verify whether items are parallel and benefit from equal grouping.",
            blocking=False,
        )
    if path.suffix.lower() in {".jsx", ".tsx", ".vue", ".html"} and not HIERARCHY_HINT_RE.search(text):
        add_finding(
            findings,
            check="missing_hierarchy",
            severity="warning",
            path=path,
            project_root=project_root,
            message="No heading tags found in a UI file.",
            blocking=False,
        )
    if path.suffix.lower() in {".css", ".scss", ".jsx", ".tsx", ".vue"} and not RESPONSIVE_RE.search(text):
        if path.suffix.lower() in {".css", ".scss"} or "return" in text:
            add_finding(
                findings,
                check="missing_responsive",
                severity="warning",
                path=path,
                project_root=project_root,
                message="No responsive breakpoint or utility evidence in source.",
                blocking=False,
            )
    if not REDUCED_MOTION_RE.search(text) and re.search(r"(animation|transition|@keyframes)", text, re.IGNORECASE):
        add_finding(
            findings,
            check="missing_reduced_motion",
            severity="warning",
            path=path,
            project_root=project_root,
            message="Motion found without a reduced-motion rule in this file; check shared styles and actual behavior.",
            blocking=False,
        )
    if path.suffix.lower() in {".jsx", ".tsx", ".vue"} and re.search(r"<button|onClick|type=['\"]submit['\"]", text):
        if not STATE_RE.search(text):
            add_finding(
                findings,
                check="missing_states",
                severity="warning",
                path=path,
                project_root=project_root,
                message="Interactive control has no loading/disabled/empty/error token in this file; verify its flow and shared state handling.",
                blocking=False,
            )


def run_ux_audit(project_root: Path) -> dict[str, Any]:
    script = Path(__file__).resolve().parents[2] / "codex-execution-quality-gate" / "scripts" / "ux_audit.py"
    if not script.exists():
        return {"status": "skipped", "reason": "ux_audit.py missing"}
    try:
        completed = subprocess.run(
            [sys.executable, str(script), "--project-root", str(project_root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
        payload["status"] = payload.get("status") or ("pass" if completed.returncode == 0 else "warn")
        return payload
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"status": "failed", "reason": str(exc)}


def detector_status() -> dict[str, Any]:
    local_bin = shutil.which("impeccable")
    npx = shutil.which("npx")
    if local_bin:
        return {"status": "available", "command": [local_bin, "detect"], "mode": "local-binary"}
    if npx:
        return {
            "status": "skipped",
            "command": ["npx", "--no-install", "impeccable", "detect"],
            "mode": "npx-no-install",
            "reason": "local impeccable binary not found; npx --no-install is optional and not executed unless binary exists",
        }
    return {"status": "skipped", "reason": "impeccable binary and npx not found", "mode": "absent"}


def run_optional_detector() -> dict[str, Any]:
    info = detector_status()
    if info.get("status") != "available":
        return info
    command = info.get("command") or []
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
            env={**os.environ, "NO_UPDATE_NOTIFIER": "1"},
        )
        info["exit_code"] = completed.returncode
        info["stdout_tail"] = completed.stdout[-1500:]
        info["status"] = "available" if completed.returncode == 0 else "failed"
        return info
    except (OSError, subprocess.TimeoutExpired) as exc:
        info["status"] = "failed"
        info["reason"] = str(exc)
        return info


def browser_capability() -> dict[str, Any]:
    return {
        "status": "manifest_required",
        "reason": "responsive capture and rendered review are validated from --capture-manifest",
    }


def build_report(
    project_root: Path,
    files: list[str],
    apply: bool,
    max_rounds: int,
    capture_manifest: str | Path | None = None,
) -> dict[str, Any]:
    ui_files = [path for path in iter_ui_files(project_root, files) if path.exists()]
    findings: list[dict[str, Any]] = []
    for path in ui_files:
        scan_file(path, project_root, findings)
    ux = run_ux_audit(project_root)
    detector = run_optional_detector() if detector_status().get("status") == "available" else detector_status()
    blocking = [item for item in findings if item.get("blocking")]
    review = browser_capability()
    capture_evidence = validate_capture_evidence(project_root, capture_manifest)
    if blocking or capture_evidence.get("status") == "fail":
        status = "fail"
    elif capture_evidence.get("status") != "pass":
        status = "DEGRADED"
    else:
        status = "pass"
    written = ""
    payload = {
        "status": status,
        "kind": "mechanical_evidence",
        "disclaimer": "Mechanical evidence from source; not an objective aesthetic score.",
        "dry_run": not apply,
        "project_root": str(project_root.resolve()),
        "files_scanned": [path.relative_to(project_root.resolve()).as_posix() for path in ui_files],
        "findings": findings,
        "blocking_count": len(blocking),
        "ux_audit": {"status": ux.get("status"), "total_issues": ux.get("total_issues")},
        "optional_detector": detector,
        "independent_review": review,
        "capture_evidence": capture_evidence,
        "max_inspect_fix_rounds": max_rounds,
        "required_viewports": DEFAULT_VIEWPORTS,
        "responsive_scan": {"min_width": RESPONSIVE_MIN_WIDTH, "max_width": RESPONSIVE_MAX_WIDTH, "step": RESPONSIVE_WIDTH_STEP},
    }
    if apply:
        out_dir = confined(project_root, Path(".codex") / "design" / "reviews")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "latest-mechanical.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written = out_path.relative_to(project_root.resolve()).as_posix()
        payload["written"] = written
    return payload


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        project_root = Path(args.project_root).expanduser().resolve()
        if not project_root.is_dir():
            raise NotADirectoryError(f"Project root does not exist or is not a directory: {project_root}")
        files = [part.strip() for part in args.files.split(",") if part.strip()]
        payload = build_report(project_root, files, args.apply, args.max_rounds, args.capture_manifest or None)
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "text":
        print(
            f"{payload['status']}: blocking={payload.get('blocking_count', 0)} "
            f"detector={payload.get('optional_detector', {}).get('status')}"
        )
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") in {"pass", "warn", "dry_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
