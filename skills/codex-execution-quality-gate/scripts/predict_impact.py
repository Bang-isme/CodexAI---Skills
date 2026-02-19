#!/usr/bin/env python3
"""
Predict blast radius for planned file edits.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Optional, Sequence, Set, Tuple


SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".next"}
SCAN_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".py"}
RESOLVE_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".json"]
TEST_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".py"}

IMPORT_FROM_PATTERN = re.compile(r"^\s*import\s+.+?\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
IMPORT_SIDE_PATTERN = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
REQUIRE_PATTERN = re.compile(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)")
PY_IMPORT_PATTERN = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)", re.MULTILINE)
PY_FROM_IMPORT_PATTERN = re.compile(r"^\s*from\s+([A-Za-z_][\w.]*|\.+[\w.]*)\s+import\s+", re.MULTILINE)

ENTRYPOINT_HINTS = {
    "src/index.js",
    "src/index.ts",
    "src/main.js",
    "src/main.ts",
    "index.js",
    "index.ts",
    "main.py",
    "app.py",
    "server.js",
    "server.ts",
}
CONFIG_FILE_NAMES = {
    "package.json",
    "tsconfig.json",
    "pyproject.toml",
    "requirements.txt",
    ".env",
    ".env.local",
    "vite.config.js",
    "vite.config.ts",
    "webpack.config.js",
    "next.config.js",
    "next.config.mjs",
}
LEVEL_SCORE = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Predict impact of file changes.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python predict_impact.py --project-root <path> --files <file1,file2>\n"

            "  python predict_impact.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--files", required=True, help="Comma-separated files planned to change")
    parser.add_argument("--depth", type=int, default=2, help="Dependent traversal depth")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def normalize_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def parse_files_arg(raw: str) -> List[str]:
    return sorted(dict.fromkeys(item.strip().replace("\\", "/") for item in raw.split(",") if item.strip()))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def collect_files(project_root: Path) -> List[Path]:
    files: List[Path] = []
    for current_root, dirs, names in os.walk(project_root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        root_path = Path(current_root)
        for name in names:
            path = root_path / name
            if path.suffix.lower() in SCAN_EXTENSIONS or path.suffix.lower() == ".json":
                files.append(path)
    return sorted(files)


def is_test_file(rel_path: str) -> bool:
    path = Path(rel_path)
    if path.suffix.lower() not in TEST_EXTENSIONS:
        return False
    text = rel_path.lower()
    name = path.name.lower()
    return (
        ".test." in name
        or ".spec." in name
        or "/tests/" in text
        or "/__tests__/" in text
        or name.startswith("test_")
    )


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
    module = module.strip()
    if not module or module.startswith(("http://", "https://", "node:")):
        return None

    base: Optional[Path] = None
    if module.startswith("."):
        base = (importer.parent / module)
    elif module.startswith("/"):
        base = (root / module.lstrip("/"))
    elif module.startswith("@/"):
        base = (root / module[2:])
    elif module.startswith("src/"):
        base = (root / module)
    else:
        return None

    return choose_existing(expand_candidates(base), root, existing)


def resolve_python_module(importer: Path, module: str, root: Path, existing: Set[Path]) -> Optional[Path]:
    module = module.strip()
    if not module:
        return None

    candidates: List[Path] = []
    if module.startswith("."):
        level = len(module) - len(module.lstrip("."))
        suffix = module[level:]
        base = importer.parent
        for _ in range(max(level - 1, 0)):
            base = base.parent
        if suffix:
            target = base / Path(suffix.replace(".", "/"))
            candidates.extend([target.with_suffix(".py"), target / "__init__.py"])
        else:
            candidates.append(base / "__init__.py")
    else:
        target = root / Path(module.replace(".", "/"))
        candidates.extend([target.with_suffix(".py"), target / "__init__.py"])

    return choose_existing(candidates, root, existing)


def parse_imports(path: Path, content: str) -> List[str]:
    ext = path.suffix.lower()
    modules: List[str] = []
    if ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        modules.extend(IMPORT_FROM_PATTERN.findall(content))
        modules.extend(IMPORT_SIDE_PATTERN.findall(content))
        modules.extend(REQUIRE_PATTERN.findall(content))
    elif ext == ".py":
        modules.extend(PY_IMPORT_PATTERN.findall(content))
        modules.extend(PY_FROM_IMPORT_PATTERN.findall(content))
    return modules


def build_dependency_maps(project_root: Path) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Set[str], List[str]]:
    files = collect_files(project_root)
    existing = {path.resolve() for path in files}
    scan_files = [path for path in files if path.suffix.lower() in SCAN_EXTENSIONS]
    rel_files = {normalize_rel(path, project_root) for path in files}

    forward: Dict[str, Set[str]] = defaultdict(set)
    reverse: Dict[str, Set[str]] = defaultdict(set)
    warnings: List[str] = []

    for importer in scan_files:
        importer_rel = normalize_rel(importer, project_root)
        content = read_text(importer)
        if not content:
            continue

        for module in parse_imports(importer, content):
            if importer.suffix.lower() == ".py":
                resolved = resolve_python_module(importer, module, project_root, existing)
            else:
                resolved = resolve_js_module(importer, module, project_root, existing)
            if not resolved:
                continue
            target_rel = normalize_rel(resolved, project_root)
            if target_rel == importer_rel:
                continue
            forward[importer_rel].add(target_rel)
            reverse[target_rel].add(importer_rel)

    return forward, reverse, rel_files, warnings


def resolve_target(raw: str, project_root: Path, existing_rel: Set[str]) -> Tuple[Optional[str], Optional[str]]:
    raw_norm = raw.strip().replace("\\", "/")
    if not raw_norm:
        return None, None

    path = Path(raw_norm)
    if path.is_absolute():
        abs_path = path.resolve()
    else:
        abs_path = (project_root / path).resolve()

    if abs_path.exists() and abs_path.is_file() and inside_root(abs_path, project_root):
        rel = normalize_rel(abs_path, project_root)
        return rel, None

    if raw_norm in existing_rel:
        return raw_norm, None

    base = abs_path if path.is_absolute() else (project_root / raw_norm)
    existing_abs = {(project_root / rel).resolve() for rel in existing_rel}
    resolved = choose_existing(expand_candidates(base), project_root, existing_abs)
    if resolved:
        return normalize_rel(resolved, project_root), None

    return raw_norm, f"Target file not found in project: {raw_norm}"


def dependent_levels(target: str, reverse: Dict[str, Set[str]], depth: int) -> Tuple[Set[str], Set[str]]:
    direct: Set[str] = set()
    indirect: Set[str] = set()
    visited: Set[str] = {target}
    queue: Deque[Tuple[str, int]] = deque([(target, 0)])

    while queue:
        current, level = queue.popleft()
        if level >= depth:
            continue
        next_level = level + 1
        for dependent in reverse.get(current, set()):
            if dependent in visited:
                continue
            visited.add(dependent)
            if next_level == 1:
                direct.add(dependent)
            else:
                indirect.add(dependent)
            queue.append((dependent, next_level))

    return direct, indirect


def is_entry_or_config(rel_file: str) -> bool:
    lower = rel_file.lower()
    name = Path(rel_file).name.lower()
    return (
        lower in ENTRYPOINT_HINTS
        or name in CONFIG_FILE_NAMES
        or "/config/" in lower
        or lower.startswith("config/")
        or lower.endswith(".config.js")
        or lower.endswith(".config.ts")
    )


def classify_level(direct_count: int, critical_signal: bool) -> str:
    if critical_signal or direct_count > 10:
        return "critical"
    if direct_count >= 5:
        return "high"
    if direct_count >= 2:
        return "medium"
    return "low"


def collect_tests(project_root: Path) -> List[str]:
    tests: List[str] = []
    for current_root, dirs, names in os.walk(project_root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        root_path = Path(current_root)
        for name in names:
            rel = normalize_rel(root_path / name, project_root)
            if is_test_file(rel):
                tests.append(rel)
    return sorted(dict.fromkeys(tests))


def find_affected_tests(project_root: Path, changed_files: List[str], all_tests: List[str]) -> List[str]:
    selected: Set[str] = set()
    test_paths = [Path(item) for item in all_tests]
    test_contents: Dict[str, str] = {}

    for test in all_tests:
        test_contents[test] = read_text(project_root / test)

    for changed in changed_files:
        changed_path = Path(changed)
        stem = changed_path.stem
        base = stem.split(".")[0]
        tokens = {stem.lower(), base.lower(), changed_path.with_suffix("").as_posix().lower()}
        found_any = False

        for test in all_tests:
            test_name = Path(test).name.lower()
            if any(token and token in test_name for token in tokens):
                selected.add(test)
                found_any = True

        for test, content in test_contents.items():
            lowered = content.lower()
            if any(token and token in lowered for token in tokens):
                selected.add(test)
                found_any = True

        if not found_any:
            parent = changed_path.parent
            for test_path in test_paths:
                if test_path.parent == parent:
                    selected.add(test_path.as_posix())
                elif test_path.parent.name == "__tests__" and test_path.parent.parent == parent:
                    selected.add(test_path.as_posix())

    return sorted(selected)


def build_recommendations(
    targets: List[str],
    dependency_tree: Dict[str, Dict[str, List[str]]],
    affected_tests: List[str],
    impact_level: str,
) -> List[str]:
    recommendations: List[str] = []

    for target in targets:
        direct_count = len(dependency_tree.get(target, {}).get("direct", []))
        if direct_count > 0:
            recommendations.append(
                f"{direct_count} direct dependents for `{target}`; review dependent call sites before editing."
            )
        else:
            recommendations.append(f"No direct dependents found for `{target}`; change risk appears localized.")

    if affected_tests:
        recommendations.append(f"Run affected tests: {len(affected_tests)} test files identified.")
    else:
        recommendations.append("No related tests were matched; consider running broader integration tests.")

    if any(token in target.lower() for target in targets for token in ["/models/", "model", "schema", "interface"]):
        recommendations.append("Consider whether this change affects API response shape or validation contracts.")

    if impact_level in {"high", "critical"}:
        recommendations.append("High blast radius detected; stage the change behind focused regression verification.")

    return recommendations[:6]


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    depth = max(1, int(args.depth))

    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    requested_files = parse_files_arg(args.files)
    if not requested_files:
        emit({"status": "error", "message": "No target files provided in --files."})
        return 1

    forward, reverse, existing_rel_files, warnings = build_dependency_maps(project_root)

    resolved_targets: List[str] = []
    for raw in requested_files:
        resolved, warn = resolve_target(raw, project_root, existing_rel_files)
        if resolved:
            resolved_targets.append(resolved)
        if warn:
            warnings.append(warn)
    resolved_targets = sorted(dict.fromkeys(resolved_targets))

    dependency_tree: Dict[str, Dict[str, List[str]]] = {}
    all_direct: Set[str] = set()
    all_indirect: Set[str] = set()
    critical_signals = False
    target_levels: List[str] = []

    for target in resolved_targets:
        direct, indirect = dependent_levels(target, reverse, depth)
        direct_sorted = sorted(direct)
        indirect_sorted = sorted(indirect)
        dependency_tree[target] = {"direct": direct_sorted, "indirect": indirect_sorted}
        all_direct.update(direct_sorted)
        all_indirect.update(indirect_sorted)
        signal = is_entry_or_config(target)
        if signal:
            critical_signals = True
        target_levels.append(classify_level(len(direct_sorted), signal))

    if not resolved_targets:
        impact_level = "low"
    else:
        impact_level = max(target_levels or ["low"], key=lambda level: LEVEL_SCORE.get(level, 0))
        if critical_signals:
            impact_level = "critical"
        elif classify_level(len(all_direct), False) in {"high", "critical"} and impact_level in {"low", "medium"}:
            impact_level = "high"

    impact_scope = sorted(set(resolved_targets) | all_direct)
    tests = collect_tests(project_root)
    affected_tests = find_affected_tests(project_root, impact_scope, tests)

    payload: Dict[str, object] = {
        "status": "predicted",
        "targets": resolved_targets,
        "impact_summary": {
            "level": impact_level,
            "direct_dependents": len(all_direct),
            "indirect_dependents": len(all_indirect),
            "total_blast_radius": len(all_direct | all_indirect),
        },
        "dependency_tree": dependency_tree,
        "affected_tests": affected_tests,
        "recommendations": build_recommendations(resolved_targets, dependency_tree, affected_tests, impact_level),
    }
    if warnings:
        payload["warnings"] = sorted(dict.fromkeys(warnings))

    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
