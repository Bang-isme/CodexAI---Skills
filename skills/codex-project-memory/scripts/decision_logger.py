#!/usr/bin/env python3
"""
Decision logger for codex-project-memory.

Writes decision records to:
<project-root>/.codex/decisions/YYYY-MM-DD-<slug>.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict


def sanitize_slug(raw: str) -> str:
    lowered = raw.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "decision"


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


def emit(payload: Dict[str, str]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Log a project decision to .codex/decisions.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--title", required=True, help="Decision title / slug source")
    parser.add_argument("--decision", required=True, help="Decision statement")
    parser.add_argument("--alternatives", required=True, help="Alternatives considered")
    parser.add_argument("--reasoning", required=True, help="Reasoning for chosen decision")
    parser.add_argument("--context", required=True, help="Decision context")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    title = args.title.strip()

    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit(
            {
                "status": "error",
                "path": "",
                "title": title,
                "message": f"Project root does not exist or is not a directory: {project_root}",
            }
        )
        return 1

    decisions_dir = project_root / ".codex" / "decisions"
    try:
        decisions_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        emit(
            {
                "status": "error",
                "path": "",
                "title": title,
                "message": f"Permission denied while creating directory: {decisions_dir}",
            }
        )
        return 1
    except OSError as exc:
        emit(
            {
                "status": "error",
                "path": "",
                "title": title,
                "message": f"Failed to create decisions directory: {exc}",
            }
        )
        return 1

    today_text = date.today().isoformat()
    slug = sanitize_slug(title)
    target_path = build_target_path(decisions_dir, today_text, slug)

    content = (
        f"# Decision: {title}\n"
        f"Date: {today_text}\n"
        "Status: accepted\n\n"
        "## Context\n"
        f"{args.context.strip()}\n\n"
        "## Decision\n"
        f"{args.decision.strip()}\n\n"
        "## Alternatives Considered\n"
        f"{args.alternatives.strip()}\n\n"
        "## Reasoning\n"
        f"{args.reasoning.strip()}\n\n"
        "## Consequences\n"
        "(to be filled after implementation)\n"
    )

    try:
        with target_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except PermissionError:
        emit(
            {
                "status": "error",
                "path": "",
                "title": title,
                "message": f"Permission denied while writing file: {target_path}",
            }
        )
        return 1
    except OSError as exc:
        emit(
            {
                "status": "error",
                "path": "",
                "title": title,
                "message": f"Failed to write decision file: {exc}",
            }
        )
        return 1

    emit(
        {
            "status": "logged",
            "path": target_path.as_posix(),
            "title": title,
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
