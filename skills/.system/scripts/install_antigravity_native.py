#!/usr/bin/env python3
"""Install the built Antigravity native plugin into IDE and/or CLI locations."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


PLUGIN_DIR_NAME = "codexai-agentic-workflow"


def default_plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]


def home_dir() -> Path:
    value = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not value:
        raise RuntimeError("USERPROFILE/HOME is not set")
    return Path(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install CodexAI Antigravity native plugin. Dry-run by default. Resolves hook paths at install time."
    )
    parser.add_argument("--plugin-root", default="", help="CodexAI repo root")
    parser.add_argument("--package-dir", default="", help="Built package directory; built on the fly if omitted")
    parser.add_argument("--project-root", default="", help="Workspace root for workspace plugin install")
    parser.add_argument("--scope", choices=("workspace", "user"), default="workspace")
    parser.add_argument("--surface", choices=("ide", "cli", "both"), default="both")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def resolve_targets(scope: str, surface: str, project_root: Path) -> list[Path]:
    targets: list[Path] = []
    if scope == "workspace":
        targets.append(project_root / ".agents" / "plugins" / PLUGIN_DIR_NAME)
        return targets
    home = home_dir()
    if surface in {"ide", "both"}:
        targets.append(home / ".gemini" / "config" / "plugins" / PLUGIN_DIR_NAME)
    if surface in {"cli", "both"}:
        targets.append(home / ".gemini" / "antigravity-cli" / "plugins" / PLUGIN_DIR_NAME)
    return targets


def copy_tree(source: Path, dest: Path, apply: bool) -> list[str]:
    copied: list[str] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(source).as_posix()
        target = dest / rel
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        copied.append(rel)
    return copied


def resolve_hooks(dest: Path, apply: bool) -> dict[str, Any]:
    hooks_path = dest / "hooks.json"
    script_path = dest / "scripts" / "pre_tool_use.py"
    python = sys.executable
    payload = json.loads(hooks_path.read_text(encoding="utf-8")) if hooks_path.exists() else {"hooks": {}}
    command = [python, str(script_path)]
    for hook_name, entries in list((payload.get("hooks") or {}).items()):
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and "command" in entry:
                entry["command"] = command
    if apply and hooks_path.exists():
        hooks_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"hooks_path": str(hooks_path), "command": command, "python": python}


def ensure_package(plugin_root: Path, package_dir: Path, apply: bool) -> dict[str, Any]:
    script = Path(__file__).resolve().parent / "build_antigravity_plugin.py"
    if package_dir.exists() and (package_dir / "plugin.json").exists():
        return {"status": "reused", "output": str(package_dir)}
    args = [sys.executable, str(script), "--plugin-root", str(plugin_root), "--output", str(package_dir), "--format", "json"]
    if apply:
        args.append("--apply")
    result = __import__("subprocess").run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"status": "error", "stdout": result.stdout[-1000:], "stderr": result.stderr[-1000:]}
    payload["exit_code"] = result.returncode
    return payload


def install(source: Path, targets: list[Path], apply: bool, uninstall: bool) -> dict[str, Any]:
    results = []
    for target in targets:
        if uninstall:
            existed = target.exists()
            if apply and existed:
                shutil.rmtree(target)
            results.append({"target": str(target), "action": "uninstall", "existed": existed, "applied": apply})
            continue
        copied = copy_tree(source, target, apply=apply) if source.exists() else []
        hooks = {"command": [sys.executable, str(target / "scripts" / "pre_tool_use.py")]}
        if apply and (target / "hooks.json").exists():
            hooks = resolve_hooks(target, apply=True)
        results.append(
            {
                "target": str(target),
                "action": "install",
                "files": len(copied),
                "hooks": hooks,
                "applied": apply,
                "source_exists": source.exists(),
            }
        )
    return {
        "status": "pass" if apply else "dry_run",
        "native_status": "native package candidate",
        "results": results,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        plugin_root = Path(args.plugin_root).expanduser().resolve() if args.plugin_root else default_plugin_root()
        project_root = Path(args.project_root).expanduser().resolve() if args.project_root else Path.cwd().resolve()
        package_dir = Path(args.package_dir).expanduser().resolve() if args.package_dir else plugin_root / "dist" / "antigravity-plugin"
        build_payload = {"status": "skipped"}
        if not args.uninstall:
            build_payload = ensure_package(plugin_root, package_dir, apply=bool(args.apply) or package_dir.exists())
            if args.apply and not (package_dir / "plugin.json").exists():
                build_payload = ensure_package(plugin_root, package_dir, apply=True)
        targets = resolve_targets(args.scope, args.surface, project_root)
        payload = install(package_dir, targets, apply=bool(args.apply), uninstall=bool(args.uninstall))
        payload["build"] = build_payload
        payload["scope"] = args.scope
        payload["surface"] = args.surface
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "text":
        print(f"{payload['status']}: targets={len(payload.get('results') or [])}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") in {"pass", "dry_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
