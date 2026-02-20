#!/usr/bin/env python3
"""
Analyze project coding patterns and write .codex/project-profile.json.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


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
SKIP_FILE_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "pipfile.lock",
    "cargo.lock",
}
CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
JS_TS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
PYTHON_EXTENSIONS = {".py"}

NODE_BUILTINS = {
    "assert",
    "buffer",
    "child_process",
    "cluster",
    "console",
    "crypto",
    "dgram",
    "dns",
    "events",
    "fs",
    "http",
    "https",
    "inspector",
    "module",
    "net",
    "os",
    "path",
    "perf_hooks",
    "process",
    "querystring",
    "readline",
    "repl",
    "stream",
    "string_decoder",
    "timers",
    "tls",
    "tty",
    "url",
    "util",
    "v8",
    "vm",
    "worker_threads",
    "zlib",
}
PYTHON_STDLIB = set(getattr(sys, "stdlib_module_names", set()))

KNOWN_STRUCTURE_DIRS = [
    "controllers",
    "services",
    "models",
    "utils",
    "components",
    "pages",
    "routes",
    "middlewares",
    "middleware",
    "hooks",
    "store",
    "stores",
]

LESS_STRICT_FUNCTION_PATTERNS = [
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^()]*\)\s*=>"),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?[A-Za-z_$][\w$]*\s*=>"),
    re.compile(r"^\s*(?:public|private|protected|static|async|\s)*([A-Za-z_$][\w$]*)\s*\([^;]*\)\s*\{"),
]
VARIABLE_JS_PATTERN = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)")
VARIABLE_PY_PATTERN = re.compile(r"^\s*([A-Za-z_][\w]*)\s*=")
FUNCTION_PY_PATTERN = re.compile(r"^\s*def\s+([A-Za-z_][\w]*)\s*\(")
COMPONENT_PATTERN = re.compile(r"^\s*(?:export\s+default\s+)?(?:function|class|const)\s+([A-Za-z_][\w]*)")

IMPORT_FROM_JS_PATTERN = re.compile(r"^\s*import\s+.+?\s+from\s+['\"]([^'\"]+)['\"]")
IMPORT_SIDE_JS_PATTERN = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]")
REQUIRE_PATTERN = re.compile(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)")
EXPORT_PATTERN = re.compile(r"^\s*export\b")
IMPORT_PY_PATTERN = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)")
FROM_IMPORT_PY_PATTERN = re.compile(r"^\s*from\s+([A-Za-z_][\w.]*|\.+[\w.]*)\s+import\s+")

QUOTE_SINGLE_PATTERN = re.compile(r"'(?:[^'\\]|\\.)*'")
QUOTE_DOUBLE_PATTERN = re.compile(r'"(?:[^"\\]|\\.)*"')
TRAILING_COMMA_PATTERN = re.compile(r",\s*(?:[}\]])")

STATE_PATTERNS = {
    "Redux": ["redux", "@reduxjs/toolkit", "createSlice", "configureStore", "useSelector(", "useDispatch("],
    "Zustand": ["zustand", "create((set", "create((state"],
    "Pinia": ["pinia", "defineStore("],
    "useReducer": ["useReducer("],
    "useState": ["useState("],
}
DATA_FETCH_PATTERNS = {
    "axios": ["axios", "axios."],
    "SWR": ["useSWR(", " from 'swr", ' from "swr'],
    "React Query": ["@tanstack/react-query", "useQuery(", "useMutation(", "QueryClient"],
    "fetch": ["fetch("],
    "custom-hooks": ["useFetch(", "useApi("],
}
ROUTING_PATTERNS = {
    "express-router": ["express.Router(", "router.", "app.use("],
    "nextjs-app-router": ["next/navigation", "/app/", "route.ts", "route.js"],
    "react-router": ["react-router", "BrowserRouter", "createBrowserRouter", "<Routes"],
}
ORM_PATTERNS = {
    "mongoose": ["mongoose", "Schema(", ".find(", ".aggregate("],
    "prisma": ["prisma.", "schema.prisma"],
    "typeorm": ["typeorm", "@Entity", "Repository<"],
    "sequelize": ["sequelize", "DataTypes", "Model.init"],
    "raw-queries": ["SELECT ", "INSERT ", "UPDATE ", "DELETE FROM"],
}
AUTH_PATTERNS = {
    "jwt": ["jsonwebtoken", "jwt.sign", "jwt.verify", "bearer "],
    "session": ["express-session", "req.session", "session("],
    "oauth": ["passport", "oauth", "openid", "google strategy"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Analyze project patterns and write project profile JSON.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python analyze_patterns.py --project-root <path>\n"

            "  python analyze_patterns.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--output", default="", help="Output profile path")
    parser.add_argument("--sample-size", type=int, default=20, help="Number of largest files to analyze")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def rel_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_candidate_file(path: Path) -> bool:
    name_lower = path.name.lower()
    if name_lower in SKIP_FILE_NAMES:
        return False
    if name_lower.endswith(".min.js"):
        return False
    if path.suffix.lower() not in CODE_EXTENSIONS:
        return False
    return True


def collect_candidate_files(project_root: Path) -> List[Path]:
    files_with_size: List[Tuple[int, Path]] = []
    for current_root, dirs, names in os.walk(project_root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        root_path = Path(current_root)
        for name in names:
            path = root_path / name
            if not is_candidate_file(path):
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            files_with_size.append((size, path))
    files_with_size.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in files_with_size]


def read_lines_for_analysis(path: Path) -> Tuple[List[str], int, bool]:
    first_500: List[str] = []
    first_2000: List[str] = []
    total = 0
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for raw in handle:
                total += 1
                line = raw.rstrip("\n\r")
                if total <= 500:
                    first_500.append(line)
                if total <= 2000:
                    first_2000.append(line)
    except OSError:
        return [], 0, False

    if total > 2000:
        return first_500, total, True
    return first_2000, total, False


def classify_identifier_style(name: str) -> str:
    if re.match(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$", name):
        return "snake_case"
    if re.match(r"^[A-Z][A-Za-z0-9]*$", name):
        return "PascalCase"
    if re.match(r"^[a-z][A-Za-z0-9]*$", name):
        return "camelCase"
    if re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)+$", name):
        return "kebab-case"
    return "other"


def dominant_from_counter(counter: Counter[str], fallback: str = "mixed") -> str:
    if not counter:
        return "unknown"
    common = counter.most_common(2)
    if len(common) > 1 and common[0][1] == common[1][1]:
        return fallback
    return common[0][0]


def p90(values: Sequence[int]) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    index = max(0, math.ceil(0.9 * len(sorted_values)) - 1)
    return int(sorted_values[index])


def detect_file_naming(project_root: Path, all_files: List[Path]) -> str:
    src_root = project_root / "src"
    targets = [path for path in all_files if path.is_file() and (src_root in path.parents)]
    if not targets:
        targets = all_files

    styles: Counter[str] = Counter()
    for path in targets:
        stem = path.stem
        stem = re.sub(r"\.(test|spec)$", "", stem, flags=re.IGNORECASE)
        style = classify_identifier_style(stem)
        if style in {"camelCase", "PascalCase", "kebab-case", "snake_case"}:
            styles[style] += 1
    return dominant_from_counter(styles)


def detect_test_pattern(project_root: Path) -> str:
    counter: Counter[str] = Counter()
    for current_root, dirs, names in os.walk(project_root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        for name in names:
            lower = name.lower()
            full = (Path(current_root) / name).as_posix().lower()
            if ".test." in lower:
                ext = lower.rsplit(".test.", 1)[1]
                counter[f"*.test.{ext}"] += 1
            if ".spec." in lower:
                ext = lower.rsplit(".spec.", 1)[1]
                counter[f"*.spec.{ext}"] += 1
            if "/__tests__/" in full:
                counter["__tests__/*"] += 1
    return dominant_from_counter(counter, fallback="mixed")


def detect_entry_point(project_root: Path) -> str:
    candidates = [
        "src/index.ts",
        "src/index.js",
        "src/main.ts",
        "src/main.js",
        "src/app.ts",
        "src/app.js",
        "app/main.py",
        "main.py",
        "server.ts",
        "server.js",
        "index.ts",
        "index.js",
        "app.py",
    ]
    for rel in candidates:
        path = project_root / rel
        if path.exists() and path.is_file():
            return rel

    package_json = project_root / "package.json"
    if package_json.exists():
        try:
            payload = json.loads(package_json.read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            main = payload.get("main")
            if isinstance(main, str) and main.strip():
                return main.strip().replace("\\", "/")

    return "unknown"


def detect_structure_directories(project_root: Path) -> List[str]:
    dir_counter: Counter[str] = Counter()
    for current_root, dirs, _ in os.walk(project_root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        for directory in dirs:
            dir_counter[directory.lower()] += 1

    picked = [name for name in KNOWN_STRUCTURE_DIRS if dir_counter.get(name, 0) > 0]
    if picked:
        return picked
    return [name for name, _ in dir_counter.most_common(6)]


def categorize_import(module: str) -> Tuple[str, bool, bool]:
    module = module.strip()
    if not module:
        return "external", False, False
    if module.startswith("@/") or module.startswith("~/"):
        return "internal", True, False
    if module.startswith(".") or module.startswith("/"):
        return "internal", False, True
    if module.startswith("node:"):
        return "built-in", False, False
    base = module.split("/", 1)[0]
    if base in NODE_BUILTINS or base in PYTHON_STDLIB:
        return "built-in", False, False
    return "external", False, False


def detect_import_ordering(categories: List[str]) -> str:
    if len(categories) < 2:
        return "unknown"
    ordering = {"built-in": 0, "external": 1, "internal": 2}
    values = [ordering.get(cat, 1) for cat in categories]
    return "ordered" if all(values[idx] >= values[idx - 1] for idx in range(1, len(values))) else "mixed"


def count_keyword_score(content: str, mapping: Dict[str, List[str]]) -> str:
    scores: Dict[str, int] = {}
    for label, keywords in mapping.items():
        score = 0
        for keyword in keywords:
            score += content.count(keyword.lower())
        scores[label] = score
    best = max(scores.items(), key=lambda item: item[1])
    return best[0] if best[1] > 0 else "unknown"


def sanitize_line_for_semicolon(line: str) -> Optional[str]:
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("/*") or stripped.startswith("*"):
        return None
    return stripped


def analyze(project_root: Path, sample_size: int) -> Dict[str, object]:
    all_candidates = collect_candidate_files(project_root)
    sampled_files = all_candidates[: max(1, sample_size)]
    warnings: List[str] = []

    variable_styles: Counter[str] = Counter()
    function_styles: Counter[str] = Counter()
    component_styles: Counter[str] = Counter()
    file_name_style = detect_file_naming(project_root, all_candidates)
    test_pattern = detect_test_pattern(project_root)

    total_line_lengths: List[int] = []
    total_file_lines = 0
    function_counts: List[int] = []
    files_analyzed = 0

    semicolon_yes = 0
    semicolon_no = 0
    quote_single = 0
    quote_double = 0
    trailing_commas = 0
    indent_tabs = 0
    indent_spaces: Counter[int] = Counter()

    module_es = 0
    module_cjs = 0
    alias_imports = 0
    relative_imports = 0
    import_order_counter: Counter[str] = Counter()

    error_style_counts: Counter[str] = Counter()
    custom_error_hits = 0
    error_json_hits = 0
    error_text_hits = 0

    combined_content_parts: List[str] = []

    for path in sampled_files:
        analyzed_lines, total_lines, truncated = read_lines_for_analysis(path)
        if total_lines == 0:
            warnings.append(f"Unable to read file: {rel_path(path, project_root)}")
            continue
        files_analyzed += 1
        total_file_lines += total_lines
        if truncated:
            warnings.append(f"Truncated analysis to first 500 lines for large file: {rel_path(path, project_root)}")

        ext = path.suffix.lower()
        file_function_count = 0
        import_categories: List[str] = []
        lowered_content = "\n".join(analyzed_lines).lower()
        combined_content_parts.append(lowered_content)

        for line in analyzed_lines:
            total_line_lengths.append(len(line))
            quote_single += len(QUOTE_SINGLE_PATTERN.findall(line))
            quote_double += len(QUOTE_DOUBLE_PATTERN.findall(line))
            if TRAILING_COMMA_PATTERN.search(line):
                trailing_commas += 1
            if line.startswith("\t"):
                indent_tabs += 1
            else:
                space_match = re.match(r"^( +)\S", line)
                if space_match:
                    indent_spaces[len(space_match.group(1))] += 1

            if ext in JS_TS_EXTENSIONS:
                clean = sanitize_line_for_semicolon(line)
                if clean is not None:
                    if clean.endswith(";"):
                        semicolon_yes += 1
                    elif clean.endswith("{") or clean.endswith("}") or clean.endswith(",") or clean.endswith(":"):
                        pass
                    else:
                        semicolon_no += 1

                for match in VARIABLE_JS_PATTERN.finditer(line):
                    style = classify_identifier_style(match.group(1))
                    if style in {"camelCase", "snake_case", "PascalCase"}:
                        variable_styles[style] += 1

                for pattern in LESS_STRICT_FUNCTION_PATTERNS:
                    found = pattern.search(line)
                    if found:
                        name = found.group(1)
                        file_function_count += 1
                        style = classify_identifier_style(name)
                        if style in {"camelCase", "snake_case", "PascalCase"}:
                            function_styles[style] += 1
                        break

                component_match = COMPONENT_PATTERN.search(line)
                if component_match:
                    name = component_match.group(1)
                    style = classify_identifier_style(name)
                    if style in {"camelCase", "snake_case", "PascalCase"}:
                        component_styles[style] += 1

                from_match = IMPORT_FROM_JS_PATTERN.search(line)
                if from_match:
                    module_es += 1
                    category, is_alias, is_relative = categorize_import(from_match.group(1))
                    import_categories.append(category)
                    alias_imports += 1 if is_alias else 0
                    relative_imports += 1 if is_relative else 0
                else:
                    side_match = IMPORT_SIDE_JS_PATTERN.search(line)
                    if side_match:
                        module_es += 1
                        category, is_alias, is_relative = categorize_import(side_match.group(1))
                        import_categories.append(category)
                        alias_imports += 1 if is_alias else 0
                        relative_imports += 1 if is_relative else 0

                for req in REQUIRE_PATTERN.findall(line):
                    module_cjs += 1
                    category, is_alias, is_relative = categorize_import(req)
                    import_categories.append(category)
                    alias_imports += 1 if is_alias else 0
                    relative_imports += 1 if is_relative else 0

                if EXPORT_PATTERN.search(line):
                    module_es += 1
                if "module.exports" in line or "exports." in line:
                    module_cjs += 1

            elif ext in PYTHON_EXTENSIONS:
                var_match = VARIABLE_PY_PATTERN.search(line)
                if var_match:
                    name = var_match.group(1)
                    if name not in {"if", "for", "while", "return", "class", "def"}:
                        style = classify_identifier_style(name)
                        if style in {"camelCase", "snake_case", "PascalCase"}:
                            variable_styles[style] += 1

                fn_match = FUNCTION_PY_PATTERN.search(line)
                if fn_match:
                    file_function_count += 1
                    style = classify_identifier_style(fn_match.group(1))
                    if style in {"camelCase", "snake_case", "PascalCase"}:
                        function_styles[style] += 1

                import_match = IMPORT_PY_PATTERN.search(line)
                if import_match:
                    category, _, is_relative = categorize_import(import_match.group(1))
                    import_categories.append(category)
                    relative_imports += 1 if is_relative else 0
                from_match = FROM_IMPORT_PY_PATTERN.search(line)
                if from_match:
                    category, _, is_relative = categorize_import(from_match.group(1))
                    import_categories.append(category)
                    relative_imports += 1 if is_relative else 0

        function_counts.append(file_function_count)

        order = detect_import_ordering(import_categories)
        if order != "unknown":
            import_order_counter[order] += 1

        error_style_counts["try-catch"] += lowered_content.count("try {") + lowered_content.count("try:")
        error_style_counts["promise-catch"] += lowered_content.count(".catch(")
        error_style_counts["error-middleware"] += lowered_content.count("next(err)") + lowered_content.count("(err, req, res, next)")
        custom_error_hits += len(re.findall(r"class\s+[A-Za-z_]\w*Error\s+extends\s+Error", lowered_content))
        custom_error_hits += len(re.findall(r"class\s+[A-Za-z_]\w*Error\s*\(.*exception.*\)", lowered_content))
        error_json_hits += lowered_content.count(".json(") + lowered_content.count("jsonify(")
        error_text_hits += lowered_content.count(".send(") + lowered_content.count("return response(")

    combined_content = "\n".join(combined_content_parts)

    module_system = "unknown"
    if module_es > 0 or module_cjs > 0:
        if module_es > module_cjs * 1.2:
            module_system = "esmodules"
        elif module_cjs > module_es * 1.2:
            module_system = "commonjs"
        else:
            module_system = "mixed"

    import_ordering = "mixed"
    ordered = import_order_counter.get("ordered", 0)
    mixed = import_order_counter.get("mixed", 0)
    if ordered > 0 and mixed == 0:
        import_ordering = "built-in-external-internal"
    elif ordered > mixed and (ordered + mixed) > 0:
        import_ordering = "mostly built-in-external-internal"

    primary_error_style = dominant_from_counter(error_style_counts, fallback="unknown")
    if primary_error_style == "unknown" and sum(error_style_counts.values()) == 0:
        primary_error_style = "unknown"

    error_response_format = "unknown"
    if error_json_hits > error_text_hits and error_json_hits > 0:
        error_response_format = "json"
    elif error_text_hits > error_json_hits and error_text_hits > 0:
        error_response_format = "text"
    elif error_json_hits > 0 and error_text_hits > 0:
        error_response_format = "mixed"

    quotes = "mixed"
    if quote_single > quote_double:
        quotes = "single"
    elif quote_double > quote_single:
        quotes = "double"

    semicolons = semicolon_yes >= semicolon_no if (semicolon_yes + semicolon_no) > 0 else True

    indent = "unknown"
    if indent_tabs > sum(indent_spaces.values()):
        indent = "tabs"
    elif indent_spaces:
        common_space = indent_spaces.most_common(1)[0][0]
        if common_space >= 4 and common_space % 4 == 0:
            indent = "4 spaces"
        elif common_space >= 2 and common_space % 2 == 0:
            indent = "2 spaces"
        else:
            indent = f"{common_space} spaces"

    avg_file_lines = round(total_file_lines / files_analyzed, 2) if files_analyzed else 0
    avg_functions = round(sum(function_counts) / len(function_counts), 2) if function_counts else 0

    state = count_keyword_score(combined_content, STATE_PATTERNS)
    data_fetching = count_keyword_score(combined_content, DATA_FETCH_PATTERNS)
    routing = count_keyword_score(combined_content, ROUTING_PATTERNS)
    orm = count_keyword_score(combined_content, ORM_PATTERNS)
    auth = count_keyword_score(combined_content, AUTH_PATTERNS)

    confidence_score = 0
    if files_analyzed >= min(sample_size, 10):
        confidence_score += 2
    elif files_analyzed >= 5:
        confidence_score += 1
    if sum(variable_styles.values()) >= 20 and sum(function_styles.values()) >= 10:
        confidence_score += 1
    if len(total_line_lengths) >= 300:
        confidence_score += 1

    confidence = "low"
    if confidence_score >= 4:
        confidence = "high"
    elif confidence_score >= 2:
        confidence = "medium"

    profile = {
        "project_name": project_root.name,
        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        "sample_size": int(sample_size),
        "files_analyzed": int(files_analyzed),
        "naming": {
            "variables": dominant_from_counter(variable_styles),
            "files": file_name_style,
            "functions": dominant_from_counter(function_styles),
            "components": dominant_from_counter(component_styles),
            "test_pattern": test_pattern,
        },
        "structure": {
            "avg_file_lines": avg_file_lines,
            "avg_functions_per_file": avg_functions,
            "directories": detect_structure_directories(project_root),
            "entry_point": detect_entry_point(project_root),
        },
        "imports": {
            "module_system": module_system,
            "alias_used": alias_imports > 0,
            "ordering": import_ordering,
        },
        "error_handling": {
            "primary_style": primary_error_style,
            "custom_errors": custom_error_hits > 0,
            "response_format": error_response_format,
        },
        "code_style": {
            "semicolons": semicolons,
            "quotes": quotes,
            "trailing_commas": trailing_commas > 0,
            "indent": indent,
            "p90_line_length": p90(total_line_lengths),
        },
        "patterns": {
            "state_management": state,
            "data_fetching": data_fetching,
            "routing": routing,
            "orm": orm,
            "auth": auth,
        },
        "confidence": confidence,
    }

    payload: Dict[str, object] = {"profile": profile}
    if warnings:
        payload["warnings"] = sorted(dict.fromkeys(warnings))
    return payload


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "path": "", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    output_path = Path(args.output).expanduser().resolve() if args.output else (project_root / ".codex" / "project-profile.json")
    sample_size = max(1, int(args.sample_size))

    try:
        analysis_payload = analyze(project_root, sample_size)
        profile = analysis_payload["profile"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(profile, handle, ensure_ascii=False, indent=2)
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

    output: Dict[str, object] = {
        "status": "generated",
        "path": output_path.as_posix(),
        "profile": profile,
    }
    if "warnings" in analysis_payload:
        output["warnings"] = analysis_payload["warnings"]
    emit(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
