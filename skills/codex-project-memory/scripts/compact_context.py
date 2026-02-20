#!/usr/bin/env python3
"""
Compact old project memory files to reduce context footprint.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SESSION_HEADER_RE = re.compile(r"^#\s*Session Summary:\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)
COMMITS_RE = re.compile(r"^- Commits:\s*(\d+)\s*$", re.MULTILINE)
FILES_CHANGED_RE = re.compile(r"^- Files changed:\s*(\d+)\s*$", re.MULTILINE)
DATE_FIELD_RE = re.compile(r"^Date:\s*(.+)$", re.MULTILINE)
CATEGORY_FIELD_RE = re.compile(r"^Category:\s*(.+)$", re.MULTILINE)

FEEDBACK_ARCHIVE_THRESHOLD = 50
MAX_SESSION_KEY_CHANGES = 8
MAX_FEEDBACK_PATTERNS = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compact old memory files under .codex to reduce context load.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python compact_context.py --project-root <path>\n"
            "  python compact_context.py --project-root <path> --dry-run --max-age-days 90 --keep-latest 5\n\n"
            "Output:\n"
            "  JSON to stdout: {\"status\":\"compacted\",\"sessions_archived\":N,\"feedback_archived\":N,"
            "\"decisions_kept\":N,\"bytes_freed\":N}"
        ),
    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--dry-run", action="store_true", help="Preview compaction without writing/deleting files")
    parser.add_argument("--max-age-days", type=int, default=90, help="Archive files older than this many days")
    parser.add_argument("--keep-latest", type=int, default=5, help="Always keep latest N session files")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def parse_iso_date(value: str) -> Optional[date]:
    value = value.strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def parse_date_from_text(text: str) -> Optional[date]:
    for line in text.splitlines():
        candidate = line.strip()
        parsed = parse_iso_date(candidate)
        if parsed:
            return parsed
        token = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", candidate)
        if token:
            parsed = parse_iso_date(token.group(1))
            if parsed:
                return parsed
    return None


def parse_session_date(content: str, fallback_file: Path) -> date:
    match = SESSION_HEADER_RE.search(content)
    if match:
        parsed = parse_iso_date(match.group(1))
        if parsed:
            return parsed
    fallback = parse_iso_date(fallback_file.stem)
    if fallback:
        return fallback
    try:
        return datetime.fromtimestamp(fallback_file.stat().st_mtime, tz=timezone.utc).date()
    except OSError:
        return date.today()


def section_lines(content: str, heading: str) -> List[str]:
    lines = content.splitlines()
    start_idx = -1
    for idx, raw in enumerate(lines):
        if raw.strip() == heading:
            start_idx = idx + 1
            break
    if start_idx < 0:
        return []
    out: List[str] = []
    for idx in range(start_idx, len(lines)):
        line = lines[idx]
        if idx > start_idx and line.startswith("## "):
            break
        out.append(line)
    return out


def extract_key_changes(content: str) -> List[str]:
    change_lines = section_lines(content, "## Changes Made")
    key_changes: List[str] = []
    for raw in change_lines:
        line = raw.strip()
        if not line.startswith("- "):
            continue
        value = line[2:].strip()
        if not value or value.lower() == "none":
            continue
        key_changes.append(value)
        if len(key_changes) >= MAX_SESSION_KEY_CHANGES:
            break
    return key_changes


def parse_session_file(path: Path) -> Dict[str, object]:
    content = safe_read_text(path)
    session_date = parse_session_date(content, path)
    commits = 0
    files_changed = 0
    commits_match = COMMITS_RE.search(content)
    files_changed_match = FILES_CHANGED_RE.search(content)
    if commits_match:
        commits = int(commits_match.group(1))
    if files_changed_match:
        files_changed = int(files_changed_match.group(1))
    key_changes = extract_key_changes(content)
    return {
        "source": path.name,
        "date": session_date.isoformat(),
        "year": session_date.year,
        "commits": commits,
        "files_changed": files_changed,
        "key_changes": key_changes,
    }


def render_session_archive(year: int, entries: List[Dict[str, object]], include_header: bool) -> str:
    lines: List[str] = []
    if include_header:
        lines.append(f"# Session Archive: {year}")
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
    else:
        lines.append(f"## Compaction Batch: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

    sorted_entries = sorted(entries, key=lambda item: str(item["date"]))
    for entry in sorted_entries:
        lines.append(f"## Session: {entry['date']}")
        lines.append(f"- Source: {entry['source']}")
        lines.append(f"- Commits: {entry['commits']}")
        lines.append(f"- Files changed: {entry['files_changed']}")
        lines.append("- Key changes:")
        changes = entry.get("key_changes", [])
        if isinstance(changes, list) and changes:
            for change in changes[:MAX_SESSION_KEY_CHANGES]:
                lines.append(f"  - {change}")
        else:
            lines.append("  - (none captured)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def append_markdown(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = safe_read_text(path)
        sep = "\n" if existing.endswith("\n") else "\n\n"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(sep)
            handle.write(content)
    else:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)


def compact_sessions(
    project_root: Path,
    dry_run: bool,
    max_age_days: int,
    keep_latest: int,
) -> Tuple[int, int]:
    sessions_dir = project_root / ".codex" / "sessions"
    if not sessions_dir.exists() or not sessions_dir.is_dir():
        return 0, 0

    candidates = [path for path in sessions_dir.glob("*.md") if path.is_file()]
    if not candidates:
        return 0, 0

    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    keep_count = max(0, keep_latest)
    keep_set = {path.resolve() for path in candidates[:keep_count]}
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(0, max_age_days))

    to_archive: List[Path] = []
    for path in candidates:
        if path.resolve() in keep_set:
            continue
        file_time = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if file_time <= cutoff:
            to_archive.append(path)

    if not to_archive:
        return 0, 0

    grouped: Dict[int, List[Dict[str, object]]] = defaultdict(list)
    bytes_freed = 0
    for path in to_archive:
        entry = parse_session_file(path)
        grouped[int(entry["year"])].append(entry)
        try:
            bytes_freed += int(path.stat().st_size)
        except OSError:
            pass

    archive_root = sessions_dir / "archive"
    for year, entries in grouped.items():
        archive_path = archive_root / f"{year}-summary.md"
        content = render_session_archive(year, entries, include_header=not archive_path.exists())
        append_markdown(archive_path, content, dry_run=dry_run)

    if not dry_run:
        for path in to_archive:
            try:
                path.unlink()
            except OSError:
                continue

    return len(to_archive), bytes_freed


def parse_feedback_entry(path: Path) -> Dict[str, str]:
    content = safe_read_text(path)
    date_match = DATE_FIELD_RE.search(content)
    category_match = CATEGORY_FIELD_RE.search(content)
    parsed_date = parse_iso_date(date_match.group(1)) if date_match else None
    if not parsed_date:
        parsed_date = parse_iso_date(path.name[:10])
    if not parsed_date:
        parsed_date = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date()

    category = (category_match.group(1).strip().lower() if category_match else "other") or "other"
    lesson_lines = section_lines(content, "## Lesson Learned")
    lesson_text = " ".join(line.strip() for line in lesson_lines if line.strip())
    if not lesson_text:
        lesson_text = f"{category} issue recurring pattern"
    return {
        "date": parsed_date.isoformat(),
        "month": parsed_date.strftime("%Y-%m"),
        "category": category,
        "lesson": lesson_text[:200],
        "source": path.name,
    }


def render_feedback_archive(month: str, entries: List[Dict[str, str]], include_header: bool) -> str:
    lines: List[str] = []
    if include_header:
        lines.append(f"# Feedback Archive: {month}")
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
    else:
        lines.append(f"## Compaction Batch: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

    category_counts: Counter[str] = Counter()
    pattern_counts: Counter[str] = Counter()
    for entry in entries:
        category_counts[entry["category"]] += 1
        lesson = entry["lesson"].strip()
        if lesson:
            pattern_counts[lesson] += 1

    lines.append(f"- Total entries: {len(entries)}")
    lines.append("")
    lines.append("## Category Counts")
    for category, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {category}: {count}")
    lines.append("")

    lines.append("## Top Patterns")
    if pattern_counts:
        rank = 1
        for pattern, count in pattern_counts.most_common(MAX_FEEDBACK_PATTERNS):
            lines.append(f"- {rank}. ({count}) {pattern}")
            rank += 1
    else:
        lines.append("- 1. No recurring pattern captured")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def compact_feedback(project_root: Path, dry_run: bool) -> Tuple[int, int]:
    feedback_dir = project_root / ".codex" / "feedback"
    if not feedback_dir.exists() or not feedback_dir.is_dir():
        return 0, 0

    files = [path for path in feedback_dir.glob("*.md") if path.is_file()]
    if len(files) <= FEEDBACK_ARCHIVE_THRESHOLD:
        return 0, 0

    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    bytes_freed = 0
    for path in files:
        grouped_key = parse_feedback_entry(path)
        grouped[grouped_key["month"]].append(grouped_key)
        try:
            bytes_freed += int(path.stat().st_size)
        except OSError:
            pass

    archive_root = feedback_dir / "archive"
    for month, entries in grouped.items():
        archive_path = archive_root / f"{month}-summary.md"
        content = render_feedback_archive(month, entries, include_header=not archive_path.exists())
        append_markdown(archive_path, content, dry_run=dry_run)

    if not dry_run:
        for path in files:
            try:
                path.unlink()
            except OSError:
                continue

    return len(files), bytes_freed


def count_decisions(project_root: Path) -> int:
    decisions_dir = project_root / ".codex" / "decisions"
    if not decisions_dir.exists() or not decisions_dir.is_dir():
        return 0
    return len([path for path in decisions_dir.glob("*.md") if path.is_file()])


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    try:
        sessions_archived, session_bytes = compact_sessions(
            project_root=project_root,
            dry_run=args.dry_run,
            max_age_days=max(0, int(args.max_age_days)),
            keep_latest=max(0, int(args.keep_latest)),
        )
        feedback_archived, feedback_bytes = compact_feedback(project_root=project_root, dry_run=args.dry_run)
        decisions_kept = count_decisions(project_root)
    except PermissionError as exc:
        emit({"status": "error", "message": f"Permission denied: {exc}"})
        return 1
    except OSError as exc:
        emit({"status": "error", "message": f"I/O failure: {exc}"})
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        emit({"status": "error", "message": f"Unexpected error: {exc}"})
        return 1

    payload = {
        "status": "compacted",
        "sessions_archived": sessions_archived,
        "feedback_archived": feedback_archived,
        "decisions_kept": decisions_kept,
        "bytes_freed": session_bytes + feedback_bytes,
    }
    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
