#!/usr/bin/env python3
"""Validate a project-local Codex hooks.json contains the CodexAI runtime hook."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATUS_MESSAGE = "Checking CodexAI project readiness"
REQUIRED_TIMEOUT_SECONDS = 30


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
    if not isinstance(payload, dict):
        return {"status": "fail", "hooks_path": str(hooks_path), "message": "hooks.json root must be an object"}
    hooks_root = payload.get("hooks")
    if not isinstance(hooks_root, dict):
        return {"status": "fail", "hooks_path": str(hooks_path), "message": "hooks must be an object"}
    session = hooks_root.get("SessionStart")
    if not isinstance(session, list):
        return {"status": "fail", "hooks_path": str(hooks_path), "message": "hooks.SessionStart must be a list"}
    failures: list[str] = []
    candidate_failures: list[str] = []
    for item in session:
        if not isinstance(item, dict):
            failures.append("SessionStart entries must be objects")
            continue
        item_failures: list[str] = []
        if item.get("matcher") != "startup|resume":
            item_failures.append("SessionStart matcher must be startup|resume")
        item_hooks = item.get("hooks", [])
        if not isinstance(item_hooks, list):
            failures.append("SessionStart hooks must be a list")
            continue
        for hook in item_hooks:
            if not isinstance(hook, dict):
                failures.append("hook entries must be objects")
                continue
            command = str(hook.get("command", ""))
            is_codexai_candidate = hook.get("statusMessage") == STATUS_MESSAGE or "runtime_hook.py" in command
            if not is_codexai_candidate:
                continue
            current_failures = list(item_failures)
            if hook.get("statusMessage") != STATUS_MESSAGE:
                current_failures.append("statusMessage mismatch")
            if hook.get("type") != "command":
                current_failures.append("CodexAI runtime hook type must be command")
            if hook.get("timeout") != REQUIRED_TIMEOUT_SECONDS:
                current_failures.append(f"CodexAI runtime hook timeout must be {REQUIRED_TIMEOUT_SECONDS}")
            for required in ("runtime_hook.py", "--project-root", "--format prompt"):
                if required not in command:
                    current_failures.append(f"CodexAI runtime hook command missing {required}")
            if not current_failures:
                return {
                    "status": "pass",
                    "hooks_path": str(hooks_path),
                    "message": "CodexAI runtime hook installed",
                }
            candidate_failures.extend(current_failures)
    return {
        "status": "fail",
        "hooks_path": str(hooks_path),
        "message": "; ".join(candidate_failures or failures) if (candidate_failures or failures) else "CodexAI runtime hook not found",
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
