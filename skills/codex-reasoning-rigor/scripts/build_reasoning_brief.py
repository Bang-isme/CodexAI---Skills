#!/usr/bin/env python3
"""Generate a deliberate reasoning brief for complex work."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "reasoning-brief-template.md"
PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-z0-9_]+)\}\}")
REQUIRED_LIST_FIELDS = {
    "constraints": "constraints",
    "non_goals": "non_goals",
    "evidence": "evidence",
    "signals": "signals",
    "risks": "risks",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a reasoning brief to force explicit goals, evidence, and monitoring.",
    )
    parser.add_argument("--title", required=True, help="Brief title")
    parser.add_argument("--goal", required=True, help="Primary goal")
    parser.add_argument(
        "--constraints",
        default="",
        help="Semicolon-separated constraints",
    )
    parser.add_argument(
        "--non-goals",
        default="",
        help="Semicolon-separated non-goals",
    )
    parser.add_argument(
        "--evidence",
        default="",
        help="Semicolon-separated proof items required before completion",
    )
    parser.add_argument(
        "--signals",
        default="",
        help="Semicolon-separated monitoring signals",
    )
    parser.add_argument(
        "--risks",
        default="",
        help="Semicolon-separated major risks",
    )
    parser.add_argument(
        "--quality-bar",
        default="",
        help="What would make the output clearly non-generic and decision-ready",
    )
    parser.add_argument(
        "--deliverable",
        default="Decision-ready implementation brief",
        help="Expected output or deliverable",
    )
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow scaffold output with _TODO_ placeholders instead of requiring every reasoning field",
    )
    parser.add_argument("--output", help="Optional markdown output path")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")
    return parser.parse_args()


def parse_list(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(";") if item.strip()]


def render_list(items: List[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def placeholder_list(values: List[str], allow_placeholders: bool) -> List[str]:
    if values:
        return values
    return ["_TODO_"] if allow_placeholders else []


def missing_required_fields(args: argparse.Namespace) -> List[str]:
    missing: List[str] = []
    if not args.quality_bar.strip():
        missing.append("quality_bar")
    for field_name, attr_name in REQUIRED_LIST_FIELDS.items():
        if not parse_list(getattr(args, attr_name)):
            missing.append(field_name)
    return missing


def build_mapping(args: argparse.Namespace) -> Dict[str, str]:
    return {
        "title": args.title.strip(),
        "goal": args.goal.strip(),
        "constraints": render_list(placeholder_list(parse_list(args.constraints), args.allow_placeholders)),
        "non_goals": render_list(placeholder_list(parse_list(args.non_goals), args.allow_placeholders)),
        "evidence": render_list(placeholder_list(parse_list(args.evidence), args.allow_placeholders)),
        "signals": render_list(placeholder_list(parse_list(args.signals), args.allow_placeholders)),
        "risks": render_list(placeholder_list(parse_list(args.risks), args.allow_placeholders)),
        "quality_bar": args.quality_bar.strip() or "_TODO_",
        "deliverable": args.deliverable.strip(),
    }


def render_template(template_text: str, mapping: Dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return mapping.get(key, "_TODO_")

    return PLACEHOLDER_PATTERN.sub(replace, template_text)


def emit(payload: Dict[str, object], fmt: str) -> None:
    if fmt == "markdown":
        sys.stdout.write(str(payload["markdown"]))
        if not str(payload["markdown"]).endswith("\n"):
            sys.stdout.write("\n")
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    if not TEMPLATE_PATH.exists():
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Missing template: {TEMPLATE_PATH}",
                },
                indent=2,
            )
        )
        return 1

    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    missing = missing_required_fields(args)
    if missing and not args.allow_placeholders:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": "Missing required reasoning fields",
                    "missing_fields": missing,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    mapping = build_mapping(args)
    markdown = render_template(template_text, mapping)

    output_path = ""
    if args.output:
        target = Path(args.output).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown, encoding="utf-8", newline="\n")
        output_path = target.as_posix()

    payload: Dict[str, object] = {
        "status": "scaffold" if missing else "ok",
        "title": args.title.strip(),
        "deliverable": args.deliverable.strip(),
        "path": output_path,
        "missing_fields": missing,
        "markdown": markdown,
    }
    emit(payload, args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
