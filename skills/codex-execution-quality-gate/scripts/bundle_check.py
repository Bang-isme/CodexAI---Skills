#!/usr/bin/env python3
"""
Bundle and dependency health check.

Output contract:
{
  "package_manager": "npm|pip|cargo|none",
  "total_dependencies": 0,
  "large_packages": [{"name": "...", "size_estimate": "..."}],
  "warnings": ["..."],
  "status": "ok|warning|not_applicable"
}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


LARGE_NPM_PACKAGES = {
    "moment": "large date library; consider dayjs or date-fns",
    "lodash": "large utility library; prefer lodash-es or per-method imports",
    "aws-sdk": "large monolithic sdk; prefer modular v3 clients",
    "firebase": "modular imports recommended to reduce bundle size",
    "antd": "ui framework can increase bundle size significantly",
}

LARGE_PY_PACKAGES = {
    "tensorflow": "large ml dependency",
    "torch": "large ml dependency",
    "opencv-python": "large native package",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run dependency and bundle checks.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    return parser.parse_args()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}


def detect_package_manager(project_root: Path) -> str:
    if (project_root / "package.json").exists():
        return "npm"
    if (project_root / "Cargo.toml").exists():
        return "cargo"
    if (project_root / "requirements.txt").exists() or (project_root / "pyproject.toml").exists():
        return "pip"
    return "none"


def normalize_pkg_name(raw: str) -> str:
    return raw.strip().lower().replace("_", "-")


def parse_requirements(path: Path) -> List[str]:
    entries: List[str] = []
    if not path.exists():
        return entries
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-r "):
            continue
        name = re.split(r"[<>=!~\[]", stripped, maxsplit=1)[0].strip()
        if name:
            entries.append(normalize_pkg_name(name))
    return entries


def parse_cargo_dependencies(path: Path) -> List[str]:
    entries: List[str] = []
    if not path.exists():
        return entries
    in_dep_section = False
    section_pattern = re.compile(r"^\s*\[(.+)\]\s*$")
    dep_sections = {"dependencies", "dev-dependencies", "build-dependencies"}
    for line in read_text(path).splitlines():
        section_match = section_pattern.match(line)
        if section_match:
            in_dep_section = section_match.group(1).strip() in dep_sections
            continue
        if not in_dep_section:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name = stripped.split("=", 1)[0].strip()
        if name:
            entries.append(normalize_pkg_name(name))
    return entries


def detect_npm_section_conflicts(package_json: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    sections = ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]
    seen: Dict[str, Tuple[str, str]] = {}
    for section in sections:
        deps = package_json.get(section, {})
        if not isinstance(deps, dict):
            continue
        for name, version in deps.items():
            if not isinstance(version, str):
                continue
            normalized = normalize_pkg_name(name)
            if normalized in seen:
                prev_section, prev_version = seen[normalized]
                if prev_version != version:
                    warnings.append(
                        f"Direct dependency version mismatch for '{name}': "
                        f"{prev_section}={prev_version}, {section}={version}"
                    )
            else:
                seen[normalized] = (section, version)
    return warnings


def lock_key_to_package_name(lock_key: str) -> str:
    marker = "node_modules/"
    if marker not in lock_key:
        return ""
    tail = lock_key.split(marker)[-1]
    if not tail:
        return ""
    parts = tail.split("/")
    if parts[0].startswith("@") and len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def detect_npm_lock_duplicates(project_root: Path, direct_names: Set[str]) -> List[str]:
    lock_path = project_root / "package-lock.json"
    if not lock_path.exists():
        return []
    lock_data = read_json(lock_path)
    packages = lock_data.get("packages")
    if not isinstance(packages, dict):
        return []

    versions_by_name: Dict[str, Set[str]] = {}
    for key, value in packages.items():
        if not isinstance(value, dict):
            continue
        package_name = normalize_pkg_name(lock_key_to_package_name(str(key)))
        version = value.get("version")
        if not package_name or not isinstance(version, str):
            continue
        if package_name not in direct_names:
            continue
        versions_by_name.setdefault(package_name, set()).add(version)

    warnings: List[str] = []
    for package_name, versions in sorted(versions_by_name.items()):
        if len(versions) > 1:
            version_list = ", ".join(sorted(versions))
            warnings.append(f"Multiple lockfile versions for direct dependency '{package_name}': {version_list}")
    return warnings


def analyze_npm(project_root: Path) -> Dict[str, Any]:
    package_json = read_json(project_root / "package.json")
    warnings: List[str] = []
    large_packages: List[Dict[str, str]] = []

    sections = ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]
    direct_deps: Dict[str, str] = {}
    for section in sections:
        deps = package_json.get(section, {})
        if not isinstance(deps, dict):
            continue
        for name, version in deps.items():
            if isinstance(name, str) and isinstance(version, str):
                direct_deps[normalize_pkg_name(name)] = version

    total_dependencies = len(direct_deps)
    if total_dependencies > 200:
        warnings.append(f"High dependency count for npm project: {total_dependencies} (>200).")

    for package_name, suggestion in LARGE_NPM_PACKAGES.items():
        if package_name in direct_deps:
            large_packages.append({"name": package_name, "size_estimate": suggestion})

    lock_files = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb"]
    if not any((project_root / lock).exists() for lock in lock_files):
        warnings.append("No npm lock file detected (package-lock.json/yarn.lock/pnpm-lock.yaml/bun.lockb).")

    warnings.extend(detect_npm_section_conflicts(package_json))
    warnings.extend(detect_npm_lock_duplicates(project_root, set(direct_deps.keys())))

    status = "warning" if warnings else "ok"
    return {
        "package_manager": "npm",
        "total_dependencies": total_dependencies,
        "large_packages": large_packages,
        "warnings": warnings,
        "status": status,
    }


def analyze_pip(project_root: Path) -> Dict[str, Any]:
    warnings: List[str] = []
    large_packages: List[Dict[str, str]] = []

    req_entries = parse_requirements(project_root / "requirements.txt")
    pyproject_text = read_text(project_root / "pyproject.toml")

    names = list(req_entries)
    if not names and pyproject_text:
        for match in re.finditer(r"^\s*([A-Za-z0-9_.-]+)\s*[<>=!~]", pyproject_text, re.MULTILINE):
            names.append(normalize_pkg_name(match.group(1)))

    total_dependencies = len(set(names))
    for package_name, hint in LARGE_PY_PACKAGES.items():
        if package_name in names:
            large_packages.append({"name": package_name, "size_estimate": hint})

    if pyproject_text and not (project_root / "poetry.lock").exists() and not (project_root / "Pipfile.lock").exists():
        warnings.append("Python project has pyproject.toml but no poetry.lock or Pipfile.lock.")
    if not (project_root / "requirements.txt").exists() and not pyproject_text:
        warnings.append("No requirements.txt or dependency list found for Python project.")

    seen: Set[str] = set()
    duplicates: Set[str] = set()
    for name in names:
        if name in seen:
            duplicates.add(name)
        seen.add(name)
    for name in sorted(duplicates):
        warnings.append(f"Duplicate dependency entry detected: {name}")

    status = "warning" if warnings else "ok"
    return {
        "package_manager": "pip",
        "total_dependencies": total_dependencies,
        "large_packages": large_packages,
        "warnings": warnings,
        "status": status,
    }


def analyze_cargo(project_root: Path) -> Dict[str, Any]:
    warnings: List[str] = []
    entries = parse_cargo_dependencies(project_root / "Cargo.toml")
    total_dependencies = len(set(entries))

    if not (project_root / "Cargo.lock").exists():
        warnings.append("Cargo.lock not found.")

    status = "warning" if warnings else "ok"
    return {
        "package_manager": "cargo",
        "total_dependencies": total_dependencies,
        "large_packages": [],
        "warnings": warnings,
        "status": status,
    }


def analyze(project_root: Path) -> Dict[str, Any]:
    if not project_root.exists() or not project_root.is_dir():
        return {
            "package_manager": "none",
            "total_dependencies": 0,
            "large_packages": [],
            "warnings": [f"Project root does not exist or is not a directory: {project_root}"],
            "status": "warning",
        }

    manager = detect_package_manager(project_root)
    if manager == "npm":
        return analyze_npm(project_root)
    if manager == "pip":
        return analyze_pip(project_root)
    if manager == "cargo":
        return analyze_cargo(project_root)
    return {
        "package_manager": "none",
        "total_dependencies": 0,
        "large_packages": [],
        "warnings": ["No supported package manager manifest detected."],
        "status": "not_applicable",
    }


def main() -> int:
    args = parse_args()
    report = analyze(Path(args.project_root).resolve())
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
