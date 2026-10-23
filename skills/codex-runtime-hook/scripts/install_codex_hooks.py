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
_UNSAFE_SHELL_CHARS = set("\"'$`;\n\r&|")


def validate_shell_safe_path(path_str: str) -> bool:
    """Accept ordinary Windows and POSIX paths. Reject shell metacharacters."""
    if not isinstance(path_str, str) or path_str.strip() == "":
        return False
    return not any(char in path_str for char in _UNSAFE_SHELL_CHARS)


def _require_shell_safe(path_value: Path | str) -> None:
    text = str(path_value)
    if not validate_shell_safe_path(text):
        raise ValueError(f"path contains shell metacharacters: {text}")


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


def _is_codexai_managed(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    hooks = entry.get("hooks", [])
    if not isinstance(hooks, list):
        return False
    for hook in hooks:
        if not isinstance(hook, dict):
            continue
        if hook.get("statusMessage") == STATUS_MESSAGE:
            return True
        command = str(hook.get("command", "")).replace("\\", "/")
        if "codex-runtime-hook/scripts/runtime_hook.py" in command:
            return True
    return False


def parse_hooks_document(existing_raw: str) -> dict[str, Any]:
    """Strip a UTF-8 BOM, refuse malformed JSON, and require hook arrays to be lists."""
    if not isinstance(existing_raw, str):
        raise ValueError("hooks config must be text")
    raw = existing_raw[1:] if existing_raw.startswith("\ufeff") else existing_raw
    if not raw.strip():
        payload: Any = {"hooks": {}}
    else:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed hooks JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("hooks config must be a JSON object")
    hooks = payload.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks must be an object")
    for name, entries in hooks.items():
        if not isinstance(entries, list):
            raise ValueError(f"hooks.{name} must be a list")
    return payload


def merge_hooks_config(existing_raw: str, managed_entry: dict[str, Any]) -> dict[str, Any]:
    """Replace only CodexAI-managed hook entries and preserve foreign user hooks."""
    if not isinstance(managed_entry, dict):
        raise ValueError("managed hook entry must be an object")
    payload = parse_hooks_document(existing_raw)
    hooks = payload["hooks"]
    session = list(hooks.get("SessionStart", []))
    replaced = False
    updated: list[Any] = []
    for item in session:
        if _is_codexai_managed(item):
            if not replaced:
                updated.append(managed_entry)
                replaced = True
            continue
        updated.append(item)
    if not replaced:
        updated.append(managed_entry)
    hooks["SessionStart"] = updated
    payload["hooks"] = hooks
    return payload


def uninstall_hooks_document(existing_raw: str) -> tuple[dict[str, Any], bool]:
    """Remove CodexAI entries. The boolean is true when the file should be deleted."""
    payload = parse_hooks_document(existing_raw)
    hooks = payload.get("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks must be an object")
    new_hooks: dict[str, Any] = {}
    foreign = False
    for name, entries in hooks.items():
        if not isinstance(entries, list):
            raise ValueError(f"hooks.{name} must be a list")
        kept = [item for item in entries if not _is_codexai_managed(item)]
        if kept:
            foreign = True
            new_hooks[name] = kept
    payload["hooks"] = new_hooks
    return payload, not foreign


def load_hooks(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"hooks": {}}
    return parse_hooks_document(path.read_text(encoding="utf-8"))


def merge_hooks(existing: dict[str, Any], hook_entry: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    merged = merge_hooks_config(json.dumps(existing), hook_entry)
    return merged, merged != existing


def _prepare_roots(project_root: Path, skills_root: Path | None) -> tuple[Path, Path]:
    _require_shell_safe(project_root)
    project = validate_project_root(project_root)
    _require_shell_safe(project)
    selected = skills_root if skills_root is not None else SKILLS_ROOT
    _require_shell_safe(selected)
    skills = validate_skills_root(selected)
    _require_shell_safe(skills)
    return project, skills


def install(project_root: Path, skills_root: Path, dry_run: bool, force: bool) -> dict[str, Any]:
    project_root, skills_root = _prepare_roots(project_root, skills_root)
    hooks_path = project_root / ".codex" / "hooks.json"
    hook_entry = codexai_session_hook(project_root, skills_root)
    if force:
        payload: dict[str, Any] = {"hooks": {"SessionStart": [hook_entry]}}
        changed = True
    else:
        before = load_hooks(hooks_path) if hooks_path.exists() else {"hooks": {}}
        raw = hooks_path.read_text(encoding="utf-8") if hooks_path.exists() else '{"hooks": {}}'
        payload = merge_hooks_config(raw, hook_entry)
        changed = payload != before
    if not dry_run and changed:
        hooks_path.parent.mkdir(parents=True, exist_ok=True)
        hooks_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "dry_run" if dry_run else ("updated" if changed else "unchanged"),
        "hooks_path": str(hooks_path),
        "changed": changed,
        "hook": hook_entry,
    }


def uninstall(project_root: Path, dry_run: bool) -> dict[str, Any]:
    _require_shell_safe(project_root)
    project_root = validate_project_root(project_root)
    _require_shell_safe(project_root)
    hooks_path = project_root / ".codex" / "hooks.json"
    if not hooks_path.exists():
        return {
            "status": "unchanged",
            "hooks_path": str(hooks_path),
            "changed": False,
            "deleted": False,
        }
    payload, delete_file = uninstall_hooks_document(hooks_path.read_text(encoding="utf-8"))
    if not dry_run:
        if delete_file:
            hooks_path.unlink()
        else:
            hooks_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "dry_run" if dry_run else ("deleted" if delete_file else "updated"),
        "hooks_path": str(hooks_path),
        "changed": True,
        "deleted": delete_file,
        "hooks": payload.get("hooks", {}),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install CodexAI runtime hook into project .codex/hooks.json.")
    parser.add_argument("--project-root", required=True, help="Project root")
    parser.add_argument("--skills-root", default="", help="Skills root. Defaults to current script's skills root")
    parser.add_argument("--apply", action="store_true", help="Write hooks.json. Default is dry-run.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only. This is the default.")
    parser.add_argument("--force", action="store_true", help="Replace hooks.json with only the CodexAI SessionStart hook")
    parser.add_argument("--uninstall", action="store_true", help="Remove only the CodexAI hook entry")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_root = Path(args.project_root)
        dry_run = not args.apply or args.dry_run
        if args.uninstall:
            if args.force:
                raise ValueError("uninstall cannot be combined with --force")
            payload = uninstall(project_root, dry_run=dry_run)
        else:
            skills_root = validate_skills_root(Path(args.skills_root)) if args.skills_root else SKILLS_ROOT
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
