#!/usr/bin/env python3
"""
Generate a resumable session summary from committed activity and the current Git working tree.
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
CHECKPOINT_CREATED_PATTERN = re.compile(r"^- Checkpoint created: (.+)$", re.MULTILINE)
SUMMARY_FIELD_PATTERN = re.compile(r"^- ([A-Za-z ]+): (.*)$", re.MULTILINE)
SESSION_PROMPT_MARKERS = (
    "[Fill from the user request]",
    "[in_progress | completed | blocked]",
    "[List verified completed milestones, or None]",
    "[Describe unfinished work and the exact resume point, or None]",
    "[Describe the blocker and needed input, or None]",
    "[List commands actually run and their observed results, or None]",
    "[Add actionable next steps, or None]",
    "[List unresolved questions, or None]",
)
UNRESOLVED_PLACEHOLDER_PATTERN = re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER|FILL ME)\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Generate coding session summary from Git history and working-tree status.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python generate_session_summary.py --project-root <path> --since last-session\n"

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


def summary_field(content: str, field_name: str) -> Optional[str]:
    for match in SUMMARY_FIELD_PATTERN.finditer(content):
        if match.group(1) == field_name:
            return match.group(2).strip()
    return None


def checkpoint_datetime(path: Path, content: Optional[str] = None) -> datetime:
    """Return a fixed checkpoint time, using its filename date for legacy summaries."""
    if content is None:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            content = ""
    match = CHECKPOINT_CREATED_PATTERN.search(content)
    if match:
        parsed = parse_iso_datetime(match.group(1))
        if parsed is not None:
            return parsed
    try:
        return datetime.combine(date.fromisoformat(path.name[:10]), time.min).astimezone()
    except ValueError:
        return datetime.fromtimestamp(path.stat().st_mtime).astimezone()


def summary_is_incomplete(content: str) -> bool:
    if any(marker in content for marker in SESSION_PROMPT_MARKERS):
        return True
    goal = summary_field(content, "Goal")
    if not goal or goal.startswith("["):
        return True
    status = summary_field(content, "Status")
    if status not in {"in_progress", "completed", "blocked"}:
        return True
    required_sections = (
        "Task State",
        "Completed",
        "In Progress",
        "Blocked",
        "Commands Verified",
        "Next Steps",
        "Open Questions",
    )
    for section in required_sections:
        heading = re.search(rf"^## {re.escape(section)}\s*$", content, flags=re.MULTILINE)
        if heading is None:
            return True
        next_heading = re.search(r"^## ", content[heading.end() :], flags=re.MULTILINE)
        section_body = content[heading.end() : heading.end() + next_heading.start()] if next_heading else content[heading.end() :]
        bullet_values = [
            match.group(1).strip()
            for line in section_body.splitlines()
            if (match := re.match(r"^\s*-\s*(.*)$", line)) is not None
        ]
        if not bullet_values or any(
            not value
            or value.startswith("[") and value.endswith("]")
            or UNRESOLVED_PLACEHOLDER_PATTERN.search(value)
            for value in bullet_values
        ):
            return True
    return False


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def session_file_sequence(path: Path) -> int:
    match = re.match(r"^\d{4}-\d{2}-\d{2}(?:-(\d+))?\.md$", path.name)
    return int(match.group(1)) if match and match.group(1) else 1


def resolve_since_datetime(
    since_raw: str,
    output_dir: Path,
    branch: Optional[str] = None,
    git_root: Optional[Path] = None,
    head: Optional[str] = None,
) -> Tuple[datetime, str, Optional[str]]:
    since = since_raw.strip().lower()
    if since == "today":
        today_start = datetime.combine(date.today(), time.min)
        return today_start, today_start.isoformat(sep=" "), None

    if since == "last-session":
        if output_dir.exists():
            files = [
                p
                for p in output_dir.glob("*.md")
                if p.is_file() and p.stat().st_size > 0 and SESSION_FILE_PATTERN.match(p.name)
            ]
            if files and not (branch and git_root):
                raise ValueError("`--since last-session` requires the current Git branch and repository root.")
            if files:
                scoped: List[Tuple[Path, str, datetime, str]] = []
                output_is_repo_local = path_is_within(output_dir, git_root)
                for path in files:
                    try:
                        content = path.read_text(encoding="utf-8")
                    except OSError:
                        continue
                    summary_branch = summary_field(content, "Branch")
                    if summary_branch != branch:
                        continue
                    summary_root = summary_field(content, "Git root")
                    if summary_root:
                        if Path(summary_root).resolve() != git_root.resolve():
                            continue
                    elif not output_is_repo_local:
                        # Older summaries lack repository identity; only trust them
                        # when their directory is inside this repository.
                        continue
                    checkpoint_head = summary_field(content, "HEAD")
                    if checkpoint_head == "unborn":
                        if branch == "detached HEAD":
                            continue
                    elif not (
                        checkpoint_head
                        and re.fullmatch(r"[0-9a-fA-F]{7,64}", checkpoint_head)
                        and head
                        and head != "unborn"
                    ):
                        continue
                    else:
                        ancestry = run_git(
                            git_root,
                            ["merge-base", "--is-ancestor", checkpoint_head, head],
                        )
                        if ancestry is None or ancestry.returncode != 0:
                            continue
                    scoped.append((path, content, checkpoint_datetime(path, content), checkpoint_head))

                if not scoped:
                    raise ValueError(
                        f"No session checkpoint found for branch '{branch}' in '{git_root}'. "
                        "Pass an explicit ISO --since value or create a checkpoint for this branch."
                    )

                latest, latest_content, dt, selected_head = max(
                    scoped,
                    key=lambda item: (
                        item[2].timestamp(),
                        session_file_sequence(item[0]),
                        item[0].name,
                    ),
                )
                if summary_is_incomplete(latest_content):
                    raise ValueError(
                        f"Latest session checkpoint is incomplete: {latest}. "
                        "Fill its task-state and verification prompts, or pass an explicit ISO --since value."
                    )
                return dt, dt.isoformat(sep=" "), selected_head
            if not files:
                fallback = datetime.combine(date.today(), time.min)
                return fallback, fallback.isoformat(sep=" "), None
        fallback = datetime.combine(date.today(), time.min)
        return fallback, fallback.isoformat(sep=" "), None

    parsed = parse_iso_datetime(since_raw)
    if parsed is not None:
        return parsed, since_raw, None

    try:
        parsed_date = date.fromisoformat(since_raw)
        parsed = datetime.combine(parsed_date, time.min)
        return parsed, parsed.isoformat(sep=" "), None
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


def parse_worktree_status(raw: str) -> Dict[str, List[str]]:
    staged: List[str] = []
    unstaged: List[str] = []
    untracked: List[str] = []

    for line in raw.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:]
        if not path:
            continue
        if status == "??":
            untracked.append(path)
            continue
        if status[0] != " ":
            staged.append(path)
        if status[1] != " ":
            unstaged.append(path)

    return {
        "staged": list(dict.fromkeys(staged)),
        "unstaged": list(dict.fromkeys(unstaged)),
        "untracked": list(dict.fromkeys(untracked)),
    }


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
    index = 1
    while True:
        suffix = "" if index == 1 else f"-{index}"
        candidate = output_dir / f"{day}{suffix}.md"
        try:
            with candidate.open("x", encoding="utf-8"):
                pass
            return candidate
        except FileExistsError:
            index += 1


def build_summary_markdown(
    checkpoint_created: datetime,
    history_range: str,
    branch: str,
    git_root: str,
    head: str,
    commits: List[Tuple[str, datetime, str]],
    per_file_stats: Dict[str, Tuple[int, int]],
    modified: Set[str],
    new_files: Set[str],
    deleted: Set[str],
    total_added: int,
    total_deleted: int,
    decisions: List[str],
    working_tree: Dict[str, List[str]],
) -> str:
    lines: List[str] = []
    session_day = date.today().isoformat()
    lines.append(f"# Session Summary: {session_day}")
    lines.append("")
    lines.append("## Overview")
    lines.append(f"- Checkpoint created: {checkpoint_created.isoformat(timespec='seconds')}")
    lines.append(f"- Branch: {branch}")
    lines.append(f"- Git root: {git_root}")
    lines.append(f"- HEAD: {head}")
    lines.append(f"- History range: {history_range}")

    if commits:
        first_dt = min(item[1] for item in commits)
        last_dt = max(item[1] for item in commits)
        duration = f"{first_dt.isoformat(sep=' ', timespec='minutes')} to {last_dt.isoformat(sep=' ', timespec='minutes')}"
    else:
        duration = f"No commits found in {history_range}"

    changed_count = len(modified | new_files | deleted)
    lines.append(f"- Duration: {duration}")
    lines.append(f"- Commits: {len(commits)}")
    lines.append(f"- Files changed: {changed_count}")
    lines.append(f"- Lines: +{total_added} / -{total_deleted}")
    working_tree_files = set(working_tree["staged"] + working_tree["unstaged"] + working_tree["untracked"])
    lines.append(f"- Working tree files: {len(working_tree_files)}")
    lines.append("")

    lines.append("## Task State")
    lines.append("- Goal: [Fill from the user request]")
    lines.append("- Status: [in_progress | completed | blocked]")
    lines.append("")

    for heading, prompt in (
        ("Completed", "List verified completed milestones, or None"),
        ("In Progress", "Describe unfinished work and the exact resume point, or None"),
        ("Blocked", "Describe the blocker and needed input, or None"),
    ):
        lines.append(f"## {heading}")
        lines.append(f"- [{prompt}]")
        lines.append("")

    lines.append("## Recent Commits")
    if commits:
        for commit_hash, commit_dt, subject in commits:
            lines.append(f"- `{commit_hash[:8]}` {commit_dt.date().isoformat()} — {subject}")
    else:
        lines.append("- None")
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

    lines.append("## Working Tree")
    for key, heading in (
        ("staged", "Staged Changes"),
        ("unstaged", "Unstaged Changes"),
        ("untracked", "Untracked Files"),
    ):
        lines.append(f"### {heading}")
        if working_tree[key]:
            lines.extend(f"- {path}" for path in working_tree[key])
        else:
            lines.append("- None")
        lines.append("")

    if not commits:
        lines.append(f"Note: No commits found in {history_range}.")
        lines.append("")

    lines.append("## Decisions Made")
    if decisions:
        lines.extend(decisions)
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Commands Verified")
    lines.append("- [List commands actually run and their observed results, or None]")
    lines.append("")

    lines.append("## Next Steps")
    lines.append("- [Add actionable next steps, or None]")
    lines.append("")

    lines.append("## Open Questions")
    lines.append("- [List unresolved questions, or None]")
    lines.append("")
    return "\n".join(lines)


def generate_summary(project_root: Path, since_raw: str, output_dir: Path) -> Dict[str, object]:
    checkpoint_created = datetime.now().astimezone().replace(microsecond=0)
    branch_result = run_git(project_root, ["branch", "--show-current"])
    if branch_result is None:
        raise RuntimeError("git branch query timed out after 60s")
    if branch_result.returncode != 0:
        raise RuntimeError((branch_result.stderr or branch_result.stdout).strip() or "git branch query failed")
    branch = branch_result.stdout.strip() or "detached HEAD"

    git_root_result = run_git(project_root, ["rev-parse", "--show-toplevel"])
    if git_root_result is None:
        raise RuntimeError("git root query timed out after 60s")
    if git_root_result.returncode != 0:
        raise RuntimeError((git_root_result.stderr or git_root_result.stdout).strip() or "git root query failed")
    git_root = str(Path(git_root_result.stdout.strip()).resolve())

    head_result = run_git(project_root, ["rev-parse", "--short", "HEAD"])
    if head_result is None:
        raise RuntimeError("git HEAD query timed out after 60s")
    head = head_result.stdout.strip() if head_result.returncode == 0 else "unborn"

    since_dt, since_label, since_head = resolve_since_datetime(
        since_raw,
        output_dir,
        branch=branch,
        git_root=Path(git_root),
        head=head,
    )
    since_git = since_dt.isoformat(sep=" ")
    if since_head == "unborn":
        history_range = "all reachable commits (checkpoint HEAD was unborn)"
        git_log_range: List[str] = []
    elif since_head:
        history_range = f"{since_head}..HEAD"
        git_log_range = [history_range]
    else:
        history_range = f"--since {since_label}"
        git_log_range = [f"--since={since_git}"]

    commit_log = run_git(project_root, ["log", *git_log_range, "--pretty=format:%H|%cI|%s"])
    if commit_log is None:
        raise RuntimeError("git log timed out after 60s")
    if commit_log.returncode != 0 and head != "unborn":
        raise RuntimeError((commit_log.stderr or commit_log.stdout).strip() or "git log failed")
    commits = parse_commit_rows(commit_log.stdout) if commit_log.returncode == 0 else []

    numstat_result = run_git(project_root, ["log", *git_log_range, "--pretty=tformat:", "--numstat"])
    if numstat_result is None:
        raise RuntimeError("git log --numstat timed out after 60s")
    if numstat_result.returncode != 0 and head != "unborn":
        raise RuntimeError((numstat_result.stderr or numstat_result.stdout).strip() or "git log --numstat failed")
    per_file_stats, total_added, total_deleted = aggregate_numstat(
        numstat_result.stdout if numstat_result.returncode == 0 else ""
    )

    status_result = run_git(project_root, ["log", *git_log_range, "--pretty=tformat:", "--name-status"])
    if status_result is None:
        raise RuntimeError("git log --name-status timed out after 60s")
    if status_result.returncode != 0 and head != "unborn":
        raise RuntimeError((status_result.stderr or status_result.stdout).strip() or "git log --name-status failed")
    modified, new_files, deleted = aggregate_name_status(
        status_result.stdout if status_result.returncode == 0 else ""
    )

    worktree_result = run_git(project_root, ["status", "--short", "--untracked-files=all"])
    if worktree_result is None:
        raise RuntimeError("git status timed out after 60s")
    if worktree_result.returncode != 0:
        raise RuntimeError((worktree_result.stderr or worktree_result.stdout).strip() or "git status failed")
    working_tree = parse_worktree_status(worktree_result.stdout)

    decisions = parse_decision_entries(project_root, since_dt)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = next_output_file(output_dir)
    content = build_summary_markdown(
        checkpoint_created=checkpoint_created,
        history_range=history_range,
        branch=branch,
        git_root=git_root,
        head=head,
        commits=commits,
        per_file_stats=per_file_stats,
        modified=modified,
        new_files=new_files,
        deleted=deleted,
        total_added=total_added,
        total_deleted=total_deleted,
        decisions=decisions,
        working_tree=working_tree,
    )
    with output_file.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)

    return {
        "status": "generated",
        "path": output_file.as_posix(),
        "branch": branch,
        "git_root": git_root,
        "head": head,
        "history_range": history_range,
        "checkpoint_created": checkpoint_created.isoformat(timespec="seconds"),
        "commits": len(commits),
        "files_changed": len(modified | new_files | deleted),
        "working_tree_files": len(
            set(working_tree["staged"] + working_tree["unstaged"] + working_tree["untracked"])
        ),
        "staged_files": len(working_tree["staged"]),
        "unstaged_files": len(working_tree["unstaged"]),
        "untracked_files": len(working_tree["untracked"]),
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
