"""Discovery helpers for Python unittest and Node's built-in test runner."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import List


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
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "coverage",
    "target",
}
NODE_TEST_EXTS = {".js", ".cjs", ".mjs"}
UNITTEST_PATTERN = re.compile(
    r"(?m)^\s*(?:import\s+unittest(?:\s*(?:#.*)?$)|from\s+unittest\s+import\b)|"
    r"\bunittest\.TestCase\b|\bunittest\.main\s*\("
)
PYTEST_PATTERN = re.compile(r"(?m)^\s*(?:import\s+pytest\b|from\s+pytest\s+import\b)")


def _iter_files(project_root: Path):
    for current, dirs, files in os.walk(project_root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        root = Path(current)
        for name in files:
            yield root / name


def _has_test_name(path: Path, extensions: set[str]) -> bool:
    if path.suffix.lower() not in extensions:
        return False
    name = path.name.lower()
    return (
        name.startswith("test_")
        or name.startswith("test-")
        or "_test." in name
        or ".test." in name
        or ".spec." in name
        or path.parent.name.lower() in {"test", "tests", "__tests__"}
    )


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def package_test_script(project_root: Path) -> str:
    package_json = project_root / "package.json"
    try:
        package = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
    value = scripts.get("test", "") if isinstance(scripts, dict) else ""
    return value.lower() if isinstance(value, str) else ""


def discover_node_test_files(project_root: Path) -> List[str]:
    explicit_node_test_script = bool(re.search(r"\bnode\s+--test\b", package_test_script(project_root)))
    tests: List[str] = []
    for path in _iter_files(project_root):
        if path.suffix.lower() not in NODE_TEST_EXTS or not _has_test_name(path, NODE_TEST_EXTS):
            continue
        content = _read(path)
        if explicit_node_test_script or "node:test" in content:
            tests.append(path.resolve().relative_to(project_root.resolve()).as_posix())
    return sorted(dict.fromkeys(tests))


def has_node_test_runner(project_root: Path) -> bool:
    script = package_test_script(project_root)
    return bool(re.search(r"\bnode\s+--test\b", script)) or bool(discover_node_test_files(project_root))


def discover_unittest_test_files(project_root: Path) -> List[str]:
    tests: List[str] = []
    for path in _iter_files(project_root):
        if path.suffix.lower() != ".py" or not _has_test_name(path, {".py"}):
            continue
        content = _read(path)
        if UNITTEST_PATTERN.search(content) and not PYTEST_PATTERN.search(content):
            tests.append(path.resolve().relative_to(project_root.resolve()).as_posix())
    return sorted(dict.fromkeys(tests))


def has_pytest_tests(project_root: Path) -> bool:
    for path in _iter_files(project_root):
        if path.suffix.lower() == ".py" and _has_test_name(path, {".py"}) and PYTEST_PATTERN.search(_read(path)):
            return True
    return False
