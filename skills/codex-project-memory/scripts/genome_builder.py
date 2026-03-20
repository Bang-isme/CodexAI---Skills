from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

TOML_ERROR = tomllib.TOMLDecodeError if tomllib is not None else ValueError


SKIP_DIRS = {
    ".analytics",
    ".codex",
    ".git",
    ".idea",
    ".mypy_cache",
    ".next",
    ".parcel-cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vscode",
    ".yarn",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
}

TEXT_EXTENSIONS = {
    ".c",
    ".cpp",
    ".cs",
    ".css",
    ".env",
    ".go",
    ".h",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".yaml",
    ".yml",
}

PATTERN_SCAN_EXTENSIONS = {
    ".c",
    ".cpp",
    ".cs",
    ".env",
    ".go",
    ".h",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".vue",
    ".yaml",
    ".yml",
}

LANGUAGE_NAMES = {
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".go": "Go",
    ".h": "C/C++ Header",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".json": "JSON",
    ".jsx": "React JSX",
    ".kt": "Kotlin",
    ".md": "Markdown",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".swift": "Swift",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "React TSX",
    ".vue": "Vue",
    ".yaml": "YAML",
    ".yml": "YAML",
}

ENTRY_POINT_CANDIDATES = {
    "app.py",
    "main.py",
    "manage.py",
    "run.py",
    "app.js",
    "index.js",
    "server.js",
    "main.js",
    "app.ts",
    "index.ts",
    "server.ts",
    "main.ts",
    "main.go",
    "Program.cs",
}

MODULE_PURPOSES = {
    "api": "API layer and request handlers",
    "app": "application shell or service bootstrap",
    "assets": "static assets and media",
    "backend": "backend services and APIs",
    "components": "reusable UI components",
    "config": "configuration and environment setup",
    "controllers": "request orchestration and controller logic",
    "db": "database access or persistence helpers",
    "docs": "documentation and guides",
    "frontend": "frontend application code",
    "lib": "shared libraries and utilities",
    "middleware": "request/response middleware",
    "migrations": "database migrations",
    "models": "data models and schemas",
    "pages": "page-level routes or screens",
    "routes": "route declarations and routers",
    "scripts": "automation or maintenance scripts",
    "services": "service integrations and domain services",
    "src": "primary application source",
    "test": "tests and fixtures",
    "tests": "tests and fixtures",
    "utils": "utility functions and helpers",
}

SPECIAL_TEXT_FILES = {
    ".env.example",
    ".env.sample",
    ".gitignore",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.py",
    "vite.config.ts",
    "vite.config.js",
}

SECTION_ORDER = [
    "architecture",
    "api",
    "data",
    "security",
    "tests",
    "file_map",
]

SECTION_TITLES = {
    "architecture": "Architecture Overview",
    "api": "API Surface",
    "data": "Data Layer",
    "security": "Security Posture",
    "tests": "Test Coverage Map",
    "file_map": "File Map",
}

SECTION_ALIASES = {
    "all": "all",
    "api": "api",
    "arch": "architecture",
    "architecture": "architecture",
    "data": "data",
    "data-layer": "data",
    "datalayer": "data",
    "file-map": "file_map",
    "filemap": "file_map",
    "files": "file_map",
    "security": "security",
    "test": "tests",
    "test-coverage": "tests",
    "tests": "tests",
    "tree": "file_map",
}

ROUTE_PATTERNS = [
    re.compile(r"""(app|router)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""", re.IGNORECASE),
    re.compile(r"""@(app|router)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""", re.IGNORECASE),
    re.compile(r"""(?<!\w)path\s*\(\s*['"]([^'"]+)['"]"""),
]

MODEL_PATTERNS = [
    re.compile(r"""(mongoose\.model|Schema)\s*\(""", re.IGNORECASE),
    re.compile(r"""(sequelize\.define|Model\.init)\s*\(""", re.IGNORECASE),
    re.compile(r"""model\s+\w+\s*\{""", re.IGNORECASE),
    re.compile(r"""class\s+\w+\(.*Model\)""", re.IGNORECASE),
]

MIDDLEWARE_PATTERNS = [
    re.compile(r"""app\.use\s*\(""", re.IGNORECASE),
    re.compile(r"""@app\.middleware""", re.IGNORECASE),
]

AUTH_PATTERNS = {
    "JWT": re.compile(r"""(jwt|jsonwebtoken)""", re.IGNORECASE),
    "Session": re.compile(r"""(session|cookie-session|express-session)""", re.IGNORECASE),
    "OAuth": re.compile(r"""(OAuth|oauth2|openid|passport)""", re.IGNORECASE),
    "Password Hashing": re.compile(r"""(bcrypt|argon2)""", re.IGNORECASE),
}

AUTH_MODULE_LABELS = {
    "argon2": "Password hashing",
    "bcrypt": "Password hashing",
    "bcryptjs": "Password hashing",
    "cookie-session": "Session",
    "express-session": "Session",
    "jsonwebtoken": "JWT",
    "oauth2-server": "OAuth",
    "openid-client": "OAuth",
    "passport": "OAuth",
}

