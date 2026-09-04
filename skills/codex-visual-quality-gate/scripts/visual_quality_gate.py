#!/usr/bin/env python3
"""Mechanical visual quality gate with optional local Node detector."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run mechanical visual checks on UI source. Dry-run by default; never installs Node packages."
    )
    parser.add_argument("--project-root", required=True, help="Project root to confine scans and writes")
    parser.add_argument("--files", default="", help="Optional comma-separated relative files; default is a UI scan")
    parser.add_argument("--apply", action="store_true", help="Write review JSON under .codex/design/reviews")
    parser.add_argument("--allow-network", action="store_true", help="Unused; detector never installs or fetches packages")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--max-rounds", type=int, default=2, help="Documented inspect/fix round limit")
    return parser.parse_args()


def confined(project_root: Path, relative: str | Path) -> Path:
    root = project_root.expanduser().resolve()
    target = (root / Path(str(relative))).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"path escapes project root: {relative}")
    return target


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
            message="Default or generic font-family found; treat as mechanical cliché evidence, not taste.",
            blocking=False,
        )
    if GRADIENT_CLICHE_RE.search(text):
        add_finding(
            findings,
            check="gradient_cliche",
            severity="warning",
            path=path,
            project_root=project_root,
            message="Blue/purple gradient cliché detected in source.",
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
            message=f"{len(unique_spacing)} distinct px spacing/radius values; likely no scale.",
            blocking=False,
        )
    if len(CTA_RE.findall(text)) >= 2:
        add_finding(
            findings,
            check="competing_ctas",
            severity="error",
            path=path,
            project_root=project_root,
            message="Multiple primary CTA markers in one file.",
            blocking=True,
        )
    if len(CARD_RE.findall(text)) >= 6:
        add_finding(
            findings,
            check="card_repetition",
            severity="warning",
            path=path,
            project_root=project_root,
            message="Repeated card markers; possible card soup.",
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
            severity="error",
            path=path,
            project_root=project_root,
            message="Motion without prefers-reduced-motion coverage.",
            blocking=True,
        )
    if path.suffix.lower() in {".jsx", ".tsx", ".vue"} and re.search(r"<button|onClick|type=['\"]submit['\"]", text):
        if not STATE_RE.search(text):
            add_finding(
                findings,
                check="missing_states",
                severity="error",
                path=path,
                project_root=project_root,
                message="Interactive UI without loading/disabled/empty/error state evidence.",
                blocking=True,
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
    if shutil.which("npx") is None:
        return {"status": "DEGRADED", "reason": "no browser runner advertised; host must supply screenshots"}
    return {"status": "unknown", "reason": "browser capture is host-owned; Python core does not fake screenshots"}


def build_report(project_root: Path, files: list[str], apply: bool, max_rounds: int) -> dict[str, Any]:
    ui_files = [path for path in iter_ui_files(project_root, files) if path.exists()]
    findings: list[dict[str, Any]] = []
    for path in ui_files:
        scan_file(path, project_root, findings)
    ux = run_ux_audit(project_root)
    detector = run_optional_detector() if detector_status().get("status") == "available" else detector_status()
    blocking = [item for item in findings if item.get("blocking")]
    review = browser_capability()
    written = ""
    payload = {
        "status": "fail" if blocking else "pass",
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
        "max_inspect_fix_rounds": max_rounds,
        "required_viewports": ["desktop", "mobile"],
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
        payload = build_report(project_root, files, args.apply, args.max_rounds)
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
