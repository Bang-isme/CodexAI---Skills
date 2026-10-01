#!/usr/bin/env python3
"""Validate the checked-in Cursor plugin and GitHub marketplace manifests."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")


def default_plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def add(checks: list[dict[str, str]], name: str, status: str, detail: str) -> None:
    checks.append({"name": name, "status": status, "detail": detail})


def safe_path(root: Path, value: str) -> Path:
    normalized = value.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if not normalized or normalized.startswith("/") or PureWindowsPath(normalized).drive or ".." in parts:
        raise ValueError(f"path must stay inside plugin root: {value}")
    resolved = (root / Path(normalized)).resolve()
    if resolved != root.resolve() and root.resolve() not in resolved.parents:
        raise ValueError(f"path escapes plugin root: {value}")
    return resolved


def validate(plugin_root: Path) -> dict[str, Any]:
    root = plugin_root.expanduser().resolve()
    checks: list[dict[str, str]] = []
    try:
        manifest_path = root / ".cursor-plugin" / "plugin.json"
        manifest = read_json(manifest_path)
        add(checks, "cursor_manifest", "pass", str(manifest_path))
    except Exception as exc:
        add(checks, "cursor_manifest", "fail", str(exc))
        manifest = {}

    plugin_name = str(manifest.get("name", ""))
    add(checks, "cursor_plugin_name", "pass" if NAME_RE.fullmatch(plugin_name) else "fail", plugin_name or "missing")
    skills_version_path = root / "skills" / "VERSION"
    skills_version = skills_version_path.read_text(encoding="utf-8").strip() if skills_version_path.exists() else ""
    manifest_version = str(manifest.get("version", ""))
    add(
        checks,
        "cursor_plugin_version",
        "pass" if skills_version and manifest_version == skills_version else "fail",
        f"plugin={manifest_version}, skills={skills_version}",
    )

    skills_value = manifest.get("skills", "./skills/")
    skill_paths = skills_value if isinstance(skills_value, list) else [skills_value]
    skill_dirs: list[Path] = []
    try:
        for value in skill_paths:
            skill_dirs.append(safe_path(root, str(value)))
        has_skills = any(path.is_dir() and any(path.rglob("SKILL.md")) for path in skill_dirs)
        add(checks, "cursor_skills", "pass" if has_skills else "fail", ", ".join(str(path) for path in skill_dirs))
    except Exception as exc:
        add(checks, "cursor_skills", "fail", str(exc))

    rules_value = manifest.get("rules", "")
    rule_paths = rules_value if isinstance(rules_value, list) else [rules_value]
    try:
        resolved_rules = [safe_path(root, str(value)) for value in rule_paths if value]
        missing_rules = [str(path) for path in resolved_rules if not path.is_file()]
        add(checks, "cursor_rules", "pass" if resolved_rules and not missing_rules else "fail", ", ".join(missing_rules or [str(path) for path in resolved_rules]))
    except Exception as exc:
        add(checks, "cursor_rules", "fail", str(exc))

    try:
        marketplace_path = root / ".cursor-plugin" / "marketplace.json"
        marketplace = read_json(marketplace_path)
        entries = marketplace.get("plugins")
        match = next(
            (item for item in entries if isinstance(item, dict) and item.get("name") == plugin_name),
            None,
        ) if isinstance(entries, list) else None
        if not isinstance(marketplace.get("owner"), dict) or not marketplace["owner"].get("name"):
            raise ValueError("marketplace owner.name is required")
        if not NAME_RE.fullmatch(str(marketplace.get("name", ""))):
            raise ValueError("marketplace name is missing or invalid")
        if not match:
            raise ValueError(f"marketplace entry for {plugin_name or 'plugin'} is missing")
        entry_root = safe_path(root, str(match.get("source", "")))
        if entry_root != root:
            raise ValueError("single-plugin marketplace source must resolve to repository root")
        if str(match.get("version", "")) != manifest_version:
            raise ValueError("marketplace and plugin manifest versions differ")
        add(checks, "cursor_marketplace", "pass", str(marketplace_path))
    except Exception as exc:
        add(checks, "cursor_marketplace", "fail", str(exc))

    failed = [item for item in checks if item["status"] == "fail"]
    return {"status": "fail" if failed else "pass", "total": len(checks), "failed": len(failed), "checks": checks}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Cursor plugin and marketplace manifests.")
    parser.add_argument("--plugin-root", default="", help="Plugin repository root; defaults to this pack.")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = validate(Path(args.plugin_root) if args.plugin_root else default_plugin_root())
    if args.format == "text":
        print(f"Status: {payload['status']}")
        for item in payload["checks"]:
            print(f"- {item['status'].upper()}: {item['name']} -- {item['detail']}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
