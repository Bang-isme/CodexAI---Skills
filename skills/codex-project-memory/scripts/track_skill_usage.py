#!/usr/bin/env python3
"""
Track and report Codex skill usage effectiveness.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


OUTCOMES = {"success", "partial", "failed"}
DEFAULT_SKILLS_ROOT = (Path.home() / ".codex" / "skills").resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track and report skill usage analytics.")
    parser.add_argument("--skills-root", default=str(DEFAULT_SKILLS_ROOT), help="Skills root path")
    parser.add_argument("--record", action="store_true", help="Record single skill usage entry")
    parser.add_argument("--skill", default="", help="Skill name for --record")
    parser.add_argument("--task", default="", help="Task description for --record")
    parser.add_argument("--outcome", default="", choices=sorted(OUTCOMES), help="Outcome for --record")
    parser.add_argument("--notes", default="", help="Optional notes for --record")
    parser.add_argument("--report", action="store_true", help="Generate usage summary report")
    parser.add_argument("--data-dir", default="", help="Analytics data directory (default: <skills-root>/.analytics)")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def estimate_duration(task_text: str) -> str:
    length = len(task_text.strip())
    if length <= 50:
        return "quick"
    if length <= 140:
        return "medium"
    return "deep"


def resolve_data_dir(skills_root: Path, data_dir_arg: str) -> Path:
    return Path(data_dir_arg).expanduser().resolve() if data_dir_arg else (skills_root / ".analytics").resolve()


def parse_date(value: str) -> Optional[date]:
    value = value.strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None


def safe_read_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def list_known_skills(skills_root: Path) -> List[str]:
    if not skills_root.exists() or not skills_root.is_dir():
        return []
    known: List[str] = []
    for item in sorted(skills_root.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_dir():
            continue
        if item.name.startswith("."):
            continue
        if (item / "SKILL.md").exists():
            known.append(item.name)
    return known


def record_usage(
    skills_root: Path,
    data_dir: Path,
    skill: str,
    task: str,
    outcome: str,
    notes: str,
) -> Dict[str, object]:
    data_dir.mkdir(parents=True, exist_ok=True)
    log_path = data_dir / "usage-log.jsonl"

    entry = {
        "date": date.today().isoformat(),
        "skill": skill.strip(),
        "task": task.strip(),
        "outcome": outcome.strip(),
        "notes": notes.strip(),
        "duration_estimate": estimate_duration(task),
    }

    with log_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {
        "status": "recorded",
        "path": log_path.as_posix(),
        "entry": entry,
        "skills_root": skills_root.as_posix(),
    }


def load_usage_entries(log_path: Path) -> Tuple[List[Dict[str, object]], List[str]]:
    entries: List[Dict[str, object]] = []
    warnings: List[str] = []

    if not log_path.exists():
        return entries, warnings

    for line_no, raw in enumerate(safe_read_lines(log_path), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            warnings.append(f"Malformed JSON line skipped at {log_path.name}:{line_no}")
            continue
        if not isinstance(payload, dict):
            warnings.append(f"Non-object JSON line skipped at {log_path.name}:{line_no}")
            continue
        skill = str(payload.get("skill", "")).strip()
        task = str(payload.get("task", "")).strip()
        outcome = str(payload.get("outcome", "")).strip().lower()
        date_text = str(payload.get("date", "")).strip()
        if not skill or not task or outcome not in OUTCOMES:
            warnings.append(f"Incomplete entry skipped at {log_path.name}:{line_no}")
            continue
        if parse_date(date_text) is None:
            warnings.append(f"Invalid date skipped at {log_path.name}:{line_no}")
            continue
        entries.append(
            {
                "date": date_text,
                "skill": skill,
                "task": task,
                "outcome": outcome,
                "notes": str(payload.get("notes", "")).strip(),
                "duration_estimate": str(payload.get("duration_estimate", "")).strip(),
            }
        )
    return entries, warnings


def compute_direction(entries: List[Dict[str, object]]) -> str:
    if len(entries) < 4:
        return "stable"
    sorted_entries = sorted(entries, key=lambda item: str(item["date"]))
    mid = len(sorted_entries) // 2
    early = sorted_entries[:mid]
    late = sorted_entries[mid:]

    def success_rate(chunk: List[Dict[str, object]]) -> float:
        if not chunk:
            return 0.0
        score = sum(1 for item in chunk if str(item["outcome"]) == "success")
        return score / len(chunk)

    early_rate = success_rate(early)
    late_rate = success_rate(late)
    diff = late_rate - early_rate
    if diff > 0.08:
        return "improving"
    if diff < -0.08:
        return "declining"
    return "stable"


def build_recommendations(
    by_skill: Dict[str, Dict[str, object]],
    unused_skills: List[str],
) -> List[str]:
    recommendations: List[str] = []
    for skill_name, stats in by_skill.items():
        uses = int(stats["uses"])
        failed = int(stats["failed"])
        success_rate = float(stats["success_rate"])
        if uses >= 3 and (failed > 0 or success_rate < 0.8):
            fail_rate = round((failed / uses) * 100)
            recommendations.append(
                f"{skill_name} has {fail_rate}% failure rate — review failed task notes for improvement areas."
            )

    for skill in unused_skills[:3]:
        recommendations.append(f"{skill} has 0 usages — consider promoting or deprecating.")

    if not recommendations:
        recommendations.append("No critical gaps detected. Continue collecting usage data for stronger trends.")
    return recommendations[:5]


def report_usage(skills_root: Path, data_dir: Path) -> Dict[str, object]:
    log_path = data_dir / "usage-log.jsonl"
    entries, warnings = load_usage_entries(log_path)
    known_skills = list_known_skills(skills_root)

    if not entries:
        payload: Dict[str, object] = {
            "status": "report_ready",
            "total_usages": 0,
            "period": {"from": "", "to": ""},
            "by_skill": {},
            "unused_skills": known_skills,
            "most_effective": "",
            "least_effective": "",
            "recommendations": ["No usage data yet. Record skill usage to generate recommendations."],
            "trends": {"overall_success_rate": 0.0, "direction": "stable"},
        }
        if warnings:
            payload["warnings"] = sorted(dict.fromkeys(warnings))
        return payload

    by_skill_counter: Dict[str, Counter[str]] = {}
    used_skills: set[str] = set()
    date_values: List[date] = []

    for entry in entries:
        skill = str(entry["skill"])
        outcome = str(entry["outcome"])
        used_skills.add(skill)
        by_skill_counter.setdefault(skill, Counter({"success": 0, "partial": 0, "failed": 0, "uses": 0}))
        by_skill_counter[skill]["uses"] += 1
        by_skill_counter[skill][outcome] += 1
        parsed = parse_date(str(entry["date"]))
        if parsed:
            date_values.append(parsed)

    by_skill: Dict[str, Dict[str, object]] = {}
    for skill_name in sorted(by_skill_counter.keys()):
        stats = by_skill_counter[skill_name]
        uses = int(stats["uses"])
        success = int(stats["success"])
        partial = int(stats["partial"])
        failed = int(stats["failed"])
        success_rate = (success / uses) if uses else 0.0
        by_skill[skill_name] = {
            "uses": uses,
            "success": success,
            "partial": partial,
            "failed": failed,
            "success_rate": round(success_rate, 2),
        }

    ranked = sorted(
        by_skill.items(),
        key=lambda item: (float(item[1]["success_rate"]), int(item[1]["uses"])),
    )
    least_effective = ranked[0][0] if ranked else ""
    most_effective = ranked[-1][0] if ranked else ""

    total = len(entries)
    success_total = sum(1 for item in entries if str(item["outcome"]) == "success")
    overall_success_rate = round(success_total / total, 2) if total else 0.0
    direction = compute_direction(entries)

    period_from = min(date_values).isoformat() if date_values else ""
    period_to = max(date_values).isoformat() if date_values else ""
    unused_skills = sorted(skill for skill in known_skills if skill not in used_skills)

    payload = {
        "status": "report_ready",
        "total_usages": total,
        "period": {"from": period_from, "to": period_to},
        "by_skill": by_skill,
        "unused_skills": unused_skills,
        "most_effective": most_effective,
        "least_effective": least_effective,
        "recommendations": build_recommendations(by_skill, unused_skills),
        "trends": {
            "overall_success_rate": overall_success_rate,
            "direction": direction,
        },
    }
    if warnings:
        payload["warnings"] = sorted(dict.fromkeys(warnings))
    return payload


def main() -> int:
    args = parse_args()
    skills_root = Path(args.skills_root).expanduser().resolve()
    data_dir = resolve_data_dir(skills_root, args.data_dir)

    if not args.record and not args.report:
        emit({"status": "error", "message": "Choose at least one mode: --record or --report."})
        return 1

    if args.record:
        required = {
            "--skill": args.skill.strip(),
            "--task": args.task.strip(),
            "--outcome": args.outcome.strip().lower(),
        }
        missing = [flag for flag, value in required.items() if not value]
        if missing:
            emit({"status": "error", "message": f"Missing required arguments for --record: {', '.join(missing)}"})
            return 1
        if required["--outcome"] not in OUTCOMES:
            emit({"status": "error", "message": f"Invalid --outcome value: {required['--outcome']}"})
            return 1

        try:
            payload = record_usage(
                skills_root=skills_root,
                data_dir=data_dir,
                skill=args.skill.strip(),
                task=args.task.strip(),
                outcome=required["--outcome"],
                notes=args.notes,
            )
        except PermissionError as exc:
            emit({"status": "error", "message": f"Permission denied: {exc}"})
            return 1
        except OSError as exc:
            emit({"status": "error", "message": f"I/O failure: {exc}"})
            return 1
        except Exception as exc:  # pragma: no cover - defensive
            emit({"status": "error", "message": f"Unexpected error: {exc}"})
            return 1
        emit(payload)
        return 0

    try:
        payload = report_usage(skills_root=skills_root, data_dir=data_dir)
    except PermissionError as exc:
        emit({"status": "error", "message": f"Permission denied: {exc}"})
        return 1
    except OSError as exc:
        emit({"status": "error", "message": f"I/O failure: {exc}"})
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        emit({"status": "error", "message": f"Unexpected error: {exc}"})
        return 1
    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
