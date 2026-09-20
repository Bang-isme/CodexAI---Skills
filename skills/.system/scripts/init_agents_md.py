#!/usr/bin/env python3
"""Create or merge CodexAI core-rules bridges for AGENTS.md, CLAUDE.md, Cursor, and Antigravity."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import render_core_rules


START_MARKER = render_core_rules.START_MARKER
END_MARKER = render_core_rules.END_MARKER
HOSTS = render_core_rules.HOSTS


def bridge_for(host: str = "agents") -> str:
    return render_core_rules.render_host_document(host)


BRIDGE = bridge_for("agents")


def validate_repo_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repo root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repo root is not a directory: {root}")
    return root


def merge_content(existing: str, rendered: str) -> tuple[str, str]:
    return render_core_rules.merge_marked(existing, rendered)


def target_path(repo_root: Path, host: str) -> Path:
    return repo_root / render_core_rules.relative_path_for(host)


def build_host_payload(repo_root: Path, host: str, mode: str, dry_run: bool) -> dict[str, Any]:
    path = target_path(repo_root, host)
    rendered = render_core_rules.render_host_document(host)
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if mode == "force":
        content = rendered if rendered.endswith("\n") else rendered + "\n"
        action = "replaced" if path.exists() else "created"
    else:
        content, action = merge_content(existing, rendered)
    changed = content != existing
    if not dry_run and changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    return {
        "status": "dry_run" if dry_run else ("unchanged" if not changed else action),
        "path": str(path),
        "host": host,
        "changed": changed,
        "mode": mode,
        "content": content if dry_run else "",
    }


def build_payload(repo_root: Path, mode: str, dry_run: bool, target: str = "agents") -> dict[str, Any]:
    hosts = HOSTS if target == "all" else (target,)
    if target != "all" and target not in HOSTS:
        raise ValueError(f"unsupported target: {target}")
    payloads = [build_host_payload(repo_root, host, mode, dry_run) for host in hosts]
    primary = payloads[0]
    if target == "all":
        changed = any(item["changed"] for item in payloads)
        statuses = [item["status"] for item in payloads]
        if dry_run:
            status = "dry_run"
        elif not changed:
            status = "unchanged"
        elif all(item == "created" for item in statuses):
            status = "created"
        elif all(item == "replaced" for item in statuses):
            status = "replaced"
        else:
            status = "updated"
        return {
            "status": status,
            "path": primary["path"],
            "host": "all",
            "changed": changed,
            "mode": mode,
            "hosts": payloads,
            "content": "" if not dry_run else primary.get("content", ""),
        }
    return primary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize CodexAI core-rules host bridges.")
    parser.add_argument("--repo-root", required=True, help="Repository root")
    parser.add_argument("--target", choices=("agents", "claude", "cursor", "antigravity", "all"), default="agents")
    parser.add_argument("--dry-run", action="store_true", help="Preview only. Default when neither --merge nor --force is passed.")
    parser.add_argument("--merge", action="store_true", help="Create or merge the CodexAI bridge block")
    parser.add_argument("--force", action="store_true", help="Replace the target file with the CodexAI bridge")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = validate_repo_root(Path(args.repo_root))
        if args.force and args.merge:
            raise ValueError("Use only one of --merge or --force")
        mode = "force" if args.force else "merge"
        dry_run = args.dry_run or not (args.merge or args.force)
        payload = build_payload(root, mode, dry_run, target=args.target)
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    if args.format == "text":
        print(f"{payload['status']}: {payload.get('path', '')}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