DB_PATTERNS = {
    "MongoDB/Mongoose": re.compile(r"""(mongoose|mongodb)""", re.IGNORECASE),
    "Prisma": re.compile(r"""prisma""", re.IGNORECASE),
    "Sequelize": re.compile(r"""sequelize""", re.IGNORECASE),
    "SQLAlchemy": re.compile(r"""sqlalchemy""", re.IGNORECASE),
    "Django ORM": re.compile(r"""django\.db|models\.Model""", re.IGNORECASE),
    "PostgreSQL": re.compile(r"""postgres|psycopg|pg\b""", re.IGNORECASE),
    "MySQL": re.compile(r"""mysql|pymysql""", re.IGNORECASE),
    "SQLite": re.compile(r"""sqlite""", re.IGNORECASE),
    "Redis": re.compile(r"""redis""", re.IGNORECASE),
}

TEST_FRAMEWORK_PATTERNS = {
    "Jest": re.compile(r"""jest""", re.IGNORECASE),
    "Vitest": re.compile(r"""vitest""", re.IGNORECASE),
    "Pytest": re.compile(r"""pytest""", re.IGNORECASE),
    "Mocha": re.compile(r"""mocha""", re.IGNORECASE),
    "Node test runner": re.compile(r"""node:test|node --test""", re.IGNORECASE),
    "Unittest": re.compile(r"""unittest""", re.IGNORECASE),
}

TEST_PACKAGE_LABELS = {
    "chai": "Chai",
    "jest": "Jest",
    "mocha": "Mocha",
    "playwright": "Playwright",
    "supertest": "Supertest",
    "vitest": "Vitest",
}

SECRET_PATTERNS = [
    re.compile(r"""(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['"][^'"]{8,}['"]"""),
    re.compile(r"""(?i)AKIA[0-9A-Z]{16}"""),
]

CORS_PATTERNS = [
    re.compile(r"""cors\(""", re.IGNORECASE),
    re.compile(r"""CORSMiddleware""", re.IGNORECASE),
    re.compile(r"""django-cors-headers""", re.IGNORECASE),
]

RATE_LIMIT_PATTERNS = [
    re.compile(r"""rate.?limit""", re.IGNORECASE),
    re.compile(r"""flask-limiter""", re.IGNORECASE),
    re.compile(r"""slowapi""", re.IGNORECASE),
]

AUTH_MIDDLEWARE_PATTERNS = [
    re.compile(r"""passport\.authenticate""", re.IGNORECASE),
    re.compile(r"""jwt""", re.IGNORECASE),
    re.compile(r"""authMiddleware|requireAuth|login_required""", re.IGNORECASE),
]

HTTPS_PATTERNS = [
    re.compile(r"""HTTPSRedirectMiddleware""", re.IGNORECASE),
    re.compile(r"""require_https|ssl_redirect|SECURE_SSL_REDIRECT""", re.IGNORECASE),
    re.compile(r"""helmet\.hsts""", re.IGNORECASE),
]

TEST_DIR_NAMES = {"__tests__", "spec", "test", "tests"}
CI_FILES = [
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    ".circleci/config.yml",
    ".github/workflows",
]
MIGRATION_DIR_HINTS = {"alembic", "migrations", "prisma", "db"}
MAX_SCAN_FILE_SIZE = 512_000


def emit_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def normalize_sections(value: str) -> List[str]:
    raw_items = [item.strip().lower() for item in value.split(",") if item.strip()]
    if not raw_items or "all" in raw_items:
        return list(SECTION_ORDER)

    selected: List[str] = []
    for item in raw_items:
        canonical = SECTION_ALIASES.get(item)
        if canonical and canonical != "all" and canonical not in selected:
            selected.append(canonical)
    return selected or list(SECTION_ORDER)


def detect_scan_depth(depth_mode: str) -> int:
    if depth_mode == "shallow":
        return 2
    return 3


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def should_scan_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in SPECIAL_TEXT_FILES


def supports_pattern_scan(item: Dict[str, Any]) -> bool:
    name = str(item["name"])
    suffix = str(item["suffix"])
    return suffix in PATTERN_SCAN_EXTENSIONS or name in SPECIAL_TEXT_FILES


def is_api_candidate(rel_path: str) -> bool:
    parts = [part.lower() for part in Path(rel_path).parts]
    filename = Path(rel_path).name.lower()
    keywords = {"api", "app", "backend", "controller", "controllers", "pages", "routes", "router", "server", "starters", "views"}
    return filename in {name.lower() for name in ENTRY_POINT_CANDIDATES} or bool(keywords.intersection(parts)) or any(
        token in filename for token in ("api", "route", "router", "server", "app", "view", "controller")
    )


def is_data_candidate(rel_path: str) -> bool:
    parts = [part.lower() for part in Path(rel_path).parts]
    filename = Path(rel_path).name.lower()
    keywords = {"db", "database", "entities", "entity", "migrations", "model", "models", "prisma", "schema", "schemas", "starters"}
    return bool(keywords.intersection(parts)) or any(
        token in filename for token in ("model", "schema", "entity", "prisma", "migration", "db")
    )


