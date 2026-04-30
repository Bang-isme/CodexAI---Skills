#!/usr/bin/env python3
"""Install CodexAI skills into Claude-native standalone skill locations."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import sync_global_skills


def default_source_root() -> Path:
    return Path(__file__).resolve().parents[2]


def home_dir() -> Path:
    value = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not value:
        raise RuntimeError("USERPROFILE/HOME is not set")
    return Path(value)


def resolve_target(scope: str, repo_root: str, target_root: str) -> Path:
    if scope == "project":
        if not repo_root:
            raise ValueError("--repo-root is required for --scope project")
        return Path(repo_root).expanduser().resolve() / ".claude" / "skills"
    if scope == "user":
        return home_dir() / ".claude" / "skills"
    if scope == "custom":
        if not target_root:
            raise ValueError("--target-root is required for --scope custom")
        return Path(target_root).expanduser().resolve()
    raise ValueError(f"unsupported scope: {scope}")


def install(source_root: Path, target_root: Path, dry_run: bool, backup_dir: Path | None = None) -> dict[str, Any]:
    payload = sync_global_skills.sync(source_root, target_root, dry_run=dry_run, backup_dir=backup_dir)
    payload["claude_target"] = str(target_root)
    payload["claude_install"] = True
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install CodexAI skills into Claude Code skill directories.")
    parser.add_argument("--source", default="", help="Source skills directory. Defaults to this repo's skills root.")
    parser.add_argument("--scope", choices=("project", "user", "custom"), default="user")
    parser.add_argument("--repo-root", default="", help="Repository root for --scope project")
    parser.add_argument("--target-root", default="", help="Explicit target for --scope custom")
    parser.add_argument("--apply", action="store_true", help="Actually copy files. Default is dry-run.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only. This is the default.")
    parser.add_argument("--backup-dir", default="", help="Backup directory for overwritten files")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        source_root = Path(args.source).expanduser().resolve() if args.source else default_source_root()
        target_root = resolve_target(args.scope, args.repo_root, args.target_root)
        dry_run = not args.apply or args.dry_run
        backup_dir = Path(args.backup_dir).expanduser().resolve() if args.backup_dir else None
        if not dry_run:
            target_root.mkdir(parents=True, exist_ok=True)
        payload = install(source_root, target_root, dry_run=dry_run, backup_dir=backup_dir)
        payload["scope"] = args.scope
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    if args.format == "text":
        print(
            f"{payload['status']}: scope={payload['scope']} target={payload['claude_target']} "
            f"changed={payload.get('changed_files_count', 0)} protected_skipped={payload.get('protected_skipped_count', 0)}"
        )
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
