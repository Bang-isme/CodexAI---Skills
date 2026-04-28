#!/usr/bin/env python3
"""Validate Codex-native plugin packaging, marketplace, and skill metadata."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
ALLOWED_INSTALLATION = {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"}
ALLOWED_AUTHENTICATION = {"ON_INSTALL", "ON_USE"}


def default_plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def add(checks: list[dict[str, Any]], name: str, status: str, detail: str, **extra: Any) -> None:
    item: dict[str, Any] = {"name": name, "status": status, "detail": detail}
    item.update(extra)
    checks.append(item)


def resolve_plugin_path(plugin_root: Path, value: str) -> Path:
    if not value.startswith("./"):
        raise ValueError(f"path must start with ./: {value}")
    resolved = (plugin_root / value[2:]).resolve()
    root = plugin_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path escapes plugin root: {value}")
    return resolved


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = read_text(path)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip("'\"")
    return data


def check_plugin_manifest(plugin_root: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    plugin_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not plugin_path.exists():
        add(checks, "plugin_manifest_exists", "fail", str(plugin_path))
        return {}
    try:
        manifest = read_json(plugin_path)
    except Exception as exc:
        add(checks, "plugin_manifest_json", "fail", f"invalid JSON: {exc}")
        return {}

    add(checks, "plugin_manifest_exists", "pass", str(plugin_path))
    name = str(manifest.get("name", ""))
    add(checks, "plugin_name", "pass" if PLUGIN_NAME_RE.match(name) else "fail", name or "missing")

    skills_path_value = str(manifest.get("skills", ""))
    try:
        skills_path = resolve_plugin_path(plugin_root, skills_path_value)
        inside_manifest_dir = ".codex-plugin" in skills_path.relative_to(plugin_root).parts
        status = "pass" if skills_path.exists() and not inside_manifest_dir else "fail"
        add(checks, "plugin_skills_path", status, f"{skills_path_value} -> {skills_path}")
    except Exception as exc:
        add(checks, "plugin_skills_path", "fail", str(exc))

    version_path = plugin_root / "skills" / "VERSION"
    source_version = read_text(version_path).strip() if version_path.exists() else ""
    plugin_version = str(manifest.get("version", ""))
    add(
        checks,
        "plugin_version",
        "pass" if source_version and plugin_version == source_version else "fail",
        f"plugin={plugin_version}, skills={source_version}",
    )

    interface = manifest.get("interface", {})
    required_interface = {"displayName", "shortDescription", "longDescription", "developerName", "category", "capabilities"}
    missing_interface = sorted(required_interface - set(interface)) if isinstance(interface, dict) else sorted(required_interface)
    add(
        checks,
        "plugin_interface",
        "pass" if not missing_interface else "fail",
        "interface metadata present" if not missing_interface else ", ".join(missing_interface),
        missing=missing_interface,
    )
    return manifest


def check_marketplace(plugin_root: Path, plugin_name: str, checks: list[dict[str, Any]]) -> None:
    marketplace_path = plugin_root / ".agents" / "plugins" / "marketplace.json"
    if not marketplace_path.exists():
        add(checks, "marketplace_exists", "fail", str(marketplace_path))
        return
    try:
        marketplace = read_json(marketplace_path)
    except Exception as exc:
        add(checks, "marketplace_json", "fail", f"invalid JSON: {exc}")
        return
    add(checks, "marketplace_exists", "pass", str(marketplace_path))

    plugins = marketplace.get("plugins", [])
    matching = [item for item in plugins if isinstance(item, dict) and item.get("name") == plugin_name]
    if not matching:
        add(checks, "marketplace_entry", "fail", f"{plugin_name} not listed")
        return
    entry = matching[0]
    failures: list[str] = []
    source = entry.get("source", {})
    source_path = str(source.get("path", "")) if isinstance(source, dict) else ""
    if not isinstance(source, dict) or source.get("source") != "local":
        failures.append("source.source must be local")
    try:
        resolve_plugin_path(plugin_root, source_path)
    except Exception as exc:
        failures.append(str(exc))
    policy = entry.get("policy", {})
    if not isinstance(policy, dict):
        failures.append("policy must be an object")
    else:
        if policy.get("installation") not in ALLOWED_INSTALLATION:
            failures.append("policy.installation invalid")
        if policy.get("authentication") not in ALLOWED_AUTHENTICATION:
            failures.append("policy.authentication invalid")
    if not entry.get("category"):
        failures.append("category missing")
    add(
        checks,
        "marketplace_entry",
        "pass" if not failures else "fail",
        "marketplace entry valid" if not failures else "; ".join(failures),
        failures=failures,
    )


def check_skill_metadata(skills_root: Path, checks: list[dict[str, Any]]) -> None:
    failures: list[str] = []
    warnings: list[str] = []
    total = 0
    for skill_md in sorted(skills_root.glob("*/SKILL.md")):
        if skill_md.parent.name.startswith("."):
            continue
        total += 1
        frontmatter = parse_frontmatter(skill_md)
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if not name:
            failures.append(f"{skill_md.parent.name}: missing name")
        if not description:
            failures.append(f"{skill_md.parent.name}: missing description")
            continue
        lowered = description.lower()
        if not (lowered.startswith("use ") or lowered.startswith("use when") or lowered.startswith("use for")):
            warnings.append(f"{skill_md.parent.name}: description should front-load Use/Use when trigger")
        if len(description) > 280:
            warnings.append(f"{skill_md.parent.name}: description longer than 280 chars")
    add(
        checks,
        "skill_metadata",
        "pass" if not failures else "fail",
        f"{total} skill metadata file(s) checked" if not failures else "; ".join(failures[:5]),
        failures=failures,
        warnings=warnings,
        warnings_count=len(warnings),
        total=total,
    )


def check_native_agents(agent_root: Path, checks: list[dict[str, Any]]) -> None:
    if not agent_root.exists():
        add(checks, "native_agents", "pass", f"native agent root absent: {agent_root}")
        return
    try:
        import tomllib
    except ModuleNotFoundError:
        add(checks, "native_agents", "warn", "tomllib unavailable; skipped TOML validation")
        return
    unsupported: list[str] = []
    for path in sorted(agent_root.glob("*.toml")):
        try:
            payload = tomllib.loads(read_text(path))
        except Exception as exc:
            unsupported.append(f"{path.name}: invalid TOML ({exc})")
            continue
        if "prompt" in payload:
            unsupported.append(f"{path.name}: unsupported field prompt")
        if not payload.get("developer_instructions"):
            unsupported.append(f"{path.name}: missing developer_instructions")
    add(
        checks,
        "native_agents",
        "pass" if not unsupported else "fail",
        "native agent TOML files valid" if not unsupported else "; ".join(unsupported[:5]),
        failures=unsupported,
    )


def summarize(checks: list[dict[str, Any]], strict: bool = False) -> dict[str, Any]:
    failed = [item for item in checks if item["status"] == "fail"]
    warned = [item for item in checks if item["status"] == "warn" or item.get("warnings_count", 0)]
    status = "fail" if failed else ("warn" if warned else "pass")
    if strict and warned and not failed:
        status = "fail"
    return {
        "status": status,
        "total": len(checks),
        "failed": len(failed),
        "warnings": len(warned),
        "checks": checks,
    }


def validate(plugin_root: Path, strict: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    root = plugin_root.expanduser().resolve()
    add(checks, "plugin_root", "pass" if root.is_dir() else "fail", str(root))
    if not root.is_dir():
        return summarize(checks, strict)
    manifest = check_plugin_manifest(root, checks)
    plugin_name = str(manifest.get("name", "")) if manifest else ""
    if plugin_name:
        check_marketplace(root, plugin_name, checks)
    check_skill_metadata(root / "skills", checks)
    check_native_agents(root / ".codex" / "agents", checks)
    return summarize(checks, strict)


def render_text(payload: dict[str, Any]) -> str:
    lines = [f"Status: {payload['status']}", f"Checks: {payload['total']} total, {payload['failed']} failed, {payload['warnings']} warning groups", ""]
    for item in payload["checks"]:
        lines.append(f"- {item['status'].upper()}: {item['name']} -- {item['detail']}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate CodexAI native plugin packaging.")
    parser.add_argument("--plugin-root", default="", help="Plugin root. Defaults to repository root.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failure.")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.plugin_root) if args.plugin_root else default_plugin_root()
    payload = validate(root, strict=args.strict)
    if args.format == "text":
        print(render_text(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] in {"pass", "warn"} and not args.strict else (0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    sys.exit(main())
