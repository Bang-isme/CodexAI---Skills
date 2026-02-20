#!/usr/bin/env python3
"""
Static accessibility checker for WCAG-oriented issues.
"""

from __future__ import annotations

import argparse
import json
import math
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
MARKUP_EXTENSIONS = {".html", ".jsx", ".tsx", ".vue"}
STYLE_EXTENSIONS = {".css", ".scss"}

IMAGE_PATTERN = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
DIV_HEADING_PATTERN = re.compile(
    r"<div\b[^>]*(class|className)\s*=\s*['\"][^'\"]*(heading|title|h1|h2|h3|h4|h5|h6)[^'\"]*['\"][^>]*>",
    re.IGNORECASE,
)
CUSTOM_CLICKABLE_PATTERN = re.compile(r"<(div|span|li|p)\b[^>]*(onClick|@click)[^>]*>", re.IGNORECASE)
ANCHOR_TEXT_PATTERN = re.compile(r"<a\b[^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
HTML_TAG_PATTERN = re.compile(r"<html\b[^>]*>", re.IGNORECASE)
FORM_CONTROL_PATTERN = re.compile(r"<(input|select|textarea)\b[^>]*>", re.IGNORECASE)
ID_PATTERN = re.compile(r"\bid\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
ROLE_PATTERN = re.compile(r"\brole\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
ARIA_ATTR_PATTERN = re.compile(r"\b(aria-[a-zA-Z-]+)\s*=", re.IGNORECASE)
CSS_BLOCK_PATTERN = re.compile(r"(?P<selector>[^{]+)\{(?P<body>[^{}]*)\}", re.DOTALL)
COLOR_DECL_PATTERN = re.compile(r"(?:^|;|\n)\s*color\s*:\s*([^;}{]+)", re.IGNORECASE)
BG_DECL_PATTERN = re.compile(r"(?:^|;|\n)\s*background(?:-color)?\s*:\s*([^;}{]+)", re.IGNORECASE)
FONT_SIZE_PATTERN = re.compile(r"font-size\s*:\s*([0-9]+(?:\.[0-9]+)?)(px|rem)", re.IGNORECASE)

VAGUE_LINK_TEXTS = {"click here", "read more", "here"}

VALID_ROLES = {
    "alert",
    "alertdialog",
    "application",
    "article",
    "banner",
    "button",
    "cell",
    "checkbox",
    "columnheader",
    "combobox",
    "complementary",
    "contentinfo",
    "definition",
    "dialog",
    "directory",
    "document",
    "feed",
    "figure",
    "form",
    "grid",
    "gridcell",
    "group",
    "heading",
    "img",
    "link",
    "list",
    "listbox",
    "listitem",
    "log",
    "main",
    "marquee",
    "math",
    "menu",
    "menubar",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "navigation",
    "none",
    "note",
    "option",
    "presentation",
    "progressbar",
    "radio",
    "radiogroup",
    "region",
    "row",
    "rowgroup",
    "rowheader",
    "scrollbar",
    "search",
    "searchbox",
    "separator",
    "slider",
    "spinbutton",
    "status",
    "switch",
    "tab",
    "table",
    "tablist",
    "tabpanel",
    "term",
    "textbox",
    "timer",
    "toolbar",
    "tooltip",
    "tree",
    "treegrid",
    "treeitem",
}

KNOWN_ARIA_ATTRS = {
    "aria-activedescendant",
    "aria-atomic",
    "aria-autocomplete",
    "aria-braillelabel",
    "aria-brailleroledescription",
    "aria-busy",
    "aria-checked",
    "aria-colcount",
    "aria-colindex",
    "aria-colindextext",
    "aria-colspan",
    "aria-controls",
    "aria-current",
    "aria-describedby",
    "aria-description",
    "aria-details",
    "aria-disabled",
    "aria-dropeffect",
    "aria-errormessage",
    "aria-expanded",
    "aria-flowto",
    "aria-grabbed",
    "aria-haspopup",
    "aria-hidden",
    "aria-invalid",
    "aria-keyshortcuts",
    "aria-label",
    "aria-labelledby",
    "aria-level",
    "aria-live",
    "aria-modal",
    "aria-multiline",
    "aria-multiselectable",
    "aria-orientation",
    "aria-owns",
    "aria-placeholder",
    "aria-posinset",
    "aria-pressed",
    "aria-readonly",
    "aria-relevant",
    "aria-required",
    "aria-roledescription",
    "aria-rowcount",
    "aria-rowindex",
    "aria-rowindextext",
    "aria-rowspan",
    "aria-selected",
    "aria-setsize",
    "aria-sort",
    "aria-valuemax",
    "aria-valuemin",
    "aria-valuenow",
    "aria-valuetext",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Run static accessibility checks.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python accessibility_check.py --project-root <path> --level AA\n"

            "  python accessibility_check.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--level", choices=["A", "AA", "AAA"], default="AA", help="WCAG level target")
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


def collect_files(project_root: Path) -> Tuple[List[Path], List[Path]]:
    markup_files: List[Path] = []
    style_files: List[Path] = []
    for current_root, dirs, names in os.walk(project_root):
        dirs[:] = [name for name in dirs if not should_skip_dir(name)]
        root_path = Path(current_root)
        for name in names:
            path = root_path / name
            ext = path.suffix.lower()
            if ext in MARKUP_EXTENSIONS:
                markup_files.append(path)
            elif ext in STYLE_EXTENSIONS:
                style_files.append(path)
    return sorted(markup_files), sorted(style_files)


def add_issue(
    issues: List[Dict[str, object]],
    seen: Set[Tuple[str, int, str, str]],
    by_wcag: Dict[str, int],
    rel_file: str,
    line: int,
    wcag: str,
    severity: str,
    message: str,
    suggestion: str,
) -> None:
    key = (rel_file, line, wcag, message)
    if key in seen:
        return
    seen.add(key)
    issues.append(
        {
            "file": rel_file,
            "line": line,
            "wcag": wcag,
            "severity": severity,
            "message": message,
            "suggestion": suggestion,
        }
    )
    by_wcag[wcag] = by_wcag.get(wcag, 0) + 1


def parse_hex_color(value: str) -> Optional[Tuple[int, int, int]]:
    raw = value.strip().lower()
    if not raw.startswith("#"):
        return None
    hex_value = raw[1:]
    if len(hex_value) == 3:
        try:
            return tuple(int(ch * 2, 16) for ch in hex_value)  # type: ignore[return-value]
        except ValueError:
            return None
    if len(hex_value) == 6:
        try:
            return (
                int(hex_value[0:2], 16),
                int(hex_value[2:4], 16),
                int(hex_value[4:6], 16),
            )
        except ValueError:
            return None
    return None


def parse_rgb_color(value: str) -> Optional[Tuple[int, int, int]]:
    match = re.search(
        r"rgb\(\s*([0-9]{1,3})(?:\s*,\s*|\s+)([0-9]{1,3})(?:\s*,\s*|\s+)([0-9]{1,3})\s*\)",
        value.strip(),
        re.IGNORECASE,
    )
    if not match:
        return None
    channels = [int(match.group(1)), int(match.group(2)), int(match.group(3))]
    if any(channel > 255 for channel in channels):
        return None
    return channels[0], channels[1], channels[2]


def parse_color(value: str) -> Optional[Tuple[int, int, int]]:
    return parse_hex_color(value) or parse_rgb_color(value)


def to_linear_channel(channel: float) -> float:
    normalized = channel / 255.0
    if normalized <= 0.03928:
        return normalized / 12.92
    return ((normalized + 0.055) / 1.055) ** 2.4


def luminance(color: Tuple[int, int, int]) -> float:
    r, g, b = color
    return 0.2126 * to_linear_channel(r) + 0.7152 * to_linear_channel(g) + 0.0722 * to_linear_channel(b)


def contrast_ratio(color_a: Tuple[int, int, int], color_b: Tuple[int, int, int]) -> float:
    l1 = luminance(color_a)
    l2 = luminance(color_b)
    high = max(l1, l2)
    low = min(l1, l2)
    return (high + 0.05) / (low + 0.05)


def parse_font_size_px(block_body: str) -> Optional[float]:
    match = FONT_SIZE_PATTERN.search(block_body)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit == "rem":
        return value * 16.0
    return value


def contrast_threshold(level: str, is_large_text: bool) -> float:
    if level == "AAA":
        return 4.5 if is_large_text else 7.0
    if level == "AA":
        return 3.0 if is_large_text else 4.5
    return 3.0


def check_markup_file(
    path: Path,
    root: Path,
    issues: List[Dict[str, object]],
    seen: Set[Tuple[str, int, str, str]],
    by_wcag: Dict[str, int],
) -> None:
    content = path.read_text(encoding="utf-8", errors="ignore")
    rel_file = rel_path(path, root)
    ext = path.suffix.lower()

    for match in IMAGE_PATTERN.finditer(content):
        tag = match.group(0)
        line = line_for_index(content, match.start())
        if not re.search(r"\balt\s*=", tag, re.IGNORECASE):
            add_issue(
                issues,
                seen,
                by_wcag,
                rel_file,
                line,
                "1.1.1",
                "warning",
                "Image element is missing alt text.",
                "Add meaningful alt text or alt=\"\" for decorative images.",
            )
        else:
            alt_match = re.search(r"\balt\s*=\s*([\"'])(.*?)\1", tag, re.IGNORECASE)
            if alt_match and not alt_match.group(2).strip():
                add_issue(
                    issues,
                    seen,
                    by_wcag,
                    rel_file,
                    line,
                    "1.1.1",
                    "info",
                    "Image has empty alt text.",
                    "Use empty alt only for decorative imagery; otherwise provide description.",
                )

    for match in DIV_HEADING_PATTERN.finditer(content):
        tag = match.group(0)
        if re.search(r"\brole\s*=\s*['\"]heading['\"]", tag, re.IGNORECASE):
            continue
        add_issue(
            issues,
            seen,
            by_wcag,
            rel_file,
            line_for_index(content, match.start()),
            "1.3.1",
            "warning",
            "Potential heading rendered with <div> instead of semantic heading tag.",
            "Use <h1>-<h6> or role='heading' with aria-level.",
        )

    for match in CUSTOM_CLICKABLE_PATTERN.finditer(content):
        tag = match.group(0)
        has_keyboard = re.search(r"\b(onKeyDown|onKeyUp|onKeyPress|@keydown)\b", tag, re.IGNORECASE) is not None
        has_accessibility_hint = re.search(r"\b(tabindex|tabIndex|role)\b", tag, re.IGNORECASE) is not None
        if has_keyboard and has_accessibility_hint:
            continue
        add_issue(
            issues,
            seen,
            by_wcag,
            rel_file,
            line_for_index(content, match.start()),
            "2.1.1",
            "critical",
            "Non-interactive element has click handler without keyboard support.",
            "Use <button> or add role='button', tabIndex=0, and keyboard event handlers.",
        )

    has_skip_link = re.search(r"href\s*=\s*['\"]#(main|content)['\"]", content, re.IGNORECASE) is not None
    has_main_landmark = re.search(r"<main\b|role\s*=\s*['\"]main['\"]", content, re.IGNORECASE) is not None
    if (ext == ".html" or "<body" in content.lower() or has_main_landmark) and not (has_skip_link or has_main_landmark):
        add_issue(
            issues,
            seen,
            by_wcag,
            rel_file,
            1,
            "2.4.1",
            "warning",
            "No skip-navigation link or main landmark detected.",
            "Add a skip link and ensure main content uses <main> or role='main'.",
        )

    if ext == ".html" and not re.search(r"<title>\s*[^<]+</title>", content, re.IGNORECASE):
        add_issue(
            issues,
            seen,
            by_wcag,
            rel_file,
            1,
            "2.4.2",
            "warning",
            "HTML document is missing a descriptive <title>.",
            "Add a meaningful page title for navigation and screen readers.",
        )

    for match in ANCHOR_TEXT_PATTERN.finditer(content):
        text = re.sub(r"<[^>]+>", "", match.group(1)).strip().lower()
        if text in VAGUE_LINK_TEXTS:
            add_issue(
                issues,
                seen,
                by_wcag,
                rel_file,
                line_for_index(content, match.start()),
                "2.4.4",
                "info",
                f"Link text '{text}' is vague.",
                "Use descriptive link text that communicates destination or action.",
            )

    html_tag = HTML_TAG_PATTERN.search(content)
    if html_tag and not re.search(r"\blang\s*=", html_tag.group(0), re.IGNORECASE):
        add_issue(
            issues,
            seen,
            by_wcag,
            rel_file,
            line_for_index(content, html_tag.start()),
            "3.1.1",
            "warning",
            "<html> tag is missing lang attribute.",
            "Set language, for example <html lang='en'>.",
        )

    for control in FORM_CONTROL_PATTERN.finditer(content):
        tag = control.group(0)
        if re.search(r"\btype\s*=\s*['\"]hidden['\"]", tag, re.IGNORECASE):
            continue
        if re.search(r"\b(aria-label|aria-labelledby)\s*=", tag, re.IGNORECASE):
            continue
        id_match = re.search(r"\bid\s*=\s*['\"]([^'\"]+)['\"]", tag, re.IGNORECASE)
        if id_match:
            control_id = re.escape(id_match.group(1))
            label_pattern = re.compile(rf"<label\b[^>]*for\s*=\s*['\"]{control_id}['\"]", re.IGNORECASE)
            if label_pattern.search(content):
                continue
        add_issue(
            issues,
            seen,
            by_wcag,
            rel_file,
            line_for_index(content, control.start()),
            "3.3.2",
            "critical",
            "Form control missing associated label.",
            "Add <label for='...'> or aria-label/aria-labelledby.",
        )

    id_locations: Dict[str, List[int]] = {}
    for id_match in ID_PATTERN.finditer(content):
        identifier = id_match.group(1)
        id_locations.setdefault(identifier, []).append(line_for_index(content, id_match.start()))
    for identifier, lines in id_locations.items():
        if len(lines) > 1:
            add_issue(
                issues,
                seen,
                by_wcag,
                rel_file,
                lines[1],
                "4.1.1",
                "critical",
                f"Duplicate id '{identifier}' detected in same document.",
                "Ensure all id attributes are unique within a page.",
            )

    for role_match in ROLE_PATTERN.finditer(content):
        role_value = role_match.group(1).strip().lower()
        if role_value not in VALID_ROLES:
            add_issue(
                issues,
                seen,
                by_wcag,
                rel_file,
                line_for_index(content, role_match.start()),
                "4.1.2",
                "warning",
                f"Invalid ARIA role '{role_value}'.",
                "Use valid ARIA role values from the WAI-ARIA specification.",
            )

    for aria_match in ARIA_ATTR_PATTERN.finditer(content):
        attribute = aria_match.group(1).lower()
        if attribute not in KNOWN_ARIA_ATTRS:
            add_issue(
                issues,
                seen,
                by_wcag,
                rel_file,
                line_for_index(content, aria_match.start()),
                "4.1.2",
                "info",
                f"Unknown ARIA attribute '{attribute}'.",
                "Check ARIA attribute spelling and usage against WAI-ARIA spec.",
            )


def check_contrast(
    style_file: Path,
    root: Path,
    level: str,
    issues: List[Dict[str, object]],
    seen: Set[Tuple[str, int, str, str]],
    by_wcag: Dict[str, int],
    warnings: List[str],
) -> None:
    content = style_file.read_text(encoding="utf-8", errors="ignore")
    rel_file = rel_path(style_file, root)
    for block in CSS_BLOCK_PATTERN.finditer(content):
        body = block.group("body")
        color_decl = COLOR_DECL_PATTERN.search(body)
        bg_decl = BG_DECL_PATTERN.search(body)
        if not color_decl or not bg_decl:
            continue
        color = parse_color(color_decl.group(1))
        background = parse_color(bg_decl.group(1))
        if color is None or background is None:
            warnings.append(
                f"Skipped contrast parse at {rel_file}:{line_for_index(content, block.start())} "
                f"(unsupported color format)"
            )
            continue

        font_size = parse_font_size_px(body)
        large_text = font_size is not None and font_size >= 24.0
        threshold = contrast_threshold(level, large_text)
        ratio = contrast_ratio(color, background)
        if ratio < threshold:
            add_issue(
                issues,
                seen,
                by_wcag,
                rel_file,
                line_for_index(content, block.start()),
                "1.4.3",
                "warning",
                f"Low text contrast ratio ({ratio:.2f}:1).",
                f"Increase contrast to at least {threshold:.1f}:1 for target WCAG level {level}.",
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

    markup_files, style_files = collect_files(project_root)
    warnings: List[str] = []
    issues: List[Dict[str, object]] = []
    seen: Set[Tuple[str, int, str, str]] = set()
    by_wcag: Dict[str, int] = {}

    for file_path in markup_files:
        check_markup_file(file_path, project_root, issues, seen, by_wcag)
    for style_path in style_files:
        check_contrast(style_path, project_root, args.level, issues, seen, by_wcag, warnings)

    by_severity = {"critical": 0, "warning": 0, "info": 0}
    for issue in issues:
        severity = str(issue.get("severity", "info"))
        by_severity[severity] = by_severity.get(severity, 0) + 1

    compliance_score = max(0, 100 - by_severity["critical"] * 8 - by_severity["warning"] * 3 - by_severity["info"] * 1)

    focus_areas = sorted(by_wcag.items(), key=lambda item: item[1], reverse=True)[:2]
    if focus_areas:
        focus_text = ", ".join(f"{criterion} ({count})" for criterion, count in focus_areas)
        summary = f"{len(issues)} WCAG {args.level} issues found. Focus areas: {focus_text}"
    else:
        summary = f"0 WCAG {args.level} issues found."

    payload: Dict[str, object] = {
        "status": "checked",
        "level": args.level,
        "files_scanned": len(markup_files) + len(style_files),
        "total_issues": len(issues),
        "by_wcag": dict(sorted(by_wcag.items(), key=lambda item: item[0])),
        "issues": issues,
        "compliance_score": compliance_score,
        "summary": summary,
    }
    if warnings:
        payload["warnings"] = warnings
    emit(payload, exit_code=0)


if __name__ == "__main__":
    main()
