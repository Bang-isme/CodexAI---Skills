#!/usr/bin/env python3
"""Build a clean CodexAI release ZIP without repository/runtime artifacts."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any


EXCLUDED_DIR_NAMES = {
    ".git",
    ".codex",
    ".analytics",
    ".codexai-backups",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "htmlcov",
    "dist",
    "build",
    "cache",
    "state",
}
EXCLUDED_FILE_NAMES = {
    ".coverage",
    ".codex-system-skills.marker",
}
EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".tmp",
    ".bak",
}
DEFAULT_ALLOWED_TOP_LEVEL = {
    ".agents",
    ".claude-plugin",
    ".codex-plugin",
    ".coveragerc",
    "docs",
    "hooks",
    "skills",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "LICENSE",
    "README.md",
}


def default_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_output(project_root: Path) -> Path:
    version_path = project_root / "skills" / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else "dev"
    return project_root / "dist" / f"CodexAI---Skills-{version}.zip"


def rel_posix(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def is_excluded(relative_path: str) -> bool:
    parts = relative_path.split("/")
    if any(part in EXCLUDED_DIR_NAMES for part in parts[:-1]):
        return True
    name = parts[-1]
    if name in EXCLUDED_DIR_NAMES or name in EXCLUDED_FILE_NAMES:
        return True
    return any(name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)


def iter_release_files(project_root: Path, include_tests: bool = True) -> list[Path]:
    files: list[Path] = []
    for item in sorted(project_root.rglob("*"), key=lambda p: p.as_posix().lower()):
        if not item.is_file():
            continue
        rel = rel_posix(project_root, item)
        top_level = rel.split("/", 1)[0]
        if top_level not in DEFAULT_ALLOWED_TOP_LEVEL:
            continue
        if not include_tests and (rel == "skills/tests" or rel.startswith("skills/tests/")):
            continue
        if is_excluded(rel):
            continue
        files.append(item)
    return files


def build_zip(project_root: Path, output_path: Path, include_tests: bool, dry_run: bool) -> dict[str, Any]:
    if not project_root.exists() or not project_root.is_dir():
        raise FileNotFoundError(f"Project root does not exist or is not a directory: {project_root}")

    files = iter_release_files(project_root, include_tests=include_tests)
    entries = [rel_posix(project_root, path) for path in files]
    payload: dict[str, Any] = {
        "status": "dry_run" if dry_run else "generated",
        "project_root": str(project_root),
        "output": str(output_path),
        "entries": len(entries),
        "include_tests": include_tests,
        "excluded_policy": {
            "directories": sorted(EXCLUDED_DIR_NAMES),
            "suffixes": sorted(EXCLUDED_SUFFIXES),
        },
        "sample_entries": entries[:20],
    }
    if dry_run:
        return payload

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, entry in zip(files, entries):
            archive.write(path, entry)
    payload["size_bytes"] = output_path.stat().st_size
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a clean CodexAI release ZIP.")
    parser.add_argument("--project-root", default="", help="Plugin repo root. Defaults to this script's repo root.")
    parser.add_argument("--output", default="", help="Output ZIP path. Defaults to dist/CodexAI---Skills-<version>.zip")
    parser.add_argument("--include-tests", action="store_true", help="Include skills/tests in the release ZIP.")
    parser.add_argument("--exclude-tests", action="store_true", help="Exclude skills/tests from the release ZIP.")
    parser.add_argument("--apply", action="store_true", help="Actually write the ZIP. Default is dry-run.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only. This is the default.")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_root = Path(args.project_root).expanduser().resolve() if args.project_root else default_project_root()
        output_path = Path(args.output).expanduser().resolve() if args.output else default_output(project_root)
        dry_run = not args.apply or args.dry_run
        include_tests = not args.exclude_tests
        if args.include_tests:
            include_tests = True
        payload = build_zip(project_root, output_path, include_tests=include_tests, dry_run=dry_run)
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    if args.format == "text":
        print(f"{payload['status']}: entries={payload['entries']} output={payload['output']}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
