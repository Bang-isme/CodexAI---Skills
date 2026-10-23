#!/usr/bin/env python3
"""Native CodexAI mechanical and responsive visual quality gate."""
from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import sys
from difflib import SequenceMatcher
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
        description="Run mechanical visual and responsive evidence checks on UI source. Dry-run by default."
    )
    parser.add_argument("--project-root", required=True, help="Project root to confine scans and writes")
    parser.add_argument("--files", default="", help="Optional comma-separated relative files; default is a UI scan")
    parser.add_argument("--apply", action="store_true", help="Write review JSON under .codex/design/reviews")
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


def run_accessibility_check(project_root: Path) -> dict[str, Any]:
    script = Path(__file__).resolve().parents[2] / "codex-execution-quality-gate" / "scripts" / "accessibility_check.py"
    if not script.exists():
        return {"status": "skipped", "reason": "accessibility_check.py missing"}
    try:
        completed = subprocess.run(
            [sys.executable, str(script), "--project-root", str(project_root), "--level", "AA"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
        critical_issues = int((payload.get("by_severity") or {}).get("critical", 0) or 0)
        payload["status"] = "fail" if critical_issues > 0 else (payload.get("status") or ("pass" if completed.returncode == 0 else "warn"))
        payload["critical_issues"] = critical_issues
        return payload
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"status": "failed", "reason": str(exc)}


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
    a11y = run_accessibility_check(project_root)
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
        "accessibility_check": {
            "status": a11y.get("status"),
            "total_issues": a11y.get("total_issues"),
            "critical_issues": a11y.get("critical_issues", 0),
        },
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


MOTION_DURATION_BANDS_MS: dict[str, tuple[float, float]] = {
    "control-feedback": (120, 220),
    "toggle-popover-toast": (180, 320),
    "section-entrance": (400, 800),
    "editorial-mask": (500, 760),
    "hero-sequence": (800, 1600),
}
SCRUB_LAG_BAND = (0.8, 1.4)
STAGGER_BANDS_S: dict[str, tuple[float, float]] = {
    "word": (0.035, 0.07),
    "line": (0.08, 0.14),
    "card": (0.06, 0.10),
}
REVEAL_TRAVEL_BANDS_PX: dict[str, tuple[float, float]] = {
    "product": (12, 24),
    "narrative": (24, 48),
}
TEXT_BLUR_PX_BAND = (4, 10)
HOVER_SCALE_CAP = 1.03
HOVER_TILT_CAP_DEG = 4
HOVER_TRAVEL_CAP_PX = 16
PARALLAX_VIEWPORT_CAP = 0.05
REVEAL_VISIBLE_FRACTION_BAND = (0.20, 0.30)
REVEAL_TOP_VIEWPORT_FRACTION = 0.82
CHAPTER_FLIP_PROGRESS = 0.39
SCENE_DWELL_SCREENS = 1.15
SCENE_MOVE_SCREENS = 0.85
SCENE_WEIGHT_VH_BAND = (0.7, 1.8)
MAX_PEER_PLANS = 3
PLAN_ROW_BAND = (3, 6)
REQUIRED_PRICING_FAQ_TOPICS = (
    "refund policy",
    "trial terms",
    "cancellation behavior",
    "seat/usage definition",
    "procurement/invoicing",
)
PROFILING_ABLATION_ORDER = (
    "lower-dpr",
    "disable-post-processing",
    "freeze-shadows",
    "disable-particles",
    "hide-groups",
    "swap-lod",
    "replace-materials",
)
WAIVABLE_MOTION_CODES = frozenset({
    "duration-out-of-band",
    "scrub-lag-out-of-band",
    "stagger-out-of-band",
    "reveal-travel-out-of-band",
    "text-blur-out-of-band",
    "reveal-trigger-out-of-band",
})
LAYOUT_SCROLL_PROPERTIES = frozenset({
    "width", "height", "top", "left", "right", "bottom",
    "margin", "padding", "min-width", "max-width", "min-height", "max-height",
    "margin-top", "margin-left", "margin-right", "margin-bottom",
    "padding-top", "padding-left", "padding-right", "padding-bottom",
    "inset",
})
_JOB_ALIASES = {
    "control-feedback": "control-feedback",
    "feedback": "control-feedback",
    "toggle-popover-toast": "toggle-popover-toast",
    "toggle": "toggle-popover-toast",
    "popover": "toggle-popover-toast",
    "toast": "toggle-popover-toast",
    "section-entrance": "section-entrance",
    "editorial-mask": "editorial-mask",
    "editorial-masks": "editorial-mask",
    "hero-sequence": "hero-sequence",
    "hero": "hero-sequence",
}
_GENERIC_GRAM_WORDS = frozenset({
    "learn", "more", "get", "started", "start", "contact", "read", "click",
    "here", "sign", "up", "submit", "buy", "now", "today",
})
_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "with",
    "your", "our", "is", "are", "be", "this", "that", "it", "at", "from", "by", "as",
})
_COMMON_NUMBERS = frozenset({
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 24, 32, 44, 48, 60, 100, 1000,
    320, 390, 768, 844, 1024, 1280, 1440, 1920, 2560,
})
_GENERIC_FRAMES = frozenset({
    "hero", "faq", "footer", "cta", "benefits", "header", "nav", "proof",
})
_GENERIC_TRAITS = frozenset({
    "black-and-white", "black and white", "monochrome", "single-accent",
    "single accent", "hero+faq", "hero-faq", "hero+faq order", "fade",
    "standard-fade", "standard fade", "standard",
})
_GENERIC_ASSETS = frozenset({"placeholder", "image", "photo", "icon", "logo"})
_HORIZONTAL_PRICING_LAYOUTS = frozenset({
    "horizontal-scroll-table",
    "horizontal-scrolling-table",
    "horizontal-scrolling-comparison-table",
    "horizontal-table",
    "comparison-table",
    "horizontal-scroll",
})
_STACKED_PRICING_LAYOUTS = frozenset({"stacked-cards", "stacked", "stack"})


