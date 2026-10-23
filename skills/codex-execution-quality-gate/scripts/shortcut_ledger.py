#!/usr/bin/env python3
"""Scan source comments for shortcut: <ceiling>, <when to upgrade> markers."""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
from pathlib import Path
from typing import Any


SKIP_DIRS = {".git", ".codex", "node_modules"}
HASH_SUFFIXES = {".py", ".sh", ".bash", ".rb", ".ps1"}
SLASH_SUFFIXES = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".php",
    ".css",
    ".scss",
}
MAX_FILE_BYTES = 1_000_000
SHORTCUT_PATTERN = re.compile(
    r"shortcut\s*:\s*(?P<ceiling>[^,\n]+?)(?:\s*,\s*(?P<when>[^\n]*))?\s*$",
    re.IGNORECASE,
)


def path_is_symlink(path: Path) -> bool:
    try:
        return Path(path).is_symlink()
    except OSError:
        return True


def _skip_quoted(text: str, start: int, quote: str) -> int:
    index = start + 1
    limit = len(text)
    while index < limit:
        if text[index] == "\\":
            index += 2
            continue
        if text[index] in "\n\r":
            return index
        if text[index] == quote:
            return index + 1
        index += 1
    return limit


def _bump_line(text: str, start: int, end: int, line: int) -> int:
    return line + text[start:end].count("\n")


def iter_hash_comments(text: str) -> list[tuple[int, str]]:
    comments: list[tuple[int, str]] = []
    index = 0
    line = 1
    limit = len(text)
    while index < limit:
        if text.startswith("\r\n", index):
            line += 1
            index += 2
            continue
        char = text[index]
        if char in "\n\r":
            line += 1
            index += 1
            continue
        if text.startswith('"""', index) or text.startswith("'''", index):
            quote = text[index : index + 3]
            end = text.find(quote, index + 3)
            if end == -1:
                break
            line = _bump_line(text, index, end + 3, line)
            index = end + 3
            continue
        if char in "'\"":
            end = _skip_quoted(text, index, char)
            line = _bump_line(text, index, end, line)
            index = end
            continue
        if char == "#":
            end = index + 1
            while end < limit and text[end] not in "\r\n":
                end += 1
            comments.append((line, text[index + 1 : end].strip()))
            index = end
            continue
        index += 1
    return comments


def iter_slash_comments(text: str) -> list[tuple[int, str]]:
    comments: list[tuple[int, str]] = []
    index = 0
    line = 1
    limit = len(text)
    while index < limit:
        if text.startswith("\r\n", index):
            line += 1
            index += 2
            continue
        char = text[index]
        if char in "\n\r":
            line += 1
            index += 1
            continue
        if char in "'\"":
            end = _skip_quoted(text, index, char)
            line = _bump_line(text, index, end, line)
            index = end
            continue
        if char == "`":
            end = text.find("`", index + 1)
            if end == -1:
                break
            line = _bump_line(text, index, end + 1, line)
            index = end + 1
            continue
        if text.startswith("//", index):
            end = index + 2
            while end < limit and text[end] not in "\r\n":
                end += 1
            comments.append((line, text[index + 2 : end].strip()))
            index = end
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            body_end = limit if end == -1 else end
            body = text[index + 2 : body_end]
            start_line = line
            for offset, part in enumerate(body.splitlines() or [""]):
                stripped = part.strip().lstrip("*").strip()
                if stripped:
                    comments.append((start_line + offset, stripped))
            line += body.count("\n")
            index = limit if end == -1 else end + 2
            continue
        index += 1
    return comments


def iter_comments(path: Path, text: str) -> list[tuple[int, str]]:
    suffix = path.suffix.lower()
    if suffix in HASH_SUFFIXES:
        return iter_hash_comments(text)
    if suffix in SLASH_SUFFIXES:
        return iter_slash_comments(text)
    return []


def _load_gitignore(root: Path) -> list[str]:
    path = root / ".gitignore"
    if not path.is_file() or path_is_symlink(path):
        return []
    patterns: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("!"):
            continue
        patterns.append(stripped)
    return patterns


def _match_gitignore(rel: str, pattern: str) -> bool:
    directory_only = pattern.endswith("/")
    pat = pattern[:-1] if directory_only else pattern
    if directory_only:
        prefix = pat.rstrip("/")
        return rel == prefix or rel.startswith(prefix + "/")
    name = rel.split("/")[-1]
    if "/" not in pat:
        return fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat)
    return fnmatch.fnmatch(rel, pat) or rel.startswith(pat.rstrip("/") + "/")


def _is_ignored(rel: str, patterns: list[str]) -> bool:
    return any(_match_gitignore(rel, pattern) for pattern in patterns)


def _shortcut_record(rel: str, line: int, comment: str) -> dict[str, Any] | None:
    match = SHORTCUT_PATTERN.search(comment.strip())
    if not match:
        return None
    ceiling = match.group("ceiling").strip()
    upgrade_when = (match.group("when") or "").strip()
    status = "documented" if upgrade_when else "no-trigger"
    return {
        "path": rel,
        "line": line,
        "ceiling": ceiling,
        "upgrade_when": upgrade_when,
        "trigger": upgrade_when,
        "status": status,
        "comment": comment.strip(),
    }


def scan_shortcuts(project_root: Path) -> dict[str, Any]:
    """Scan real comments for shortcut markers. Prose, markdown, and strings are ignored."""
    root = Path(project_root)
    if not root.is_dir():
        raise ValueError(f"project root is not a directory: {root}")
    patterns = _load_gitignore(root)
    shortcuts: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        if path_is_symlink(current):
            dirnames[:] = []
            continue
        relative_dir = current.relative_to(root).as_posix()
        kept: list[str] = []
        for name in dirnames:
            child_rel = name if relative_dir == "." else f"{relative_dir}/{name}"
            child = current / name
            if name in SKIP_DIRS or path_is_symlink(child) or _is_ignored(child_rel, patterns):
                continue
            kept.append(name)
        dirnames[:] = kept
        for filename in filenames:
            path = current / filename
            if path_is_symlink(path):
                continue
            suffix = path.suffix.lower()
            if suffix not in HASH_SUFFIXES and suffix not in SLASH_SUFFIXES:
                continue
            rel = path.relative_to(root).as_posix()
            if _is_ignored(rel, patterns):
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "\x00" in text:
                continue
            for line, comment in iter_comments(path, text):
                record = _shortcut_record(rel, line, comment)
                if record is not None:
                    shortcuts.append(record)
    shortcuts.sort(key=lambda item: (item["path"], item["line"], item["status"]))
    documented = sum(1 for item in shortcuts if item["status"] == "documented")
    missing = sum(1 for item in shortcuts if item["status"] == "no-trigger")
    return {
        "ok": True,
        "project_root": str(root),
        "shortcuts": shortcuts,
        "counts": {"documented": documented, "no-trigger": missing, "total": len(shortcuts)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List shortcut comments and tag markers that have no upgrade trigger.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(argv)
    try:
        report = scan_shortcuts(Path(args.project_root))
    except (OSError, ValueError) as exc:
        payload = {"ok": False, "message": str(exc), "shortcuts": []}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"shortcuts: {report['counts']['total']}")
        for item in report["shortcuts"]:
            trigger = item["upgrade_when"] or "no-trigger"
            print(f"{item['path']}:{item['line']} {item['status']} ceiling={item['ceiling']} trigger={trigger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
