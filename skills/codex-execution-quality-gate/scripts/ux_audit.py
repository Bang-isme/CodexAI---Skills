#!/usr/bin/env python3
"""
Static UX audit for frontend codebases without launching a browser.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple


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
    ".yarn",
}
UI_EXTENSIONS = {".jsx", ".tsx", ".vue", ".html"}
STATE_EXTENSIONS = {".jsx", ".tsx", ".vue"}
STYLE_EXTENSIONS = {".css", ".scss"}

ASYNC_PATTERN = re.compile(r"\b(fetch\s*\(|axios\.[a-z]+|await\s+|useQuery\s*\(|queryClient\.)", re.IGNORECASE)
LOADING_HINT_PATTERN = re.compile(r"\b(loading|isLoading|spinner|skeleton|pending|setLoading)\b", re.IGNORECASE)
ERROR_HANDLER_PATTERN = re.compile(r"\b(try\s*{|catch\s*\(|\.catch\s*\()", re.IGNORECASE)
ERROR_UI_PATTERN = re.compile(
    r"(error\s*&&|setError\s*\(|errorMessage|<Error\b|role\s*=\s*['\"]alert['\"]|toast\.error|showError)",
    re.IGNORECASE,
)
EMPTY_GUARD_PATTERN = re.compile(
    r"(\.length\s*===\s*0|\.length\s*>\s*0|!\s*[A-Za-z0-9_.]+\s*\.length|empty\s*state|No\s+[A-Za-z])",
    re.IGNORECASE,
)
VALIDATION_PATTERN = re.compile(
    r"\b(required|pattern=|minLength=|maxLength=|validate|react-hook-form|yup|zod|vee-validate|onInvalid|aria-invalid)\b",
    re.IGNORECASE,
)
BUTTON_PATTERN = re.compile(r"<button\b[^>]*(onClick|@click)[^>]*>", re.IGNORECASE)
IMG_TAG_PATTERN = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
ANCHOR_PATTERN = re.compile(r"<a\b[^>]*>", re.IGNORECASE)
CUSTOM_INTERACTIVE_PATTERN = re.compile(r"<(div|span|li|p)\b[^>]*(onClick|@click)[^>]*>", re.IGNORECASE)
CSS_BLOCK_PATTERN = re.compile(r"(?P<selector>[^{]+)\{(?P<body>[^{}]*)\}", re.DOTALL)
SIZE_PATTERN = re.compile(r"(?P<name>width|height|min-width|min-height)\s*:\s*(?P<value>\d+(?:\.\d+)?)px", re.IGNORECASE)
INTERACTIVE_SELECTOR_PATTERN = re.compile(
    r"(\bbutton\b|\ba\b|\binput\b|\bselect\b|\btextarea\b|\.btn\b|\[role\s*=\s*['\"]?button['\"]?\])",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Run static UX audit checks.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python ux_audit.py --project-root <path>\n"

            "  python ux_audit.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--framework", choices=["react", "vue", "html"], default="", help="Framework override")
    return parser.parse_args()


def emit(payload: Dict[str, object], exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


def should_skip_dir(name: str) -> bool:
    return name.startswith(".") or name in SKIP_DIRS


def rel_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def line_for_index(text: str, index: int) -> int:
    return text.count("\n", 0, max(index, 0)) + 1


def first_line_for_pattern(pattern: re.Pattern, text: str) -> int:
    match = pattern.search(text)
    if not match:
        return 1
    return line_for_index(text, match.start())


def safe_read(path: Path, warnings: List[str]) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        warnings.append(f"Unable to read {path.as_posix()}: {exc}")
        return ""


def collect_files(project_root: Path) -> Tuple[List[Path], List[Path]]:
    ui_files: List[Path] = []
    style_files: List[Path] = []
    for current_root, dirs, names in os.walk(project_root):
        dirs[:] = [name for name in dirs if not should_skip_dir(name)]
        root_path = Path(current_root)
        for name in names:
            path = root_path / name
            ext = path.suffix.lower()
            if ext in UI_EXTENSIONS:
                ui_files.append(path)
            elif ext in STYLE_EXTENSIONS:
                style_files.append(path)
    return sorted(ui_files), sorted(style_files)


def detect_framework(ui_files: Sequence[Path]) -> str:
    has_vue = any(path.suffix.lower() == ".vue" for path in ui_files)
    has_react = any(path.suffix.lower() in {".jsx", ".tsx"} for path in ui_files)
    if has_vue:
        return "vue"
    if has_react:
        return "react"
    return "html"


def normalize_selector_base(selector: str) -> str:
    normalized = selector.strip()
    normalized = re.sub(r":{1,2}hover\b", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r":{1,2}focus-visible\b", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r":{1,2}focus\b", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def add_issue(
    issues: List[Dict[str, object]],
    seen: Set[Tuple[str, int, str, str]],
    rel_file: str,
    line: int,
    severity: str,
    check: str,
    message: str,
    suggestion: str,
) -> None:
    key = (rel_file, line, check, message)
    if key in seen:
        return
    seen.add(key)
    issues.append(
        {
            "file": rel_file,
            "line": line,
            "severity": severity,
            "check": check,
            "message": message,
            "suggestion": suggestion,
        }
    )


def scan_ui_file(path: Path, project_root: Path, issues: List[Dict[str, object]], seen: Set[Tuple[str, int, str, str]]) -> None:
    content = path.read_text(encoding="utf-8", errors="ignore")
    rel_file = rel_path(path, project_root)
    ext = path.suffix.lower()

    if ext in STATE_EXTENSIONS:
        has_async = ASYNC_PATTERN.search(content) is not None
        has_loading = LOADING_HINT_PATTERN.search(content) is not None
        if has_async and not has_loading:
            add_issue(
                issues,
                seen,
                rel_file,
                first_line_for_pattern(ASYNC_PATTERN, content),
                "critical",
                "missing_loading_state",
                "Async data fetching detected without loading UI state.",
                "Add a loading indicator (spinner/skeleton/message) while async work is pending.",
            )

        has_error_handler = ERROR_HANDLER_PATTERN.search(content) is not None
        has_error_ui = ERROR_UI_PATTERN.search(content) is not None
        if has_error_handler and not has_error_ui:
            add_issue(
                issues,
                seen,
                rel_file,
                first_line_for_pattern(ERROR_HANDLER_PATTERN, content),
                "critical",
                "missing_error_state",
                "Error handling logic exists but no error UI is rendered.",
                "Render a visible error state with user guidance and retry action.",
            )

        has_map = re.search(r"\.map\s*\(", content) is not None
        has_empty_guard = EMPTY_GUARD_PATTERN.search(content) is not None
        if has_map and not has_empty_guard:
            add_issue(
                issues,
                seen,
                rel_file,
                first_line_for_pattern(re.compile(r"\.map\s*\("), content),
                "warning",
                "missing_empty_state",
                "List rendering uses .map() without an empty-state branch.",
                "Add explicit empty-state UI for zero-item results.",
            )

    if re.search(r"<form\b|<input\b", content, re.IGNORECASE) and not VALIDATION_PATTERN.search(content):
        add_issue(
            issues,
            seen,
            rel_file,
            first_line_for_pattern(re.compile(r"<form\b|<input\b", re.IGNORECASE), content),
            "warning",
            "form_without_validation",
            "Form/input elements detected without visible validation rules.",
            "Add required/pattern/min/max or schema-based validation and inline messages.",
        )

    button_count = 0
    for match in BUTTON_PATTERN.finditer(content):
        tag = match.group(0)
        if re.search(r"\b(disabled|aria-disabled|:disabled)\b", tag, re.IGNORECASE):
            continue
        add_issue(
            issues,
            seen,
            rel_file,
            line_for_index(content, match.start()),
            "warning",
            "button_without_disabled_state",
            "Action button has click handler but no disabled state guard.",
            "Disable submit/action buttons while request is running or inputs are invalid.",
        )
        button_count += 1
        if button_count >= 3:
            break

    image_count = 0
    for match in IMG_TAG_PATTERN.finditer(content):
        tag = match.group(0)
        line = line_for_index(content, match.start())
        if not re.search(r"\balt\s*=", tag, re.IGNORECASE):
            add_issue(
                issues,
                seen,
                rel_file,
                line,
                "warning",
                "image_without_alt",
                "Image is missing alt text.",
                "Add meaningful alt text or alt=\"\" for decorative imagery.",
            )
        else:
            alt_match = re.search(r"\balt\s*=\s*([\"'])(.*?)\1", tag, re.IGNORECASE)
            if alt_match and not alt_match.group(2).strip():
                add_issue(
                    issues,
                    seen,
                    rel_file,
                    line,
                    "info",
                    "image_without_alt",
                    "Image alt attribute is empty.",
                    "Confirm this image is decorative; otherwise provide descriptive alt text.",
                )
        image_count += 1
        if image_count >= 5:
            break

    link_count = 0
    for match in ANCHOR_PATTERN.finditer(content):
        tag = match.group(0)
        line = line_for_index(content, match.start())
        href_match = re.search(r"\bhref\s*=\s*([\"'])(.*?)\1", tag, re.IGNORECASE)
        if not href_match:
            add_issue(
                issues,
                seen,
                rel_file,
                line,
                "warning",
                "link_without_href",
                "Anchor element has no href target.",
                "Use a real URL, route link component, or convert to a button for actions.",
            )
        else:
            href_value = href_match.group(2).strip().lower()
            if href_value in {"#", "javascript:void(0)", "javascript:void(0);"}:
                add_issue(
                    issues,
                    seen,
                    rel_file,
                    line,
                    "warning",
                    "link_without_href",
                    "Anchor uses placeholder href and may confuse navigation.",
                    "Replace placeholder href with a valid path or use a button for non-navigation actions.",
                )
        link_count += 1
        if link_count >= 5:
            break

    custom_count = 0
    for match in CUSTOM_INTERACTIVE_PATTERN.finditer(content):
        tag = match.group(0)
        if re.search(r"\b(role|aria-label|aria-labelledby|tabindex|tabIndex)\b", tag, re.IGNORECASE):
            continue
        add_issue(
            issues,
            seen,
            rel_file,
            line_for_index(content, match.start()),
            "critical",
            "missing_aria_labels",
            "Custom interactive element has click handler without role/aria-label support.",
            "Prefer <button>; otherwise add role, keyboard handlers, tabIndex, and aria-label.",
        )
        custom_count += 1
        if custom_count >= 3:
            break


def scan_style_file(path: Path, project_root: Path, issues: List[Dict[str, object]], seen: Set[Tuple[str, int, str, str]]) -> None:
    content = path.read_text(encoding="utf-8", errors="ignore")
    rel_file = rel_path(path, project_root)
    hover_bases: List[Tuple[str, int, str]] = []
    focus_bases: Set[str] = set()

    for block in CSS_BLOCK_PATTERN.finditer(content):
        selector_text = block.group("selector")
        body = block.group("body")
        start_line = line_for_index(content, block.start("selector"))

        selectors = [item.strip() for item in selector_text.split(",") if item.strip()]
        for selector in selectors:
            base = normalize_selector_base(selector)
            if ":hover" in selector:
                hover_bases.append((base, start_line, selector))
            if ":focus-visible" in selector:
                focus_bases.add(base)

        if INTERACTIVE_SELECTOR_PATTERN.search(selector_text):
            sizes: Dict[str, float] = {}
            for size_match in SIZE_PATTERN.finditer(body):
                sizes[size_match.group("name").lower()] = float(size_match.group("value"))
            width = sizes.get("width", sizes.get("min-width"))
            height = sizes.get("height", sizes.get("min-height"))
            too_small = False
            if width is not None and width < 44:
                too_small = True
            if height is not None and height < 44:
                too_small = True
            if too_small:
                add_issue(
                    issues,
                    seen,
                    rel_file,
                    start_line,
                    "info",
                    "touch_target_too_small",
                    "Interactive selector has touch target smaller than 44px.",
                    "Increase target size or min-size to at least 44x44px for touch accessibility.",
                )

    for base, line, selector in hover_bases:
        if base and base not in focus_bases:
            add_issue(
                issues,
                seen,
                rel_file,
                line,
                "warning",
                "missing_focus_visible",
                f"Hover style exists without matching focus-visible style for selector '{selector}'.",
                "Define :focus-visible styles for the same interactive selector.",
            )


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit(
            {
                "status": "error",
                "message": f"Project root does not exist or is not a directory: {project_root.as_posix()}",
            },
            exit_code=1,
        )

    warnings: List[str] = []
    ui_files, style_files = collect_files(project_root)
    framework = args.framework or detect_framework(ui_files)

    issues: List[Dict[str, object]] = []
    seen: Set[Tuple[str, int, str, str]] = set()

    for file_path in ui_files:
        scan_ui_file(file_path, project_root, issues, seen)
    for file_path in style_files:
        scan_style_file(file_path, project_root, issues, seen)

    by_severity = {"critical": 0, "warning": 0, "info": 0}
    for issue in issues:
        severity = str(issue.get("severity", "info"))
        by_severity[severity] = by_severity.get(severity, 0) + 1

    score = max(0, 100 - by_severity["critical"] * 10 - by_severity["warning"] * 3 - by_severity["info"] * 1)
    summary = (
        f"{len(issues)} UX issues: "
        f"{by_severity['critical']} critical, {by_severity['warning']} warnings, {by_severity['info']} info"
    )

    payload: Dict[str, object] = {
        "status": "audited",
        "framework": framework,
        "files_scanned": len(ui_files) + len(style_files),
        "total_issues": len(issues),
        "by_severity": by_severity,
        "issues": issues,
        "summary": summary,
        "score": score,
    }
    if warnings:
        payload["warnings"] = warnings
    emit(payload, exit_code=0)


if __name__ == "__main__":
    main()
