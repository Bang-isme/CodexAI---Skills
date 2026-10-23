#!/usr/bin/env python3
"""Compact, sanitized index of reusable helpers already in a project.

Folder names and exported symbols must be plain identifiers. Symlinks are not
followed. The rendered index stays under the character budget and fails open.
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
INJECTION_MARKERS = ("system notice", "ignore previous instructions")
SKIP_DIRS = {"tests", "node_modules", "dist", "vendor", ".git", ".codex", "__pycache__"}
SHARED_DIR_ORDER = ("utils", "lib", "shared", "common", "helpers", "services")
SHARED_RANK = {name: index for index, name in enumerate(SHARED_DIR_ORDER)}
DEFAULT_MAX_CHARS = 2000
MAX_FILE_BYTES = 512_000
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".rs"}

_PY_EXPORT = re.compile(r"^(?:async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
_JS_EXPORTS = (
    re.compile(r"^export\s+(?:async\s+)?function\s*\*?\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
    re.compile(r"^export\s+(?:default\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
    re.compile(r"^export\s+(?:const|let|var|type|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
    re.compile(r"^module\.exports\.([A-Za-z_][A-Za-z0-9_]*)\s*="),
    re.compile(r"^exports\.([A-Za-z_][A-Za-z0-9_]*)\s*="),
)
_JS_EXPORT_LIST = re.compile(r"^export\s*\{([^}]+)\}")
_GO_EXPORTS = (
    re.compile(r"^func\s+(?:\([^)\n]*\)\s*)?([A-Z][A-Za-z0-9_]*)\b"),
    re.compile(r"^type\s+([A-Z][A-Za-z0-9_]*)\b"),
    re.compile(r"^var\s+([A-Z][A-Za-z0-9_]*)\b"),
    re.compile(r"^const\s+([A-Z][A-Za-z0-9_]*)\b"),
)
_RUST_EXPORT = re.compile(
    r"^pub(?:\([^)\n]*\))?\s+(?:async\s+)?(?:unsafe\s+)?(?:fn|struct|enum|trait|type|const|static|mod)\s+([A-Za-z_][A-Za-z0-9_]*)\b"
)


def is_safe_identifier(name: str) -> bool:
    """True only for a single identifier with no injection text or newlines."""
    if not isinstance(name, str) or IDENTIFIER_RE.fullmatch(name) is None:
        return False
    if any(char in name for char in "\n\r\x00"):
        return False
    lowered = name.lower()
    return not any(marker in lowered for marker in INJECTION_MARKERS)


def path_is_symlink(path: Path) -> bool:
    try:
        return Path(path).is_symlink()
    except OSError:
        return True


def _keep_symbol(name: str) -> bool:
    return is_safe_identifier(name) and not name.startswith("_")


def _names_from_line(line: str, patterns: tuple[re.Pattern[str], ...]) -> list[str]:
    names: list[str] = []
    for pattern in patterns:
        match = pattern.match(line)
        if match and _keep_symbol(match.group(1)):
            names.append(match.group(1))
    return names


def parse_python(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        if not line or line[0] in " \t":
            continue
        names.extend(_names_from_line(line, (_PY_EXPORT,)))
    return names


def parse_javascript(text: str) -> list[str]:
    names: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        names.extend(_names_from_line(line, _JS_EXPORTS))
        listed = _JS_EXPORT_LIST.match(line)
        if not listed:
            continue
        for part in listed.group(1).split(","):
            piece = part.strip()
            if not piece:
                continue
            if " as " in piece:
                piece = piece.split(" as ", 1)[1].strip()
            piece = piece.split(":", 1)[0].strip()
            if _keep_symbol(piece):
                names.append(piece)
    return names


def parse_go(text: str) -> list[str]:
    names: list[str] = []
    for raw in text.splitlines():
        names.extend(_names_from_line(raw.strip(), _GO_EXPORTS))
    return names


def parse_rust(text: str) -> list[str]:
    names: list[str] = []
    for raw in text.splitlines():
        names.extend(_names_from_line(raw.strip(), (_RUST_EXPORT,)))
    return names


_PARSERS = {
    ".py": parse_python,
    ".js": parse_javascript,
    ".jsx": parse_javascript,
    ".mjs": parse_javascript,
    ".cjs": parse_javascript,
    ".ts": parse_javascript,
    ".tsx": parse_javascript,
    ".go": parse_go,
    ".rs": parse_rust,
}


def _folder_key(relative_dir: str) -> str | None:
    if relative_dir in {"", "."}:
        return "root"
    parts = [part for part in relative_dir.split("/") if part]
    if not parts or any(not is_safe_identifier(part) for part in parts):
        return None
    if any(part in SKIP_DIRS for part in parts):
        return None
    return "/".join(parts)


def _folder_sort_key(name: str) -> tuple[int, int, str]:
    base = name.split("/")[-1]
    if base in SHARED_RANK:
        return (0, SHARED_RANK[base], name)
    return (1, 0, name)


def _format_index(entries: list[tuple[str, list[str]]], omitted: int) -> str:
    lines = [f"{name}: {', '.join(symbols)}" for name, symbols in entries if symbols]
    text = "\n".join(lines)
    if omitted > 0:
        suffix = f"... (+{omitted} more folders omitted)"
        return f"{text}\n{suffix}" if text else suffix
    return text


def render_reuse_index(entries: list[tuple[str, list[str]]], max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """Render folder lines under ``max_chars`` and append an omission count when cut."""
    if max_chars <= 0:
        return ""
    cleaned = [(name, symbols) for name, symbols in entries if symbols]
    chosen: list[tuple[str, list[str]]] = []
    for name, symbols in cleaned:
        trial = chosen + [(name, symbols)]
        omitted = len(cleaned) - len(trial)
        if len(_format_index(trial, omitted)) < max_chars:
            chosen = trial
            continue
        partial: list[tuple[str, list[str]]] | None = None
        for count in range(len(symbols) - 1, 0, -1):
            trial = chosen + [(name, symbols[:count])]
            omitted = len(cleaned) - len(chosen) - 1
            if len(_format_index(trial, omitted)) < max_chars:
                partial = trial
                break
        if partial is not None:
            chosen = partial
        break
    omitted = len(cleaned) - len(chosen)
    rendered = _format_index(chosen, omitted)
    if len(rendered) < max_chars:
        return rendered
    suffix = f"... (+{len(cleaned)} more folders omitted)" if cleaned else ""
    if suffix and len(suffix) < max_chars:
        return suffix
    return ""


def _collect_entries(root: Path) -> list[tuple[str, list[str]]]:
    buckets: dict[str, set[str]] = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        if path_is_symlink(current):
            dirnames[:] = []
            continue
        kept_dirs: list[str] = []
        for name in dirnames:
            child = current / name
            if name in SKIP_DIRS or path_is_symlink(child) or not is_safe_identifier(name):
                continue
            kept_dirs.append(name)
        dirnames[:] = kept_dirs
        relative_dir = current.relative_to(root).as_posix()
        folder = _folder_key(relative_dir)
        if folder is None:
            continue
        for filename in filenames:
            if filename.startswith(".") or any(char in filename for char in "\n\r\x00"):
                continue
            path = current / filename
            if path_is_symlink(path):
                continue
            parser = _PARSERS.get(path.suffix.lower())
            if parser is None:
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for symbol in parser(text):
                buckets.setdefault(folder, set()).add(symbol)
    ordered = sorted(buckets, key=_folder_sort_key)
    return [(name, sorted(buckets[name])) for name in ordered if buckets[name]]


def build_reuse_map(project_root: Path | str, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """Build the reuse index. Any unexpected error returns an empty string."""
    try:
        root = Path(project_root)
        if path_is_symlink(root) or not root.is_dir():
            return ""
        return render_reuse_index(_collect_entries(root), max_chars)
    except Exception:
        return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a sanitized reuse map for a project.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    args = parser.parse_args(argv)
    print(build_reuse_map(args.project_root, max_chars=args.max_chars))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
