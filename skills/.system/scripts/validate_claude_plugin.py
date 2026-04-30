#!/usr/bin/env python3
"""Validate Claude Code plugin packaging for CodexAI skills."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


def default_plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")
    return payload


def add(checks: list[dict[str, Any]], name: str, status: str, detail: str, **extra: Any) -> None:
    item: dict[str, Any] = {"name": name, "status": status, "detail": detail}
    item.update(extra)
    checks.append(item)


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = read_text(path).splitlines()
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


def check_manifest(root: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    path = root / ".claude-plugin" / "plugin.json"
    if not path.exists():
        add(checks, "claude_manifest_exists", "fail", str(path))
        return {}
    try:
        manifest = read_json(path)
    except Exception as exc:
        add(checks, "claude_manifest_json", "fail", f"invalid JSON: {exc}")
        return {}

    add(checks, "claude_manifest_exists", "pass", str(path))
    name = str(manifest.get("name", ""))
    add(checks, "claude_plugin_name", "pass" if PLUGIN_NAME_RE.match(name) else "fail", name or "missing")
    add(checks, "claude_plugin_description", "pass" if str(manifest.get("description", "")).strip() else "fail", "description present")

    version = str(manifest.get("version", ""))
    source_version_path = root / "skills" / "VERSION"
    source_version = read_text(source_version_path).strip() if source_version_path.exists() else ""
    add(
        checks,
        "claude_plugin_version",
        "pass" if version and version == source_version else "fail",
        f"plugin={version}, skills={source_version}",
    )
    return manifest


def check_skills(root: Path, checks: list[dict[str, Any]]) -> None:
    skills_root = root / "skills"
    if not skills_root.is_dir():
        add(checks, "claude_skills_dir", "fail", str(skills_root))
        return
    failures: list[str] = []
    warnings: list[str] = []
    total = 0
    seen: dict[str, str] = {}
    for skill_md in sorted(skills_root.glob("*/SKILL.md")):
        if skill_md.parent.name.startswith("."):
            continue
        total += 1
        frontmatter = parse_frontmatter(skill_md)
        description = frontmatter.get("description", "")
        name = frontmatter.get("name", skill_md.parent.name)
        if not description:
            failures.append(f"{skill_md.parent.name}: missing description")
        if name != skill_md.parent.name:
            warnings.append(f"{skill_md.parent.name}: frontmatter name differs from folder name {name}")
        previous = seen.get(skill_md.parent.name)
        if previous:
            failures.append(f"{skill_md.parent.name}: duplicate folder also seen at {previous}")
        seen[skill_md.parent.name] = str(skill_md)
    add(
        checks,
        "claude_skill_metadata",
        "pass" if total and not failures else "fail",
        f"{total} Claude skill folder(s) checked" if not failures else "; ".join(failures[:5]),
        total=total,
        failures=failures,
        warnings=warnings,
        warnings_count=len(warnings),
    )


def check_hooks(root: Path, checks: list[dict[str, Any]]) -> None:
    path = root / "hooks" / "hooks.json"
    if not path.exists():
        add(checks, "claude_hooks", "warn", "hooks/hooks.json absent; skills still usable")
        return
    try:
        payload = read_json(path)
    except Exception as exc:
        add(checks, "claude_hooks", "fail", f"invalid JSON: {exc}")
        return
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict):
        add(checks, "claude_hooks", "fail", "hooks must be an object")
        return
    session = hooks.get("SessionStart")
    if not isinstance(session, list):
        add(checks, "claude_hooks", "fail", "hooks.SessionStart must be a list")
        return
    failures: list[str] = []
    found = False
    for group in session:
        if not isinstance(group, dict):
            failures.append("SessionStart entries must be objects")
            continue
        if group.get("matcher") != "startup|resume":
            failures.append("SessionStart matcher must be startup|resume")
        for hook in group.get("hooks", []):
            if not isinstance(hook, dict):
                failures.append("hook entries must be objects")
                continue
            command = str(hook.get("command", ""))
            if "runtime_hook.py" not in command:
                continue
            found = True
            if hook.get("type") != "command":
                failures.append("runtime hook type must be command")
            if hook.get("timeout") != 30:
                failures.append("runtime hook timeout must be 30")
            for token in ("${CLAUDE_PLUGIN_ROOT}", "${CLAUDE_PROJECT_DIR}", "--format prompt"):
                if token not in command:
                    failures.append(f"runtime hook command missing {token}")
    if not found:
        failures.append("runtime_hook.py command not found")
    add(
        checks,
        "claude_hooks",
        "pass" if not failures else "fail",
        "Claude plugin SessionStart hook valid" if not failures else "; ".join(failures),
        failures=failures,
    )


def summarize(checks: list[dict[str, Any]], strict: bool) -> dict[str, Any]:
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
    check_manifest(root, checks)
    check_skills(root, checks)
    check_hooks(root, checks)
    return summarize(checks, strict)


def render_text(payload: dict[str, Any]) -> str:
    lines = [f"Status: {payload['status']}", f"Checks: {payload['total']} total, {payload['failed']} failed, {payload['warnings']} warning groups", ""]
    for item in payload["checks"]:
        lines.append(f"- {item['status'].upper()}: {item['name']} -- {item['detail']}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Claude Code plugin compatibility.")
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
