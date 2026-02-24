#!/usr/bin/env python3
"""
Generate end-of-session summary markdown from git activity.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


SESSION_FILE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(?:-\d+)?\.md$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Generate coding session summary.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python generate_session_summary.py --project-root <path> --since today\n"

            "  python generate_session_summary.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--since", default="today", help='ISO datetime, "today", or "last-session"')
    parser.add_argument("--output-dir", default="", help="Output directory (default: <project-root>/.codex/sessions)")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def run_git(project_root: Path, args: List[str]) -> Optional[subprocess.CompletedProcess]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return None


def git_ready(project_root: Path) -> bool:
    version = run_git(project_root, ["--version"])
    if version is None or version.returncode != 0:
        return False
    inside = run_git(project_root, ["rev-parse", "--is-inside-work-tree"])
    if inside is None:
        return False
    return inside.returncode == 0 and inside.stdout.strip().lower() == "true"


def parse_iso_datetime(value: str) -> Optional[datetime]:
    value = value.strip()
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def resolve_since_datetime(since_raw: str, output_dir: Path) -> Tuple[datetime, str]:
    since = since_raw.strip().lower()
    if since == "today":
        today_start = datetime.combine(date.today(), time.min)
        return today_start, today_start.isoformat(sep=" ")

    if since == "last-session":
        if output_dir.exists():
            files = [
                p
                for p in output_dir.glob("*.md")
                if p.is_file() and SESSION_FILE_PATTERN.match(p.name)
            ]
            if files:
                latest = max(files, key=lambda p: p.stat().st_mtime)
                dt = datetime.fromtimestamp(latest.stat().st_mtime)
                return dt, dt.isoformat(sep=" ")
        fallback = datetime.combine(date.today(), time.min)
        return fallback, fallback.isoformat(sep=" ")

    parsed = parse_iso_datetime(since_raw)
    if parsed is not None:
        return parsed, since_raw

    try:
        parsed_date = date.fromisoformat(since_raw)
        parsed = datetime.combine(parsed_date, time.min)
        return parsed, parsed.isoformat(sep=" ")
    except ValueError:
        raise ValueError(f"Invalid --since value: {since_raw}")


def parse_commit_rows(raw: str) -> List[Tuple[str, datetime, str]]:
    commits: List[Tuple[str, datetime, str]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        commit_hash, date_text, subject = parts
        dt = parse_iso_datetime(date_text)
        if dt is None:
            continue
        commits.append((commit_hash, dt, subject))
    return commits


def aggregate_numstat(raw: str) -> Tuple[Dict[str, Tuple[int, int]], int, int]:
    per_file: Dict[str, Tuple[int, int]] = {}
    total_added = 0
    total_deleted = 0
    for line in raw.splitlines():
        row = line.strip()
        if not row:
            continue
        parts = row.split("\t")
        if len(parts) != 3:
            continue
        add_s, del_s, file_path = parts
        added = int(add_s) if add_s.isdigit() else 0
        deleted = int(del_s) if del_s.isdigit() else 0
        total_added += added
        total_deleted += deleted
        old = per_file.get(file_path, (0, 0))
        per_file[file_path] = (old[0] + added, old[1] + deleted)
    return per_file, total_added, total_deleted


def aggregate_name_status(raw: str) -> Tuple[Set[str], Set[str], Set[str]]:
    modified: Set[str] = set()
    new_files: Set[str] = set()
    deleted: Set[str] = set()

    for line in raw.splitlines():
        row = line.strip()
        if not row:
            continue
        parts = row.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        if status.startswith("A"):
            new_files.add(parts[1])
        elif status.startswith("D"):
            deleted.add(parts[1])
        elif status.startswith("R") or status.startswith("C"):
            target = parts[2] if len(parts) >= 3 else parts[-1]
            modified.add(target)
        elif status.startswith("M"):
            modified.add(parts[1])
        else:
            modified.add(parts[-1])

    modified -= new_files
    modified -= deleted
    new_files -= deleted
    return modified, new_files, deleted


def parse_decision_entries(project_root: Path, since_dt: datetime) -> List[str]:
    decisions_dir = project_root / ".codex" / "decisions"
    if not decisions_dir.exists() or not decisions_dir.is_dir():
        return []
    items: List[Tuple[float, str]] = []
    since_ts = since_dt.timestamp()

    for path in decisions_dir.glob("*.md"):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime < since_ts:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        title_match = re.search(r"^#\s*Decision:\s*(.+)$", content, flags=re.MULTILINE)
        date_match = re.search(r"^Date:\s*(.+)$", content, flags=re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        date_text = date_match.group(1).strip() if date_match else path.name[:10]
        items.append((mtime, f"- [{date_text}] {title}"))

    items.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in items]


def next_output_file(output_dir: Path) -> Path:
    day = date.today().isoformat()
    base = output_dir / f"{day}.md"
    if not base.exists():
        return base
    index = 2
    while True:
        candidate = output_dir / f"{day}-{index}.md"
        if not candidate.exists():
            return candidate
        index += 1


def build_summary_markdown(
    since_label: str,
    commits: List[Tuple[str, datetime, str]],
    per_file_stats: Dict[str, Tuple[int, int]],
    modified: Set[str],
    new_files: Set[str],
    deleted: Set[str],
    total_added: int,
    total_deleted: int,
    decisions: List[str],
) -> str:
    lines: List[str] = []
    session_day = date.today().isoformat()
    lines.append(f"# Session Summary: {session_day}")
    lines.append("")
    lines.append("## Overview")

    if commits:
        first_dt = min(item[1] for item in commits)
        last_dt = max(item[1] for item in commits)
        duration = f"{first_dt.isoformat(sep=' ', timespec='minutes')} to {last_dt.isoformat(sep=' ', timespec='minutes')}"
    else:
        duration = f"No commits found since {since_label}"

    changed_count = len(modified | new_files | deleted)
    lines.append(f"- Duration: {duration}")
    lines.append(f"- Commits: {len(commits)}")
    lines.append(f"- Files changed: {changed_count}")
    lines.append(f"- Lines: +{total_added} / -{total_deleted}")
    lines.append("")

    lines.append("## Changes Made")
    lines.append("### Modified")
    if modified:
        for file_path in sorted(modified):
            stats = per_file_stats.get(file_path, (0, 0))
            lines.append(f"- {file_path} (+{stats[0]}/-{stats[1]})")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("### New Files")
    if new_files:
        for file_path in sorted(new_files):
            lines.append(f"- {file_path}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("### Deleted Files")
    if deleted:
        for file_path in sorted(deleted):
            lines.append(f"- {file_path}")
    else:
        lines.append("- None")
    lines.append("")

    if not commits:
        lines.append(f"Note: No commits found since {since_label}.")
        lines.append("")

    lines.append("## Decisions Made")
    if decisions:
        lines.extend(decisions)
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## What's Next")
    lines.append("(to be filled manually or by AI)")
    lines.append("")
    return "\n".join(lines)


def generate_summary(project_root: Path, since_raw: str, output_dir: Path) -> Dict[str, object]:
    since_dt, since_label = resolve_since_datetime(since_raw, output_dir)
    since_git = since_dt.isoformat(sep=" ")

    commit_log = run_git(project_root, ["log", f"--since={since_git}", "--pretty=format:%H|%cI|%s"])
    if commit_log is None:
        raise RuntimeError("git log timed out after 60s")
    if commit_log.returncode != 0:
        raise RuntimeError((commit_log.stderr or commit_log.stdout).strip() or "git log failed")
    commits = parse_commit_rows(commit_log.stdout)

    numstat_result = run_git(project_root, ["log", f"--since={since_git}", "--pretty=tformat:", "--numstat"])
    if numstat_result is None:
        raise RuntimeError("git log --numstat timed out after 60s")
    if numstat_result.returncode != 0:
        raise RuntimeError((numstat_result.stderr or numstat_result.stdout).strip() or "git log --numstat failed")
    per_file_stats, total_added, total_deleted = aggregate_numstat(numstat_result.stdout)

    status_result = run_git(project_root, ["log", f"--since={since_git}", "--pretty=tformat:", "--name-status"])
    if status_result is None:
        raise RuntimeError("git log --name-status timed out after 60s")
    if status_result.returncode != 0:
        raise RuntimeError((status_result.stderr or status_result.stdout).strip() or "git log --name-status failed")
    modified, new_files, deleted = aggregate_name_status(status_result.stdout)

    decisions = parse_decision_entries(project_root, since_dt)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = next_output_file(output_dir)
    content = build_summary_markdown(
        since_label=since_label,
        commits=commits,
        per_file_stats=per_file_stats,
        modified=modified,
        new_files=new_files,
        deleted=deleted,
        total_added=total_added,
        total_deleted=total_deleted,
        decisions=decisions,
    )
    with output_file.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)

    return {
        "status": "generated",
        "path": output_file.as_posix(),
        "commits": len(commits),
        "files_changed": len(modified | new_files | deleted),
    }


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "path": "", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else (project_root / ".codex" / "sessions").resolve()
    )

    if not git_ready(project_root):
        emit({"status": "error", "path": "", "message": "Git required for session summary"})
        return 1

    try:
        result = generate_summary(project_root, args.since, output_dir)
    except ValueError as exc:
        emit({"status": "error", "path": "", "message": str(exc)})
        return 1
    except PermissionError as exc:
        emit({"status": "error", "path": "", "message": f"Permission denied: {exc}"})
        return 1
    except OSError as exc:
        emit({"status": "error", "path": "", "message": f"I/O failure: {exc}"})
        return 1
    except RuntimeError as exc:
        emit({"status": "error", "path": "", "message": str(exc)})
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        emit({"status": "error", "path": "", "message": f"Unexpected error: {exc}"})
        return 1

    emit(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
