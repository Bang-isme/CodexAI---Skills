#!/usr/bin/env python3
"""Validate an Antigravity native plugin package."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


STRICT_SKILL_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
DOCUMENTED_TOOLS = {
    "view_file",
    "replace_file_content",
    "run_command",
    "grep_search",
    "glob_search",
}
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
RULE_CHAR_LIMIT = 12000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Antigravity plugin schema, skills, agents, rules, and hooks.")
    parser.add_argument("--package-dir", required=True, help="Built plugin directory containing plugin.json")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def add(checks: list[dict[str, Any]], name: str, status: str, detail: str) -> None:
    checks.append({"name": name, "status": status, "detail": detail})


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: dict[str, str] = {}
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("'\"")
    return data


def validate_package(package_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    plugin_path = package_dir / "plugin.json"
    if not plugin_path.exists():
        add(checks, "plugin_json", "fail", "missing plugin.json")
        return {"status": "fail", "checks": checks}
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    name_ok = isinstance(plugin.get("name"), str) and bool(plugin.get("name"))
    desc_ok = isinstance(plugin.get("description"), str) and bool(plugin.get("description"))
    add(checks, "plugin_schema", "pass" if name_ok and desc_ok else "fail", "name and description required")

    workflows = package_dir / ".agents" / "workflows"
    add(checks, "no_deprecated_workflows", "pass" if not workflows.exists() else "fail", str(workflows))

    skill_files = list((package_dir / "skills").glob("*/SKILL.md")) if (package_dir / "skills").exists() else []
    bad_skills = []
    for path in skill_files:
        text = path.read_text(encoding="utf-8")
        data = parse_frontmatter(text)
        unexpected = sorted(set(data) - STRICT_SKILL_KEYS - {"name", "description"})
        # nested metadata keys appear as "metadata" only in this simple parser
        if "load_priority" in data or "file_ownership" in data or "skills" in data:
            bad_skills.append(path.as_posix())
        if unexpected and any(key in {"trigger", "loads", "version"} for key in unexpected):
            bad_skills.append(path.as_posix())
    add(checks, "skill_frontmatter", "pass" if not bad_skills else "fail", "strict Agent Skills fields" if not bad_skills else ", ".join(bad_skills[:8]))

    agent_files = list((package_dir / "agents").glob("*/agent.md"))
    add(checks, "agents_present", "pass" if agent_files else "fail", f"{len(agent_files)} agent.md files")
    bad_tools = []
    for path in agent_files:
        text = path.read_text(encoding="utf-8")
        parts = text.split("---")
        block = parts[1] if text.startswith("---") and len(parts) > 2 else ""
        if "file_ownership:" in block:
            bad_tools.append(f"{path.parent.name}:file_ownership")
        tools = re.findall(r"^  - ([a-z_]+)$", text, re.MULTILINE)
        unknown = [tool for tool in tools if tool not in DOCUMENTED_TOOLS]
        if unknown:
            bad_tools.append(f"{path.parent.name}:{','.join(unknown)}")
    add(checks, "agent_tools", "pass" if not bad_tools else "fail", "documented tools only" if not bad_tools else ", ".join(bad_tools[:8]))

    rule_issues = []
    for path in (package_dir / "rules").glob("*.md") if (package_dir / "rules").exists() else []:
        size = len(path.read_text(encoding="utf-8"))
        if size > RULE_CHAR_LIMIT:
            rule_issues.append(f"{path.name}:{size}")
    add(checks, "rule_size", "pass" if not rule_issues else "fail", "rules under 12000 chars" if not rule_issues else ", ".join(rule_issues))

    hooks_path = package_dir / "hooks.json"
    add(checks, "hooks_json", "pass" if hooks_path.exists() else "fail", str(hooks_path))
    status_path = package_dir / "NATIVE_STATUS.txt"
    native_ok = status_path.exists() and "native package candidate" in status_path.read_text(encoding="utf-8")
    add(checks, "native_status_label", "pass" if native_ok else "fail", "must remain a candidate until live smoke")

    agy = shutil.which("agy")
    agy_smoke = {"status": "skipped", "reason": "binary unavailable"}
    if agy:
        try:
            result = subprocess.run([agy, "plugin", "list"], capture_output=True, text=True, timeout=20, check=False)
            agy_smoke = {"status": "ran", "exit_code": result.returncode, "stdout_tail": result.stdout[-500:]}
        except (OSError, subprocess.TimeoutExpired) as exc:
            agy_smoke = {"status": "failed", "reason": str(exc)}
    add(checks, "agy_smoke", "pass" if agy_smoke["status"] in {"skipped", "ran"} else "fail", json.dumps(agy_smoke))

    failed = [item for item in checks if item["status"] == "fail"]
    return {
        "status": "fail" if failed else "pass",
        "package_dir": str(package_dir),
        "checks": checks,
        "agy_smoke": agy_smoke,
        "native_status": "native package candidate",
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        package_dir = Path(args.package_dir).expanduser().resolve()
        payload = validate_package(package_dir)
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "text":
        print(f"{payload['status']}: checks={len(payload.get('checks') or [])}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
