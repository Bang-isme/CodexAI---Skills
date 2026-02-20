#!/usr/bin/env python3
"""
Generate improvement suggestions for recently changed files.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
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
CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}
TEST_EXTENSIONS = CODE_EXTENSIONS

TODO_PATTERN = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)
MAGIC_NUMBER_PATTERN = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")
DEBUG_PATTERN_JS = re.compile(r"\bconsole\.log\s*\(", re.IGNORECASE)
DEBUG_PATTERN_PY = re.compile(r"\bprint\s*\(")
HUNK_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
EFFORT_BY_CATEGORY = {
    "missing_tests": "medium",
    "long_function": "low",
    "large_file": "medium",
    "todo_fixme": "low",
    "duplicate_block": "medium",
    "magic_number": "low",
    "deep_nesting": "medium",
    "debug_statement": "low",
}


@dataclass
class JsBraceState:
    in_block_comment: bool = False
    in_single: bool = False
    in_double: bool = False
    in_template: bool = False
    escaped: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Suggest improvements near changed code.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python suggest_improvements.py --project-root <path> --source last-commit\n"

            "  python suggest_improvements.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--changed-files", default="", help="Comma-separated changed files")
    parser.add_argument("--source", choices=["staged", "unstaged", "last-commit"], default="last-commit")
    parser.add_argument("--max-suggestions", type=int, default=5, help="Maximum suggestions to return")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def run_git(project_root: Path, args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def git_ready(project_root: Path) -> bool:
    result = run_git(project_root, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def parse_changed_files(raw: str) -> List[str]:
    if not raw.strip():
        return []
    values = [item.strip().replace("\\", "/") for item in raw.split(",") if item.strip()]
    return sorted(dict.fromkeys(values))


def changed_files_from_git(project_root: Path, source: str) -> List[str]:
    if source == "staged":
        args = ["diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    elif source == "unstaged":
        args = ["diff", "--name-only", "--diff-filter=ACMR"]
    else:
        args = ["show", "--name-only", "--pretty=format:", "HEAD"]
    result = run_git(project_root, args)
    if result.returncode != 0:
        return []
    files = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
    return sorted(dict.fromkeys(files))


def parse_added_lines(diff_text: str) -> Dict[str, Set[int]]:
    added: Dict[str, Set[int]] = {}
    current_file: Optional[str] = None
    new_line_no: Optional[int] = None

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("+++ "):
            target = raw_line[4:].strip()
            if target == "/dev/null":
                current_file = None
            elif target.startswith("b/"):
                current_file = target[2:]
            else:
                current_file = target
            new_line_no = None
            continue

        if raw_line.startswith("@@ "):
            match = HUNK_PATTERN.match(raw_line)
            if match:
                new_line_no = int(match.group(1))
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            if current_file is not None and new_line_no is not None:
                added.setdefault(current_file.replace("\\", "/"), set()).add(new_line_no)
                new_line_no += 1
            continue

        if raw_line.startswith("-") and not raw_line.startswith("---"):
            continue

        if raw_line.startswith(" ") and new_line_no is not None:
            new_line_no += 1

    return added


def added_lines_from_git(project_root: Path, source: str) -> Dict[str, Set[int]]:
    if source == "staged":
        args = ["diff", "--cached", "--unified=0", "--no-color"]
    elif source == "unstaged":
        args = ["diff", "--unified=0", "--no-color"]
    else:
        args = ["show", "--unified=0", "--no-color", "--pretty=format:", "HEAD"]
    result = run_git(project_root, args)
    if result.returncode != 0:
        return {}
    return parse_added_lines(result.stdout)


def rel_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def is_test_file(rel_file: str) -> bool:
    path = Path(rel_file)
    name = path.name.lower()
    text = rel_file.lower().replace("\\", "/")
    return (
        path.suffix.lower() in TEST_EXTENSIONS
        and (
            ".test." in name
            or ".spec." in name
            or "/tests/" in text
            or "/__tests__/" in text
            or name.startswith("test_")
        )
    )


def is_config_file(rel_file: str) -> bool:
    path = Path(rel_file)
    name = path.name.lower()
    config_names = {
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "tsconfig.json",
        "pyproject.toml",
        "requirements.txt",
        ".eslintrc",
        ".eslintrc.js",
        ".eslintrc.json",
        "eslint.config.js",
        "eslint.config.mjs",
        ".prettierrc",
        ".prettierrc.json",
        ".env",
        ".env.local",
    }
    if name in config_names:
        return True
    if name.startswith(".env"):
        return True
    if path.suffix.lower() in {".json", ".yaml", ".yml", ".toml", ".ini", ".lock"}:
        return True
    return False


def should_scan_file(rel_file: str) -> bool:
    normalized = rel_file.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    if any(part in SKIP_DIRS for part in parts):
        return False
    path = Path(normalized)
    if path.suffix.lower() not in CODE_EXTENSIONS:
        return False
    if is_test_file(normalized):
        return False
    if is_config_file(normalized):
        return False
    return True


def suggestion(
    file_path: str,
    line: int,
    priority: str,
    category: str,
    message: str,
) -> Dict[str, object]:
    return {
        "file": file_path,
        "line": line,
        "priority": priority,
        "category": category,
        "suggestion": message,
        "effort": EFFORT_BY_CATEGORY.get(category, "low"),
    }


def parse_python_functions(file_path: Path, rel_file: str, warnings: List[str]) -> List[Tuple[str, int, int]]:
    source = read_text(file_path)
    if not source:
        return []
    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        warnings.append(f"Python AST parse failed for {rel_file}: {exc.msg}")
        return []
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"Python AST parse failed for {rel_file}: {exc}")
        return []

    functions: List[Tuple[str, int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = int(getattr(node, "lineno", 0) or 0)
            end = int(getattr(node, "end_lineno", start) or start)
            functions.append((node.name, start, end))
    return functions


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


def parse_js_functions(file_path: Path, rel_file: str, warnings: List[str]) -> List[Tuple[str, int, int]]:
    lines = read_text(file_path).splitlines()
    if not lines:
        return []

    patterns = [
        re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^()]*\)\s*=>"),
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?[A-Za-z_$][\w$]*\s*=>"),
        re.compile(r"^\s*(?:public|private|protected|static|async|\s)*([A-Za-z_$][\w$]*)\s*\([^;]*\)\s*\{"),
    ]
    reserved = {"if", "for", "while", "switch", "catch", "return", "new", "else", "try"}
    result: List[Tuple[str, int, int]] = []

    for idx, line in enumerate(lines):
        function_name: Optional[str] = None
        for pattern in patterns:
            match = pattern.search(line)
            if not match:
                continue
            candidate = match.group(1)
            if candidate in reserved:
                continue
            function_name = candidate
            break

        if not function_name:
            continue

        end_idx = estimate_js_block_end(lines, idx)
        if end_idx is None:
            warnings.append(f"JS/TS block parse failed for {rel_file}:{idx + 1}")
            continue
        result.append((function_name, idx + 1, end_idx + 1))

    unique = sorted(dict.fromkeys(result), key=lambda item: (item[1], item[0]))
    return unique


def collect_long_function_suggestions(
    file_path: Path,
    rel_file: str,
    warnings: List[str],
) -> List[Dict[str, object]]:
    ext = file_path.suffix.lower()
    if ext == ".py":
        functions = parse_python_functions(file_path, rel_file, warnings)
    else:
        functions = parse_js_functions(file_path, rel_file, warnings)

    suggestions: List[Dict[str, object]] = []
    for name, start, end in functions:
        length = end - start + 1
        if length > 40:
            suggestions.append(
                suggestion(
                    rel_file,
                    start,
                    "medium",
                    "long_function",
                    f"Function {name} is {length} lines, consider extracting smaller helpers.",
                )
            )
    return suggestions


def collect_large_file_suggestion(file_path: Path, rel_file: str) -> Optional[Dict[str, object]]:
    total_lines = len(read_text(file_path).splitlines())
    if total_lines <= 400:
        return None
    return suggestion(
        rel_file,
        1,
        "medium",
        "large_file",
        f"File has {total_lines} lines, consider splitting by responsibility.",
    )


def line_scope(total_lines: int, added_lines: Set[int]) -> Set[int]:
    if added_lines:
        return {line for line in added_lines if 1 <= line <= total_lines}
    return set(range(1, total_lines + 1))


def collect_todo_suggestions(rel_file: str, lines: List[str], scope_lines: Set[int]) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    for idx, line in enumerate(lines, start=1):
        if idx not in scope_lines:
            continue
        if TODO_PATTERN.search(line):
            results.append(
                suggestion(
                    rel_file,
                    idx,
                    "low",
                    "todo_fixme",
                    f"Pending TODO/FIXME at line {idx}: {line.strip()}",
                )
            )
        if len(results) >= 2:
            break
    return results


def normalize_line_for_dup(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def collect_duplicate_suggestion(rel_file: str, lines: List[str]) -> Optional[Dict[str, object]]:
    window = 3
    if len(lines) < window:
        return None

    seen: Dict[str, List[int]] = {}
    normalized = [normalize_line_for_dup(line) for line in lines]
    for idx in range(0, len(normalized) - window + 1):
        block = normalized[idx : idx + window]
        if any(not item for item in block):
            continue
        key = "\n".join(block)
        seen.setdefault(key, []).append(idx + 1)

    for starts in seen.values():
        if len(starts) >= 2:
            first = starts[0]
            second = starts[1]
            return suggestion(
                rel_file,
                first,
                "medium",
                "duplicate_block",
                f"Lines {first}-{first + 2} repeat at lines {second}-{second + 2}, consider extracting shared logic.",
            )
    return None


def collect_magic_number_suggestion(rel_file: str, lines: List[str], scope_lines: Set[int]) -> Optional[Dict[str, object]]:
    ignore_keywords = {"port", "timeout", "version", "status", "http", "https"}
    for idx, line in enumerate(lines, start=1):
        if idx not in scope_lines:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue
        lowered = stripped.lower()
        if any(keyword in lowered for keyword in ignore_keywords):
            continue
        for match in MAGIC_NUMBER_PATTERN.finditer(stripped):
            try:
                value = float(match.group(1))
            except ValueError:
                continue
            if value in {0.0, 1.0}:
                continue
            return suggestion(
                rel_file,
                idx,
                "low",
                "magic_number",
                f"Magic number {match.group(1)} at line {idx}, consider a named constant.",
            )
    return None


def detect_base_indent(lines: List[str]) -> int:
    indents: List[int] = []
    for line in lines:
        if not line.strip():
            continue
        leading = len(line) - len(line.lstrip(" "))
        if leading > 0:
            indents.append(leading)
    if not indents:
        return 4
    return max(1, min(indents))


def collect_deep_nesting_suggestion(rel_file: str, lines: List[str], scope_lines: Set[int]) -> Optional[Dict[str, object]]:
    base_indent = detect_base_indent(lines)
    for idx, line in enumerate(lines, start=1):
        if idx not in scope_lines:
            continue
        if not line.strip():
            continue
        spaces = len(line) - len(line.lstrip(" "))
        level = spaces // base_indent if base_indent else 0
        if level > 4:
            return suggestion(
                rel_file,
                idx,
                "medium",
                "deep_nesting",
                f"Deep nesting detected at line {idx}, consider early return or extraction.",
            )
    return None


def collect_debug_suggestions(rel_file: str, lines: List[str], scope_lines: Set[int], extension: str) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    pattern = DEBUG_PATTERN_PY if extension == ".py" else DEBUG_PATTERN_JS
    for idx, line in enumerate(lines, start=1):
        if idx not in scope_lines:
            continue
        if pattern.search(line):
            results.append(
                suggestion(
                    rel_file,
                    idx,
                    "low",
                    "debug_statement",
                    f"Debug statement at line {idx}, remove before production.",
                )
            )
        if len(results) >= 2:
            break
    return results


def collect_test_files(project_root: Path) -> List[str]:
    test_files: List[str] = []
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        root_path = Path(root)
        for name in files:
            path = root_path / name
            rel = path.resolve().relative_to(project_root.resolve()).as_posix()
            if is_test_file(rel):
                test_files.append(rel)
    return sorted(dict.fromkeys(test_files))


def has_related_test(rel_file: str, all_tests: List[str]) -> bool:
    stem = Path(rel_file).stem.lower()
    stem_base = stem.split(".")[0]
    parent = Path(rel_file).parent.as_posix().lower()

    for test in all_tests:
        test_lower = test.lower()
        test_name = Path(test).stem.lower()
        if stem in test_name or stem_base in test_name:
            return True
        if parent and parent in test_lower and ("tests/" in test_lower or "__tests__/" in test_lower):
            return True
    return False


def format_summary(suggestions: List[Dict[str, object]], scanned_count: int) -> str:
    if not suggestions:
        return f"No improvement suggestions found for {scanned_count} changed files."
    counts = {"high": 0, "medium": 0, "low": 0}
    for item in suggestions:
        counts[str(item.get("priority", "low"))] += 1
    total = len(suggestions)
    return (
        f"{total} suggestions for {scanned_count} changed files "
        f"({counts['high']} high, {counts['medium']} medium, {counts['low']} low priority)"
    )


def scan_file(
    project_root: Path,
    rel_file: str,
    added_lines: Set[int],
    all_tests: List[str],
    warnings: List[str],
) -> List[Dict[str, object]]:
    file_path = project_root / rel_file
    if not file_path.exists() or not file_path.is_file():
        warnings.append(f"File does not exist, skipped: {rel_file}")
        return []

    lines = read_text(file_path).splitlines()
    if not lines:
        return []

    scope_lines = line_scope(len(lines), added_lines)
    suggestions: List[Dict[str, object]] = []

    large_file = collect_large_file_suggestion(file_path, rel_file)
    if large_file:
        suggestions.append(large_file)

    suggestions.extend(collect_long_function_suggestions(file_path, rel_file, warnings))
    suggestions.extend(collect_todo_suggestions(rel_file, lines, scope_lines))

    duplicate = collect_duplicate_suggestion(rel_file, lines)
    if duplicate:
        suggestions.append(duplicate)

    if not has_related_test(rel_file, all_tests):
        suggestions.append(
            suggestion(
                rel_file,
                1,
                "high",
                "missing_tests",
                f"No test file found for {Path(rel_file).name}, consider adding tests.",
            )
        )

    magic = collect_magic_number_suggestion(rel_file, lines, scope_lines)
    if magic:
        suggestions.append(magic)

    deep = collect_deep_nesting_suggestion(rel_file, lines, scope_lines)
    if deep:
        suggestions.append(deep)

    suggestions.extend(collect_debug_suggestions(rel_file, lines, scope_lines, file_path.suffix.lower()))
    return suggestions


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    changed_files = parse_changed_files(args.changed_files)
    git_available = git_ready(project_root)
    if not changed_files:
        if not git_available:
            emit({"status": "error", "message": "Git required when --changed-files is not provided."})
            return 1
        changed_files = changed_files_from_git(project_root, args.source)

    changed_files = sorted(dict.fromkeys(path for path in changed_files if path))
    changed_set = set(changed_files)
    added_lines_map = added_lines_from_git(project_root, args.source) if git_available else {}

    warnings: List[str] = []
    all_tests = collect_test_files(project_root)
    all_suggestions: List[Dict[str, object]] = []
    scanned_count = 0

    for rel_file in changed_files:
        rel_file = rel_file.replace("\\", "/")
        if rel_file not in changed_set:
            continue
        if not should_scan_file(rel_file):
            continue
        scanned_count += 1
        all_suggestions.extend(
            scan_file(
                project_root=project_root,
                rel_file=rel_file,
                added_lines=added_lines_map.get(rel_file, set()),
                all_tests=all_tests,
                warnings=warnings,
            )
        )

    all_suggestions.sort(
        key=lambda item: (
            PRIORITY_ORDER.get(str(item.get("priority", "low")), 99),
            str(item.get("file", "")),
            int(item.get("line", 0)),
        )
    )
    limited = all_suggestions[: max(0, int(args.max_suggestions))]

    payload: Dict[str, object] = {
        "status": "suggestions_ready",
        "changed_files_scanned": scanned_count,
        "suggestions": limited,
        "summary": format_summary(limited, scanned_count),
    }
    if warnings:
        payload["warnings"] = sorted(dict.fromkeys(warnings))

    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
