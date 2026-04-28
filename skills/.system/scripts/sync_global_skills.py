#!/usr/bin/env python3
"""Sync CodexAI skills to the global Codex skills directory, including dot directories."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


SKIP_NAMES = {".codex", ".codexai-backups", ".pytest_cache", "__pycache__"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
PROTECTED_RELATIVE_PREFIXES = {
    ".system/.codex-system-skills.marker",
    ".system/imagegen",
    ".system/openai-docs",
    ".system/plugin-creator",
    ".system/skill-creator",
    ".system/skill-installer",
}


def default_source_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_global_root() -> Path:
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not home:
        raise RuntimeError("USERPROFILE/HOME is not set; pass --global-root explicitly")
    return Path(home) / ".codex" / "skills"


def should_skip(path: Path) -> bool:
    return path.name in SKIP_NAMES or path.suffix in SKIP_SUFFIXES


def relative_posix(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def is_protected(relative_path: str) -> bool:
    normalized = relative_path.strip("/").replace("\\", "/")
    return any(normalized == prefix or normalized.startswith(prefix + "/") for prefix in PROTECTED_RELATIVE_PREFIXES)


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def files_equal(source: Path, target: Path) -> bool:
    if not target.exists() or not target.is_file():
        return False
    if source.stat().st_size != target.stat().st_size:
        return False
    return file_digest(source) == file_digest(target)


def iter_source_files(source_root: Path) -> list[Path]:
    files: list[Path] = []
    for item in sorted(source_root.rglob("*"), key=lambda p: p.as_posix().lower()):
        if any(should_skip(Path(part)) for part in item.relative_to(source_root).parts):
            continue
        if item.is_file():
            files.append(item)
    return files


def iter_source_items(source_root: Path) -> list[Path]:
    return [item for item in sorted(source_root.iterdir(), key=lambda p: p.name.lower()) if not should_skip(item)]


def default_backup_dir(global_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return global_root / ".codexai-backups" / f"sync-{timestamp}"


def backup_existing(target: Path, global_root: Path, backup_root: Path) -> str:
    relative = relative_posix(global_root, target)
    backup_path = backup_root / relative
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup_path)
    return relative


def sync(source_root: Path, global_root: Path, dry_run: bool = True, backup_dir: Path | None = None) -> dict[str, Any]:
    if not source_root.exists() or not source_root.is_dir():
        raise FileNotFoundError(f"Source skills root does not exist or is not a directory: {source_root}")
    planned_items = [item.name for item in iter_source_items(source_root)]
    source_files = iter_source_files(source_root)
    planned_files: list[str] = []
    copied_files: list[str] = []
    changed_files: list[str] = []
    unchanged_files: list[str] = []
    backed_up_files: list[str] = []
    protected_skipped: list[str] = []
    backup_root = backup_dir or default_backup_dir(global_root)

    for source in source_files:
        rel = relative_posix(source_root, source)
        if is_protected(rel):
            protected_skipped.append(rel)
            continue
        target = global_root / rel
        planned_files.append(rel)
        if target.exists() and files_equal(source, target):
            unchanged_files.append(rel)
            continue
        changed_files.append(rel)
        if dry_run:
            continue
        if target.exists() and target.is_file():
            backed_up_files.append(backup_existing(target, global_root, backup_root))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied_files.append(rel)
    return {
        "status": "dry_run" if dry_run else "synced",
        "source_root": str(source_root),
        "global_root": str(global_root),
        "items": planned_items,
        "items_count": len(planned_items),
        "planned_files": planned_files,
        "planned_files_count": len(planned_files),
        "changed_files": changed_files,
        "changed_files_count": len(changed_files),
        "copied_files": copied_files,
        "copied_files_count": len(copied_files),
        "unchanged_files_count": len(unchanged_files),
        "protected_skipped": protected_skipped,
        "protected_skipped_count": len(protected_skipped),
        "backup_dir": str(backup_root) if (not dry_run and backed_up_files) else "",
        "backed_up_files": backed_up_files,
        "protected_system_policy": "skip built-in .system skills and marker files",
    }


def restore_backup(backup_dir: Path, global_root: Path, dry_run: bool = True) -> dict[str, Any]:
    if not backup_dir.exists() or not backup_dir.is_dir():
        raise FileNotFoundError(f"Backup directory does not exist: {backup_dir}")
    restored: list[str] = []
    planned: list[str] = []
    for source in sorted(backup_dir.rglob("*"), key=lambda p: p.as_posix().lower()):
        if not source.is_file():
            continue
        rel = relative_posix(backup_dir, source)
        planned.append(rel)
        if dry_run:
            continue
        target = global_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        restored.append(rel)
    return {
        "status": "dry_run" if dry_run else "restored",
        "backup_dir": str(backup_dir),
        "global_root": str(global_root),
        "planned_files": planned,
        "planned_files_count": len(planned),
        "restored_files": restored,
        "restored_files_count": len(restored),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync CodexAI skills to global Codex skills root.")
    parser.add_argument("--source-root", default="", help="Source skills root. Defaults to this script's skills root")
    parser.add_argument("--global-root", default="", help="Global skills root. Defaults to USERPROFILE/HOME .codex/skills")
    parser.add_argument("--apply", action="store_true", help="Actually copy files. Default is dry-run.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied. This is the default.")
    parser.add_argument("--backup-dir", default="", help="Backup directory for overwritten files when --apply is used")
    parser.add_argument("--restore", default="", help="Restore files from a previous backup directory")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        source_root = Path(args.source_root).expanduser().resolve() if args.source_root else default_source_root()
        global_root = Path(args.global_root).expanduser().resolve() if args.global_root else default_global_root()
        dry_run = not args.apply or args.dry_run
        if args.restore:
            payload = restore_backup(Path(args.restore).expanduser().resolve(), global_root, dry_run=dry_run)
        elif not dry_run:
            global_root.mkdir(parents=True, exist_ok=True)
            backup_dir = Path(args.backup_dir).expanduser().resolve() if args.backup_dir else None
            payload = sync(source_root, global_root, dry_run=False, backup_dir=backup_dir)
        else:
            payload = sync(source_root, global_root, dry_run=True)
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    if args.format == "text":
        if payload["status"] == "restored":
            print(f"{payload['status']}: {payload['restored_files_count']} file(s) restored to {payload['global_root']}")
        else:
            print(
                f"{payload['status']}: {payload.get('changed_files_count', 0)} changed file(s), "
                f"{payload.get('protected_skipped_count', 0)} protected skipped, "
                f"{payload.get('items_count', 0)} top-level item(s) from {payload.get('source_root', '')} -> {payload['global_root']}"
            )
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
