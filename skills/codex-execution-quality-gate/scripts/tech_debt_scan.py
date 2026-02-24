#!/usr/bin/env python3
"""
Tech debt scanner for code repositories.

Checks:
- TODO/FIXME/HACK comments
- long functions
- long files
- duplicate 5-line code blocks
- unused exports in TypeScript files
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


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

CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx"}
TS_EXTENSIONS = {".ts", ".tsx"}
MAX_FILE_SIZE = 1_500_000

TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK)\b", re.IGNORECASE)
IMPORT_BRACES_PATTERN = re.compile(
    r"\bimport\s+(?:type\s+)?\{([^}]+)\}\s+from\s+['\"][^'\"]+['\"]", re.MULTILINE
)
EXPORT_FROM_PATTERN = re.compile(
    r"\bexport\s+\{([^}]+)\}\s+from\s+['\"][^'\"]+['\"]", re.MULTILINE
)
EXPORT_DECL_PATTERN = re.compile(
    r"^\s*export\s+(?:declare\s+)?(?:async\s+)?"
    r"(?:const|let|var|function|class|type|interface|enum)\s+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
EXPORT_INLINE_PATTERN = re.compile(r"\bexport\s*\{([^}]+)\}", re.MULTILINE)


@dataclass
class JsBraceState:
    in_block_comment: bool = False
    in_single: bool = False
    in_double: bool = False
    in_template: bool = False
    escaped: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Scan project tech debt and emit JSON.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python tech_debt_scan.py --project-root <path>\n"

            "  python tech_debt_scan.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--max-function-lines", type=int, default=50, help="Max function lines")
    parser.add_argument("--max-file-lines", type=int, default=500, help="Max file lines")
    parser.add_argument("--todo-age-days", type=int, default=30, help="Mark TODO older than this as medium")
    parser.add_argument("--human", action="store_true", help="Print human-readable summary to stderr")
    return parser.parse_args()


def rel_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def collect_code_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for current_root, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(current_root)
        for name in names:
            path = root_path / name
            if path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            try:
                if path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue
            files.append(path)
    files.sort()
    return files


def git_available() -> bool:
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except OSError:
        return False


def inside_git_repo(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def parse_blame_porcelain(stdout: Optional[str]) -> Dict[int, int]:
    line_to_time: Dict[int, int] = {}
    if not stdout:
        return line_to_time
    current_start = None
    current_count = None
    current_time = None

    for raw_line in stdout.splitlines():
        if re.match(r"^[0-9a-f^]{7,40}\s+\d+\s+\d+\s+\d+$", raw_line):
            parts = raw_line.split()
            current_start = int(parts[2])
            current_count = int(parts[3])
            current_time = None
            continue
        if raw_line.startswith("author-time "):
            try:
                current_time = int(raw_line.split(" ", 1)[1].strip())
            except (TypeError, ValueError):
                current_time = None
            continue
        if raw_line.startswith("\t") and current_start is not None and current_count is not None:
            if current_time is not None:
                for offset in range(current_count):
                    line_to_time[current_start + offset] = current_time
            current_start = None
            current_count = None
            current_time = None

    return line_to_time


def load_blame_times(
    root: Path,
    file_path: Path,
    warnings: List[str],
    blame_cache: Dict[str, Dict[int, int]],
) -> Dict[int, int]:
    rel = rel_path(file_path, root)
    if rel in blame_cache:
        return blame_cache[rel]

    try:
        result = subprocess.run(
            ["git", "blame", "--line-porcelain", "--", rel],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        warnings.append(f"Git blame timed out (60s) for {rel}; TODO age fallback applied.")
        blame_cache[rel] = {}
        return {}
    except OSError as exc:
        warnings.append(f"Git blame unavailable for {rel}: {exc}")
        blame_cache[rel] = {}
        return {}

    if result.returncode != 0:
        stderr = (result.stderr or "").strip() or (result.stdout or "").strip()
        warnings.append(f"Git blame failed for {rel}: {stderr or 'unknown error'}")
        blame_cache[rel] = {}
        return {}

    parsed = parse_blame_porcelain(result.stdout)
    blame_cache[rel] = parsed
    return parsed


def todo_priority(
    author_time: Optional[int],
    todo_age_days: int,
) -> str:
    if author_time is None:
        return "low"
    authored = datetime.fromtimestamp(author_time, tz=timezone.utc).date()
    age_days = (datetime.now(timezone.utc).date() - authored).days
    return "medium" if age_days > todo_age_days else "low"


def scan_todos(
    files: Iterable[Path],
    root: Path,
    todo_age_days: int,
    warnings: List[str],
) -> List[Dict[str, object]]:
    issues: List[Dict[str, object]] = []
    blame_cache: Dict[str, Dict[int, int]] = {}
    use_blame = git_available() and inside_git_repo(root)

    for file_path in files:
        content = read_text(file_path)
        if not content:
            continue
        lines = content.splitlines()
        blame_times: Dict[int, int] = {}
        blame_attempted = False

        for idx, line in enumerate(lines, start=1):
            if not TODO_PATTERN.search(line):
                continue

            if use_blame and not blame_attempted:
                blame_times = load_blame_times(root, file_path, warnings, blame_cache)
                blame_attempted = True

            author_time = blame_times.get(idx) if blame_times else None
            issues.append(
                {
                    "file": rel_path(file_path, root),
                    "line": idx,
                    "text": line.strip(),
                    "priority": todo_priority(author_time, todo_age_days),
                }
            )

    issues.sort(key=lambda item: (str(item["file"]), int(item["line"])))
    return issues


def scan_python_functions(
    file_path: Path,
    root: Path,
    max_function_lines: int,
    warnings: List[str],
) -> List[Dict[str, object]]:
    issues: List[Dict[str, object]] = []
    source = read_text(file_path)
    if not source:
        return issues

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        warnings.append(f"Python AST parse failed for {rel_path(file_path, root)}: {exc.msg}")
        return issues
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"Python AST parse failed for {rel_path(file_path, root)}: {exc}")
        return issues

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = int(getattr(node, "lineno", 0) or 0)
            end = int(getattr(node, "end_lineno", start) or start)
            length = max(0, end - start + 1)
            if length > max_function_lines:
                issues.append(
                    {
                        "file": rel_path(file_path, root),
                        "line": start,
                        "name": node.name,
                        "lines": length,
                        "priority": "medium",
                    }
                )
    return issues


def js_brace_counts(line: str, state: JsBraceState) -> Tuple[int, int, JsBraceState]:
    opens = 0
    closes = 0
    i = 0
    in_line_comment = False

    while i < len(line):
        ch = line[i]
        nxt = line[i + 1] if i + 1 < len(line) else ""

        if in_line_comment:
            break

        if state.in_block_comment:
            if ch == "*" and nxt == "/":
                state.in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if state.in_single:
            if state.escaped:
                state.escaped = False
            elif ch == "\\":
                state.escaped = True
            elif ch == "'":
                state.in_single = False
            i += 1
            continue

        if state.in_double:
            if state.escaped:
                state.escaped = False
            elif ch == "\\":
                state.escaped = True
            elif ch == '"':
                state.in_double = False
            i += 1
            continue

        if state.in_template:
            if state.escaped:
                state.escaped = False
            elif ch == "\\":
                state.escaped = True
            elif ch == "`":
                state.in_template = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            state.in_block_comment = True
            i += 2
            continue
        if ch == "'":
            state.in_single = True
            i += 1
            continue
        if ch == '"':
            state.in_double = True
            i += 1
            continue
        if ch == "`":
            state.in_template = True
            i += 1
            continue
        if ch == "{":
            opens += 1
        elif ch == "}":
            closes += 1
        i += 1

    state.escaped = False
    return opens, closes, state


def estimate_js_block_end(lines: List[str], start_idx: int) -> Optional[int]:
    depth = 0
    opened = False
    state = JsBraceState()

    for idx in range(start_idx, len(lines)):
        open_count, close_count, state = js_brace_counts(lines[idx], state)
        if open_count > 0:
            opened = True
        depth += open_count
        depth -= close_count
        if opened and depth <= 0:
            return idx
    return None


def scan_js_ts_functions(
    file_path: Path,
    root: Path,
    max_function_lines: int,
    warnings: List[str],
) -> List[Dict[str, object]]:
    issues: List[Dict[str, object]] = []
    source = read_text(file_path)
    if not source:
        return issues

    lines = source.splitlines()
    if not lines:
        return issues

    patterns = [
        re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?[A-Za-z_$][\w$]*\s*=>"),
        re.compile(r"^\s*(?:public|private|protected|static|async|\s)*([A-Za-z_$][\w$]*)\s*\([^;]*\)\s*\{"),
    ]

    reserved = {"if", "for", "while", "switch", "catch", "return", "new"}

    for idx, line in enumerate(lines):
        function_name = None
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                candidate = match.group(1)
                if candidate and candidate not in reserved:
                    function_name = candidate
                    break

        if not function_name:
            continue

        end_idx = estimate_js_block_end(lines, idx)
        if end_idx is None:
            warnings.append(f"JS/TS block parse failed for {rel_path(file_path, root)}:{idx + 1}")
            continue

        length = end_idx - idx + 1
        if length > max_function_lines:
            issues.append(
                {
                    "file": rel_path(file_path, root),
                    "line": idx + 1,
                    "name": function_name,
                    "lines": length,
                    "priority": "medium",
                }
            )

    return issues


def scan_long_functions(
    files: Iterable[Path],
    root: Path,
    max_function_lines: int,
    warnings: List[str],
) -> List[Dict[str, object]]:
    issues: List[Dict[str, object]] = []
    for file_path in files:
        ext = file_path.suffix.lower()
        if ext == ".py":
            issues.extend(scan_python_functions(file_path, root, max_function_lines, warnings))
        elif ext in {".js", ".jsx", ".ts", ".tsx"}:
            issues.extend(scan_js_ts_functions(file_path, root, max_function_lines, warnings))
    issues.sort(key=lambda item: (str(item["file"]), int(item["line"])))
    return issues


def scan_long_files(
    files: Iterable[Path],
    root: Path,
    max_file_lines: int,
) -> List[Dict[str, object]]:
    issues: List[Dict[str, object]] = []
    for file_path in files:
        text = read_text(file_path)
        if not text:
            continue
        total_lines = len(text.splitlines())
        if total_lines > max_file_lines:
            issues.append(
                {
                    "file": rel_path(file_path, root),
                    "lines": total_lines,
                    "priority": "medium",
                }
            )
    issues.sort(key=lambda item: (str(item["file"]), int(item["lines"])))
    return issues


def normalize_dup_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def scan_duplicates(
    files: Iterable[Path],
    root: Path,
) -> List[Dict[str, object]]:
    block_map: Dict[str, List[Tuple[str, int]]] = {}
    window_size = 5

    for file_path in files:
        lines = read_text(file_path).splitlines()
        if len(lines) < window_size:
            continue

        rel = rel_path(file_path, root)
        normalized = [normalize_dup_line(line) for line in lines]

        for idx in range(0, len(normalized) - window_size + 1):
            block = normalized[idx : idx + window_size]
            if any(not item for item in block):
                continue
            key = "\n".join(block)
            block_map.setdefault(key, []).append((rel, idx + 1))

    issues: List[Dict[str, object]] = []
    seen_files_signatures: Set[Tuple[str, ...]] = set()

    for occurrences in block_map.values():
        if len(occurrences) < 2:
            continue
        files_only = sorted({entry[0] for entry in occurrences})
        signature = tuple(files_only)
        if signature in seen_files_signatures:
            continue
        seen_files_signatures.add(signature)
        issues.append(
            {
                "files": files_only,
                "lines": 5,
                "priority": "low",
            }
        )

    issues.sort(key=lambda item: tuple(item["files"]))
    return issues


def parse_brace_names(blob: str) -> List[str]:
    names: List[str] = []
    for part in blob.split(","):
        token = part.strip()
        if not token:
            continue
        if token.startswith("type "):
            token = token[5:].strip()
        side = token.split(" as ")
        exported_name = side[-1].strip()
        if re.match(r"^[A-Za-z_$][\w$]*$", exported_name):
            names.append(exported_name)
    return names


def index_to_line(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def collect_imported_names(files: Iterable[Path]) -> Set[str]:
    imported: Set[str] = set()
    for file_path in files:
        text = read_text(file_path)
        if not text:
            continue
        for match in IMPORT_BRACES_PATTERN.finditer(text):
            imported.update(parse_brace_names(match.group(1)))
        for match in EXPORT_FROM_PATTERN.finditer(text):
            imported.update(parse_brace_names(match.group(1)))
    return imported


def collect_exports_for_file(file_path: Path) -> List[Tuple[str, int]]:
    text = read_text(file_path)
    if not text:
        return []

    found: List[Tuple[str, int]] = []
    for match in EXPORT_DECL_PATTERN.finditer(text):
        found.append((match.group(1), index_to_line(text, match.start(1))))
    for match in EXPORT_INLINE_PATTERN.finditer(text):
        for name in parse_brace_names(match.group(1)):
            found.append((name, index_to_line(text, match.start(1))))
    return found


def scan_unused_exports(
    files: Iterable[Path],
    root: Path,
) -> List[Dict[str, object]]:
    ts_files = [path for path in files if path.suffix.lower() in TS_EXTENSIONS]
    imported_names = collect_imported_names(files)
    issues: List[Dict[str, object]] = []

    for ts_file in ts_files:
        for name, line in collect_exports_for_file(ts_file):
            if name not in imported_names:
                issues.append(
                    {
                        "file": rel_path(ts_file, root),
                        "name": name,
                        "line": line,
                        "priority": "low",
                    }
                )

    unique: Dict[Tuple[str, str, int], Dict[str, object]] = {}
    for issue in issues:
        key = (str(issue["file"]), str(issue["name"]), int(issue["line"]))
        unique[key] = issue
    deduped = list(unique.values())
    deduped.sort(key=lambda item: (str(item["file"]), int(item["line"]), str(item["name"])))
    return deduped


def build_summary(by_category: Dict[str, List[Dict[str, object]]], total: int) -> str:
    return (
        f"{total} issues found: "
        f"{len(by_category['todo_fixme'])} TODOs, "
        f"{len(by_category['long_functions'])} long functions, "
        f"{len(by_category['long_files'])} long files, "
        f"{len(by_category['duplicates'])} duplicate blocks, "
        f"{len(by_category['unused_exports'])} unused exports"
    )


def scan_project(
    project_root: Path,
    max_function_lines: int,
    max_file_lines: int,
    todo_age_days: int,
) -> Dict[str, object]:
    warnings: List[str] = []

    if not project_root.exists() or not project_root.is_dir():
        return {
            "scan_root": project_root.as_posix(),
            "total_issues": 0,
            "by_category": {
                "todo_fixme": [],
                "long_functions": [],
                "long_files": [],
                "duplicates": [],
                "unused_exports": [],
            },
            "summary": "0 issues found: 0 TODOs, 0 long functions, 0 long files, 0 duplicate blocks, 0 unused exports",
            "warnings": [f"Project root does not exist or is not a directory: {project_root}"],
        }

    files = collect_code_files(project_root)
    if not files:
        warnings.append("No supported code files found for scanning.")

    todo_issues = scan_todos(files, project_root, todo_age_days, warnings)
    function_issues = scan_long_functions(files, project_root, max_function_lines, warnings)
    long_file_issues = scan_long_files(files, project_root, max_file_lines)
    duplicate_issues = scan_duplicates(files, project_root)
    unused_export_issues = scan_unused_exports(files, project_root)

    by_category = {
        "todo_fixme": todo_issues,
        "long_functions": function_issues,
        "long_files": long_file_issues,
        "duplicates": duplicate_issues,
        "unused_exports": unused_export_issues,
    }
    total_issues = sum(len(items) for items in by_category.values())

    return {
        "scan_root": project_root.as_posix(),
        "total_issues": total_issues,
        "by_category": by_category,
        "summary": build_summary(by_category, total_issues),
        "warnings": sorted(set(warnings)),
    }


def render_human_box(title: str, rows: List[str]) -> str:
    width = max(38, len(title), *(len(row) for row in rows))
    top = "╔" + ("═" * width) + "╗"
    mid = "╠" + ("═" * width) + "╣"
    bottom = "╚" + ("═" * width) + "╝"
    out = [top, f"║{title.center(width)}║", mid]
    for row in rows:
        out.append(f"║ {'{}'.format(row).ljust(width - 2)} ║")
    out.append(bottom)
    return "\n".join(out)


def print_human_summary(report: Dict[str, object]) -> None:
    by_category = report.get("by_category", {})
    if not isinstance(by_category, dict):
        by_category = {}

    total_signals = int(report.get("total_issues", 0) or 0)
    signal_by_file: Counter[str] = Counter()
    critical_count = 0

    for items in by_category.values():
        if not isinstance(items, list):
            continue
        for issue in items:
            if not isinstance(issue, dict):
                continue
            priority = str(issue.get("priority", "")).strip().lower()
            if priority in {"high", "critical"}:
                critical_count += 1
            file_path = issue.get("file")
            if isinstance(file_path, str) and file_path:
                signal_by_file[file_path] += 1
            files = issue.get("files")
            if isinstance(files, list):
                for file_item in files:
                    if isinstance(file_item, str) and file_item:
                        signal_by_file[file_item] += 1

    rows: List[str] = [
        f"Total Signals: {total_signals}",
        f"Critical:      {critical_count}",
        "Top Files:",
    ]
    if signal_by_file:
        for idx, (file_path, count) in enumerate(signal_by_file.most_common(3), start=1):
            rows.append(f"  {idx}. {file_path} ({count} signals)")
    else:
        rows.append("  1. none (0 signals)")

    print(render_human_box("TECH DEBT SCAN RESULTS", rows), file=sys.stderr)


def emit_json(payload: Dict[str, object]) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    try:
        print(rendered)
    except UnicodeEncodeError:
        print(json.dumps(payload, indent=2, ensure_ascii=True))


def main() -> int:
    args = parse_args()
    report = scan_project(
        project_root=Path(args.project_root).expanduser().resolve(),
        max_function_lines=args.max_function_lines,
        max_file_lines=args.max_file_lines,
        todo_age_days=args.todo_age_days,
    )
    emit_json(report)
    if args.human:
        print_human_summary(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
