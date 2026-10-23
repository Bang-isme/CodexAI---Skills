#!/usr/bin/env python3
"""Validate a review report against the CodexAI 4-part finding contract."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PRIORITY_PATTERN = re.compile(
    r"correct\s*(?:->|→|>)+\s*safe\s*(?:->|→|>)+\s*holds at expected load\s*(?:->|→|>)+\s*"
    r"tested\s*(?:->|→|>)+\s*fast\s*(?:->|→|>)+\s*lean\b",
    re.IGNORECASE,
)
LOAD_PATTERN = re.compile(r"assumed load\s*:\s*(\d+)", re.IGNORECASE)
NOT_CHECKED_PATTERN = re.compile(r"not checked\s*/\s*out of scope", re.IGNORECASE)
SECTION_PATTERN = re.compile(
    r"(?m)^#{1,6}[ \t]+(Must-Fix|Should-Fix|Nice-to-Have)\s*:?\s*$",
    re.IGNORECASE,
)
FINDING_PATTERN = re.compile(r"(?m)^[ \t]*(\d+)\.\s+")
FILE_LINE_PATTERN = re.compile(r"[\w./\\-]+\.[A-Za-z0-9]+:\d+")
SHORTCUT_PATTERN = re.compile(
    r"shortcut\s*:\s*(\d+)\b([^,\n]{0,80})?(?:,\s*([^\n]+))?",
    re.IGNORECASE,
)
PART_PATTERNS = (
    ("what", re.compile(r"what it is(?:\s*\([^)]*\))?\s*:\s*(.*)$", re.IGNORECASE)),
    ("problem", re.compile(r"the problem(?:\s*\([^)]*\))?\s*:\s*(.*)$", re.IGNORECASE)),
    ("fix", re.compile(r"the smallest fix\s*:\s*(.*)$", re.IGNORECASE)),
    ("skipped", re.compile(r"what happens if skipped\s*:\s*(.*)$", re.IGNORECASE)),
)
GROUP_ORDER = ("Must-Fix", "Should-Fix", "Nice-to-Have")
GROUP_CANONICAL = {name.lower(): name for name in GROUP_ORDER}
FABRICATED_SAVINGS_PATTERNS = (
    re.compile(r"\b(?:this|the)\s+(?:repo|repository|codebase|project)\s+saved\s+\d[\d,]*\s+lines\b", re.IGNORECASE),
    re.compile(r"\byou\s+saved\s+\d+(?:\.\d+)?\s*%\s+tokens\b", re.IGNORECASE),
    re.compile(r"\bsaved\s+\d+(?:\.\d+)?\s*%\s+(?:of\s+)?tokens\b", re.IGNORECASE),
    re.compile(r"\b\d[\d,]*\s+lines\s+saved\b", re.IGNORECASE),
)


def find_fabricated_savings_claims(text: str) -> list[str]:
    """Return invented per-repo line or token savings claims."""
    if not isinstance(text, str) or not text:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for pattern in FABRICATED_SAVINGS_PATTERNS:
        for match in pattern.finditer(text):
            claim = match.group(0).strip()
            key = claim.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(claim)
    return found


def has_concrete_case(problem: str) -> bool:
    """A finding needs a concrete input, quoted case, or callable scenario."""
    if re.search(r"`[^`]+`", problem):
        return True
    if re.search(r"""['"][^'"]+['"]""", problem):
        return True
    if re.search(r"\b(?:input|payload|case)\b\s*[:=]", problem, re.IGNORECASE):
        return True
    if re.search(r"\b[A-Za-z_][A-Za-z0-9_]*\([^)\n]{0,120}\)", problem):
        return True
    return False


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _parse_parts(block: str) -> dict[str, str]:
    lines = block.splitlines()
    if lines:
        lines[0] = re.sub(r"^\s*\d+\.\s*", "", lines[0], count=1)
    parts = {"what": "", "problem": "", "fix": "", "skipped": ""}
    current: str | None = None
    for line in lines:
        stripped = line.strip()
        matched = False
        for key, pattern in PART_PATTERNS:
            match = pattern.search(stripped)
            if match:
                current = key
                parts[key] = match.group(1).strip()
                matched = True
                break
        if not matched and current and stripped:
            parts[current] = f"{parts[current]} {stripped}".strip()
    return parts


def _group_for(position: int, sections: list[tuple[int, int, str]]) -> str:
    group = ""
    for start, end, name in sections:
        if start <= position < end:
            group = name
    return group


def validate_review_report(text: str, assumed_load: int | None = None) -> dict[str, Any]:
    """Validate continuous 4-part findings, shortcut ceilings, and metric honesty."""
    errors: list[str] = []
    if not isinstance(text, str):
        return {
            "ok": False,
            "status": "fail",
            "errors": ["report text must be a string"],
            "findings": [],
            "excluded_shortcuts": [],
            "assumed_load": assumed_load,
            "not_checked": False,
            "priority_order_ok": False,
            "fabricated_savings": [],
        }
    body = _normalize_newlines(text)
    priority_order_ok = PRIORITY_PATTERN.search(body) is not None
    if not priority_order_ok:
        errors.append("report must state priority order Correct -> Safe -> Holds at expected load -> Tested -> Fast -> Lean")

    load_match = LOAD_PATTERN.search(body)
    parsed_load = int(load_match.group(1)) if load_match else None
    if parsed_load is None:
        errors.append("report must state Assumed Load")
    if assumed_load is not None and parsed_load is not None and assumed_load != parsed_load:
        errors.append("assumed load does not match the report")
    effective_load = assumed_load if assumed_load is not None else parsed_load

    not_checked = NOT_CHECKED_PATTERN.search(body) is not None
    if not not_checked:
        errors.append("report must state Not Checked / Out of Scope")

    fabricated = find_fabricated_savings_claims(body)
    if fabricated:
        errors.append("fabricated per-repo savings claim: " + "; ".join(fabricated))

    section_matches = list(SECTION_PATTERN.finditer(body))
    sections: list[tuple[int, int, str]] = []
    seen_groups: list[str] = []
    for index, match in enumerate(section_matches):
        name = GROUP_CANONICAL[match.group(1).lower()]
        start = match.end()
        end = section_matches[index + 1].start() if index + 1 < len(section_matches) else len(body)
        sections.append((start, end, name))
        seen_groups.append(name)
    group_indexes = [GROUP_ORDER.index(name) for name in seen_groups]
    if group_indexes != sorted(group_indexes):
        errors.append("review groups must stay in Must-Fix, Should-Fix, Nice-to-Have order")

    finding_matches = list(FINDING_PATTERN.finditer(body))
    heading_starts = {match.start() for match in re.finditer(r"(?m)^#{1,6}[ \t]+\S", body)}
    boundary_starts = sorted({match.start() for match in finding_matches} | heading_starts | {len(body)})
    spans: list[tuple[int, int, int]] = []
    for match in finding_matches:
        start = match.start()
        end = next(point for point in boundary_starts if point > start)
        spans.append((start, end, int(match.group(1))))

    for start, end, name in sections:
        if not any(start <= finding_start < end for finding_start, _, _ in spans):
            errors.append(f"empty group must be omitted: {name}")

    numbers = [number for _, _, number in spans]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append("finding numbers must be continuous starting at 1 across groups")

    findings: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for start, end, number in spans:
        block = body[start:end]
        group = _group_for(start, sections)
        if not group:
            errors.append(f"finding {number} is outside Must-Fix, Should-Fix, and Nice-to-Have")
        shortcut = SHORTCUT_PATTERN.search(block)
        if shortcut and effective_load is not None and effective_load <= int(shortcut.group(1)):
            when = (shortcut.group(3) or "").strip()
            excluded.append(
                {
                    "number": number,
                    "ceiling": int(shortcut.group(1)),
                    "upgrade_when": when,
                    "reason": "assumed load is within the documented shortcut ceiling",
                }
            )
            continue
        parts = _parse_parts(block)
        missing = [name for name in ("what", "problem", "fix", "skipped") if not parts[name]]
        if missing:
            errors.append(f"finding {number} is missing: {', '.join(missing)}")
        if parts["what"] and FILE_LINE_PATTERN.search(parts["what"]) is None:
            errors.append(f"finding {number} must include file:line")
        concrete = has_concrete_case(parts["problem"]) if parts["problem"] else False
        if parts["problem"] and not concrete:
            errors.append(f"finding {number} has no concrete case")
        findings.append(
            {
                "number": number,
                "group": group,
                "what": parts["what"],
                "problem": parts["problem"],
                "fix": parts["fix"],
                "if_skipped": parts["skipped"],
                "concrete": concrete,
            }
        )

    if effective_load is not None:
        covered = [(start, end) for start, end, _ in spans]
        for match in SHORTCUT_PATTERN.finditer(body):
            if any(start <= match.start() < end for start, end in covered):
                continue
            ceiling = int(match.group(1))
            if effective_load > ceiling:
                errors.append(f"shortcut ceiling {ceiling} exceeded without a finding")

    ok = not errors
    return {
        "ok": ok,
        "status": "pass" if ok else "fail",
        "errors": errors,
        "findings": findings,
        "excluded_shortcuts": excluded,
        "assumed_load": effective_load,
        "not_checked": not_checked,
        "priority_order_ok": priority_order_ok,
        "fabricated_savings": fabricated,
    }


def _load_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file:
        return Path(args.file).expanduser().read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("Provide --file, --text, or pipe a report via stdin")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a review report against the 4-part finding contract.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", default=None, help="Inline review markdown")
    source.add_argument("--file", help="Path to a review markdown file")
    parser.add_argument("--assumed-load", type=int, default=None)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(argv)
    try:
        report = validate_review_report(_load_text(args), assumed_load=args.assumed_load)
    except (OSError, ValueError) as exc:
        payload = {"ok": False, "status": "error", "errors": [str(exc)]}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report["status"])
        for item in report["errors"]:
            print(f"- {item}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
