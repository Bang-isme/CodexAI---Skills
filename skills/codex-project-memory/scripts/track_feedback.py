#!/usr/bin/env python3
"""
Track user feedback for AI-generated code and aggregate trends.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional


CATEGORIES = ["naming", "logic", "style", "performance", "security", "architecture", "other"]
SEVERITIES = ["minor", "moderate", "significant"]

LESSON_BY_CATEGORY = {
    "naming": "Prefer project's naming convention (see project-profile.json)",
    "logic": "Verify edge cases and business logic assumptions before generating",
    "style": "Match existing code style in surrounding context",
    "performance": "Profile before optimizing; avoid premature optimization",
    "security": "Never generate code with hardcoded secrets or unsanitized inputs",
    "architecture": "Follow existing patterns; check decisions/ before proposing new patterns",
    "other": "Review generated code carefully for project-specific requirements",
}

IMPROVEMENT_BY_CATEGORY = {
    "naming": "apply naming checks from project profile before code generation.",
    "logic": "improve edge-case reasoning and business rule validation.",
    "style": "align generated code to surrounding file style.",
    "performance": "review complexity and data access paths before final output.",
    "security": "add stricter security checks before proposing code.",
    "architecture": "consult decision history before suggesting structural changes.",
    "other": "increase project-specific context checks prior to completion.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Track and aggregate user feedback for AI output.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python track_feedback.py --project-root <path> --file <file> --ai-version <text> --user-fix <text> --category <category>\n"

            "  python track_feedback.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--file", default="", help="File fixed by user")
    parser.add_argument("--ai-version", default="", help="Short description of AI-generated version")
    parser.add_argument("--user-fix", default="", help="Short description of user fix")
    parser.add_argument("--category", default="", choices=CATEGORIES, help="Feedback category")
    parser.add_argument("--severity", default="moderate", choices=SEVERITIES, help="Feedback severity")
    parser.add_argument("--aggregate", action="store_true", help="Aggregate feedback summary")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def sanitize_slug(raw: str) -> str:
    lowered = raw.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "feedback"


def build_target_path(base_dir: Path, date_text: str, slug: str) -> Path:
    candidate = base_dir / f"{date_text}-{slug}.md"
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        next_candidate = base_dir / f"{date_text}-{slug}-{index}.md"
        if not next_candidate.exists():
            return next_candidate
        index += 1


def lesson_for_category(category: str) -> str:
    return LESSON_BY_CATEGORY.get(category, LESSON_BY_CATEGORY["other"])


def extract_field(text: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_section(text: str, heading: str) -> str:
    pattern = rf"^##\s*{re.escape(heading)}\s*$\n(.+?)(?=^##\s|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def summarize_fix(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    summary = lines[0]
    return summary[:157] + "..." if len(summary) > 160 else summary


def write_feedback(
    project_root: Path,
    file_path: str,
    ai_version: str,
    user_fix: str,
    category: str,
    severity: str,
) -> Dict[str, object]:
    feedback_dir = project_root / ".codex" / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    slug = sanitize_slug(f"{category}-{Path(file_path).stem}")
    target = build_target_path(feedback_dir, today, slug)

    content = (
        f"# Feedback: {category} issue in {file_path}\n"
        f"Date: {today}\n"
        f"Severity: {severity}\n"
        f"Category: {category}\n\n"
        "## What AI Generated\n"
        f"{ai_version.strip()}\n\n"
        "## What User Fixed\n"
        f"{user_fix.strip()}\n\n"
        "## File\n"
        f"{file_path.strip()}\n\n"
        "## Lesson Learned\n"
        f"{lesson_for_category(category)}\n"
    )

    with target.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)

    return {
        "status": "logged",
        "path": target.as_posix(),
        "file": file_path,
        "category": category,
        "severity": severity,
    }


def parse_feedback_file(path: Path) -> Optional[Dict[str, str]]:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None

    date_text = extract_field(content, "Date") or path.name[:10]
    category = (extract_field(content, "Category") or "other").lower()
    if category not in CATEGORIES:
        category = "other"
    severity = (extract_field(content, "Severity") or "moderate").lower()
    if severity not in SEVERITIES:
        severity = "moderate"
    file_path = extract_section(content, "File") or "unknown"
    user_fix = extract_section(content, "What User Fixed")
    fix_summary = summarize_fix(user_fix)

    return {
        "date": date_text,
        "category": category,
        "severity": severity,
        "file": file_path,
        "fix_summary": fix_summary,
    }


def parse_date_for_sort(value: str) -> datetime:
    value = value.strip()
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(f"{value}T00:00:00")
    except ValueError:
        return datetime.fromtimestamp(0)


def aggregate_feedback(project_root: Path) -> Dict[str, object]:
    feedback_dir = project_root / ".codex" / "feedback"
    if not feedback_dir.exists() or not feedback_dir.is_dir():
        return {
            "total_feedback": 0,
            "by_category": {category: 0 for category in CATEGORIES},
            "by_severity": {severity: 0 for severity in SEVERITIES},
            "top_files": [],
            "recent": [],
            "patterns": "No feedback logged yet. Consider tracking fixes to improve future generations.",
        }

    entries: List[Dict[str, str]] = []
    for file_path in sorted(feedback_dir.glob("*.md")):
        parsed = parse_feedback_file(file_path)
        if parsed:
            entries.append(parsed)

    by_category: Counter[str] = Counter({category: 0 for category in CATEGORIES})
    by_severity: Counter[str] = Counter({severity: 0 for severity in SEVERITIES})
    file_counter: Counter[str] = Counter()

    for entry in entries:
        by_category[entry["category"]] += 1
        by_severity[entry["severity"]] += 1
        file_counter[entry["file"]] += 1

    total = len(entries)
    top_files = [
        {"file": file_path, "count": count}
        for file_path, count in file_counter.most_common(5)
    ]

    recent_sorted = sorted(entries, key=lambda item: parse_date_for_sort(item["date"]), reverse=True)
    recent = [
        {
            "date": item["date"],
            "category": item["category"],
            "file": item["file"],
            "fix_summary": item["fix_summary"],
        }
        for item in recent_sorted[:5]
    ]

    if total == 0:
        pattern_message = "No feedback logged yet. Consider tracking fixes to improve future generations."
    else:
        top_category, top_count = max(by_category.items(), key=lambda item: item[1])
        percentage = round((top_count / total) * 100)
        recommendation = IMPROVEMENT_BY_CATEGORY.get(top_category, IMPROVEMENT_BY_CATEGORY["other"])
        pattern_message = (
            f"Most frequent: {top_category} issues ({percentage}%). "
            f"Consider: {recommendation}"
        )

    return {
        "total_feedback": total,
        "by_category": {category: int(by_category[category]) for category in CATEGORIES},
        "by_severity": {severity: int(by_severity[severity]) for severity in SEVERITIES},
        "top_files": top_files,
        "recent": recent,
        "patterns": pattern_message,
    }


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "path": "", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    if args.aggregate:
        try:
            payload = aggregate_feedback(project_root)
        except OSError as exc:
            emit({"status": "error", "path": "", "message": f"I/O failure: {exc}"})
            return 1
        except Exception as exc:  # pragma: no cover - defensive
            emit({"status": "error", "path": "", "message": f"Unexpected error: {exc}"})
            return 1
        emit(payload)
        return 0

    required = {
        "--file": args.file.strip(),
        "--ai-version": args.ai_version.strip(),
        "--user-fix": args.user_fix.strip(),
        "--category": args.category.strip(),
    }
    missing = [flag for flag, value in required.items() if not value]
    if missing:
        emit({"status": "error", "path": "", "message": f"Missing required arguments for feedback logging: {', '.join(missing)}"})
        return 1

    try:
        payload = write_feedback(
            project_root=project_root,
            file_path=args.file.strip().replace("\\", "/"),
            ai_version=args.ai_version,
            user_fix=args.user_fix,
            category=args.category,
            severity=args.severity,
        )
    except PermissionError as exc:
        emit({"status": "error", "path": "", "message": f"Permission denied: {exc}"})
        return 1
    except OSError as exc:
        emit({"status": "error", "path": "", "message": f"I/O failure: {exc}"})
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        emit({"status": "error", "path": "", "message": f"Unexpected error: {exc}"})
        return 1

    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
