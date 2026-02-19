#!/usr/bin/env python3
"""
Build a project knowledge graph with dependencies, module boundaries, routes, and models.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".next"}
CODE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".py", ".mjs", ".cjs"}
RESOLVE_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".json"]
TEST_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".py"}

IMPORT_FROM_PATTERN = re.compile(r"^\s*import\s+.+?\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
IMPORT_SIDE_PATTERN = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
REQUIRE_PATTERN = re.compile(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)")
PY_IMPORT_PATTERN = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)", re.MULTILINE)
PY_FROM_IMPORT_PATTERN = re.compile(r"^\s*from\s+([A-Za-z_][\w.]*|\.+[\w.]*)\s+import\s+", re.MULTILINE)

JS_IMPORT_DEFAULT_PATTERN = re.compile(r"^\s*import\s+([A-Za-z_$][\w$]*)\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
JS_IMPORT_NAMED_PATTERN = re.compile(r"^\s*import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
JS_REQUIRE_ALIAS_PATTERN = re.compile(r"^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)", re.MULTILINE)
JS_REQUIRE_NAMED_PATTERN = re.compile(r"^\s*(?:const|let|var)\s+\{([^}]+)\}\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)", re.MULTILINE)

ROUTE_CALL_PATTERN = re.compile(
    r"\b(?:router|app)\.(get|post|put|delete|patch|options|head|all)\s*\(\s*['\"`]([^'\"`]+)['\"`]\s*,\s*(.+)"
)
ROUTE_FILE_HINT = re.compile(r"route", re.IGNORECASE)

MODULE_HINTS = {
    "controllers",
    "services",
    "models",
    "utils",
    "routes",
    "middlewares",
    "middleware",
    "config",
    "repositories",
    "repository",
    "hooks",
    "store",
    "stores",
    "pages",
    "components",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Build project knowledge graph JSON.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python build_knowledge_graph.py --project-root <path>\n"

            "  python build_knowledge_graph.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--output", default="", help="Output graph path")
    parser.add_argument("--include-tests", action="store_true", help="Include test files in graph")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def normalize_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_test_file(rel_path: str) -> bool:
    path = Path(rel_path)
    if path.suffix.lower() not in TEST_EXTENSIONS:
        return False
    lower = rel_path.lower()
    name = path.name.lower()
    return (
        ".test." in name
        or ".spec." in name
        or "/tests/" in lower
        or "/__tests__/" in lower
        or name.startswith("test_")
    )


def collect_code_files(project_root: Path, include_tests: bool) -> List[Path]:
    files: List[Path] = []
    for current_root, dirs, names in os.walk(project_root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        root_path = Path(current_root)
        for name in names:
            path = root_path / name
            if path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            rel = normalize_rel(path, project_root)
            if not include_tests and is_test_file(rel):
                continue
            files.append(path)
    return sorted(files)


def read_limited(path: Path, warnings: List[str], rel_file: str) -> Tuple[str, List[str]]:
    lines: List[str] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line_no, raw in enumerate(handle, start=1):
                if line_no <= 500:
                    lines.append(raw.rstrip("\n\r"))
                if line_no > 2000:
                    warnings.append(f"Large file truncated to first 500 lines: {rel_file}")
                    break
    except OSError:
        warnings.append(f"Unable to read file: {rel_file}")
        return "", []
    text = "\n".join(lines)
    return text, lines


def parse_import_modules(file_path: Path, content: str) -> List[str]:
    ext = file_path.suffix.lower()
    modules: List[str] = []
    if ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        modules.extend(IMPORT_FROM_PATTERN.findall(content))
        modules.extend(IMPORT_SIDE_PATTERN.findall(content))
        modules.extend(REQUIRE_PATTERN.findall(content))
    elif ext == ".py":
        modules.extend(PY_IMPORT_PATTERN.findall(content))
        modules.extend(PY_FROM_IMPORT_PATTERN.findall(content))
    return modules


def expand_candidates(base: Path) -> List[Path]:
    candidates: List[Path] = []
    if base.suffix:
        candidates.append(base)
    else:
        for ext in RESOLVE_EXTENSIONS:
            candidates.append(base.with_suffix(ext))
        for ext in RESOLVE_EXTENSIONS:
            candidates.append(base / f"index{ext}")
    return candidates


def inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def choose_existing(candidates: Iterable[Path], root: Path, existing: Set[Path]) -> Optional[Path]:
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in existing:
            return resolved
        if resolved.exists() and resolved.is_file() and inside_root(resolved, root):
            return resolved
    return None


def resolve_js_module(importer: Path, module: str, root: Path, existing: Set[Path]) -> Optional[Path]:
    value = module.strip()
    if not value or value.startswith(("http://", "https://", "node:")):
        return None
    if value.startswith("."):
        base = importer.parent / value
    elif value.startswith("/"):
        base = root / value.lstrip("/")
    elif value.startswith("@/"):
        base = root / value[2:]
    elif value.startswith("src/"):
        base = root / value
    else:
        return None
    return choose_existing(expand_candidates(base), root, existing)


def resolve_python_module(importer: Path, module: str, root: Path, existing: Set[Path]) -> Optional[Path]:
    value = module.strip()
    if not value:
        return None
    candidates: List[Path] = []
    if value.startswith("."):
        level = len(value) - len(value.lstrip("."))
        suffix = value[level:]
        base = importer.parent
        for _ in range(max(level - 1, 0)):
            base = base.parent
        if suffix:
            target = base / Path(suffix.replace(".", "/"))
            candidates.extend([target.with_suffix(".py"), target / "__init__.py"])
        else:
            candidates.append(base / "__init__.py")
    else:
        target = root / Path(value.replace(".", "/"))
        candidates.extend([target.with_suffix(".py"), target / "__init__.py"])
    return choose_existing(candidates, root, existing)


def build_dependency_graph(
    project_root: Path,
    files: List[Path],
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, str], Dict[str, List[str]]]:
    existing = {path.resolve() for path in files}
    imports_map: Dict[str, Set[str]] = defaultdict(set)
    reverse_map: Dict[str, Set[str]] = defaultdict(set)
    raw_content: Dict[str, str] = {}
    lines_cache: Dict[str, List[str]] = {}
    warnings: List[str] = []

    for file_path in files:
        rel = normalize_rel(file_path, project_root)
        content, lines = read_limited(file_path, warnings, rel)
        raw_content[rel] = content
        lines_cache[rel] = lines
        if not content:
            continue
        for module in parse_import_modules(file_path, content):
            if file_path.suffix.lower() == ".py":
                resolved = resolve_python_module(file_path, module, project_root, existing)
            else:
                resolved = resolve_js_module(file_path, module, project_root, existing)
            if not resolved:
                continue
            target_rel = normalize_rel(resolved, project_root)
            if target_rel == rel:
                continue
            imports_map[rel].add(target_rel)
            reverse_map[target_rel].add(rel)

    for rel in [normalize_rel(path, project_root) for path in files]:
        imports_map.setdefault(rel, set())
        reverse_map.setdefault(rel, set())

    return imports_map, reverse_map, raw_content, {"warnings": warnings, "lines": lines_cache}  # type: ignore[return-value]


def module_name(rel_file: str) -> str:
    parts = list(Path(rel_file).parts)
    if not parts:
        return "root"
    lowered = [part.lower() for part in parts]
    for hint in MODULE_HINTS:
        if hint in lowered:
            return "middlewares" if hint == "middleware" else hint
    if lowered[0] in {"src", "app", "server", "backend", "frontend", "lib"} and len(lowered) > 1:
        return lowered[1]
    return lowered[0]


def build_module_boundaries(file_deps: Dict[str, Set[str]]) -> Tuple[Dict[str, Dict[str, Set[str]]], List[List[str]]]:
    module_map: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: {"imports_from": set(), "imported_by": set()})
    module_graph: Dict[str, Set[str]] = defaultdict(set)

    for source, imports in file_deps.items():
        source_module = module_name(source)
        module_map[source_module]
        for target in imports:
            target_module = module_name(target)
            module_map[target_module]
            if source_module == target_module:
                continue
            module_map[source_module]["imports_from"].add(target_module)
            module_map[target_module]["imported_by"].add(source_module)
            module_graph[source_module].add(target_module)

    cycles = strongly_connected_components(module_graph)
    return module_map, cycles


def strongly_connected_components(graph: Dict[str, Set[str]]) -> List[List[str]]:
    index = 0
    indices: Dict[str, int] = {}
    low_links: Dict[str, int] = {}
    stack: List[str] = []
    on_stack: Set[str] = set()
    result: List[List[str]] = []

    def strong_connect(node: str) -> None:
        nonlocal index
        indices[node] = index
        low_links[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in sorted(graph.get(node, set())):
            if neighbor not in indices:
                strong_connect(neighbor)
                low_links[node] = min(low_links[node], low_links[neighbor])
            elif neighbor in on_stack:
                low_links[node] = min(low_links[node], indices[neighbor])

        if low_links[node] == indices[node]:
            component: List[str] = []
            while stack:
                popped = stack.pop()
                on_stack.discard(popped)
                component.append(popped)
                if popped == node:
                    break
            component = sorted(component)
            if len(component) > 1:
                result.append(component)
            elif len(component) == 1 and component[0] in graph.get(component[0], set()):
                result.append(component)

    for node in sorted(set(graph.keys()) | {item for values in graph.values() for item in values}):
        if node not in indices:
            strong_connect(node)

    result.sort()
    return result


def parse_aliases_for_route_file(
    route_path: Path,
    route_rel: str,
    content: str,
    project_root: Path,
    existing: Set[Path],
) -> Tuple[Dict[str, str], Dict[str, Tuple[str, str]]]:
    alias_to_module: Dict[str, str] = {}
    symbol_to_module: Dict[str, Tuple[str, str]] = {}

    def resolve(module: str) -> Optional[str]:
        resolved = resolve_js_module(route_path, module, project_root, existing)
        if not resolved:
            return None
        return normalize_rel(resolved, project_root)

    for alias, module in JS_IMPORT_DEFAULT_PATTERN.findall(content):
        module_rel = resolve(module)
        if module_rel:
            alias_to_module[alias.strip()] = module_rel

    for inside, module in JS_IMPORT_NAMED_PATTERN.findall(content):
        module_rel = resolve(module)
        if not module_rel:
            continue
        for part in inside.split(","):
            token = part.strip()
            if not token:
                continue
            if " as " in token:
                source, local = [value.strip() for value in token.split(" as ", 1)]
            else:
                source = token
                local = token
            symbol_to_module[local] = (module_rel, source)

    for alias, module in JS_REQUIRE_ALIAS_PATTERN.findall(content):
        module_rel = resolve(module)
        if module_rel:
            alias_to_module[alias.strip()] = module_rel

    for inside, module in JS_REQUIRE_NAMED_PATTERN.findall(content):
        module_rel = resolve(module)
        if not module_rel:
            continue
        for part in inside.split(","):
            token = part.strip()
            if not token:
                continue
            if ":" in token:
                source, local = [value.strip() for value in token.split(":", 1)]
            else:
                source = token
                local = token
            symbol_to_module[local] = (module_rel, source)

    return alias_to_module, symbol_to_module


def normalize_handler(raw: str) -> str:
    token = raw.strip()
    token = token.rstrip(");")
    token = token.rstrip(")")
    token = token.strip()
    if "," in token:
        parts = [part.strip() for part in token.split(",") if part.strip()]
        if parts:
            token = parts[-1]
    wrapper = re.match(r"^[A-Za-z_$][\w$]*\(([^()]+)\)$", token)
    if wrapper:
        inner = wrapper.group(1).strip()
        if "." in inner:
            token = inner
    return token.strip()


def model_names_from_controller(controller_rel: str, file_deps: Dict[str, Set[str]]) -> List[str]:
    names: Set[str] = set()
    for dep in file_deps.get(controller_rel, set()):
        lower = dep.lower()
        if "/models/" in lower or ".model." in lower:
            stem = Path(dep).stem
            stem = re.sub(r"\.model$", "", stem, flags=re.IGNORECASE)
            names.add(stem)
    return sorted(names)


def build_api_route_map(
    project_root: Path,
    files: List[Path],
    file_deps: Dict[str, Set[str]],
    raw_content: Dict[str, str],
) -> List[Dict[str, object]]:
    existing = {path.resolve() for path in files}
    routes: List[Dict[str, object]] = []

    for route_path in files:
        ext = route_path.suffix.lower()
        if ext not in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
            continue
        route_rel = normalize_rel(route_path, project_root)
        content = raw_content.get(route_rel, "")
        if not content:
            continue
        if not ROUTE_FILE_HINT.search(route_rel) and "router." not in content and "app." not in content:
            continue

        alias_map, symbol_map = parse_aliases_for_route_file(route_path, route_rel, content, project_root, existing)
        for line in content.splitlines():
            match = ROUTE_CALL_PATTERN.search(line)
            if not match:
                continue
            method = match.group(1).upper()
            path_value = match.group(2).strip()
            handler_chunk = match.group(3).strip()
            handler_token = normalize_handler(handler_chunk)

            handler_label = handler_token
            model_hints: List[str] = []
            if "." in handler_token:
                alias, method_name = handler_token.split(".", 1)
                controller_rel = alias_map.get(alias.strip())
                if controller_rel:
                    handler_label = f"{Path(controller_rel).stem}.{method_name.strip()}"
                    model_hints = model_names_from_controller(controller_rel, file_deps)
            else:
                symbol = symbol_map.get(handler_token)
                if symbol:
                    controller_rel, exported = symbol
                    handler_label = f"{Path(controller_rel).stem}.{exported}"
                    model_hints = model_names_from_controller(controller_rel, file_deps)

            route_item: Dict[str, object] = {
                "method": method,
                "path": path_value,
                "handler": handler_label,
                "file": route_rel,
            }
            if model_hints:
                route_item["models"] = model_hints
            routes.append(route_item)

    return routes


def extract_first_object_block(text: str, start_pos: int) -> str:
    brace_start = text.find("{", start_pos)
    if brace_start == -1:
        return ""
    depth = 0
    in_single = False
    in_double = False
    escaped = False
    for idx in range(brace_start, len(text)):
        ch = text[idx]
        if in_single:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == "'":
                in_single = False
            continue
        if in_double:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_double = False
            continue
        if ch == "'":
            in_single = True
            continue
        if ch == '"':
            in_double = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[brace_start : idx + 1]
    return ""


def extract_keys_from_block(block: str) -> List[str]:
    keys: List[str] = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^['\"]?([A-Za-z_][\w]*)['\"]?\s*:", stripped)
        if not match:
            continue
        key = match.group(1)
        if key.lower() in {"type", "required", "default", "ref", "allowNull", "primaryKey", "unique", "validate"}:
            continue
        keys.append(key)
    deduped = sorted(dict.fromkeys(keys))
    return deduped[:60]


def detect_model_type(text: str) -> str:
    lower = text.lower()
    if "new schema(" in lower or "mongoose.model(" in lower:
        return "mongoose"
    if "sequelize.define(" in lower or ".init(" in lower or "datatypes." in lower:
        return "sequelize"
    if "@entity" in lower or "typeorm" in lower:
        return "typeorm"
    return "unknown"


def detect_model_name(rel_file: str, text: str) -> str:
    patterns = [
        re.compile(r"mongoose\.model\(\s*['\"]([A-Za-z_]\w*)['\"]"),
        re.compile(r"sequelize\.define\(\s*['\"]([A-Za-z_]\w*)['\"]"),
        re.compile(r"class\s+([A-Za-z_]\w*)\s+extends\s+Model"),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1)
    stem = Path(rel_file).stem
    stem = re.sub(r"\.model$", "", stem, flags=re.IGNORECASE)
    return stem


def detect_relationships(text: str) -> List[Dict[str, str]]:
    relations: List[Dict[str, str]] = []
    for match in re.finditer(r"([A-Za-z_]\w*)\s*:\s*\{[^{}]*ref\s*:\s*['\"]([A-Za-z_]\w*)['\"]", text, flags=re.DOTALL):
        relations.append({"type": "ref", "target": match.group(2), "field": match.group(1)})
    for relation_type, target in re.findall(
        r"\.(belongsTo|hasMany|hasOne|belongsToMany)\(\s*([A-Za-z_]\w*)",
        text,
    ):
        relations.append({"type": relation_type, "target": target, "field": ""})
    unique: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()
    for relation in relations:
        key = (relation["type"], relation["target"], relation["field"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(relation)
    return unique


def build_data_model_map(
    project_root: Path,
    files: List[Path],
    raw_content: Dict[str, str],
) -> Dict[str, Dict[str, object]]:
    models: Dict[str, Dict[str, object]] = {}
    for file_path in files:
        rel = normalize_rel(file_path, project_root)
        lower = rel.lower()
        if "/models/" not in lower and "model" not in Path(rel).stem.lower():
            continue
        content = raw_content.get(rel, "")
        if not content:
            continue

        model_type = detect_model_type(content)
        model_name = detect_model_name(rel, content)

        block = ""
        schema_match = re.search(r"new\s+Schema\s*\(", content)
        define_match = re.search(r"sequelize\.define\s*\(", content)
        init_match = re.search(r"\.init\s*\(", content)
        if schema_match:
            block = extract_first_object_block(content, schema_match.end())
        elif define_match:
            block = extract_first_object_block(content, define_match.end())
        elif init_match:
            block = extract_first_object_block(content, init_match.end())

        fields = extract_keys_from_block(block) if block else []
        relationships = detect_relationships(content)
        models[model_name] = {
            "file": rel,
            "type": model_type,
            "fields": fields,
            "relationships": relationships,
        }
    return dict(sorted(models.items(), key=lambda item: item[0].lower()))


def convert_dependency_map(imports_map: Dict[str, Set[str]], reverse_map: Dict[str, Set[str]]) -> Dict[str, Dict[str, List[str]]]:
    result: Dict[str, Dict[str, List[str]]] = {}
    files = sorted(set(imports_map.keys()) | set(reverse_map.keys()))
    for rel in files:
        result[rel] = {
            "imports": sorted(imports_map.get(rel, set())),
            "imported_by": sorted(reverse_map.get(rel, set())),
        }
    return result


def to_module_boundary_output(boundaries: Dict[str, Dict[str, Set[str]]]) -> Dict[str, Dict[str, List[str]]]:
    output: Dict[str, Dict[str, List[str]]] = {}
    for module in sorted(boundaries.keys()):
        output[module] = {
            "imports_from": sorted(boundaries[module]["imports_from"]),
            "imported_by": sorted(boundaries[module]["imported_by"]),
        }
    return output


def build_graph(project_root: Path, include_tests: bool) -> Dict[str, object]:
    files = collect_code_files(project_root, include_tests=include_tests)
    imports_map, reverse_map, raw_content, aux = build_dependency_graph(project_root, files)
    warnings: List[str] = list(aux["warnings"])

    module_boundaries_raw, module_cycles = build_module_boundaries(imports_map)
    routes = build_api_route_map(project_root, files, imports_map, raw_content)
    models = build_data_model_map(project_root, files, raw_content)

    edges = sum(len(values) for values in imports_map.values())
    module_boundaries = to_module_boundary_output(module_boundaries_raw)
    dependency_tree = convert_dependency_map(imports_map, reverse_map)

    graph = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": project_root.as_posix(),
        "stats": {
            "total_files": len(files),
            "total_edges": edges,
            "modules": len(module_boundaries),
            "routes": len(routes),
            "models": len(models),
            "circular_dependencies": len(module_cycles),
        },
        "file_dependencies": dependency_tree,
        "module_boundaries": module_boundaries,
        "api_routes": routes,
        "data_models": models,
        "circular_dependencies": module_cycles,
        "warnings": sorted(dict.fromkeys(warnings)),
    }
    return graph


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else (project_root / ".codex" / "knowledge-graph.json")

    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "path": "", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    try:
        graph = build_graph(project_root, include_tests=args.include_tests)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(graph, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except PermissionError as exc:
        emit({"status": "error", "path": "", "message": f"Permission denied: {exc}"})
        return 1
    except OSError as exc:
        emit({"status": "error", "path": "", "message": f"I/O failure: {exc}"})
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        emit({"status": "error", "path": "", "message": f"Unexpected error: {exc}"})
        return 1

    payload = {"status": "generated", "path": output_path.as_posix(), **graph}
    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
