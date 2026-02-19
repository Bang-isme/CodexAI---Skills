#!/usr/bin/env python3
"""
Gather code context to support teaching-mode explanations.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".next"}
CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}

IMPORT_REF_PATTERN = re.compile(
    r"(?:from\s+['\"]([^'\"]+)['\"]|require\(\s*['\"]([^'\"]+)['\"]\s*\)|import\s+['\"]([^'\"]+)['\"])"
)
JS_IMPORT_FROM_PATTERN = re.compile(r"^\s*import\s+(.+?)\s+from\s+['\"]([^'\"]+)['\"]")
JS_IMPORT_SIDE_EFFECT_PATTERN = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]")
JS_REQUIRE_PATTERN = re.compile(r"^\s*(?:const|let|var)\s+(.+?)\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)")


@dataclass
class JsBraceState:
    in_block_comment: bool = False
    in_single: bool = False
    in_double: bool = False
    in_template: bool = False
    escaped: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Extract file context for teaching mode.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python explain_code.py --project-root <path> --file <file>\n"

            "  python explain_code.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--file", required=True, help="Target file path (absolute or project-relative)")
    parser.add_argument("--function", default="", help="Optional function name to focus on")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def parse_python_params(node: ast.AST) -> List[str]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    names: List[str] = []
    for arg in getattr(node.args, "posonlyargs", []):
        names.append(arg.arg)
    for arg in node.args.args:
        names.append(arg.arg)
    if node.args.vararg:
        names.append(f"*{node.args.vararg.arg}")
    for arg in node.args.kwonlyargs:
        names.append(arg.arg)
    if node.args.kwarg:
        names.append(f"**{node.args.kwarg.arg}")
    return names


def parse_python_file(file_path: Path, root: Path, warnings: List[str]) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    source = read_text(file_path)
    if not source:
        return [], []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        warnings.append(f"Python AST parse failed for {rel_path(file_path, root)}: {exc.msg}")
        return [], []
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"Python AST parse failed for {rel_path(file_path, root)}: {exc}")
        return [], []

    functions: List[Dict[str, object]] = []
    imports: List[Dict[str, object]] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            line_start = int(getattr(node, "lineno", 0) or 0)
            line_end = int(getattr(node, "end_lineno", line_start) or line_start)
            functions.append(
                {
                    "name": node.name,
                    "line_start": line_start,
                    "line_end": line_end,
                    "params": parse_python_params(node),
                }
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".")[-1]
                imports.append({"module": alias.name, "names": [local_name]})
        elif isinstance(node, ast.ImportFrom):
            base = "." * int(getattr(node, "level", 0) or 0)
            module = f"{base}{node.module or ''}"
            names = [alias.asname or alias.name for alias in node.names]
            imports.append({"module": module, "names": names})

    functions.sort(key=lambda item: (int(item["line_start"]), str(item["name"])))
    return functions, dedupe_imports(imports)


def parse_js_params(raw: str) -> List[str]:
    cleaned: List[str] = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        token = token.strip("() ").lstrip(".")
        token = token.split("=", 1)[0].strip()
        match = re.match(r"^([A-Za-z_$][\w$]*)\s*:\s*.+$", token)
        if match:
            token = match.group(1)
        token = token.strip("() ").strip()
        if token in {"async", "()"}:
            continue
        if token:
            cleaned.append(token)
    return cleaned


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


def estimate_js_block_end(lines: List[str], start_index: int) -> Optional[int]:
    depth = 0
    opened = False
    state = JsBraceState()
    for idx in range(start_index, len(lines)):
        open_count, close_count, state = js_brace_counts(lines[idx], state)
        if open_count > 0:
            opened = True
        depth += open_count
        depth -= close_count
        if opened and depth <= 0:
            return idx
    return None


def parse_js_import_clause(clause: str) -> List[str]:
    names: List[str] = []
    text = clause.strip()
    if not text:
        return names

    if text.startswith("* as "):
        wildcard = text[5:].strip()
        if wildcard:
            names.append(wildcard)
        return names

    if "{" in text and "}" in text:
        before, _, rest = text.partition("{")
        if before.strip().rstrip(","):
            names.append(before.strip().rstrip(","))
        inside = rest.rsplit("}", 1)[0]
        for part in inside.split(","):
            item = part.strip()
            if not item:
                continue
            if " as " in item:
                item = item.split(" as ", 1)[1].strip()
            if item:
                names.append(item)
        return names

    names.append(text)
    return names


def parse_js_file(file_path: Path, root: Path, warnings: List[str]) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    source = read_text(file_path)
    if not source:
        return [], []

    lines = source.splitlines()
    functions: List[Dict[str, object]] = []
    imports: List[Dict[str, object]] = []

    patterns = [
        re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)"),
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(([^()]*)\)\s*=>"),
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?([A-Za-z_$][\w$]*)\s*=>"),
        re.compile(r"^\s*(?:public|private|protected|static|async|\s)*([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{"),
    ]
    reserved = {"if", "for", "while", "switch", "catch", "return", "new", "else", "try"}

    for idx, line in enumerate(lines):
        for pattern in patterns:
            match = pattern.search(line)
            if not match:
                continue
            function_name = match.group(1)
            if function_name in reserved:
                continue
            params_raw = match.group(2) if len(match.groups()) > 1 else ""
            params = parse_js_params(params_raw)
            end_idx = estimate_js_block_end(lines, idx)
            if end_idx is None:
                warnings.append(f"JS/TS block parse failed for {rel_path(file_path, root)}:{idx + 1}")
                continue
            functions.append(
                {
                    "name": function_name,
                    "line_start": idx + 1,
                    "line_end": end_idx + 1,
                    "params": params,
                }
            )
            break

    for line in lines:
        from_match = JS_IMPORT_FROM_PATTERN.search(line)
        if from_match:
            names = parse_js_import_clause(from_match.group(1))
            imports.append({"module": from_match.group(2), "names": names})
            continue

        side_match = JS_IMPORT_SIDE_EFFECT_PATTERN.search(line)
        if side_match:
            imports.append({"module": side_match.group(1), "names": []})
            continue

        require_match = JS_REQUIRE_PATTERN.search(line)
        if require_match:
            names = parse_js_import_clause(require_match.group(1))
            imports.append({"module": require_match.group(2), "names": names})

    unique_functions: Dict[Tuple[str, int, int], Dict[str, object]] = {}
    for item in functions:
        key = (str(item["name"]), int(item["line_start"]), int(item["line_end"]))
        unique_functions[key] = item

    ordered_functions = sorted(unique_functions.values(), key=lambda item: (int(item["line_start"]), str(item["name"])))
    return ordered_functions, dedupe_imports(imports)


def dedupe_imports(imports: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    seen: Set[Tuple[str, Tuple[str, ...]]] = set()
    result: List[Dict[str, object]] = []
    for item in imports:
        module = str(item.get("module", "")).strip()
        names = [str(name).strip() for name in list(item.get("names", [])) if str(name).strip()]
        key = (module, tuple(sorted(names)))
        if key in seen:
            continue
        seen.add(key)
        result.append({"module": module, "names": names})
    result.sort(key=lambda item: str(item["module"]))
    return result


def expand_module_base(base: Path) -> List[Path]:
    candidates: List[Path] = []
    if base.suffix:
        candidates.append(base)
    else:
        for ext in CODE_EXTENSIONS:
            candidates.append(base.with_suffix(ext))
        for ext in CODE_EXTENSIONS:
            candidates.append(base / f"index{ext}")
    return candidates


def module_matches_target(module: str, importer_path: Path, target_path: Path, project_root: Path) -> bool:
    normalized_module = module.replace("\\", "/").strip()
    target_abs = target_path.resolve()
    target_rel_no_ext = rel_path(target_path, project_root)
    target_rel_no_ext = str(Path(target_rel_no_ext).with_suffix("")).replace("\\", "/")
    target_name_no_ext = target_path.stem

    if normalized_module.startswith(".") or normalized_module.startswith("/"):
        base = (importer_path.parent / normalized_module) if normalized_module.startswith(".") else (project_root / normalized_module.lstrip("/"))
        for candidate in expand_module_base(base):
            try:
                if candidate.resolve() == target_abs:
                    return True
            except OSError:
                continue
    else:
        if normalized_module.endswith(target_rel_no_ext):
            return True
        if normalized_module.endswith(target_name_no_ext):
            return True
        if normalized_module.endswith(target_path.name):
            return True

    return False


def collect_code_files(project_root: Path) -> List[Path]:
    files: List[Path] = []
    for root, dirs, names in os.walk(project_root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        root_path = Path(root)
        for name in names:
            path = root_path / name
            if path.suffix.lower() in CODE_EXTENSIONS:
                files.append(path)
    return sorted(files)


def find_imported_by(project_root: Path, target_file: Path) -> List[str]:
    imported_by: List[str] = []
    for candidate in collect_code_files(project_root):
        try:
            if candidate.resolve() == target_file.resolve():
                continue
        except OSError:
            continue

        content = read_text(candidate)
        if not content:
            continue
        found = False
        for match in IMPORT_REF_PATTERN.finditer(content):
            module = next((item for item in match.groups() if item), "")
            if not module:
                continue
            if module_matches_target(module, candidate, target_file, project_root):
                imported_by.append(rel_path(candidate, project_root))
                found = True
                break
        if found:
            continue

    return sorted(dict.fromkeys(imported_by))


def complexity_estimate(total_lines: int, function_count: int) -> str:
    if total_lines >= 300:
        return "high"
    if total_lines < 100 and function_count < 5:
        return "low"
    return "medium"


def filter_functions(functions: List[Dict[str, object]], focus_name: str) -> List[Dict[str, object]]:
    if not focus_name.strip():
        return functions
    exact = [item for item in functions if str(item.get("name")) == focus_name]
    if exact:
        return exact
    lowered = [item for item in functions if str(item.get("name", "")).lower() == focus_name.lower()]
    return lowered


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    file_arg = Path(args.file)
    target_file = file_arg if file_arg.is_absolute() else (project_root / file_arg)
    target_file = target_file.resolve()

    if not target_file.exists() or not target_file.is_file():
        emit({"status": "error", "message": f"Target file does not exist or is not a file: {target_file}"})
        return 1

    warnings: List[str] = []
    ext = target_file.suffix.lower()
    if ext not in CODE_EXTENSIONS:
        warnings.append(f"Unsupported extension for function parsing: {ext}")

    if ext == ".py":
        functions, imports = parse_python_file(target_file, project_root, warnings)
    elif ext in {".js", ".jsx", ".ts", ".tsx"}:
        functions, imports = parse_js_file(target_file, project_root, warnings)
    else:
        functions, imports = [], []

    focused_functions = filter_functions(functions, args.function)
    if args.function.strip() and not focused_functions:
        warnings.append(f"Function '{args.function}' was not found in {rel_path(target_file, project_root)}")

    total_lines = len(read_text(target_file).splitlines())
    payload: Dict[str, object] = {
        "file": rel_path(target_file, project_root),
        "total_lines": total_lines,
        "functions": focused_functions,
        "imports": imports,
        "imported_by": find_imported_by(project_root, target_file),
        "complexity_estimate": complexity_estimate(total_lines, len(functions)),
    }
    if warnings:
        payload["warnings"] = sorted(dict.fromkeys(warnings))

    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
