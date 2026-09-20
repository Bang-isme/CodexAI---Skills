#!/usr/bin/env python3
"""One-command CodexAI install dispatcher and doctor for Codex, Claude, Cursor, and Antigravity."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import init_agents_md
import install_claude_native
import install_codex_native
import install_cursor_native
import render_core_rules


HOSTS = ("codex", "claude", "cursor", "antigravity")
BRIDGE_BY_HOST = {
    "codex": "agents",
    "claude": "claude",
    "cursor": "cursor",
    "antigravity": "antigravity",
}


def default_source_root() -> Path:
    return Path(__file__).resolve().parents[2]


def plugin_root_from_skills(skills_root: Path) -> Path:
    return skills_root.resolve().parent


def home_dir() -> Path:
    value = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not value:
        raise RuntimeError("USERPROFILE/HOME is not set")
    return Path(value)


def resolve_scope(host: str, scope: str, repo_root: str) -> str:
    if host == "claude" and scope == "repo":
        return "project"
    if host == "antigravity" and scope == "repo":
        return "workspace"
    return scope


def expected_skills_root(host: str, scope: str, repo_root: Path | None) -> Path:
    native_scope = resolve_scope(host, scope, str(repo_root or ""))
    if host == "codex":
        return install_codex_native.resolve_target(native_scope if native_scope != "project" else "repo", str(repo_root or ""), "")
    if host == "claude":
        return install_claude_native.resolve_target(native_scope if native_scope != "repo" else "project", str(repo_root or ""), "")
    if host == "cursor":
        return install_cursor_native.resolve_target(native_scope if native_scope != "project" else "repo", str(repo_root or ""), "")
    if native_scope in {"workspace", "repo"}:
        if not repo_root:
            raise ValueError("--repo-root is required for Antigravity workspace/repo install")
        return repo_root / ".agents" / "plugins" / "codexai-agentic-workflow"
    return home_dir() / ".gemini" / "config" / "plugins" / "codexai-agentic-workflow"


def expected_bridge_path(host: str, repo_root: Path | None) -> Path | None:
    if repo_root is None:
        return None
    return repo_root / render_core_rules.relative_path_for(BRIDGE_BY_HOST[host])


def run_install_host(
    host: str,
    skills_root: Path,
    scope: str,
    repo_root: Path | None,
    apply: bool,
) -> dict[str, Any]:
    native_scope = resolve_scope(host, scope, str(repo_root or ""))
    dry_run = not apply
    if host == "codex":
        target = install_codex_native.resolve_target(native_scope if native_scope != "project" else "repo", str(repo_root or ""), "")
        if apply:
            target.mkdir(parents=True, exist_ok=True)
        payload = install_codex_native.install(skills_root, target, dry_run=dry_run)
    elif host == "claude":
        target = install_claude_native.resolve_target(native_scope if native_scope != "repo" else "project", str(repo_root or ""), "")
        if apply:
            target.mkdir(parents=True, exist_ok=True)
        payload = install_claude_native.install(skills_root, target, dry_run=dry_run)
    elif host == "cursor":
        target = install_cursor_native.resolve_target(native_scope if native_scope != "project" else "repo", str(repo_root or ""), "")
        if apply:
            target.mkdir(parents=True, exist_ok=True)
        payload = install_cursor_native.install(skills_root, target, dry_run=dry_run, repo_root=repo_root)
    else:
        plugin_root = plugin_root_from_skills(skills_root)
        args = [
            sys.executable,
            str(SCRIPT_DIR / "install_antigravity_native.py"),
            "--plugin-root",
            str(plugin_root),
            "--scope",
            native_scope if native_scope in {"workspace", "user"} else "workspace",
            "--surface",
            "both",
            "--format",
            "json",
        ]
        if repo_root:
            args.extend(["--project-root", str(repo_root)])
        if apply:
            args.append("--apply")
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240, check=False)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {"status": "fail", "stdout": result.stdout[-2000:], "stderr": result.stderr[-2000:]}
        payload["exit_code"] = result.returncode
        target = expected_skills_root(host, scope, repo_root)

    bridge = None
    if repo_root is not None:
        bridge = init_agents_md.build_payload(repo_root, "merge", dry_run=dry_run, target=BRIDGE_BY_HOST[host])
    payload["host"] = host
    payload["scope"] = scope
    payload["native_scope"] = native_scope
    payload["skills_target"] = str(target)
    if bridge:
        payload["bridge"] = bridge
    return payload


PLUGIN_SOURCE_MANIFESTS = {
    "codex": ".codex-plugin/plugin.json",
    "claude": ".claude-plugin/plugin.json",
    "antigravity": "antigravity/plugin.json",
    "cursor": ".cursor/rules/codexai-core.mdc",
}
# Plugin source checkout is a pass for every host. Cursor consumers still materialize
# `.cursor/skills` with `install.py --host cursor --apply`; doctor reports that in detail.
PLUGIN_SOURCE_STATUS = {"codex": "pass", "claude": "pass", "antigravity": "pass", "cursor": "pass"}


def plugin_source_root(host: str, repo_root: Path | None) -> Path | None:
    """Return repo_root/skills when repo_root is the plugin source itself for a manifest-loaded host."""
    if repo_root is None or host not in PLUGIN_SOURCE_MANIFESTS:
        return None
    skills_root = repo_root / "skills"
    if not (skills_root / "codex-master-instructions" / "SKILL.md").exists():
        return None
    if not (repo_root / PLUGIN_SOURCE_MANIFESTS[host]).exists():
        return None
    return skills_root


def doctor_host(host: str, scope: str, repo_root: Path | None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    skills_target = None
    try:
        skills_target = expected_skills_root(host, scope, repo_root)
        exists = skills_target.exists()
        source_root = None if exists else plugin_source_root(host, repo_root)
        if exists:
            checks.append({"name": "skills_root", "status": "pass", "detail": str(skills_target)})
            skill_md = skills_target / "codex-master-instructions" / "SKILL.md"
            if host == "antigravity":
                skill_md = skills_target / "skills" / "codex-master-instructions" / "SKILL.md"
        elif source_root is not None:
            detail = f"plugin source {source_root} (host loads via {PLUGIN_SOURCE_MANIFESTS[host]})"
            if host == "cursor":
                detail = f"plugin source {source_root}; run install.py --host cursor --scope repo --apply to materialize {skills_target}"
            checks.append({"name": "skills_root", "status": PLUGIN_SOURCE_STATUS[host], "detail": detail})
            skill_md = source_root / "codex-master-instructions" / "SKILL.md"
        else:
            checks.append({"name": "skills_root", "status": "fail", "detail": str(skills_target)})
            skill_md = skills_target / "codex-master-instructions" / "SKILL.md"
            if host == "antigravity":
                skill_md = skills_target / "skills" / "codex-master-instructions" / "SKILL.md"
        checks.append(
            {
                "name": "master_skill",
                "status": "pass" if skill_md.exists() else "fail",
                "detail": str(skill_md),
            }
        )
    except Exception as exc:
        checks.append({"name": "skills_root", "status": "fail", "detail": str(exc)})

    bridge_path = expected_bridge_path(host, repo_root)
    if bridge_path is not None:
        present = bridge_path.exists() and render_core_rules.START_MARKER in bridge_path.read_text(encoding="utf-8", errors="replace")
        checks.append({"name": "core_bridge", "status": "pass" if present else "fail", "detail": str(bridge_path)})
    else:
        checks.append({"name": "core_bridge", "status": "warn", "detail": "pass --repo-root to verify the host bridge file"})

    if host == "claude" and repo_root is not None:
        hook_path = repo_root / "hooks" / "hooks.json"
        if not hook_path.exists():
            hook_path = plugin_root_from_skills(default_source_root()) / "hooks" / "hooks.json"
        checks.append({"name": "session_hook", "status": "pass" if hook_path.exists() else "warn", "detail": str(hook_path)})
    if host == "codex" and repo_root is not None:
        hook_path = repo_root / ".codex" / "hooks.json"
        checks.append({"name": "session_hook", "status": "pass" if hook_path.exists() else "warn", "detail": str(hook_path)})
    if host == "cursor" and repo_root is not None:
        rule_path = repo_root / ".cursor" / "rules" / "codexai-core.mdc"
        checks.append({"name": "cursor_rule", "status": "pass" if rule_path.exists() else "fail", "detail": str(rule_path)})

    failed = [item for item in checks if item["status"] == "fail"]
    warned = [item for item in checks if item["status"] == "warn"]
    return {
        "host": host,
        "scope": scope,
        "skills_target": str(skills_target) if skills_target else "",
        "status": "fail" if failed else ("warn" if warned else "pass"),
        "checks": checks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install or diagnose CodexAI host wiring.")
    parser.add_argument("command", nargs="?", default="install", choices=("install", "doctor"))
    parser.add_argument("--host", choices=("codex", "claude", "cursor", "antigravity", "all"), default="all")
    parser.add_argument("--scope", choices=("user", "repo"), default="repo")
    parser.add_argument("--source", default="", help="Source skills directory")
    parser.add_argument("--repo-root", default="", help="Target repository root")
    parser.add_argument("--apply", action="store_true", help="Copy files and write bridges. Default is dry-run.")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        skills_root = Path(args.source).expanduser().resolve() if args.source else default_source_root()
        repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else Path.cwd()
        hosts = HOSTS if args.host == "all" else (args.host,)
        if args.command == "doctor":
            reports = [doctor_host(host, args.scope, repo_root) for host in hosts]
            failed = any(item["status"] == "fail" for item in reports)
            warned = any(item["status"] == "warn" for item in reports)
            payload: dict[str, Any] = {
                "status": "fail" if failed else ("warn" if warned else "pass"),
                "command": "doctor",
                "hosts": reports,
            }
        else:
            reports = [run_install_host(host, skills_root, args.scope, repo_root, args.apply) for host in hosts]
            failed = any(str(item.get("status") or "").lower() in {"error", "fail"} for item in reports)
            payload = {
                "status": "fail" if failed else ("dry_run" if not args.apply else "pass"),
                "command": "install",
                "applied": bool(args.apply),
                "hosts": reports,
            }
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    if args.format == "text":
        print(f"{payload['status']}: {payload.get('command')} hosts={len(payload.get('hosts', []))}")
        for item in payload.get("hosts", []):
            print(f"- {item.get('host')}: {item.get('status')} {item.get('skills_target') or item.get('path') or ''}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") in {"pass", "warn", "dry_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