def is_auth_candidate(rel_path: str, text: str, routes: Sequence[str]) -> bool:
    lowered_path = rel_path.lower()
    if any(token in lowered_path for token in ("auth", "password", "refresh", "session", "token")):
        return True
    if any(module_display_name(module_name).lower() in AUTH_MODULE_LABELS for module_name in extract_module_references(text)):
        return True
    return any("/refresh" in route.lower() or "refresh" in route.lower() for route in routes)


def walk_inventory(project_root: Path, max_depth: int) -> List[Dict[str, Any]]:
    inventory: List[Dict[str, Any]] = []
    for root_str, dirs, files in os.walk(project_root):
        root = Path(root_str)
        rel_root = root.relative_to(project_root)
        depth = len(rel_root.parts)
        dirs[:] = sorted(item for item in dirs if item not in SKIP_DIRS)
        if depth >= max_depth:
            dirs[:] = []

        for filename in sorted(files):
            file_path = root / filename
            try:
                size = file_path.stat().st_size
            except OSError:
                continue

            rel_path = file_path.relative_to(project_root).as_posix()
            item: Dict[str, Any] = {
                "path": file_path,
                "rel_path": rel_path,
                "name": filename,
                "suffix": file_path.suffix.lower(),
                "size": size,
                "line_count": count_lines(file_path) if should_scan_text(file_path) and size <= MAX_SCAN_FILE_SIZE else 0,
                "text": "",
            }
            if should_scan_text(file_path) and size <= MAX_SCAN_FILE_SIZE:
                item["text"] = safe_read_text(file_path)
            inventory.append(item)
    return inventory


def limit_items(items: Sequence[str], size: int = 10) -> List[str]:
    return list(items[:size])


