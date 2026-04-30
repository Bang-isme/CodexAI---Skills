#!/usr/bin/env python3
"""Install a project-local Codex hooks.json adapter for CodexAI runtime preflight."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SKILLS_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_HOOK = SKILLS_ROOT / "codex-runtime-hook" / "scripts" / "runtime_hook.py"
STATUS_MESSAGE = "Checking CodexAI project readiness"


def validate_project_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Project root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {root}")
    return root


def validate_skills_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    runtime_hook = root / "codex-runtime-hook" / "scripts" / "runtime_hook.py"
    if not runtime_hook.exists():
        raise FileNotFoundError(f"runtime_hook.py not found under skills root: {runtime_hook}")
    if not runtime_hook.is_file():
        raise FileNotFoundError(f"runtime_hook.py is not a file: {runtime_hook}")
    return root


def quote_arg(value: Path | str) -> str:
    return '"' + str(value).replace('"', '\\"') + '"'


def hook_command(project_root: Path, skills_root: Path) -> str:
    runtime_hook = skills_root / "codex-runtime-hook" / "scripts" / "runtime_hook.py"
    return f'{quote_arg(sys.executable)} {quote_arg(runtime_hook)} --project-root {quote_arg(project_root)} --format prompt'


def codexai_session_hook(project_root: Path, skills_root: Path) -> dict[str, Any]:
    return {
        "matcher": "startup|resume",
        "hooks": [
            {
                "type": "command",
                "command": hook_command(project_root, skills_root),
                "timeout": 30,
                "statusMessage": STATUS_MESSAGE,
            }
        ],
    }


def load_hooks(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"hooks": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def merge_hooks(existing: dict[str, Any], hook_entry: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    payload = dict(existing)
    hooks = payload.setdefault("hooks", {})
    session = hooks.setdefault("SessionStart", [])
    for item in session:
        if isinstance(item, dict):
            for hook in item.get("hooks", []):
                if isinstance(hook, dict) and hook.get("statusMessage") == STATUS_MESSAGE:
                    return payload, False
    session.append(hook_entry)
    return payload, True


def install(project_root: Path, skills_root: Path, dry_run: bool, force: bool) -> dict[str, Any]:
    skills_root = validate_skills_root(skills_root)
    hooks_path = project_root / ".codex" / "hooks.json"
    hook_entry = codexai_session_hook(project_root, skills_root)
    if force:
        payload = {"hooks": {"SessionStart": [hook_entry]}}
        changed = True
    else:
        existing = load_hooks(hooks_path)
        payload, changed = merge_hooks(existing, hook_entry)
    if not dry_run and changed:
        hooks_path.parent.mkdir(parents=True, exist_ok=True)
        hooks_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "dry_run" if dry_run else ("updated" if changed else "unchanged"),
        "hooks_path": str(hooks_path),
        "changed": changed,
        "hook": hook_entry,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install CodexAI runtime hook into project .codex/hooks.json.")
    parser.add_argument("--project-root", required=True, help="Project root")
    parser.add_argument("--skills-root", default="", help="Skills root. Defaults to current script's skills root")
    parser.add_argument("--apply", action="store_true", help="Write hooks.json. Default is dry-run.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only. This is the default.")
    parser.add_argument("--force", action="store_true", help="Replace hooks.json with only the CodexAI SessionStart hook")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_root = validate_project_root(Path(args.project_root))
        skills_root = validate_skills_root(Path(args.skills_root)) if args.skills_root else validate_skills_root(SKILLS_ROOT)
        dry_run = not args.apply or args.dry_run
        payload = install(project_root, skills_root, dry_run=dry_run, force=args.force)
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "text":
        print(f"{payload['status']}: {payload.get('hooks_path', '')}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
