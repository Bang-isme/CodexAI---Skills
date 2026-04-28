#!/usr/bin/env python3
"""Build a compact decision matrix scaffold."""
from __future__ import annotations

import argparse
import json
from typing import Any


DEFAULT_OPTIONS = ["minimal change", "balanced improvement", "larger redesign"]


def parse_options(raw: str | None, max_options: int) -> list[str]:
    if not raw:
        return DEFAULT_OPTIONS[:max_options]
    options: list[str] = []
    seen: set[str] = set()
    for item in raw.split(","):
        option = item.strip()
        key = option.lower()
        if option and key not in seen:
            options.append(option)
            seen.add(key)
        if len(options) >= max_options:
            break
    return options or DEFAULT_OPTIONS[:max_options]


def build_matrix(problem: str, options: list[str], constraints: str | None = None) -> dict[str, Any]:
    rows = []
    for option in options:
        rows.append(
            {
                "option": option,
                "when_it_wins": "Use when this option satisfies the goal with the least justified complexity.",
                "cost": "Estimate implementation, maintenance, operational, and token cost.",
                "risk": "Name the failure mode or tradeoff that could make this option wrong.",
                "evidence_needed": "List exact files, commands, metrics, or user constraints needed to validate it.",
            }
        )
    return {
        "status": "ok",
        "problem": problem,
        "constraints": constraints or "",
        "options": rows,
        "recommendation": "Choose the option with the strongest repo evidence, smallest reversible change, and clear verification path.",
        "verification": ["Run the smallest command or inspection that can falsify the chosen option."],
        "stop_conditions": ["New evidence shows the selected option violates a hard constraint."],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "## Decision Surface",
        "",
        f"Problem: {payload['problem']}",
    ]
    if payload.get("constraints"):
        lines.append(f"Constraints: {payload['constraints']}")
    lines.extend(
        [
            "",
            "| Option | When it wins | Cost | Risk | Evidence needed |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["options"]:
        lines.append(
            f"| {row['option']} | {row['when_it_wins']} | {row['cost']} | {row['risk']} | {row['evidence_needed']} |"
        )
    lines.extend(
        [
            "",
            "## Recommendation",
            payload["recommendation"],
            "",
            "## Verification",
            *[f"- {item}" for item in payload["verification"]],
            "",
            "## Stop Conditions",
            *[f"- {item}" for item in payload["stop_conditions"]],
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a compact decision matrix scaffold.")
    parser.add_argument("--problem", required=True, help="Problem or decision to evaluate")
    parser.add_argument("--options", help="Comma-separated candidate options")
    parser.add_argument("--constraints", help="Known constraints")
    parser.add_argument("--max-options", type=int, default=4, choices=(2, 3, 4))
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_matrix(args.problem, parse_options(args.options, args.max_options), args.constraints)
    if args.format == "markdown":
        print(render_markdown(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
