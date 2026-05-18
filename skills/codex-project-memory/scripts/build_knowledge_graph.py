#!/usr/bin/env python3
"""
Build a project knowledge graph with dependencies, module boundaries, routes, and models.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

SCHEMA_VERSION = "2.0"
GRAPH_ARTIFACT_TYPE = "knowledge-graph"

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from redaction import REDACTION_PATTERNS_VERSION, redact_artifact


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
    ".codexai",
    ".idea",
    ".vscode",
    ".yarn",
}
JAVASCRIPT_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte"}
PYTHON_EXTENSIONS = {".py"}
TEST_EXTENSIONS = JAVASCRIPT_EXTENSIONS | PYTHON_EXTENSIONS

IMPORT_FROM_PATTERN = re.compile(r"^\s*import\s+.+?\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
IMPORT_SIDE_PATTERN = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
REQUIRE_PATTERN = re.compile(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)")
PY_IMPORT_PATTERN = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)", re.MULTILINE)
PY_FROM_IMPORT_PATTERN = re.compile(r"^\s*from\s+([A-Za-z_][\w.]*|\.+[\w.]*)\s+import\s+", re.MULTILINE)
GO_IMPORT_SINGLE_PATTERN = re.compile(r'^\s*import\s+(?:[._A-Za-z]\w*\s+)?["`]([^"`]+)["`]', re.MULTILINE)
GO_IMPORT_BLOCK_PATTERN = re.compile(r"^\s*import\s*\((.*?)\)", re.MULTILINE | re.DOTALL)
RUST_USE_PATTERN = re.compile(r"^\s*(?:pub\s+)?use\s+([^;]+);", re.MULTILINE)
JAVA_IMPORT_PATTERN = re.compile(r"^\s*import\s+(?:static\s+)?([A-Za-z_][\w.]*)(?:\.\*)?\s*;", re.MULTILINE)
CSHARP_USING_PATTERN = re.compile(r"^\s*using\s+(?:static\s+)?([A-Za-z_][\w.]*)(?:\s*=\s*[A-Za-z_][\w.]*)?\s*;", re.MULTILINE)
PHP_USE_PATTERN = re.compile(r"^\s*use\s+([^;]+);", re.MULTILINE)
PHP_REQUIRE_PATTERN = re.compile(r"\b(?:require|require_once|include|include_once)\s*(?:\(?\s*)['\"]([^'\"]+)['\"]", re.MULTILINE)
RUBY_REQUIRE_PATTERN = re.compile(r"^\s*require(?:_relative)?\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
KOTLIN_IMPORT_PATTERN = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)(?:\.\*)?", re.MULTILINE)
SWIFT_IMPORT_PATTERN = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)", re.MULTILINE)
CSS_IMPORT_PATTERN = re.compile(r"@import\s+(?:url\()?['\"]?([^'\")\s;]+)", re.MULTILINE)
HTML_ASSET_PATTERN = re.compile(r"(?:src|href)\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
SQL_INCLUDE_PATTERN = re.compile(r"^\s*(?:\\i|SOURCE)\s+([^\s;]+)", re.MULTILINE | re.IGNORECASE)
TERRAFORM_SOURCE_PATTERN = re.compile(r"\bsource\s*=\s*['\"]([^'\"]+)['\"]")
YAML_REFERENCE_PATTERN = re.compile(r"^\s*(?:file|path|source):\s*['\"]?([^'\"\s]+)", re.MULTILINE)

JS_IMPORT_DEFAULT_PATTERN = re.compile(r"^\s*import\s+([A-Za-z_$][\w$]*)\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
JS_IMPORT_NAMED_PATTERN = re.compile(r"^\s*import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
JS_REQUIRE_ALIAS_PATTERN = re.compile(r"^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)", re.MULTILINE)
JS_REQUIRE_NAMED_PATTERN = re.compile(r"^\s*(?:const|let|var)\s+\{([^}]+)\}\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)", re.MULTILINE)
JS_EXPORT_FUNCTION_PATTERN = re.compile(r"\bexport\s+(?:async\s+)?function\s+([A-Za-z_$][\w$]*)")
JS_EXPORT_CONST_PATTERN = re.compile(r"\bexport\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)")
JS_EXPORTS_PATTERN = re.compile(r"\bexports\.([A-Za-z_$][\w$]*)\s*=")
JS_MODULE_EXPORTS_PATTERN = re.compile(r"\bmodule\.exports\s*=\s*([A-Za-z_$][\w$]*)")
JS_CLASS_PATTERN = re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)")
JS_FUNCTION_PATTERN = re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(")
PY_DEF_PATTERN = re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
PY_ASYNC_DEF_PATTERN = re.compile(r"^\s*async\s+def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
PY_CLASS_PATTERN = re.compile(r"^\s*class\s+([A-Za-z_]\w*)", re.MULTILINE)
FALLBACK_DEFINITION_PATTERNS = (
    re.compile(r"\b(?:class|interface|trait|struct|enum|type|module|namespace)\s+([A-Za-z_][\w$]*)"),
    re.compile(r"\b(?:func|fn|function|def)\s+([A-Za-z_][\w$]*)\s*[<(]"),
    re.compile(r"\b(?:route|resource|data|provider|module|variable|output)\s+['\"]?([A-Za-z_][\w.-]*)['\"]?\s*[{(]"),
)
CONFIG_BLOCK_PATTERN = re.compile(r"^\s*([A-Za-z_][\w.-]*)\s*:\s*(?:$|[|>{\[])", re.MULTILINE)
JSON_KEY_PATTERN = re.compile(r'"([A-Za-z_][\w.-]*)"\s*:')

DANGEROUS_SINK_PATTERN = re.compile(
    r"\b(eval|exec|spawn|execFile|child_process|subprocess|pickle\.loads?|yaml\.load|innerHTML|dangerouslySetInnerHTML)\b"
)
SECRET_FILE_HINT = re.compile(r"(\.env|secret|credential|token|private[-_]?key|id_rsa)", re.IGNORECASE)

ROUTE_CALL_PATTERN = re.compile(
    r"\b(?:router|app)\.(get|post|put|delete|patch|options|head|all)\s*\(\s*['\"`]([^'\"`]+)['\"`]\s*,\s*(.+)"
)
ROUTE_FILE_HINT = re.compile(r"route", re.IGNORECASE)


def load_traversal():
    traversal_path = Path(__file__).with_name("project_traversal.py")
    spec = importlib.util.spec_from_file_location("codexai_project_traversal", traversal_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Unable to load traversal helper: {traversal_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
    parser.add_argument("--no-redaction", action="store_true", help="Disable artifact redaction; not recommended")
    load_traversal().add_traversal_args(parser)
    return parser.parse_args()


def normalize_warning_messages(warnings: List[Any]) -> List[str]:
    messages: List[str] = []
    for item in warnings:
        if isinstance(item, str):
            messages.append(item)
        elif isinstance(item, dict):
            parts = [str(item[key]) for key in ("severity", "type", "path", "reason") if item.get(key)]
            messages.append(": ".join(parts) if parts else json.dumps(item, sort_keys=True))
        else:
            messages.append(str(item))
    return sorted(dict.fromkeys(messages))


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def load_codebase_indexer():
    indexer_path = Path(__file__).with_name("codebase_indexer.py")
    spec = importlib.util.spec_from_file_location("codexai_codebase_indexer", indexer_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Unable to load codebase indexer: {indexer_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compact_codebase_index(index: Dict[str, object]) -> Dict[str, object]:
    return {
        key: index.get(key)
        for key in (
            "schema_version",
            "generated_at",
            "files",
            "chunks",
            "symbols",
            "references",
            "routes",
            "models",
            "configs",
            "risk_signals",
            "read_order",
            "confidence",
            "semantic",
        )
    }


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
    traversal = collect_code_file_entries(project_root, include_tests=include_tests)
    return [entry.path for entry in traversal.files]


def collect_code_file_entries(
    project_root: Path,
    include_tests: bool,
    traversal_config=None,
):
    traversal = load_traversal()

    def code_filter(rel: str, path: Path) -> bool:
        if path.suffix.lower() not in LANGUAGE_REGISTRY:
            return False
        if not include_tests and is_test_file(rel):
            return False
        return True

    return traversal.traverse_project(project_root, traversal_config, file_filter=code_filter)


def read_limited(path: Path, warnings: List[dict[str, str]], rel_file: str) -> Tuple[str, List[str]]:
    traversal = load_traversal()
    try:
        content, _bytes_read, large = traversal.sample_for_index(path, traversal.TraversalConfig().max_file_bytes)
    except OSError as exc:
        warnings.append(traversal.structured_warning("read_error", rel_file, f"Unable to read file: {exc}", "warning"))
        return "", []
    if large:
        warnings.append(traversal.structured_warning("large_file_sampled", rel_file, "sampled with header, symbol window, and tail metadata", "warning"))
    return content, content.splitlines()


class LanguageProfile:
    def __init__(
        self,
        language: str,
        parser: str,
        import_extractor: Callable[[Path, str], List[str]],
        definition_extractor: Callable[[Path, str], List[str]],
        resolver_strategy: str,
        confidence: str,
    ) -> None:
        self.language = language
        self.parser = parser
        self.import_extractor = import_extractor
        self.definition_extractor = definition_extractor
        self.resolver_strategy = resolver_strategy
        self.confidence = confidence


def unique_sorted(values: Iterable[str]) -> List[str]:
    return sorted(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def extract_javascript_imports(file_path: Path, content: str) -> List[str]:
    modules: List[str] = []
    modules.extend(IMPORT_FROM_PATTERN.findall(content))
    modules.extend(IMPORT_SIDE_PATTERN.findall(content))
    modules.extend(REQUIRE_PATTERN.findall(content))
    return unique_sorted(modules)


def extract_python_imports(file_path: Path, content: str) -> List[str]:
    modules: List[str] = []
    modules.extend(PY_IMPORT_PATTERN.findall(content))
    modules.extend(PY_FROM_IMPORT_PATTERN.findall(content))
    return unique_sorted(modules)


def extract_go_imports(file_path: Path, content: str) -> List[str]:
    modules = GO_IMPORT_SINGLE_PATTERN.findall(content)
    for block in GO_IMPORT_BLOCK_PATTERN.findall(content):
        modules.extend(re.findall(r'(?:^|\n)\s*(?:[._A-Za-z]\w*\s+)?["`]([^"`]+)["`]', block))
    return unique_sorted(modules)


def normalize_rust_use_path(cleaned: str) -> str:
    value = cleaned.strip()
    if not value:
        return ""
    first = value.split("::", 1)[0].strip("{} ")
    if first in {"crate", "self", "super"}:
        if "{" in value:
            value = value.split("{", 1)[0].rstrip(":").strip()
        return value
    if "::{" in value:
        return value.split("::{", 1)[0].strip()
    return value.split("::", 1)[0].strip()


def extract_rust_imports(file_path: Path, content: str) -> List[str]:
    modules: List[str] = []
    for raw in RUST_USE_PATTERN.findall(content):
        cleaned = re.sub(r"\s+as\s+\w+", "", raw).strip()
        normalized = normalize_rust_use_path(cleaned)
        if normalized:
            modules.append(normalized)
    for match in re.findall(r"\bmod\s+([A-Za-z_]\w*)\s*;", content):
        modules.append(f"self::{match}")
    return unique_sorted(modules)


def extract_java_imports(file_path: Path, content: str) -> List[str]:
    return unique_sorted(JAVA_IMPORT_PATTERN.findall(content))


def extract_csharp_imports(file_path: Path, content: str) -> List[str]:
    return unique_sorted(CSHARP_USING_PATTERN.findall(content))


def extract_php_imports(file_path: Path, content: str) -> List[str]:
    modules = PHP_USE_PATTERN.findall(content)
    modules.extend(PHP_REQUIRE_PATTERN.findall(content))
    return unique_sorted(module.split(" as ", 1)[0].strip().replace("\\", "/") for module in modules)


def extract_ruby_imports(file_path: Path, content: str) -> List[str]:
    return unique_sorted(RUBY_REQUIRE_PATTERN.findall(content))


def extract_kotlin_imports(file_path: Path, content: str) -> List[str]:
    return unique_sorted(KOTLIN_IMPORT_PATTERN.findall(content))


def extract_swift_imports(file_path: Path, content: str) -> List[str]:
    return unique_sorted(SWIFT_IMPORT_PATTERN.findall(content))


def extract_asset_imports(file_path: Path, content: str) -> List[str]:
    modules = CSS_IMPORT_PATTERN.findall(content)
    if file_path.suffix.lower() == ".html":
        modules.extend(HTML_ASSET_PATTERN.findall(content))
    return unique_sorted(modules)


def extract_sql_imports(file_path: Path, content: str) -> List[str]:
    return unique_sorted(SQL_INCLUDE_PATTERN.findall(content))


def extract_terraform_imports(file_path: Path, content: str) -> List[str]:
    return unique_sorted(TERRAFORM_SOURCE_PATTERN.findall(content))


def extract_yaml_imports(file_path: Path, content: str) -> List[str]:
    return unique_sorted(YAML_REFERENCE_PATTERN.findall(content))


def extract_no_imports(file_path: Path, content: str) -> List[str]:
    return []


def extract_javascript_definitions(file_path: Path, content: str) -> List[str]:
    names: Set[str] = set()
    for pattern in (
        JS_EXPORT_FUNCTION_PATTERN,
        JS_EXPORT_CONST_PATTERN,
        JS_EXPORTS_PATTERN,
        JS_MODULE_EXPORTS_PATTERN,
        JS_CLASS_PATTERN,
        JS_FUNCTION_PATTERN,
    ):
        names.update(pattern.findall(content))
    names.update(extract_fallback_definitions(file_path, content))
    return unique_sorted(names)


def extract_python_definitions(file_path: Path, content: str) -> List[str]:
    names: Set[str] = set()
    names.update(PY_DEF_PATTERN.findall(content))
    names.update(PY_ASYNC_DEF_PATTERN.findall(content))
    names.update(PY_CLASS_PATTERN.findall(content))
    return unique_sorted(names)


def extract_fallback_definitions(file_path: Path, content: str) -> List[str]:
    names: Set[str] = set()
    for pattern in FALLBACK_DEFINITION_PATTERNS:
        names.update(pattern.findall(content))
    ext = file_path.suffix.lower()
    if ext in {".yaml", ".yml"}:
        names.update(f"config:{name}" for name in CONFIG_BLOCK_PATTERN.findall(content))
    elif ext == ".json":
        names.update(f"config:{name}" for name in JSON_KEY_PATTERN.findall(content))
    elif ext in {".vue", ".svelte"} and re.search(r"<script|<template", content, flags=re.IGNORECASE):
        names.add(Path(file_path).stem)
    return unique_sorted(names)


def make_profile(
    language: str,
    parser: str,
    import_extractor: Callable[[Path, str], List[str]],
    definition_extractor: Callable[[Path, str], List[str]],
    resolver_strategy: str,
    confidence: str,
) -> LanguageProfile:
    return LanguageProfile(language, parser, import_extractor, definition_extractor, resolver_strategy, confidence)


LANGUAGE_REGISTRY: Dict[str, LanguageProfile] = {
    ".js": make_profile("JavaScript", "javascript", extract_javascript_imports, extract_javascript_definitions, "javascript", "high"),
    ".jsx": make_profile("React JSX", "javascript", extract_javascript_imports, extract_javascript_definitions, "javascript", "high"),
    ".ts": make_profile("TypeScript", "javascript", extract_javascript_imports, extract_javascript_definitions, "javascript", "high"),
    ".tsx": make_profile("React TSX", "javascript", extract_javascript_imports, extract_javascript_definitions, "javascript", "high"),
    ".mjs": make_profile("JavaScript ESM", "javascript", extract_javascript_imports, extract_javascript_definitions, "javascript", "high"),
    ".cjs": make_profile("JavaScript CJS", "javascript", extract_javascript_imports, extract_javascript_definitions, "javascript", "high"),
    ".py": make_profile("Python", "python", extract_python_imports, extract_python_definitions, "python", "high"),
    ".go": make_profile("Go", "pattern", extract_go_imports, extract_fallback_definitions, "go", "medium"),
    ".rs": make_profile("Rust", "pattern", extract_rust_imports, extract_fallback_definitions, "rust", "medium"),
    ".java": make_profile("Java", "pattern", extract_java_imports, extract_fallback_definitions, "package", "medium"),
    ".cs": make_profile("C#", "pattern", extract_csharp_imports, extract_fallback_definitions, "package", "medium"),
    ".php": make_profile("PHP", "pattern", extract_php_imports, extract_fallback_definitions, "relative", "medium"),
    ".rb": make_profile("Ruby", "pattern", extract_ruby_imports, extract_fallback_definitions, "relative", "medium"),
    ".kt": make_profile("Kotlin", "pattern", extract_kotlin_imports, extract_fallback_definitions, "package", "medium"),
    ".kts": make_profile("Kotlin Script", "pattern", extract_kotlin_imports, extract_fallback_definitions, "package", "medium"),
    ".swift": make_profile("Swift", "pattern", extract_swift_imports, extract_fallback_definitions, "package", "medium"),
    ".vue": make_profile("Vue", "javascript+component", extract_javascript_imports, extract_javascript_definitions, "javascript", "medium"),
    ".svelte": make_profile("Svelte", "javascript+component", extract_javascript_imports, extract_javascript_definitions, "javascript", "medium"),
    ".html": make_profile("HTML", "pattern", extract_asset_imports, extract_fallback_definitions, "relative", "low"),
    ".css": make_profile("CSS", "pattern", extract_asset_imports, extract_fallback_definitions, "relative", "low"),
    ".scss": make_profile("SCSS", "pattern", extract_asset_imports, extract_fallback_definitions, "relative", "low"),
    ".sql": make_profile("SQL", "pattern", extract_sql_imports, extract_fallback_definitions, "relative", "low"),
    ".tf": make_profile("Terraform", "pattern", extract_terraform_imports, extract_fallback_definitions, "relative", "medium"),
    ".yaml": make_profile("YAML", "pattern", extract_yaml_imports, extract_fallback_definitions, "none", "medium"),
    ".yml": make_profile("YAML", "pattern", extract_yaml_imports, extract_fallback_definitions, "none", "medium"),
    ".json": make_profile("JSON", "pattern", extract_no_imports, extract_fallback_definitions, "none", "medium"),
}


def language_profile(file_path: Path) -> Optional[LanguageProfile]:
    return LANGUAGE_REGISTRY.get(file_path.suffix.lower())


def parse_import_modules(file_path: Path, content: str) -> List[str]:
    profile = language_profile(file_path)
    if not profile:
        return []
    return profile.import_extractor(file_path, content)


def external_modules_for_file(file_path: Path, content: str, internal_imports: Optional[Set[str]] = None) -> List[str]:
    profile = language_profile(file_path)
    modules = parse_import_modules(file_path, content)
    externals: Set[str] = set()
    internal_stems = {Path(item).stem for item in (internal_imports or set())}
    for module in modules:
        value = module.strip()
        if not value or value.startswith((".", "/", "@/", "src/", "http://", "https://", "node:", "crate", "self", "super")):
            continue
        ext = file_path.suffix.lower()
        if ext == ".py":
            top_level = value.split(".", 1)[0]
            if top_level == "__future__" or top_level in getattr(sys, "stdlib_module_names", set()) or top_level in internal_stems:
                continue
            externals.add(top_level)
        elif ext in JAVASCRIPT_EXTENSIONS:
            if value.startswith("@"):
                parts = value.split("/")
                externals.add("/".join(parts[:2]) if len(parts) >= 2 else value)
            else:
                externals.add(value.split("/", 1)[0])
        elif ext == ".go":
            if "." in value or "/" in value:
                externals.add(value.split("/", 1)[0])
        elif ext in {".java", ".kt", ".kts"}:
            top_level = value.split(".", 1)[0]
            if top_level not in {"java", "javax", "kotlin"}:
                externals.add(top_level)
        elif ext == ".cs":
            top_level = value.split(".", 1)[0]
            if top_level not in {"System", "Microsoft"}:
                externals.add(top_level)
        elif ext in {".css", ".scss", ".html", ".sql", ".tf", ".yaml", ".yml"}:
            continue
        else:
            externals.add(value.split("/", 1)[0].split(".", 1)[0])
    return sorted(externals)


def extract_definitions(file_path: Path, content: str) -> List[str]:
    profile = language_profile(file_path)
    if not profile:
        return []
    return profile.definition_extractor(file_path, content)


def parser_metadata(file_path: Path) -> Dict[str, str]:
    profile = language_profile(file_path)
    if not profile:
        return {"parser": "none", "confidence": "none", "resolver_strategy": "none"}
    return {"parser": profile.parser, "confidence": profile.confidence, "resolver_strategy": profile.resolver_strategy}


def line_count(lines: Sequence[str]) -> int:
    return len(lines)


def build_chunk_preview(lines: Sequence[str], max_lines: int = 5) -> str:
    preview_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(preview_lines[:max_lines])


def build_chunks(lines: Sequence[str], chunk_size: int = 80) -> List[Dict[str, object]]:
    chunks: List[Dict[str, object]] = []
    for start in range(0, len(lines), chunk_size):
        section = lines[start : start + chunk_size]
        if not section:
            continue
        chunks.append({
            "start_line": start + 1,
            "end_line": start + len(section),
            "preview": build_chunk_preview(section),
        })
        if len(chunks) >= 5:
            break
    return chunks


def build_code_index(
    project_root: Path,
    files: List[Path],
    imports_map: Dict[str, Set[str]],
    reverse_map: Dict[str, Set[str]],
    raw_content: Dict[str, str],
    lines_cache: Dict[str, List[str]],
) -> Tuple[Dict[str, Dict[str, object]], Dict[str, Dict[str, object]], List[Dict[str, object]], List[str]]:
    code_index: Dict[str, Dict[str, object]] = {}
    external_dependencies: Dict[str, Dict[str, object]] = {}
    risk_signals: List[Dict[str, object]] = []
    entrypoints: Set[str] = set()

    for file_path in files:
        rel = normalize_rel(file_path, project_root)
        content = raw_content.get(rel, "")
        lines = lines_cache.get(rel, [])
        externals = external_modules_for_file(file_path, content, imports_map.get(rel, set()))
        definitions = extract_definitions(file_path, content)
        module = module_name(rel)
        lowered = rel.lower()
        if "route" in lowered or "app." in content or "router." in content or "__main__" in content:
            entrypoints.add(rel)
        if SECRET_FILE_HINT.search(rel):
            risk_signals.append({"type": "sensitive_file_name", "file": rel, "reason": "File path suggests secrets or credentials."})
        if DANGEROUS_SINK_PATTERN.search(content):
            risk_signals.append({"type": "dangerous_sink", "file": rel, "reason": "File contains a sink that needs security review when input is attacker-controlled."})
        if "password" in content.lower() or "token" in content.lower() or "jwt" in content.lower():
            risk_signals.append({"type": "auth_or_secret_logic", "file": rel, "reason": "File contains auth, token, password, or credential-related terms."})

        code_index[rel] = {
            "path": rel,
            "language": (language_profile(file_path).language if language_profile(file_path) else file_path.suffix.lstrip(".") or "unknown"),
            "module": module,
            "parser": parser_metadata(file_path),
            "lines": line_count(lines),
            "definitions": definitions[:40],
            "preview": build_chunk_preview(lines),
            "chunks": build_chunks(lines),
            "imports": sorted(imports_map.get(rel, set())),
            "imported_by": sorted(reverse_map.get(rel, set())),
            "external_imports": externals,
            "is_test": is_test_file(rel),
            "is_entrypoint": rel in entrypoints,
            "risk_tags": [
                item["type"]
                for item in risk_signals
                if item.get("file") == rel
            ],
        }
        for package in externals:
            info = external_dependencies.setdefault(package, {"used_by": []})
            info["used_by"].append(rel)  # type: ignore[index]

    for info in external_dependencies.values():
        info["used_by"] = sorted(set(info["used_by"]))  # type: ignore[index]

    return code_index, dict(sorted(external_dependencies.items())), risk_signals, sorted(entrypoints)


def build_ai_context(
    graph_stats: Dict[str, object],
    module_boundaries: Dict[str, Dict[str, List[str]]],
    dependency_tree: Dict[str, Dict[str, List[str]]],
    routes: List[Dict[str, object]],
    models: Dict[str, Dict[str, object]],
    risk_signals: List[Dict[str, object]],
    entrypoints: List[str],
) -> Dict[str, object]:
    top_dependents = sorted(
        (
            {"file": file_path, "imported_by_count": len(item.get("imported_by", []))}
            for file_path, item in dependency_tree.items()
        ),
        key=lambda item: (-int(item["imported_by_count"]), str(item["file"])),
    )[:10]
    recommended_read_order = []
    recommended_read_order.extend(entrypoints[:8])
    recommended_read_order.extend(item["file"] for item in top_dependents if item["file"] not in recommended_read_order)
    summary = (
        f"{graph_stats['total_files']} code files, {graph_stats['modules']} modules, "
        f"{graph_stats['total_edges']} internal edges, {len(routes)} routes, {len(models)} models, "
        f"{len(risk_signals)} risk signals."
    )
    return {
        "summary": summary,
        "recommended_read_order": recommended_read_order[:15],
        "top_dependents": top_dependents,
        "module_contracts": module_boundaries,
        "security_review_targets": risk_signals[:20],
        "usage": "Read recommended_read_order first, then inspect module_contracts and depended_by before cross-module edits.",
    }


def build_human_context(
    module_boundaries: Dict[str, Dict[str, List[str]]],
    routes: List[Dict[str, object]],
    models: Dict[str, Dict[str, object]],
    risk_signals: List[Dict[str, object]],
) -> Dict[str, object]:
    return {
        "navigation_hints": [
            "Use Modules to understand boundaries before editing.",
            "Use Files to search definitions, imports, and downstream dependents.",
            "Use Routes and Models to inspect runtime-facing surfaces.",
            "Use Risk Signals as review prompts, not automatic vulnerabilities.",
        ],
        "module_count": len(module_boundaries),
        "route_count": len(routes),
        "model_count": len(models),
        "risk_signal_count": len(risk_signals),
    }


def expand_candidates(base: Path) -> List[Path]:
    candidates: List[Path] = []
    if base.suffix:
        candidates.append(base)
        for ext in LANGUAGE_REGISTRY:
            candidates.append(Path(str(base) + ext))
    else:
        for ext in LANGUAGE_REGISTRY:
            candidates.append(Path(str(base) + ext))
        for ext in LANGUAGE_REGISTRY:
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
        local_target = importer.parent / Path(value.replace(".", "/"))
        candidates.extend([local_target.with_suffix(".py"), local_target / "__init__.py"])
    return choose_existing(candidates, root, existing)


def resolve_relative_module(importer: Path, module: str, root: Path, existing: Set[Path]) -> Optional[Path]:
    value = module.strip().strip('"\'')
    if not value or value.startswith(("http://", "https://")):
        return None
    if value.startswith("."):
        base = importer.parent / value
    elif value.startswith("/"):
        base = root / value.lstrip("/")
    else:
        base = importer.parent / value
    return choose_existing(expand_candidates(base), root, existing)


def resolve_go_module(importer: Path, module: str, root: Path, existing: Set[Path]) -> Optional[Path]:
    value = module.strip()
    if not value:
        return None
    candidates = [root / Path(value), importer.parent / Path(value.rsplit("/", 1)[-1])]
    expanded: List[Path] = []
    for candidate in candidates:
        expanded.extend([candidate.with_suffix(".go"), candidate / "main.go", candidate / f"{candidate.name}.go"])
    return choose_existing(expanded, root, existing)


def resolve_rust_module(importer: Path, module: str, root: Path, existing: Set[Path]) -> Optional[Path]:
    value = module.strip()
    if not value:
        return None
    if value.startswith(("crate::", "self::")):
        parts = value.split("::")[1:]
        base = root / "src" if (root / "src").exists() else importer.parent
    elif value.startswith("super::"):
        parts = value.split("::")[1:]
        base = importer.parent.parent
    else:
        parts = value.split("::")
        base = importer.parent
    if not parts:
        return None
    target = base.joinpath(*parts)
    candidates = [target.with_suffix(".rs"), target / "mod.rs", base / f"{parts[0]}.rs"]
    return choose_existing(candidates, root, existing)


def resolve_package_module(importer: Path, module: str, root: Path, existing: Set[Path]) -> Optional[Path]:
    value = module.strip().rstrip(".*")
    if not value:
        return None
    path_value = Path(value.replace(".", "/"))
    candidates = [root / path_value, importer.parent / path_value]
    expanded: List[Path] = []
    for candidate in candidates:
        expanded.extend(expand_candidates(candidate))
    return choose_existing(expanded, root, existing)


def resolve_import_module(importer: Path, module: str, root: Path, existing: Set[Path]) -> Optional[Path]:
    profile = language_profile(importer)
    strategy = profile.resolver_strategy if profile else "none"
    if strategy == "javascript":
        return resolve_js_module(importer, module, root, existing)
    if strategy == "python":
        return resolve_python_module(importer, module, root, existing)
    if strategy == "relative":
        return resolve_relative_module(importer, module, root, existing)
    if strategy == "go":
        return resolve_go_module(importer, module, root, existing)
    if strategy == "rust":
        return resolve_rust_module(importer, module, root, existing)
    if strategy == "package":
        return resolve_package_module(importer, module, root, existing)
    return None


def build_dependency_graph_from_entries(
    project_root: Path,
    entries: List[object],
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, str], Dict[str, object]]:
    files = [entry.path for entry in entries]
    existing = {path.resolve() for path in files}
    imports_map: Dict[str, Set[str]] = defaultdict(set)
    reverse_map: Dict[str, Set[str]] = defaultdict(set)
    raw_content: Dict[str, str] = {}
    lines_cache: Dict[str, List[str]] = {}
    warnings: List[dict[str, str]] = []

    for entry in entries:
        file_path = entry.path
        rel = entry.rel_path
        content = entry.content
        lines = entry.lines
        raw_content[rel] = content
        lines_cache[rel] = lines
        if not content:
            continue
        for module in parse_import_modules(file_path, content):
            resolved = resolve_import_module(file_path, module, project_root, existing)
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

    return imports_map, reverse_map, raw_content, {"warnings": warnings, "lines": lines_cache}


def build_dependency_graph(
    project_root: Path,
    files: List[Path],
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, str], Dict[str, List[str]]]:
    existing = {path.resolve() for path in files}
    imports_map: Dict[str, Set[str]] = defaultdict(set)
    reverse_map: Dict[str, Set[str]] = defaultdict(set)
    raw_content: Dict[str, str] = {}
    lines_cache: Dict[str, List[str]] = {}
    warnings: List[dict[str, str]] = []

    for file_path in files:
        rel = normalize_rel(file_path, project_root)
        content, lines = read_limited(file_path, warnings, rel)
        raw_content[rel] = content
        lines_cache[rel] = lines
        if not content:
            continue
        for module in parse_import_modules(file_path, content):
            resolved = resolve_import_module(file_path, module, project_root, existing)
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
    if lowered[0] == "skills" and len(lowered) > 1:
        return lowered[1] if not Path(parts[1]).suffix else "skills"
    for hint in MODULE_HINTS:
        if hint in lowered:
            return "middlewares" if hint == "middleware" else hint
    if lowered[0] in {"src", "app", "server", "backend", "frontend", "lib"} and len(lowered) > 1:
        if len(lowered) == 2 and Path(parts[1]).suffix:
            return "root"
        return lowered[1]
    if len(parts) == 1:
        return "root"
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
    schema_meta_keys = {
        # Mongoose meta
        "type",
        "required",
        "default",
        "ref",
        "unique",
        "validate",
        "index",
        "sparse",
        "enum",
        "min",
        "max",
        "minlength",
        "maxlength",
        "lowercase",
        "uppercase",
        "trim",
        "match",
        "alias",
        "immutable",
        "select",
        "get",
        "set",
        "transform",
        "expires",
        # Sequelize meta
        "allownull",
        "primarykey",
        "autoincrement",
        "defaultvalue",
        "references",
        "ondelete",
        "onupdate",
        "field",
        "comment",
        "constraints",
        "through",
    }
    keys: List[str] = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^['\"]?([A-Za-z_][\w]*)['\"]?\s*:", stripped)
        if not match:
            continue
        key = match.group(1)
        if key.lower() in schema_meta_keys:
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
        stem_lower = Path(rel).stem.lower()
        if stem_lower in {"index", "init", "setup", "associations", "connection"}:
            continue
        content = raw_content.get(rel, "")
        if not content:
            continue

        model_type = detect_model_type(content)
        model_name = detect_model_name(rel, content)

        block = ""
        schema_match = re.search(r"new\s+(?:mongoose\.)?Schema\s*\(", content)
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


def build_graph(
    project_root: Path,
    include_tests: bool,
    traversal_config=None,
    redaction_enabled: bool = True,
) -> Dict[str, object]:
    traversal_result = collect_code_file_entries(project_root, include_tests=include_tests, traversal_config=traversal_config)
    files = [entry.path for entry in traversal_result.files]
    imports_map, reverse_map, raw_content, aux = build_dependency_graph_from_entries(project_root, traversal_result.files)
    warnings: List[dict[str, str]] = list(traversal_result.warnings) + list(aux["warnings"])
    lines_cache: Dict[str, List[str]] = aux["lines"]  # type: ignore[assignment]

    module_boundaries_raw, module_cycles = build_module_boundaries(imports_map)
    routes = build_api_route_map(project_root, files, imports_map, raw_content)
    models = build_data_model_map(project_root, files, raw_content)
    codebase_index: Dict[str, object] = {}
    try:
        indexer = load_codebase_indexer()
        codebase_index = indexer.build_codebase_index(
            project_root,
            output_path=project_root / ".codex" / "knowledge" / "codebase-index.json",
            incremental=True,
            rebuild=False,
        )
    except Exception as exc:
        warnings.append(f"Codebase index unavailable: {exc}")

    edges = sum(len(values) for values in imports_map.values())
    module_boundaries = to_module_boundary_output(module_boundaries_raw)
    dependency_tree = convert_dependency_map(imports_map, reverse_map)
    code_index, external_dependencies, risk_signals, entrypoints = build_code_index(
        project_root,
        files,
        imports_map,
        reverse_map,
        raw_content,
        lines_cache,
    )

    graph = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": GRAPH_ARTIFACT_TYPE,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project_root": project_root.as_posix(),
        "stats": {
            "total_files": len(files),
            "total_edges": edges,
            "modules": len(module_boundaries),
            "routes": len(routes),
            "models": len(models),
            "circular_dependencies": len(module_cycles),
            "files_scanned": traversal_result.coverage["files_scanned"],
            "files_skipped": traversal_result.coverage["files_skipped"],
            "bytes_scanned": traversal_result.coverage["bytes_scanned"],
        },
        "warnings": normalize_warning_messages(warnings),
        "redaction": {
            "enabled": False,
            "strategy": "none",
            "description": "Knowledge graph stores paths, symbols, imports, routes, and model field names only; source bodies are not persisted.",
        },
        "coverage": traversal_result.coverage,
        "file_dependencies": dependency_tree,
        "code_index": code_index,
        "codebase_index": code_index,
        "entrypoints": entrypoints,
        "external_dependencies": external_dependencies,
        "module_boundaries": module_boundaries,
        "api_routes": routes,
        "data_models": models,
        "circular_dependencies": module_cycles,
        "risk_signals": risk_signals,
        "codebase_index": compact_codebase_index(codebase_index) if codebase_index else {},
        "ai_context": build_ai_context(
            {
                "total_files": len(files),
                "total_edges": edges,
                "modules": len(module_boundaries),
            },
            module_boundaries,
            dependency_tree,
            routes,
            models,
            risk_signals,
            entrypoints,
        ),
        "human_context": build_human_context(module_boundaries, routes, models, risk_signals),
    }
    graph, _count = redact_artifact(graph, "knowledge-graph.json", enabled=redaction_enabled)
    return graph


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else (project_root / ".codex" / "knowledge-graph.json")

    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "path": "", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    try:
        traversal_config = load_traversal().config_from_args(args)
        graph = build_graph(
            project_root,
            include_tests=args.include_tests,
            traversal_config=traversal_config,
            redaction_enabled=not args.no_redaction,
        )
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