def unique_preserve(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def load_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def parse_named_aliases(raw_value: str) -> List[str]:
    aliases: List[str] = []
    for part in raw_value.split(","):
        cleaned = part.strip()
        if not cleaned:
            continue
        if " as " in cleaned:
            cleaned = cleaned.split(" as ", 1)[1].strip()
        if ":" in cleaned:
            cleaned = cleaned.split(":", 1)[1].strip()
        aliases.append(cleaned)
    return aliases


def build_import_alias_map(text: str) -> Dict[str, str]:
    alias_map: Dict[str, str] = {}
    patterns = [
        re.compile(r"""(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*require\(\s*['"]([^'"]+)['"]\s*\)"""),
        re.compile(r"""import\s+([A-Za-z_$][\w$]*)\s+from\s+['"]([^'"]+)['"]"""),
    ]
    named_patterns = [
        re.compile(r"""(?:const|let|var)\s*\{([^}]+)\}\s*=\s*require\(\s*['"]([^'"]+)['"]\s*\)"""),
        re.compile(r"""import\s*\{([^}]+)\}\s*from\s+['"]([^'"]+)['"]"""),
    ]

    for pattern in patterns:
        for match in pattern.finditer(text):
            alias_map[match.group(1).strip()] = match.group(2).strip()

    for pattern in named_patterns:
        for match in pattern.finditer(text):
            module_name = match.group(2).strip()
            for alias in parse_named_aliases(match.group(1)):
                alias_map[alias] = module_name

    return alias_map


def extract_module_references(text: str) -> List[str]:
    modules: List[str] = []
    patterns = [
        re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
        re.compile(r"""from\s+['"]([^'"]+)['"]"""),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            modules.append(match.group(1).strip())
    return unique_preserve(modules)


def kebab_case(value: str) -> str:
    normalized = re.sub(r"""([a-z0-9])([A-Z])""", r"\1-\2", value)
    normalized = normalized.replace("_", "-")
    normalized = normalized.strip("-").lower()
    return normalized


def module_display_name(module_name: str) -> str:
    normalized = module_name.strip()
    if not normalized:
        return ""
    if normalized.startswith("."):
        stem = Path(normalized).stem or Path(normalized).name
        return stem or normalized
    if normalized.startswith("@") and "/" in normalized:
        return normalized.split("/", 1)[1]
    if "/" in normalized:
        return normalized.rsplit("/", 1)[1]
    return normalized


def normalize_middleware_name(expression: str, alias_map: Dict[str, str]) -> str | None:
    cleaned = expression.strip()
    if not cleaned:
        return None
    if cleaned.startswith(("function", "(")):
        return None

    base_expression = cleaned
    function_match = re.match(r"""([A-Za-z_$][\w$.]*)\s*\(""", cleaned)
    if function_match:
        base_expression = function_match.group(1)

    module_name = alias_map.get(base_expression)
    if module_name is None and "." not in base_expression:
        module_name = alias_map.get(base_expression.split(".")[0], "")

    lowered_expression = cleaned.lower()
    lowered_module = module_name.lower() if module_name else ""
    if "/routes/" in lowered_module or lowered_module.endswith("/routes") or lowered_expression.endswith(("routes", "router")):
        return None

    if "." in base_expression:
        label = base_expression
    elif module_name:
        label = module_display_name(module_name)
    else:
        label = base_expression

    if "." not in label:
        label = label.removesuffix("Middleware").removesuffix("Handler").removesuffix("Protection")
        if label.endswith("Limiter"):
            label = label[: -len("Limiter")] + "Limit"

    normalized = kebab_case(label) if "." not in label else label
    return normalized or None


def split_top_level_commas(value: str) -> List[str]:
    parts: List[str] = []
    current: List[str] = []
    paren_depth = 0
    brace_depth = 0
    bracket_depth = 0
    quote_char = ""
    escape_next = False

    for char in value:
        current.append(char)
        if quote_char:
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == quote_char:
                quote_char = ""
            continue

        if char in {"'", '"', "`"}:
            quote_char = char
            continue
        if char == "(":
            paren_depth += 1
            continue
        if char == ")":
            paren_depth = max(paren_depth - 1, 0)
            continue
        if char == "{":
            brace_depth += 1
            continue
        if char == "}":
            brace_depth = max(brace_depth - 1, 0)
            continue
        if char == "[":
            bracket_depth += 1
            continue
        if char == "]":
            bracket_depth = max(bracket_depth - 1, 0)
            continue
        if char == "," and paren_depth == 0 and brace_depth == 0 and bracket_depth == 0:
            current.pop()
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def extract_call_bodies(text: str, call_prefix: str) -> List[str]:
    bodies: List[str] = []
    start_index = 0
    while True:
        match_index = text.find(call_prefix, start_index)
        if match_index == -1:
            break
        cursor = match_index + len(call_prefix)
        depth = 1
        quote_char = ""
        escape_next = False
        body_start = cursor
        while cursor < len(text):
            char = text[cursor]
            if quote_char:
                if escape_next:
                    escape_next = False
                elif char == "\\":
                    escape_next = True
                elif char == quote_char:
                    quote_char = ""
                cursor += 1
                continue

            if char in {"'", '"', "`"}:
                quote_char = char
                cursor += 1
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    bodies.append(text[body_start:cursor])
                    cursor += 1
                    break
            cursor += 1
        start_index = cursor
    return bodies


def extract_middleware_chain(text: str, rel_path: str) -> List[str]:
    alias_map = build_import_alias_map(text)
    middleware: List[str] = []
    for body in extract_call_bodies(text, "app.use("):
        args = split_top_level_commas(body)
        if not args:
            continue
        candidate_args = args[1:] if re.match(r"""['"]""", args[0].strip()) else args
        for candidate in candidate_args:
            label = normalize_middleware_name(candidate, alias_map)
            if label:
                middleware.append(label)
    return unique_preserve(middleware)


def is_non_production_example_path(rel_path: str) -> bool:
    parts = [part.lower() for part in Path(rel_path).parts]
    filename = Path(rel_path).name.lower()
    if any(part in {"__tests__", "example", "examples", "fixture", "fixtures", "test", "tests"} for part in parts):
        return True
    return any(token in filename for token in ("example", "sample", "template"))


def detect_detailed_auth_patterns(text: str, rel_path: str, routes: Sequence[str]) -> List[str]:
    detailed_hits: List[str] = []
    for module_name in extract_module_references(text):
        module_key = module_display_name(module_name).lower()
        label = AUTH_MODULE_LABELS.get(module_key)
        if label:
            detailed_hits.append(f"{label} ({module_display_name(module_name)}) - {rel_path}")

    for route in routes:
        if "/refresh" in route.lower() or "refresh" in route.lower():
            detailed_hits.append(f"Refresh token flow - {rel_path} ({route})")

    return unique_preserve(detailed_hits)


def detect_generic_auth_patterns(text: str) -> List[str]:
    return [label for label, pattern in AUTH_PATTERNS.items() if pattern.search(text)]


def detect_test_frameworks_from_package(project_root: Path) -> List[str]:
    payload = load_json_file(project_root / "package.json")
    if not payload:
        return []

    frameworks: List[str] = []
    dependencies = payload.get("dependencies", {})
    dev_dependencies = payload.get("devDependencies", {})
    for package_name, label in TEST_PACKAGE_LABELS.items():
        if isinstance(dev_dependencies, dict) and package_name in dev_dependencies:
            frameworks.append(label)
        elif isinstance(dependencies, dict) and package_name in dependencies:
            frameworks.append(label)

    scripts = payload.get("scripts", {})
    test_script = scripts.get("test", "") if isinstance(scripts, dict) else ""
    script_patterns = {
        "jest": "Jest",
        "vitest": "Vitest",
        "mocha": "Mocha",
        "chai": "Chai",
        "supertest": "Supertest",
        "playwright": "Playwright",
    }
    lower_script = str(test_script).lower()
    for token, label in script_patterns.items():
        if token in lower_script:
            frameworks.append(label)
    if "node --test" in lower_script or "node:test" in lower_script:
        frameworks.append("Node test runner")

    return unique_preserve(frameworks)


def parse_package_dependencies(path: Path) -> List[str]:
    payload = load_json_file(path)
    names: List[str] = []
    for key in ("dependencies", "devDependencies"):
        deps = payload.get(key, {})
        if isinstance(deps, dict):
            names.extend(sorted(str(name) for name in deps.keys()))
    return limit_items(unique_preserve(names), 12)


def parse_requirements(path: Path) -> List[str]:
    if not path.exists():
        return []
    names: List[str] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            normalized = re.split(r"[<>=~!]", stripped, maxsplit=1)[0].strip()
            if normalized:
                names.append(normalized)
    except OSError:
        return []
    return limit_items(unique_preserve(names), 12)


def parse_pyproject_dependencies(path: Path) -> List[str]:
    if not path.exists() or tomllib is None:
        return []
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, TOML_ERROR):
        return []

    names: List[str] = []
    project = payload.get("project", {})
    if isinstance(project, dict):
        deps = project.get("dependencies", [])
        if isinstance(deps, list):
            for item in deps:
                if isinstance(item, str):
                    names.append(re.split(r"[<>=~! ]", item, maxsplit=1)[0].strip())

    poetry = payload.get("tool", {}).get("poetry", {}) if isinstance(payload.get("tool"), dict) else {}
    if isinstance(poetry, dict):
        deps = poetry.get("dependencies", {})
        if isinstance(deps, dict):
            for name in deps.keys():
                if name != "python":
                    names.append(str(name))

    return limit_items(unique_preserve(names), 12)


def detect_tech_stack(project_root: Path, inventory: Sequence[Dict[str, Any]]) -> List[str]:
    signals: List[str] = []
    suffix_counts = Counter(str(item["suffix"]) for item in inventory)
    if (project_root / "package.json").exists():
        signals.append("Node.js")
    if (project_root / "requirements.txt").exists() or (project_root / "pyproject.toml").exists():
        signals.append("Python")
    if (project_root / "Dockerfile").exists() or (project_root / "docker-compose.yml").exists():
        signals.append("Docker")
    if suffix_counts.get(".ts", 0) or suffix_counts.get(".tsx", 0):
        signals.append("TypeScript")
    if suffix_counts.get(".js", 0) or suffix_counts.get(".jsx", 0):
        signals.append("JavaScript")
    if suffix_counts.get(".py", 0):
        signals.append("Python")
    if suffix_counts.get(".vue", 0):
        signals.append("Vue")
    if suffix_counts.get(".tsx", 0) or suffix_counts.get(".jsx", 0):
        signals.append("React")
    if any("fastapi" in str(item["text"]).lower() for item in inventory if item.get("text")):
        signals.append("FastAPI")
    if any("express" in str(item["text"]).lower() for item in inventory if item.get("text")):
        signals.append("Express")
    return unique_preserve(signals)


def build_architecture_section(project_root: Path, inventory: Sequence[Dict[str, Any]], scan_depth: int) -> Dict[str, Any]:
    entry_points = sorted(
        item["rel_path"]
        for item in inventory
        if str(item["name"]) in ENTRY_POINT_CANDIDATES or str(item["rel_path"]).startswith("src/main.")
    )

    top_level_dirs: Dict[str, int] = defaultdict(int)
    for item in inventory:
        rel_path = str(item["rel_path"])
        top = rel_path.split("/", 1)[0] if "/" in rel_path else "."
        top_level_dirs[top] += 1

    module_boundaries = []
    for name, count in sorted(top_level_dirs.items(), key=lambda pair: (-pair[1], pair[0])):
        if name == ".":
            purpose = "root-level config and entry files"
        else:
            purpose = MODULE_PURPOSES.get(name.lower(), "application area")
        module_boundaries.append(f"{name} ({count} files): {purpose}")

    dependencies = unique_preserve(
        parse_package_dependencies(project_root / "package.json")
        + parse_requirements(project_root / "requirements.txt")
        + parse_requirements(project_root / "requirements-dev.txt")
        + parse_pyproject_dependencies(project_root / "pyproject.toml")
    )

    total_files = len(inventory)
    total_lines = sum(int(item.get("line_count", 0)) for item in inventory)
    return {
        "entry_points": entry_points or ["Not detected"],
        "module_boundaries": limit_items(module_boundaries, 12) or ["Not detected"],
        "key_dependencies": dependencies or ["Not detected"],
        "tech_stack": detect_tech_stack(project_root, inventory) or ["Not detected"],
        "scan_summary": {
            "max_depth": scan_depth,
            "total_files": total_files,
            "total_lines": total_lines,
        },
    }


def detect_routes(text: str) -> List[str]:
    routes: List[str] = []
    for pattern in ROUTE_PATTERNS:
        for match in pattern.finditer(text):
            if pattern.pattern.startswith("path"):
                path_value = match.group(1).strip()
                if re.fullmatch(r"""[/\w:<>.*-]*""", path_value):
                    routes.append(f"PATH {path_value or '/'}")
            else:
                path_value = match.group(3).strip()
                if "\n" in path_value or "," in path_value:
                    continue
                if re.fullmatch(r"""[/\w:<>.*-]+""", path_value):
                    routes.append(f"{match.group(2).upper()} {path_value}")
    return routes


def build_api_section(inventory: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    routes_found: List[str] = []
    middleware_summaries: List[str] = []
    middleware_groups: Dict[str, List[str]] = {}
    detailed_auth_patterns: List[str] = []
    generic_auth_patterns: List[str] = []

    for item in inventory:
        if not supports_pattern_scan(item):
            continue
        text = str(item.get("text", ""))
        if not text:
            continue

        rel_path = str(item["rel_path"])
        routes = detect_routes(text)
        if is_api_candidate(rel_path):
            for route in routes:
                routes_found.append(f"{route} ({rel_path})")

            middleware_chain = extract_middleware_chain(text, rel_path)
            if middleware_chain:
                middleware_groups[rel_path] = middleware_chain
                middleware_summaries.append(f"{rel_path}: {', '.join(middleware_chain)}")

        if is_auth_candidate(rel_path, text, routes) and not is_non_production_example_path(rel_path):
            detailed_auth_patterns.extend(detect_detailed_auth_patterns(text, rel_path, routes))
            if not detailed_auth_patterns:
                generic_auth_patterns.extend(detect_generic_auth_patterns(text))

    auth_patterns = unique_preserve(detailed_auth_patterns or generic_auth_patterns) or ["Not detected"]

    return {
        "routes": limit_items(unique_preserve(routes_found), 25) or ["Not detected"],
        "middleware_chain": limit_items(unique_preserve(middleware_summaries), 12) or ["Not detected"],
        "middleware_chain_groups": middleware_groups,
        "auth_patterns": auth_patterns,
    }


def build_data_section(project_root: Path, inventory: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    databases: List[str] = []
    models: List[str] = []
    migration_dirs: List[str] = []

    for item in inventory:
        if not supports_pattern_scan(item):
            continue
        text = str(item.get("text", ""))
        rel_path = str(item["rel_path"])
        lower_path = rel_path.lower()
        if not is_data_candidate(rel_path):
            continue

        for label, pattern in DB_PATTERNS.items():
            if text and pattern.search(text):
                databases.append(label)

        if any(pattern.search(text) for pattern in MODEL_PATTERNS) or "model" in lower_path or "schema" in lower_path:
            models.append(rel_path)

        path_parts = {part.lower() for part in Path(rel_path).parts}
        if MIGRATION_DIR_HINTS.intersection(path_parts):
            if "migration" in lower_path or "alembic" in lower_path or "prisma" in lower_path:
                parent = str(Path(rel_path).parent).replace("\\", "/")
                migration_dirs.append(parent or ".")

    return {
        "database_types": unique_preserve(databases) or ["Not detected"],
        "models_and_schemas": limit_items(sorted(unique_preserve(models)), 20) or ["Not detected"],
        "migration_status": sorted(unique_preserve(migration_dirs)) or ["Not detected"],
        "config_sources": [
            path.name
            for path in (
                project_root / "package.json",
                project_root / "requirements.txt",
                project_root / "pyproject.toml",
            )
            if path.exists()
        ] or ["Not detected"],
    }


def build_security_section(project_root: Path, inventory: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    env_files = sorted(
        item["rel_path"]
        for item in inventory
        if str(item["name"]).startswith(".env")
    )
    gitignore_path = project_root / ".gitignore"
    gitignore_text = safe_read_text(gitignore_path)
    env_ignored = any(
        line.strip() in {".env", ".env*", "**/.env", "**/.env*"}
        for line in gitignore_text.splitlines()
    )

    secret_risks: List[str] = []
    auth_middleware: List[str] = []
    cors_hits: List[str] = []
    rate_limits: List[str] = []
    https_enforcement: List[str] = []

    for item in inventory:
        if not supports_pattern_scan(item):
            continue
        text = str(item.get("text", ""))
        if not text:
            continue

        rel_path = str(item["rel_path"])
        if is_non_production_example_path(rel_path):
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            secret_risks.append(rel_path)
        if any(pattern.search(text) for pattern in AUTH_MIDDLEWARE_PATTERNS):
            auth_middleware.append(rel_path)
        if any(pattern.search(text) for pattern in CORS_PATTERNS):
            cors_hits.append(rel_path)
        if any(pattern.search(text) for pattern in RATE_LIMIT_PATTERNS):
            rate_limits.append(rel_path)
        if any(pattern.search(text) for pattern in HTTPS_PATTERNS):
            https_enforcement.append(rel_path)

    env_summary = "Not detected"
    if env_files:
        env_summary = f"Env files found: {', '.join(env_files[:5])}"
        env_summary += "; protected by .gitignore" if env_ignored else "; .gitignore protection not detected"
    elif env_ignored:
        env_summary = ".env patterns are ignored in .gitignore"

    return {
        "env_handling": [env_summary],
        "secret_exposure_risk": limit_items(sorted(unique_preserve(secret_risks)), 10) or ["Not detected"],
        "auth_middleware_present": sorted(unique_preserve(auth_middleware)) or ["Not detected"],
        "cors_configured": sorted(unique_preserve(cors_hits)) or ["Not detected"],
        "rate_limiting": sorted(unique_preserve(rate_limits)) or ["Not detected"],
        "https_enforcement": sorted(unique_preserve(https_enforcement)) or ["Not detected"],
    }


def normalize_test_stem(path: str) -> str:
    stem = Path(path).stem.lower()
    stem = re.sub(r"""(\.test|\.spec)$""", "", stem)
    stem = re.sub(r"""^test_""", "", stem)
    stem = re.sub(r"""_test$""", "", stem)
    return stem


def build_test_section(project_root: Path, inventory: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    test_dirs = sorted(
        unique_preserve(
            str(Path(item["rel_path"]).parent).replace("\\", "/")
            for item in inventory
            if TEST_DIR_NAMES.intersection({part.lower() for part in Path(str(item["rel_path"])).parts})
        )
    )

    frameworks: List[str] = detect_test_frameworks_from_package(project_root)
    test_stems: set[str] = set()
    source_candidates: List[str] = []

    for item in inventory:
        if not supports_pattern_scan(item):
            continue
        text = str(item.get("text", ""))
        rel_path = str(item["rel_path"])
        lower_path = rel_path.lower()

        for label, pattern in TEST_FRAMEWORK_PATTERNS.items():
            if text and pattern.search(text):
                frameworks.append(label)

        is_test_file = (
            any(part.lower() in TEST_DIR_NAMES for part in Path(rel_path).parts)
            or ".spec." in lower_path
            or ".test." in lower_path
            or Path(rel_path).name.startswith("test_")
            or Path(rel_path).stem.endswith("_test")
        )
        if is_test_file:
            test_stems.add(normalize_test_stem(rel_path))
        elif Path(rel_path).suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".py", ".go", ".java", ".rb", ".php"}:
            source_candidates.append(rel_path)

    missing_tests = [
        path
        for path in source_candidates
        if normalize_test_stem(path) not in test_stems and "migrations/" not in path and "/scripts/" not in path
    ]

    ci_pipelines = []
    for candidate in CI_FILES:
        if (project_root / candidate).exists():
            ci_pipelines.append(candidate)
    if (project_root / ".github" / "workflows").exists():
        workflows = sorted(path.relative_to(project_root).as_posix() for path in (project_root / ".github" / "workflows").glob("*.y*ml"))
        ci_pipelines.extend(workflows)

    return {
        "test_directories": test_dirs or ["Not detected"],
        "test_frameworks": unique_preserve(frameworks) or ["Not detected"],
        "files_without_tests": limit_items(missing_tests, 10) or ["Not detected"],
        "ci_pipeline": unique_preserve(ci_pipelines) or ["Not detected"],
    }


def build_directory_tree(project_root: Path, max_depth: int = 2) -> List[str]:
    lines: List[str] = []
    for root_str, dirs, _files in os.walk(project_root):
        root = Path(root_str)
        rel_root = root.relative_to(project_root)
        depth = len(rel_root.parts)
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        if depth > max_depth:
            dirs[:] = []
            continue
        if depth == 0:
            continue
        indent = "  " * (depth - 1)
        lines.append(f"{indent}- {rel_root.as_posix()}/")
        if depth >= max_depth:
            dirs[:] = []
    return lines[:30]


def build_file_map_section(project_root: Path, inventory: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    language_counts: Counter[str] = Counter()
    for item in inventory:
        label = LANGUAGE_NAMES.get(str(item["suffix"]))
        if label:
            language_counts[label] += 1

    largest_files = [
        f"{item['rel_path']} ({round(int(item['size']) / 1024, 1)} KB)"
        for item in sorted(inventory, key=lambda current: int(current["size"]), reverse=True)
    ]

    return {
        "directory_tree": build_directory_tree(project_root, max_depth=2) or ["Not detected"],
        "files_by_language": [
            f"{language}: {count}"
            for language, count in language_counts.most_common()
        ] or ["Not detected"],
        "largest_files": limit_items(largest_files, 10) or ["Not detected"],
    }


def render_section_lines(title: str, groups: Sequence[tuple[str, Sequence[str] | Dict[str, Any]]]) -> List[str]:
    lines = [title]
    for label, values in groups:
        lines.append(f"- {label}")
        if isinstance(values, dict):
            for key, value in values.items():
                lines.append(f"  - {key.replace('_', ' ').title()}: {value}")
            continue
        items = list(values)
        if not items:
            lines.append("  - Not detected")
            continue
        for item in items:
            lines.append(f"  - {item}")
    return lines


def render_markdown(project_root: Path, generated_at: str, sections: Dict[str, Dict[str, Any]]) -> str:
    lines = [
        f"# Project Genome: {project_root.name}",
        f"Generated: {generated_at}",
        "",
    ]

    visible_index = 1
    for section_name in SECTION_ORDER:
        section = sections.get(section_name)
        if not section:
            continue
        heading = f"## {visible_index}. {SECTION_TITLES[section_name]}"
        if section_name == "architecture":
            lines.extend(
                render_section_lines(
                    heading,
                    [
                        ("Entry points", section.get("entry_points", ["Not detected"])),
                        ("Module boundaries", section.get("module_boundaries", ["Not detected"])),
                        ("Key dependencies", section.get("key_dependencies", ["Not detected"])),
                        ("Tech stack detected", section.get("tech_stack", ["Not detected"])),
                        ("Scan summary", section.get("scan_summary", {})),
                    ],
                )
            )
        elif section_name == "api":
            lines.append(heading)
            lines.append("- Routes/endpoints found")
            for item in section.get("routes", ["Not detected"]):
                lines.append(f"  - {item}")
            middleware_groups = section.get("middleware_chain_groups", {})
            if isinstance(middleware_groups, dict) and middleware_groups:
                for file_path, middleware_items in middleware_groups.items():
                    lines.append(f"- Middleware chain ({file_path})")
                    for middleware_name in middleware_items:
                        lines.append(f"  - {middleware_name}")
            else:
                lines.append("- Middleware chain")
                for item in section.get("middleware_chain", ["Not detected"]):
                    lines.append(f"  - {item}")
            lines.append("- Auth patterns detected")
            for item in section.get("auth_patterns", ["Not detected"]):
                lines.append(f"  - {item}")
        elif section_name == "data":
            lines.extend(
                render_section_lines(
                    heading,
                    [
                        ("Database type", section.get("database_types", ["Not detected"])),
                        ("Models/schemas found", section.get("models_and_schemas", ["Not detected"])),
                        ("Migration status", section.get("migration_status", ["Not detected"])),
                        ("Config sources", section.get("config_sources", ["Not detected"])),
                    ],
                )
            )
        elif section_name == "security":
            lines.extend(
                render_section_lines(
                    heading,
                    [
                        (".env handling", section.get("env_handling", ["Not detected"])),
                        ("Secrets exposure risk", section.get("secret_exposure_risk", ["Not detected"])),
                        ("Auth middleware present", section.get("auth_middleware_present", ["Not detected"])),
                        ("CORS configured", section.get("cors_configured", ["Not detected"])),
                        ("Rate limiting", section.get("rate_limiting", ["Not detected"])),
                        ("HTTPS enforcement", section.get("https_enforcement", ["Not detected"])),
                    ],
                )
            )
        elif section_name == "tests":
            lines.extend(
                render_section_lines(
                    heading,
                    [
                        ("Test directories found", section.get("test_directories", ["Not detected"])),
                        ("Test frameworks detected", section.get("test_frameworks", ["Not detected"])),
                        ("Files without corresponding test files", section.get("files_without_tests", ["Not detected"])),
                        ("CI pipeline detected", section.get("ci_pipeline", ["Not detected"])),
                    ],
                )
            )
        elif section_name == "file_map":
            lines.extend(
                render_section_lines(
                    heading,
                    [
                        ("Directory tree (depth 2)", section.get("directory_tree", ["Not detected"])),
                        ("Total files by language", section.get("files_by_language", ["Not detected"])),
                        ("Largest files", section.get("largest_files", ["Not detected"])),
                    ],
                )
            )
        lines.append("")
        visible_index += 1

    return "\n".join(lines).rstrip() + "\n"


def build_sections(project_root: Path, inventory: Sequence[Dict[str, Any]], selected_sections: Sequence[str], scan_depth: int) -> Dict[str, Dict[str, Any]]:
    sections: Dict[str, Dict[str, Any]] = {}
    for section_name in selected_sections:
        if section_name == "architecture":
            sections[section_name] = build_architecture_section(project_root, inventory, scan_depth)
        elif section_name == "api":
            sections[section_name] = build_api_section(inventory)
        elif section_name == "data":
            sections[section_name] = build_data_section(project_root, inventory)
        elif section_name == "security":
            sections[section_name] = build_security_section(project_root, inventory)
        elif section_name == "tests":
            sections[section_name] = build_test_section(project_root, inventory)
        elif section_name == "file_map":
            sections[section_name] = build_file_map_section(project_root, inventory)
    return sections


def build_genome_report(project_root: Path, depth_mode: str, sections_value: str) -> Dict[str, Any]:
    scan_depth = detect_scan_depth(depth_mode)
    selected_sections = normalize_sections(sections_value)
    inventory = walk_inventory(project_root, max_depth=scan_depth)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    sections = build_sections(project_root, inventory, selected_sections, scan_depth)
    markdown = render_markdown(project_root, generated_at, sections)

    report: Dict[str, Any] = {
        "status": "ok",
        "project": project_root.name,
        "generated_at": generated_at,
        "depth": depth_mode,
        "scan_depth": scan_depth,
        "sections_scanned": selected_sections,
        "total_files": len(inventory),
        "total_lines": sum(int(item.get("line_count", 0)) for item in inventory),
        "module_maps_count": 0,
        "sections": sections,
        "markdown": markdown,
    }
    return report


def write_genome_file(project_root: Path, markdown: str) -> Path:
    context_dir = project_root / ".codex" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    genome_path = context_dir / "genome.md"
    genome_path.write_text(markdown, encoding="utf-8")
    return genome_path
