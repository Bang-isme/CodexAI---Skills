#!/usr/bin/env python3
"""
Generate a user-friendly markdown changelog from git commit history.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple


CATEGORY_ORDER = [
    ("breaking_changes", "Breaking Changes"),
    ("features", "Features"),
    ("bug_fixes", "Bug Fixes"),
    ("improvements", "Improvements"),
    ("documentation", "Documentation"),
]

SKIP_PREFIXES = ("chore", "merge", "bump")
TEST_PREFIXES = ("test",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate user-facing changelog markdown from git commits.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python generate_changelog.py --project-root "d:\\SIP_CS 2" --since "2026-02-01"\n'
            '  python generate_changelog.py --project-root "d:\\SIP_CS 2" --version "v1.2.0" --output ".codex/changelog.md"\n'
            "  python generate_changelog.py --help\n\n"
            'Output:\n  JSON to stdout: {"status":"generated","version":"...","total_commits":N,...}'
        ),
    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--since", default="", help="Date/tag/range selector; default uses last tag or 30 days")
    parser.add_argument("--version", default="", help="Release version label")
    parser.add_argument("--output", default="", help="Output markdown file path (optional)")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=True, indent=2))


def run_git(project_root: Path, args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def git_ready(project_root: Path) -> bool:
    version = run_git(project_root, ["--version"])
    if version.returncode != 0:
        return False
    inside = run_git(project_root, ["rev-parse", "--is-inside-work-tree"])
    return inside.returncode == 0 and inside.stdout.strip().lower() == "true"


def latest_tag(project_root: Path) -> Optional[str]:
    proc = run_git(project_root, ["describe", "--tags", "--abbrev=0"])
    if proc.returncode != 0:
        return None
    tag = proc.stdout.strip()
    return tag or None


def build_log_args(project_root: Path, since_arg: str) -> Tuple[List[str], str]:
    since_text = since_arg.strip()
    if since_text:
        if ".." in since_text:
            return ["log", "--oneline", "--no-merges", since_text], since_text
        return ["log", "--oneline", "--no-merges", f"--since={since_text}"], since_text

    tag = latest_tag(project_root)
    if tag:
        range_spec = f"{tag}..HEAD"
        return ["log", "--oneline", "--no-merges", range_spec], range_spec

    fallback = "30 days ago"
    return ["log", "--oneline", "--no-merges", f"--since={fallback}"], fallback


def parse_commit_line(line: str) -> Optional[Tuple[str, str]]:
    raw = line.strip()
    if not raw:
        return None
    parts = raw.split(" ", 1)
    if len(parts) != 2:
        return None
    return parts[0], parts[1].strip()


def normalize_subject(subject: str) -> str:
    cleaned = re.sub(r"^\s*(?:[A-Za-z]+(?:\([^)]*\))?!?:)\s*", "", subject.strip())
    cleaned = cleaned.strip()
    if not cleaned:
        return subject.strip()
    return cleaned[0].upper() + cleaned[1:]


def classify_subject(subject: str) -> Optional[str]:
    lowered = subject.lower().strip()
    if not lowered:
        return None

    if "breaking" in subject or "breaking" in lowered:
        return "breaking_changes"

    if any(lowered.startswith(prefix) for prefix in SKIP_PREFIXES):
        return None
    if any(lowered.startswith(prefix) for prefix in TEST_PREFIXES):
        return "tests"

    if any(word in lowered for word in ["feat", "add", "new"]):
        return "features"
    if any(word in lowered for word in ["fix", "bug", "patch", "resolve"]):
        return "bug_fixes"
    if any(word in lowered for word in ["improve", "update", "enhance", "refactor"]):
        return "improvements"
    if any(word in lowered for word in ["doc", "readme", "comment"]):
        return "documentation"
    return "improvements"


def build_markdown(version: str, categories: Dict[str, List[str]]) -> str:
    today = date.today().isoformat()
    heading = version.strip() if version.strip() else "Unreleased"
    lines: List[str] = [f"## {heading} - {today}", ""]
    rendered_any = False
    for key, title in CATEGORY_ORDER:
        items = categories.get(key, [])
        if not items:
            continue
        rendered_any = True
        lines.append(f"### {title}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    if not rendered_any:
        lines.append("- No user-visible changes in the selected range.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_output(content: str, output_arg: str, project_root: Path) -> Optional[str]:
    if not output_arg.strip():
        return None
    output_path = Path(output_arg).expanduser()
    if not output_path.is_absolute():
        output_path = (project_root / output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8", newline="\n")
    return output_path.as_posix()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    if not git_ready(project_root):
        emit({"status": "error", "message": "Git repository not available for changelog generation"})
        return 1

    log_args, effective_since = build_log_args(project_root, args.since)
    log_proc = run_git(project_root, log_args)
    if log_proc.returncode != 0:
        detail = (log_proc.stderr or log_proc.stdout).strip() or "git log failed"
        emit({"status": "error", "message": detail, "since": effective_since})
        return 1

    categories: Dict[str, List[str]] = {key: [] for key, _ in CATEGORY_ORDER}
    counts: Dict[str, int] = {key: 0 for key, _ in CATEGORY_ORDER}
    total_commits = 0

    for raw_line in log_proc.stdout.splitlines():
        parsed = parse_commit_line(raw_line)
        if not parsed:
            continue
        _, subject = parsed
        label = classify_subject(subject)
        if label is None:
            continue
        if label == "tests":
            continue
        categories.setdefault(label, []).append(normalize_subject(subject))
        counts[label] = counts.get(label, 0) + 1
        total_commits += 1

    markdown = build_markdown(args.version, categories)

    try:
        output_path = write_output(markdown, args.output, project_root)
    except PermissionError as exc:
        emit({"status": "error", "message": f"Permission denied: {exc}"})
        return 1
    except OSError as exc:
        emit({"status": "error", "message": f"I/O failure: {exc}"})
        return 1

    payload: Dict[str, object] = {
        "status": "generated",
        "version": args.version.strip() or "Unreleased",
        "since": effective_since,
        "total_commits": total_commits,
        "categories": counts,
        "path": output_path or "",
        "changelog_markdown": markdown,
    }
    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
