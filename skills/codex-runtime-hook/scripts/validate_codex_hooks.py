#!/usr/bin/env python3
"""Validate a project-local Codex hooks.json contains the CodexAI runtime hook."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATUS_MESSAGE = "Checking CodexAI project readiness"


def validate_project_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Project root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {root}")
    return root


def validate_hooks(project_root: Path) -> dict[str, Any]:
    hooks_path = project_root / ".codex" / "hooks.json"
    if not hooks_path.exists():
        return {"status": "fail", "hooks_path": str(hooks_path), "message": "hooks.json not found"}
    try:
        payload = json.loads(hooks_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"status": "fail", "hooks_path": str(hooks_path), "message": f"invalid JSON: {exc}"}
    session = payload.get("hooks", {}).get("SessionStart", [])
    found = False
    for item in session if isinstance(session, list) else []:
        if not isinstance(item, dict):
            continue
        for hook in item.get("hooks", []):
            if isinstance(hook, dict) and hook.get("statusMessage") == STATUS_MESSAGE and "runtime_hook.py" in str(hook.get("command", "")):
                found = True
    return {
        "status": "pass" if found else "fail",
        "hooks_path": str(hooks_path),
        "message": "CodexAI runtime hook installed" if found else "CodexAI runtime hook not found",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate CodexAI runtime hook installation.")
    parser.add_argument("--project-root", required=True, help="Project root")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_root = validate_project_root(Path(args.project_root))
        payload = validate_hooks(project_root)
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "text":
        print(f"{payload['status']}: {payload.get('message', '')}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
