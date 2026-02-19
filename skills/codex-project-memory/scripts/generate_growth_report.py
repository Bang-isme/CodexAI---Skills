#!/usr/bin/env python3
"""
Generate developer growth report from feedback, sessions, and skill usage logs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


CATEGORY_RECOMMENDATIONS = {
    "logic": "Add regression tests for edge cases and validate business rules before final output.",
    "performance": "Profile hotspots first, then refactor high-cost functions and query paths.",
    "security": "Harden input validation/auth checks and add a security-focused review checklist.",
    "architecture": "Review prior decisions and align new changes to established module boundaries.",
    "style": "Run style checks earlier and align generated code to nearby project conventions.",
    "naming": "Adopt project-profile naming conventions and lint naming consistency in touched files.",
    "other": "Capture recurring issues explicitly and convert them into repeatable review steps.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate developer growth report from local project memory data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python generate_growth_report.py --project-root "d:\\SIP_CS 2"\n'
            '  python generate_growth_report.py --project-root "d:\\SIP_CS 2" --skills-root "C:\\Users\\tranb\\.codex\\skills" --since 30\n'
            "  python generate_growth_report.py --help\n\n"
            'Output:\n  JSON to stdout: {"status":"generated","path":"...","improvement_areas":N,...}'
        ),
    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--skills-root", default=str((Path.home() / ".codex" / "skills").resolve()), help="Skills root path")
    parser.add_argument("--since", default="30", help="Days count or ISO date/datetime")
    parser.add_argument("--output", default="", help="Custom output file path")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def parse_since(value: str) -> datetime:
    raw = value.strip()
    if not raw:
        return datetime.now() - timedelta(days=30)
    if raw.isdigit():
        return datetime.now() - timedelta(days=int(raw))
    for candidate in [raw, raw.replace("Z", "+00:00")]:
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    try:
        return datetime.combine(date.fromisoformat(raw), datetime.min.time())
    except ValueError:
        raise ValueError(f"Invalid --since value: {value}")


def parse_date_text(raw: str) -> Optional[datetime]:
    text = raw.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        return datetime.combine(date.fromisoformat(text[:10]), datetime.min.time())
    except ValueError:
        return None


def parse_feedback_file(path: Path) -> Dict[str, str]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    date_match = re.search(r"^Date:\s*(.+)$", content, flags=re.MULTILINE)
    category_match = re.search(r"^Category:\s*(.+)$", content, flags=re.MULTILINE)
    severity_match = re.search(r"^Severity:\s*(.+)$", content, flags=re.MULTILINE)
    file_block = re.search(r"^##\s*File\s*$\n(.+?)(?=^##\s|\Z)", content, flags=re.MULTILINE | re.DOTALL)

    return {
        "date": (date_match.group(1).strip() if date_match else path.name[:10]),
        "category": (category_match.group(1).strip().lower() if category_match else "other"),
        "severity": (severity_match.group(1).strip().lower() if severity_match else "moderate"),
        "file": (file_block.group(1).strip() if file_block else "unknown"),
    }


def parse_session_file(path: Path) -> Dict[str, int]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    commits = 0
    files_changed = 0
    plus_lines = 0
    minus_lines = 0

    match_commits = re.search(r"^- Commits:\s*(\d+)", content, flags=re.MULTILINE)
    match_files = re.search(r"^- Files changed:\s*(\d+)", content, flags=re.MULTILINE)
    match_lines = re.search(r"^- Lines:\s*\+(\d+)\s*/\s*-(\d+)", content, flags=re.MULTILINE)
    if match_commits:
        commits = int(match_commits.group(1))
    if match_files:
        files_changed = int(match_files.group(1))
    if match_lines:
        plus_lines = int(match_lines.group(1))
        minus_lines = int(match_lines.group(2))

    return {
        "commits": commits,
        "files_changed": files_changed,
        "plus_lines": plus_lines,
        "minus_lines": minus_lines,
    }


def read_usage_entries(path: Path, since_dt: datetime, warnings: List[str]) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    if not path.exists():
        return entries

    for idx, raw in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            warnings.append(f"Malformed usage line skipped at {path.name}:{idx}")
            continue
        if not isinstance(payload, dict):
            continue

        skill_name = str(payload.get("skill") or payload.get("skill_name") or "").strip()
        outcome = str(payload.get("outcome") or payload.get("result") or "").strip().lower()
        date_raw = str(payload.get("date") or "").strip()
        parsed_date = parse_date_text(date_raw)
        if not skill_name or not outcome:
            continue
        if parsed_date and parsed_date < since_dt:
            continue
        entries.append(
            {
                "skill": skill_name,
                "outcome": outcome,
            }
        )
    return entries


def impact_level(count: int) -> str:
    if count >= 5:
        return "high"
    if count >= 2:
        return "medium"
    return "low"


def ensure_output_path(project_root: Path, output_arg: str) -> Path:
    if output_arg.strip():
        output_path = Path(output_arg).expanduser()
        if not output_path.is_absolute():
            output_path = (project_root / output_path).resolve()
        return output_path

    output_dir = (project_root / ".codex" / "growth-reports").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / f"{date.today().isoformat()}.md"
    if not base.exists():
        return base
    index = 2
    while True:
        candidate = output_dir / f"{date.today().isoformat()}-{index}.md"
        if not candidate.exists():
            return candidate
        index += 1


def build_report(
    since_dt: datetime,
    feedback_by_category: Counter[str],
    feedback_count: int,
    sessions_count: int,
    commits_total: int,
    files_total: int,
    plus_lines: int,
    minus_lines: int,
    skill_stats: Dict[str, Dict[str, float]],
) -> Tuple[str, int]:
    today = date.today().isoformat()
    period = f"{since_dt.date().isoformat()} to {today}"
    lines: List[str] = [
        "# Developer Growth Report",
        f"Period: {period}",
        "",
        "## Activity Summary",
        f"- Sessions: {sessions_count}",
        f"- Total commits: {commits_total}",
        f"- Files changed: {files_total}",
        f"- Lines: +{plus_lines} / -{minus_lines}",
        "",
        "## Improvement Areas (Prioritized)",
    ]

    ranked = [(cat, count) for cat, count in feedback_by_category.most_common() if count > 0]
    improvement_areas = 0
    if not ranked:
        lines.extend(
            [
                "- No data yet",
                "  - Evidence: No feedback entries matched this period.",
                "  - Impact: low",
                "  - Recommendation: Keep logging feedback to unlock personalized growth insights.",
            ]
        )
    else:
        for idx, (category, count) in enumerate(ranked[:3], start=1):
            improvement_areas += 1
            impact = impact_level(count)
            recommendation = CATEGORY_RECOMMENDATIONS.get(category, CATEGORY_RECOMMENDATIONS["other"])
            lines.extend(
                [
                    f"### {idx}. {category.title()}",
                    f"- Evidence: {count} feedback items in '{category}' category.",
                    f"- Impact: {impact}",
                    f"- Recommendation: {recommendation}",
                    "",
                ]
            )

    lines.append("## Strengths Observed")
    if skill_stats:
        best_skill = max(skill_stats.items(), key=lambda item: (item[1]["success_rate"], item[1]["used"]))[0]
        lines.append(f"- Highest skill success rate: {best_skill}")
    else:
        lines.append("- No skill usage data yet")

    if feedback_count > 0:
        least_category = min((item for item in feedback_by_category.items() if item[1] > 0), key=lambda x: x[1])[0]
        lines.append(f"- Lowest recurring feedback area: {least_category}")
    else:
        lines.append("- No feedback data yet")
    lines.append("")

    lines.append("## Skill Effectiveness")
    lines.append("| Skill | Used | Success Rate |")
    lines.append("|---|---|---|")
    if skill_stats:
        for skill in sorted(skill_stats.keys()):
            stat = skill_stats[skill]
            rate_percent = f"{round(stat['success_rate'] * 100, 1)}%"
            lines.append(f"| {skill} | {int(stat['used'])} | {rate_percent} |")
    else:
        lines.append("| No data | 0 | 0% |")
    lines.append("")

    lines.extend(
        [
            "## Action Items",
            "1. Address the top improvement area with one concrete refactor or guardrail this week.",
            "2. Keep logging feedback after AI-generated changes to improve signal quality.",
            "3. Review skill usage report weekly and tune low-performing skill instructions.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n", improvement_areas


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    skills_root = Path(args.skills_root).expanduser().resolve()

    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "path": "", "message": f"Project root does not exist or is not a directory: {project_root}"})
        return 1

    try:
        since_dt = parse_since(args.since)
    except ValueError as exc:
        emit({"status": "error", "path": "", "message": str(exc)})
        return 1

    warnings: List[str] = []

    feedback_dir = project_root / ".codex" / "feedback"
    sessions_dir = project_root / ".codex" / "sessions"
    usage_file = skills_root / ".analytics" / "usage-log.jsonl"

    feedback_by_category: Counter[str] = Counter()
    feedback_count = 0
    if feedback_dir.exists():
        for file_path in sorted(feedback_dir.glob("*.md")):
            try:
                parsed = parse_feedback_file(file_path)
            except OSError as exc:
                warnings.append(f"Feedback parse skipped for {file_path.name}: {exc}")
                continue
            parsed_date = parse_date_text(parsed["date"])
            if parsed_date and parsed_date < since_dt:
                continue
            feedback_by_category[parsed["category"]] += 1
            feedback_count += 1

    sessions_count = 0
    commits_total = 0
    files_total = 0
    plus_lines = 0
    minus_lines = 0
    if sessions_dir.exists():
        for file_path in sorted(sessions_dir.glob("*.md")):
            try:
                session_date = parse_date_text(file_path.stem[:10])
                if session_date and session_date < since_dt:
                    continue
                stats = parse_session_file(file_path)
            except OSError as exc:
                warnings.append(f"Session parse skipped for {file_path.name}: {exc}")
                continue
            sessions_count += 1
            commits_total += stats["commits"]
            files_total += stats["files_changed"]
            plus_lines += stats["plus_lines"]
            minus_lines += stats["minus_lines"]

    usage_entries = read_usage_entries(usage_file, since_dt, warnings)
    skill_counter: Dict[str, Counter[str]] = defaultdict(Counter)
    for row in usage_entries:
        skill = row["skill"]
        outcome = row["outcome"]
        skill_counter[skill]["used"] += 1
        if outcome in {"success", "partial", "failed"}:
            skill_counter[skill][outcome] += 1

    skill_stats: Dict[str, Dict[str, float]] = {}
    for skill_name, counts in skill_counter.items():
        used = float(counts.get("used", 0))
        success = float(counts.get("success", 0))
        success_rate = (success / used) if used else 0.0
        skill_stats[skill_name] = {"used": used, "success_rate": success_rate}

    report_text, area_count = build_report(
        since_dt=since_dt,
        feedback_by_category=feedback_by_category,
        feedback_count=feedback_count,
        sessions_count=sessions_count,
        commits_total=commits_total,
        files_total=files_total,
        plus_lines=plus_lines,
        minus_lines=minus_lines,
        skill_stats=skill_stats,
    )

    try:
        output_path = ensure_output_path(project_root, args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_text, encoding="utf-8", newline="\n")
    except PermissionError as exc:
        emit({"status": "error", "path": "", "message": f"Permission denied: {exc}"})
        return 1
    except OSError as exc:
        emit({"status": "error", "path": "", "message": f"I/O failure: {exc}"})
        return 1

    payload: Dict[str, object] = {
        "status": "generated",
        "path": output_path.as_posix(),
        "improvement_areas": area_count,
        "sessions_analyzed": sessions_count,
    }
    if warnings:
        payload["warnings"] = warnings
    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