def _issue(code: str, message: str, severity: str = "blocking") -> dict[str, Any]:
    return {"code": code, "message": message, "severity": severity}


def _finish(issues: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    blocking = [item for item in issues if item.get("severity") != "warning"]
    status = "fail" if blocking else "pass"
    payload: dict[str, Any] = {
        "status": status,
        "ok": status == "pass",
        "issues": issues,
        "warnings": [item for item in issues if item.get("severity") == "warning"],
    }
    payload.update(extra)
    return payload


def _documented(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if len(text) < 12 or not re.search(r"[A-Za-z]", text):
        return False
    if text.lower() in {"exception", "justified", "yes", "true", "documented"}:
        return False
    return True


def _in_band(value: float, low: float, high: float) -> bool:
    return (low - 1e-9) <= float(value) <= (high + 1e-9)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        return float(match.group(0)) if match else None
    return None


def _flag(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "highlighted", "recommended"}
    return value is True


def _normalize_job(job: Any) -> str:
    if not job:
        return ""
    text = re.sub(r"\s+", "-", str(job).strip().lower().replace("_", "-").replace("/", " "))
    return _JOB_ALIASES.get(text, text)


def _fraction(value: Any) -> float | None:
    number = _number(value)
    if number is None:
        return None
    if number > 1.5:
        return number / 100.0
    return number


def _property_name(value: str) -> str:
    kebab = re.sub(r"([a-z])([A-Z])", r"\1-\2", value.strip())
    return kebab.lower().replace("_", "-")


def _name_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [_property_name(part) for part in re.split(r"[,\s]+", value) if part.strip()]
    if isinstance(value, (list, tuple)):
        return [_property_name(str(item)) for item in value if str(item).strip()]
    return []


def _reveal_context(value: Any) -> str:
    text = str(value or "").strip().lower()
    if "narrat" in text or "story" in text or "editorial" in text:
        return "narrative"
    if "product" in text or text in {"ui", "operate"}:
        return "product"
    return text


def _norm_step(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def evaluate_motion_contract(spec: dict) -> dict[str, Any]:
    """Validate duration bands, travel, parallax, reduced motion, and scroll properties.

    Out-of-band durations, staggers, travel, blur, scrub lag, and reveal triggers
    are waived only when ``spec["exception"]`` is a documented note. Caps, utility
    card staggers, hidden ``0.01ms`` reduced motion, and layout-property scroll
    animation are not waived.
    """
    if not isinstance(spec, dict):
        return _finish([_issue("invalid-motion-spec", "Motion spec must be an object.")])
    issues: list[dict[str, Any]] = []
    job = _normalize_job(spec.get("job"))
    if "duration_ms" in spec:
        duration = _number(spec.get("duration_ms"))
        if duration is None:
            issues.append(_issue("invalid-motion-value", "duration_ms must be a number of milliseconds."))
        elif job not in MOTION_DURATION_BANDS_MS:
            code = "missing-motion-job" if not job else "unknown-motion-job"
            issues.append(_issue(code, "A duration needs a known motion job so it can be checked against a band."))
        else:
            low, high = MOTION_DURATION_BANDS_MS[job]
            if not _in_band(duration, low, high):
                issues.append(_issue(
                    "duration-out-of-band",
                    f"{job} duration {duration:g}ms is outside {low:g}–{high:g}ms.",
                ))
    if job == "hero-sequence" and "beats_ms" in spec:
        raw_beats = spec.get("beats_ms")
        beats = [_number(item) for item in raw_beats] if isinstance(raw_beats, (list, tuple)) else []
        if not isinstance(raw_beats, (list, tuple)) or any(item is None for item in beats) or len(beats) < 2:
            issues.append(_issue(
                "hero-missing-beats",
                "A hero sequence needs at least two internal beats inside 800–1600ms.",
            ))
        else:
            total = sum(item for item in beats if item is not None)
            if not _in_band(total, *MOTION_DURATION_BANDS_MS["hero-sequence"]):
                issues.append(_issue(
                    "duration-out-of-band",
                    f"Hero beat sum {total:g}ms is outside 800–1600ms.",
                ))
            duration = _number(spec.get("duration_ms")) if "duration_ms" in spec else None
            if duration is not None and abs(duration - total) > 1:
                issues.append(_issue(
                    "hero-beat-sum-mismatch",
                    "Hero duration_ms and the sum of beats_ms disagree.",
                ))
    elif job == "hero-sequence" and "duration_ms" in spec:
        duration = _number(spec.get("duration_ms"))
        low, high = MOTION_DURATION_BANDS_MS["hero-sequence"]
        if duration is not None and _in_band(duration, low, high):
            issues.append(_issue(
                "hero-beats-not-recorded",
                "Hero sequence is inside 800–1600ms but does not record internal beats.",
                severity="warning",
            ))
    lag_source = spec["scrub_lag"] if "scrub_lag" in spec else spec.get("scrub")
    if lag_source is not None and not isinstance(lag_source, bool):
        lag = _number(lag_source)
        if lag is None or not _in_band(lag, *SCRUB_LAG_BAND):
            issues.append(_issue(
                "scrub-lag-out-of-band",
                "Numeric scroll scrub lag must sit in 0.8–1.4. Direct scrub: true is not a lag value.",
            ))
    stagger = spec.get("stagger_s")
    if isinstance(stagger, dict):
        for name, band in STAGGER_BANDS_S.items():
            if name not in stagger:
                continue
            amount = _number(stagger.get(name))
            if amount is None or not _in_band(amount, *band):
                issues.append(_issue(
                    "stagger-out-of-band",
                    f"{name} stagger is outside {band[0]:g}–{band[1]:g}s.",
                ))
    if "reveal_travel_px" in spec:
        context = _reveal_context(spec.get("reveal_context") or spec.get("context"))
        travel = _number(spec.get("reveal_travel_px"))
        if context not in REVEAL_TRAVEL_BANDS_PX:
            issues.append(_issue(
                "reveal-context-missing",
                "Reveal travel needs a product or narrative context.",
            ))
        elif travel is None or not _in_band(abs(travel), *REVEAL_TRAVEL_BANDS_PX[context]):
            low, high = REVEAL_TRAVEL_BANDS_PX[context]
            issues.append(_issue(
                "reveal-travel-out-of-band",
                f"{context} reveal travel must sit in {low:g}–{high:g}px.",
            ))
    if "text_blur_px" in spec or "text_blur_end_px" in spec:
        if "text_blur_px" in spec:
            start = _number(spec.get("text_blur_px"))
            if start is None or not _in_band(start, *TEXT_BLUR_PX_BAND):
                issues.append(_issue(
                    "text-blur-out-of-band",
                    "Text blur reveal starts in 4–10px and resolves to 0px.",
                ))
        end = _number(spec.get("text_blur_end_px", 0))
        if end is None or abs(end) > 1e-9:
            issues.append(_issue(
                "text-blur-end-not-zero",
                "Text blur must resolve to 0px. A soft final frame leaves the headline illegible.",
            ))
    hover = spec.get("hover")
    if isinstance(hover, dict):
        scale = _number(hover.get("scale")) if "scale" in hover else None
        tilt = _number(hover.get("tilt_deg")) if "tilt_deg" in hover else None
        hover_travel = _number(hover.get("travel_px")) if "travel_px" in hover else None
        if (scale is not None and not scale < HOVER_SCALE_CAP) or (
            tilt is not None and not abs(tilt) < HOVER_TILT_CAP_DEG
        ) or (hover_travel is not None and not abs(hover_travel) < HOVER_TRAVEL_CAP_PX):
            issues.append(_issue(
                "hover-cap-exceeded",
                "Magnetic hover must stay under scale 1.03, tilt 4deg, and 16px of travel.",
            ))
    if "parallax_viewport_fraction" in spec:
        parallax = _number(spec.get("parallax_viewport_fraction"))
        if parallax is None or not abs(parallax) < PARALLAX_VIEWPORT_CAP:
            issues.append(_issue(
                "parallax-cap-exceeded",
                "Parallax must stay under 5% of viewport travel.",
            ))
    if "reveal_visible_fraction" in spec:
        visible = _fraction(spec.get("reveal_visible_fraction"))
        if visible is None or not _in_band(visible, *REVEAL_VISIBLE_FRACTION_BAND):
            issues.append(_issue(
                "reveal-trigger-out-of-band",
                "A reveal triggers at 20–30% visible, or when its top hits 82% of the viewport.",
            ))
    if "reveal_top_viewport_fraction" in spec:
        top = _fraction(spec.get("reveal_top_viewport_fraction"))
        if top is None or abs(top - REVEAL_TOP_VIEWPORT_FRACTION) > 1e-3:
            issues.append(_issue(
                "reveal-trigger-out-of-band",
                "The reveal line is the element top at 82% of the viewport.",
            ))
    surface = re.sub(r"\s+", " ", str(spec.get("surface") or "").strip().lower().replace("_", " ").replace("-", " "))
    scope = re.sub(r"[\s_]+", " ", str(spec.get("stagger_scope") or "").strip().lower().replace("-", " "))
    every_card = spec.get("stagger_every_card") is True or scope in {"every card", "all cards"}
    if every_card and (surface in {"utility", "utility page", "operate", "utility heavy"} or "utility" in surface):
        issues.append(_issue(
            "utility-card-stagger",
            "A utility or operate surface must not stagger every card. Stagger a focal cluster only.",
        ))
    reduced = spec.get("reduced_motion")
    if isinstance(reduced, dict):
        mode = str(reduced.get("mode") or "").strip().lower().replace("_", "-")
        hidden = bool(reduced.get("initial_state_hidden") or reduced.get("initial_hidden"))
        visible_flag = reduced.get("content_visible")
        visible = (not hidden) if visible_flag is None else bool(visible_flag)
        duration_value = reduced.get("duration_ms", reduced.get("duration"))
        collapsed = False
        if isinstance(duration_value, str) and "ms" in duration_value.lower():
            match = re.search(r"([\d.]+)\s*ms", duration_value.lower())
            collapsed = bool(match and float(match.group(1)) <= 1)
        else:
            duration_number = _number(duration_value) if duration_value is not None else None
            collapsed = duration_number is not None and duration_number <= 1
        designed = mode in {"designed-still", "designed-still-frame", "still", "designed-still-frame"}
        if designed and visible and not hidden:
            pass
        elif collapsed and hidden and not designed:
            issues.append(_issue(
                "fake-reduced-motion",
                "A 0.01ms duration collapse of a hidden initial state is not reduced motion. Render a designed still frame.",
            ))
        elif designed and hidden and not visible:
            issues.append(_issue(
                "fake-reduced-motion",
                "The reduced-motion frame is still the hidden initial state. Render the designed still frame.",
            ))
        elif collapsed and hidden:
            issues.append(_issue(
                "fake-reduced-motion",
                "A 0.01ms duration collapse of a hidden initial state is not reduced motion. Render a designed still frame.",
            ))
    scroll_linked = spec.get("scroll_linked") is True or str(spec.get("trigger") or "").lower() in {
        "scroll", "scrub", "scrolltrigger",
    } or spec.get("on") == "scroll"
    if scroll_linked:
        properties = _name_list(spec.get("animated_properties")) + _name_list(spec.get("properties"))
        layout_props = [name for name in properties if name in LAYOUT_SCROLL_PROPERTIES]
        if layout_props:
            issues.append(_issue(
                "layout-scroll-property",
                "Scroll-linked motion must not animate layout properties "
                f"({', '.join(layout_props)}). Use transform and opacity.",
            ))
    runtime = spec.get("runtime")
    if isinstance(runtime, dict):
        _check_runtime(runtime, issues)
    waived: list[str] = []
    accepted = _documented(spec.get("exception"))
    if accepted:
        kept: list[dict[str, Any]] = []
        for item in issues:
            if item["code"] in WAIVABLE_MOTION_CODES:
                waived.append(item["code"])
            else:
                kept.append(item)
        issues = kept
    return _finish(issues, exception_accepted=accepted, waived_codes=waived)


def _check_runtime(runtime: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    limit = 1 / 30
    step = _number(runtime.get("dt")) if "dt" in runtime else _number(runtime.get("raw_dt"))
    if step is not None and step > limit + 1e-9:
        issues.append(_issue("dt-unclamped", "Integration dt must be clamped to <= 1/30s."))
    raw = _number(runtime.get("raw_dt")) if "raw_dt" in runtime else None
    used = _number(runtime.get("dt")) if "dt" in runtime else None
    if used is not None and raw is not None and used > raw + 1e-9:
        issues.append(_issue("dt-unclamped", "The clamped dt cannot be larger than the raw frame step."))
    pixel_ratio = None
    for key in ("device_pixel_ratio", "devicePixelRatio", "dpr"):
        if key in runtime:
            pixel_ratio = _number(runtime.get(key))
            break
    if pixel_ratio is not None and pixel_ratio > 2 + 1e-9:
        issues.append(_issue("dpr-above-cap", "devicePixelRatio must be capped at <= 2."))
    hidden = runtime.get("document_hidden") is True or runtime.get("documentHidden") is True
    offscreen = runtime.get("canvas_offscreen") is True or runtime.get("canvasOffscreen") is True
    paused = runtime.get("paused") is True or runtime.get("rendering") is False
    if (hidden or offscreen) and not paused:
        issues.append(_issue(
            "runtime-not-paused",
            "Pause rendering when document.hidden or the canvas is offscreen.",
        ))
    if offscreen:
        if "offscreen_running_animations" in runtime:
            running = runtime.get("offscreen_running_animations")
        else:
            running = runtime.get("offscreenRunningAnimations") if "offscreenRunningAnimations" in runtime else None
        if running is None or int(running) != 0:
            issues.append(_issue(
                "offscreen-animations-running",
                "Offscreen running animations must be 0.",
            ))
    if "ablation_order" in runtime:
        raw_order = runtime.get("ablation_order")
        normalized = tuple(_norm_step(str(step_name)) for step_name in raw_order) if isinstance(raw_order, (list, tuple)) else tuple()
        if normalized != PROFILING_ABLATION_ORDER:
            issues.append(_issue(
                "ablation-order",
                "Profiling ablation order is lower DPR -> disable post-processing -> freeze shadows -> "
                "disable particles -> hide groups -> swap LOD -> replace materials.",
            ))


def _active_chapter_index(progress: float, chapter_count: int) -> int:
    count = int(chapter_count)
    if count <= 1:
        return 0
    if progress >= 1:
        return count - 1
    gap = 1.0 / (count - 1)
    index = 0
    for step in range(1, count):
        threshold = (step - 1 + CHAPTER_FLIP_PROGRESS) * gap
        if progress + 1e-9 >= threshold:
            index = step
        else:
            break
    return index


def _chapter_hidden(chapter: dict[str, Any]) -> bool:
    if chapter.get("hidden") is True:
        return True
    if str(chapter.get("visibility") or "").lower() == "hidden":
        return True
    opacity = chapter.get("opacity", 1)
    number = _number(opacity)
    return number is not None and number == 0


def _chapter_inert(chapter: dict[str, Any]) -> bool:
    if "inert" not in chapter:
        return False
    value = chapter.get("inert")
    if value is False or value is None:
        return False
    if isinstance(value, str) and value.strip().lower() in {"false", "0", "no"}:
        return False
    return True


def _smooth_during_capture(chapter: dict[str, Any]) -> bool:
    capturing = chapter.get("capturing") is True or chapter.get("capture") is True or chapter.get("programmatic_jump") is True
    if str(chapter.get("role") or "").lower() == "capture":
        capturing = True
    if not capturing:
        return False
    for key in ("scroll_behavior", "scrollBehavior"):
        if "smooth" in str(chapter.get(key) or "").lower():
            return True
    css = str(chapter.get("css") or chapter.get("html_css") or "").lower()
    return "scroll-behavior" in css and "smooth" in css


def _scene_signature(progress: float, index: int, chapter_count: int, chapters: list[dict[str, Any]]) -> str:
    ids: list[str] = []
    for chapter in chapters:
        role = str(chapter.get("role") or "").lower()
        if role in {"capture", "document", "playback"} or "id" not in chapter:
            continue
        ids.append(str(chapter["id"]))
    return f"progress={progress:.6f};index={index};chapters={int(chapter_count)};ids={','.join(ids)}"


def evaluate_scroll_chapter_state(
    scroll_y: float,
    scroll_height: float,
    inner_height: float,
    chapter_count: int,
    chapters_dom: list[dict],
) -> dict[str, Any]:
    """Compute live scroll progress and the chapter index that flips at 0.39.

    The scene signature ignores navigation direction, so forward scroll, reverse
    scroll, a direct anchor jump, and a reload at the same depth match.
    """
    issues: list[dict[str, Any]] = []
    try:
        scroll_y_f = float(scroll_y)
        scroll_height_f = float(scroll_height)
        inner_height_f = float(inner_height)
        count = int(chapter_count)
    except (TypeError, ValueError):
        return _finish(
            [_issue("invalid-scroll-geometry", "Scroll position, heights, and chapter count must be numeric.")],
            progress=0.0,
            normalized_progress=0.0,
            active_index=0,
            scene_signature="",
            played_transitions=[],
            tracks=[],
            cadence=_scene_cadence(),
        )
    if inner_height_f <= 0 or scroll_height_f < 0 or count < 1:
        issues.append(_issue("invalid-viewport", "Progress needs a positive live viewport height and at least one chapter."))
        progress = 0.0
        count = max(count, 1)
    else:
        travel = scroll_height_f - inner_height_f
        progress = 0.0 if travel <= 0 else min(1.0, max(0.0, scroll_y_f / travel))
    index = _active_chapter_index(progress, count)
    chapters = list(chapters_dom or [])
    targets: list[int] = []
    tracks: list[dict[str, Any]] = []
    for position, chapter in enumerate(chapters):
        if not isinstance(chapter, dict):
            issues.append(_issue("invalid-chapter", f"Chapter entry {position} must be an object."))
            continue
        role = str(chapter.get("role") or "").lower()
        if role not in {"capture", "document", "playback"} and _chapter_hidden(chapter) and not _chapter_inert(chapter):
            issues.append(_issue(
                "hidden-chapter-not-inert",
                f"Hidden chapter {chapter.get('id', position)} must set inert so offscreen controls cannot trap keyboard focus.",
            ))
        if _smooth_during_capture(chapter):
            issues.append(_issue(
                "smooth-scroll-during-capture",
                "Disable scroll-behavior: smooth on html during programmatic and capture jumps so screenshots do not land mid-transition.",
                severity="warning",
            ))
        if "scene_weight_vh" in chapter:
            weight = _number(chapter.get("scene_weight_vh"))
            if weight is None or not _in_band(weight, *SCENE_WEIGHT_VH_BAND):
                if not _documented(chapter.get("exception")):
                    issues.append(_issue(
                        "scene-weight-out-of-band",
                        "Scene weight must stay inside 0.7–1.8 viewport heights unless the brief records an exception.",
                    ))
        if "span" in chapter:
            span = _number(chapter.get("span"))
            if span is not None:
                track = (span + 1.0) * 100.0
                if abs(track - round(track)) < 1e-9:
                    track = int(round(track))
                tracks.append({"id": chapter.get("id"), "span": span, "track_vh": track})
        if "fast_skip_to" in chapter:
            target = _number(chapter.get("fast_skip_to"))
            if target is None:
                issues.append(_issue("invalid-fast-skip", "fast_skip_to must be a chapter index."))
            else:
                targets.append(int(target))
    played = [max(targets)] if targets else [index]
    return _finish(
        issues,
        progress=progress,
        normalized_progress=progress,
        active_index=index,
        scene_signature=_scene_signature(progress, index, count, [item for item in chapters if isinstance(item, dict)]),
        played_transitions=played,
        tracks=tracks,
        cadence=_scene_cadence(),
        inner_height=inner_height_f,
        scroll_y=scroll_y_f,
        scroll_height=scroll_height_f,
    )


def _scene_cadence() -> dict[str, Any]:
    return {
        "dwell_screens": SCENE_DWELL_SCREENS,
        "move_screens": SCENE_MOVE_SCREENS,
        "scene_weight_vh": [SCENE_WEIGHT_VH_BAND[0], SCENE_WEIGHT_VH_BAND[1]],
        "track_rule": "(span + 1) * 100vh",
        "flip_progress": CHAPTER_FLIP_PROGRESS,
    }


def _css_px(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"\d+(?:\.\d+)?", str(value))
    return float(match.group(0)) if match else None


def _cta_verb(cta: str) -> str:
    match = re.search(r"[a-z0-9]+", cta.lower())
    return match.group(0) if match else ""


def _row_list(plan: dict[str, Any], keys: tuple[str, ...]) -> list[Any] | None:
    for key in keys:
        if key in plan:
            value = plan.get(key)
            if isinstance(value, (list, tuple)):
                return list(value)
            return []
    return None


def _faq_blob(pricing: dict[str, Any]) -> str:
    raw = pricing.get("faq_topics", pricing.get("faq", []))
    parts: list[str] = []
    if isinstance(raw, dict):
        raw = list(raw.keys()) + [str(value) for value in raw.values()]
    if isinstance(raw, str):
        raw = [raw]
    for item in raw or []:
        if isinstance(item, dict):
            parts.extend(str(item.get(key) or "") for key in ("topic", "question", "title"))
        else:
            parts.append(str(item))
    blob = " ".join(parts).lower()
    blob = re.sub(r"\s*/\s*", "/", blob)
    return re.sub(r"\s+", " ", blob)


def evaluate_pricing_contract(pricing: dict) -> dict[str, Any]:
    """Enforce peer-plan count, row bands, CTA verb, 390px stacking, FAQ, and indexing."""
    if not isinstance(pricing, dict):
        return _finish([_issue("invalid-pricing-spec", "Pricing spec must be an object.")], plan_count=0, cta_verbs=[])
    issues: list[dict[str, Any]] = []
    plans = pricing.get("peer_plans", pricing.get("plans"))
    if not isinstance(plans, list) or not plans:
        issues.append(_issue("missing-plans", "Pricing needs at least one peer plan."))
        plans = []
    exception = pricing.get("peer_plan_exception") or pricing.get("plan_count_exception") or pricing.get("exception")
    if len(plans) > MAX_PEER_PLANS and not _documented(exception):
        issues.append(_issue(
            "too-many-plans",
            "At most 3 peer plans are allowed unless the brief records why another plan is a real buying path.",
        ))
    verbs: list[str] = []
    highlighted = 0
    for index, plan in enumerate(plans):
        if not isinstance(plan, dict):
            issues.append(_issue("invalid-plan", f"Plan {index + 1} must be an object."))
            continue
        label = str(plan.get("name") or f"plan {index + 1}")
        if _flag(plan.get("highlighted")) or _flag(plan.get("recommended")):
            highlighted += 1
        limits = _row_list(plan, ("limits", "quota_rows", "limit_rows", "quotas"))
        features = _row_list(plan, ("features", "included_features", "feature_rows"))
        if limits is None:
            issues.append(_issue("missing-limit-rows", f"{label} is missing its 3–6 quota/limit rows."))
        elif not PLAN_ROW_BAND[0] <= len(limits) <= PLAN_ROW_BAND[1]:
            issues.append(_issue(
                "limit-row-count",
                f"{label} has {len(limits)} quota/limit rows; the band is 3–6.",
            ))
        if features is None:
            issues.append(_issue("missing-feature-rows", f"{label} is missing its 3–6 included feature rows."))
        elif not PLAN_ROW_BAND[0] <= len(features) <= PLAN_ROW_BAND[1]:
            issues.append(_issue(
                "feature-row-count",
                f"{label} has {len(features)} included feature rows; the band is 3–6.",
            ))
        verb = _cta_verb(str(plan.get("cta") or plan.get("action") or ""))
        if not verb:
            issues.append(_issue("missing-cta", f"{label} is missing a plan CTA."))
        else:
            verbs.append(verb)
    if plans and highlighted != 1:
        issues.append(_issue(
            "highlighted-plan-count",
            f"Exactly one plan is highlighted. This spec highlights {highlighted}.",
        ))
    if len(set(verbs)) > 1:
        issues.append(_issue(
            "cta-verb-mismatch",
            f"Peer-plan CTAs must share one action verb. Found {', '.join(verbs)}.",
        ))
    toggle = pricing.get("billing_toggle", pricing.get("billing"))
    if not isinstance(toggle, dict) or not _flag(toggle.get("monthly")) or not _flag(toggle.get("annual")):
        issues.append(_issue(
            "missing-billing-toggle",
            "Monthly and annual billing need an explicit toggle and savings math.",
        ))
    else:
        savings = toggle.get("savings_math", toggle.get("savings"))
        numeric_savings = isinstance(savings, (int, float)) and not isinstance(savings, bool)
        written_savings = isinstance(savings, str) and bool(re.search(r"\d", savings))
        if not numeric_savings and not written_savings:
            issues.append(_issue(
                "missing-savings-math",
                "The annual billing state must show explicit savings math, not only the word save.",
            ))
    mobile = pricing.get("mobile") if isinstance(pricing.get("mobile"), dict) else {}
    width = _css_px(mobile.get("width", mobile.get("viewport")))
    layout = str(mobile.get("layout") or "").strip().lower().replace("_", "-").replace(" ", "-")
    overflow = mobile.get("horizontal_overflow", mobile.get("horizontalOverflow"))
    if width is None:
        issues.append(_issue("missing-mobile-layout", "Pricing must declare the 390px layout."))
    elif width == 390 and (layout in _HORIZONTAL_PRICING_LAYOUTS or overflow is True or layout not in _STACKED_PRICING_LAYOUTS):
        issues.append(_issue(
            "mobile-horizontal-scroll",
            "At 390px, plans reflow to stacked cards. A horizontal-scrolling comparison table fails.",
        ))
    blob = _faq_blob(pricing)
    for topic in REQUIRED_PRICING_FAQ_TOPICS:
        if topic not in blob:
            issues.append(_issue("missing-faq-topic", f"Pricing FAQ is missing {topic}."))
    landing = pricing.get("landing") if isinstance(pricing.get("landing"), dict) else {}
    indexing = pricing.get("indexing") if isinstance(pricing.get("indexing"), dict) else {}
    merged = {**indexing, **landing}
    kind = str(merged.get("kind") or merged.get("offer_kind") or pricing.get("offer_kind") or pricing.get("kind") or "").lower()
    time_bound = bool(merged.get("time_bound") or pricing.get("time_bound"))
    robots = str(merged.get("robots") or pricing.get("robots") or "").lower()
    campaign = "campaign" in kind or "time-bound" in kind or "time bound" in kind or time_bound
    if campaign and "noindex" not in robots:
        issues.append(_issue(
            "campaign-missing-noindex",
            "A time-bound campaign is noindex. An indexable campaign page fails.",
        ))
    elif "evergreen" in kind and "noindex" in robots:
        issues.append(_issue(
            "evergreen-not-indexable",
            "An evergreen offer is indexable. noindex is for a time-bound campaign.",
        ))
    return _finish(
        issues,
        plan_count=len(plans),
        cta_verbs=verbs,
        exception_accepted=bool(len(plans) > MAX_PEER_PLANS and _documented(exception)),
    )


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", text.lower())


def _text_parts(payload: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    copy = payload.get("copy")
    if isinstance(copy, str) and copy.strip():
        parts.append(copy)
    claims = payload.get("claims") or []
    if isinstance(claims, str):
        claims = [claims]
    if isinstance(claims, (list, tuple)):
        parts.extend(str(claim) for claim in claims if str(claim).strip())
    return parts


def _generic_gram(gram: str) -> bool:
    content = [word for word in gram.split() if word not in _STOPWORDS]
    if not content:
        return True
    return all(word in _GENERIC_GRAM_WORDS for word in content)


def _gram_set(payload: dict[str, Any]) -> set[str]:
    grams: set[str] = set()
    for text in _text_parts(payload):
        words = _words(text)
        if len(words) < 8:
            continue
        for index in range(len(words) - 7):
            gram = " ".join(words[index:index + 8])
            if not _generic_gram(gram):
                grams.add(gram)
    return grams


def _canon_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _unusual_keys(payload: dict[str, Any]) -> set[str]:
    keys: set[str] = set()

    def add(raw: str, *, currency: bool = False, percent: bool = False) -> None:
        number = _number(raw.replace("$", "").replace("%", ""))
        if number is None:
            return
        unusual = currency or percent
        if not unusual and abs(number - round(number)) < 1e-9:
            integer = int(round(number))
            if integer in _COMMON_NUMBERS or 1900 <= integer <= 2100:
                return
            unusual = True
        elif not unusual:
            unusual = True
        if unusual:
            keys.add(_canon_number(number))

    for text in _text_parts(payload):
        for match in re.findall(r"\$?\d+(?:\.\d+)?%?", text):
            add(match, currency=match.startswith("$"), percent=match.endswith("%"))
    for item in payload.get("numbers") or []:
        add(str(item), currency=str(item).strip().startswith("$"), percent=str(item).strip().endswith("%"))
    for item in payload.get("prices") or []:
        add(str(item), currency=True)
    return keys


def _brands(payload: dict[str, Any]) -> set[str]:
    raw = payload.get("brand_names") or []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return set()
    generic = {"learn more", "get started", "contact us", "the", "app", "product"}
    return {
        str(name).strip().lower()
        for name in raw
        if str(name).strip() and str(name).strip().lower() not in generic
    }


def _frame_sequence(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("frames") or payload.get("crops") or []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return []
    return [str(item).strip().lower() for item in raw if str(item).strip()]


def _specific_layout(payload: dict[str, Any]) -> tuple[str, ...]:
    raw = payload.get("layout_traits") or []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return tuple()
    return tuple(
        str(item).strip().lower()
        for item in raw
        if str(item).strip() and str(item).strip().lower() not in _GENERIC_TRAITS
    )


def _trait_set(payload: dict[str, Any], key: str) -> set[str]:
    raw = payload.get(key) or []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return set()
    return {
        str(item).strip().lower()
        for item in raw
        if str(item).strip() and str(item).strip().lower() not in _GENERIC_TRAITS
    }


def _normalize_numbers(text: str) -> str:
    return re.sub(r"\$?\d+(?:\.\d+)?%?", "#", text).lower()


def _structure_copied(candidate: dict[str, Any], reference: dict[str, Any]) -> bool:
    left = _specific_layout(candidate)
    right = _specific_layout(reference)
    if len(left) >= 2 and left == right:
        return True
    signature_left = str(candidate.get("layout_signature") or "").strip().lower()
    signature_right = str(reference.get("layout_signature") or "").strip().lower()
    if signature_left and signature_left == signature_right:
        return True
    copy_left = _normalize_numbers(" ".join(_text_parts(candidate)))
    copy_right = _normalize_numbers(" ".join(_text_parts(reference)))
    if len(copy_left) >= 40 and len(copy_right) >= 40 and SequenceMatcher(None, copy_left, copy_right).ratio() >= 0.9:
        return True
    return False


def _price_points(payload: dict[str, Any]) -> list[float]:
    amounts: list[float] = []
    raw_prices = payload.get("prices") or []
    if isinstance(raw_prices, (int, float)) and not isinstance(raw_prices, bool):
        raw_prices = [raw_prices]
    if isinstance(raw_prices, (list, tuple)):
        for item in raw_prices:
            number = _number(item)
            if number is not None:
                amounts.append(number)
    for text in _text_parts(payload):
        amounts.extend(float(match) for match in re.findall(r"\$\s*(\d+(?:\.\d+)?)", text))
    return amounts


def _money_label(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"${int(round(value))}"
    return f"${value:.2f}"


def _bytes_token(payload: dict[str, Any]) -> str | None:
    value = payload.get("bytes", payload.get("asset_bytes"))
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        items = [str(item).strip() for item in value if str(item).strip()]
        return "|".join(items) or None
    text = str(value).strip()
    return text or None


def _asset_ids(payload: dict[str, Any]) -> tuple[str, ...]:
    raw = payload.get("asset_ids", payload.get("assets", []))
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return tuple()
    items = tuple(str(item).strip() for item in raw if str(item).strip())
    if items and all(item.lower() in _GENERIC_ASSETS for item in items):
        return tuple()
    return items


def _conventions(payload: dict[str, Any]) -> list[str]:
    found: list[str] = []
    palette = str(payload.get("palette") or "").lower()
    if "black-and-white" in palette or "black and white" in palette:
        found.append("black-and-white palette")
    if payload.get("accent_count") == 1 or payload.get("single_accent") is True:
        found.append("single accent")
    order = payload.get("section_order") or []
    if isinstance(order, str):
        order = [order]
    normalized = [str(item).strip().lower() for item in order] if isinstance(order, (list, tuple)) else []
    if normalized and normalized[0] == "hero" and "faq" in normalized:
        found.append("hero+FAQ order")
    motion = re.sub(r"\s+", " ", str(payload.get("motion") or "").lower().replace("_", " ").replace("-", " ")).strip()
    if motion in {"fade", "standard fade"}:
        found.append("standard fade")
    copy = str(payload.get("copy") or "").strip().lower().rstrip(".")
    if copy == "learn more":
        found.append("Learn more")
    return found


def _finding(code: str, rung: int, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"code": code, "rung": rung, "severity": "high", "message": message}
    payload.update(extra)
    return payload


def evaluate_originality_check(candidate: dict, reference: dict) -> dict[str, Any]:
    """Apply the five-rung originality ladder and reject nudged-number copy fixes.

    Generic conventions (black-and-white, a single accent, hero+FAQ, a standard
    fade, and "Learn more") are reported as ignored exclusions, not findings.
    """
    if not isinstance(candidate, dict) or not isinstance(reference, dict):
        return _finish(
            [_issue("invalid-originality-input", "Originality check needs a candidate object and a reference object.")],
            severity="high",
            findings=[],
            false_positives_ignored=[],
            rungs=[],
            strongest_rung=0,
        )
    findings: list[dict[str, Any]] = []
    candidate_bytes = _bytes_token(candidate)
    reference_bytes = _bytes_token(reference)
    if candidate_bytes and candidate_bytes == reference_bytes:
        findings.append(_finding(
            "identical-bytes",
            1,
            "Candidate and reference share identical bytes.",
        ))
    candidate_assets = _asset_ids(candidate)
    reference_assets = _asset_ids(reference)
    if candidate_assets and candidate_assets == reference_assets:
        findings.append(_finding(
            "identical-assets",
            1,
            "Candidate and reference use the same asset identifiers.",
        ))
    shared_grams = sorted(_gram_set(candidate) & _gram_set(reference))
    if shared_grams:
        findings.append(_finding(
            "verbatim-copy",
            2,
            f"Verbatim copy/claims share an 8-word phrase: {shared_grams[0]}.",
        ))
    shared_numbers = sorted(_unusual_keys(candidate) & _unusual_keys(reference))
    if shared_numbers:
        findings.append(_finding(
            "unusual-number",
            3,
            "Brand names & unusual numbers overlap: " + ", ".join(shared_numbers) + ".",
        ))
    shared_brands = sorted(_brands(candidate) & _brands(reference))
    if shared_brands:
        findings.append(_finding(
            "brand-name",
            3,
            "Brand names & unusual numbers overlap: " + ", ".join(shared_brands) + ".",
        ))
    frames = _frame_sequence(candidate)
    reference_frames = _frame_sequence(reference)
    distinctive = [frame for frame in frames if frame not in _GENERIC_FRAMES]
    if frames and frames == reference_frames and len(frames) >= 3 and len(distinctive) >= 2:
        findings.append(_finding(
            "frame-sequence",
            4,
            "Distinctive crop/frame sequence matches the reference.",
        ))
    shared_layout = _trait_set(candidate, "layout_traits") & _trait_set(reference, "layout_traits")
    shared_motion = _trait_set(candidate, "motion_traits") & _trait_set(reference, "motion_traits")
    if len(shared_layout) >= 2 and len(shared_motion) >= 2:
        findings.append(_finding(
            "multi-trait-cluster",
            5,
            "Multi-trait layout+motion cluster matches the reference.",
        ))
    if _structure_copied(candidate, reference):
        pairs = []
        for left in _price_points(reference):
            for right in _price_points(candidate):
                if 1e-9 < abs(left - right) <= 2 + 1e-9:
                    pairs.append((left, right))
        if pairs:
            source, nudged = pairs[0]
            findings.append(_finding(
                "nudged-number-copy-fix",
                3,
                f"Copied structure keeps a nudged number ({_money_label(source)} -> {_money_label(nudged)}). "
                "Nudging a copied price is not an originality fix.",
                fix_pattern=True,
            ))
    ignored_candidate = _conventions(candidate)
    ignored_reference = set(_conventions(reference))
    ignored = [label for label in ignored_candidate if label in ignored_reference]
    rungs = sorted({int(item["rung"]) for item in findings})
    severity = "high" if findings else "none"
    result = _finish(issues=[], severity=severity, findings=findings, false_positives_ignored=ignored, rungs=rungs, strongest_rung=(rungs[0] if rungs else 0))
    if findings:
        result["status"] = "fail"
        result["ok"] = False
        result["issues"] = [
            _issue(item["code"], item["message"])
            for item in findings
        ]
    return result


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
        print(f"{payload['status']}: blocking={payload.get('blocking_count', 0)}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") in {"pass", "warn", "dry_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
