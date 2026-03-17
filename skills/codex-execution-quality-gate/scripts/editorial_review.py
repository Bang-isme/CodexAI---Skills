#!/usr/bin/env python3
"""Evaluate whether a deliverable reads like a decision-ready human artifact."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import output_guard


DECISION_PATTERNS = {
    "decision": re.compile(r"\b(decision|recommended path|recommendation|chosen path|go\/no-go|ship|no-ship)\b", re.IGNORECASE),
    "finding": re.compile(r"\b(finding|findings|verdict|assessment)\b", re.IGNORECASE),
    "state": re.compile(r"\b(current state|status|handoff)\b", re.IGNORECASE),
}
TRADEOFF_PATTERN = re.compile(
    r"\b(risk|tradeoff|blast radius|failure mode|rollback|open question|uncertainty|cost)\b",
    re.IGNORECASE,
)
NEXT_STEP_PATTERN = re.compile(r"\b(next step|next steps|follow-up|owner|exit criteria|action item|blocker)\b", re.IGNORECASE)
HEADING_PATTERN = re.compile(r"^\s{0,3}(?:#{1,6}\s+.+|[A-Z][A-Za-z /-]{2,}:\s*)$")
BULLET_PATTERN = re.compile(r"^\s*(?:[-*]\s+|\d+\.\s+)")
LABELLED_LINE_PATTERN = re.compile(r"^\s*[A-Z][A-Za-z /-]{2,}:\s+\S")
HEDGE_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("might want to", re.compile(r"\bmight want to\b", re.IGNORECASE)),
    ("may want to", re.compile(r"\bmay want to\b", re.IGNORECASE)),
    ("could consider", re.compile(r"\bcould consider\b", re.IGNORECASE)),
    ("it depends", re.compile(r"\bit depends\b", re.IGNORECASE)),
    ("appears to", re.compile(r"\bappears to\b", re.IGNORECASE)),
    ("seems to", re.compile(r"\bseems to\b", re.IGNORECASE)),
    ("potentially", re.compile(r"\bpotentially\b", re.IGNORECASE)),
)
AI_SPEAK_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("as an ai", re.compile(r"\bas an ai\b", re.IGNORECASE)),
    ("here's a breakdown", re.compile(r"\bhere(?:'|’)s a breakdown\b", re.IGNORECASE)),
    ("in conclusion", re.compile(r"\bin conclusion\b", re.IGNORECASE)),
    ("overall, the best approach", re.compile(r"\boverall,\s+the best approach\b", re.IGNORECASE)),
    ("utilize", re.compile(r"\butilize\b", re.IGNORECASE)),
    ("leverage", re.compile(r"\bleverage\b", re.IGNORECASE)),
)
DELIVERABLE_MARKERS = {
    "plan": ("success criteria", "task breakdown", "verification", "rollback"),
    "review": ("findings", "severity", "risk", "open questions"),
    "handoff": ("current state", "blockers", "next steps", "owner"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review a deliverable for human-like editorial quality and decision readiness.",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", help="Path to a text or markdown file")
    source.add_argument("--text", help="Inline text to score")
    parser.add_argument("--repo-root", help="Optional repo root used for grounding checks")
    parser.add_argument(
        "--deliverable-kind",
        choices=("auto", "generic", "plan", "review", "handoff"),
        default="auto",
        help="Deliverable type used for rubric tuning",
    )
    parser.add_argument("--min-score", type=int, default=65, help="Minimum passing score (default: 65)")
    parser.add_argument("--format", choices=("json", "table"), default="json", help="Output format")
    return parser.parse_args()


def load_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file:
        return Path(args.file).expanduser().read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("Provide --file, --text, or pipe text via stdin")


def normalize_hits(patterns: Sequence[Tuple[str, re.Pattern[str]]], text: str) -> List[str]:
    hits: List[str] = []
    for label, pattern in patterns:
        if pattern.search(text):
            hits.append(label)
    return hits


def infer_deliverable_kind(text: str, requested: str) -> str:
    if requested != "auto":
        return requested
    lowered = text.lower()
    for kind, markers in DELIVERABLE_MARKERS.items():
        if sum(marker in lowered for marker in markers) >= 2:
            return kind
    return "generic"


def score_decision_clarity(text: str, deliverable_kind: str, guard_report: Dict[str, object]) -> Tuple[int, List[str]]:
    lowered = text.lower()
    hits: List[str] = []
    score = 0
    for label, pattern in DECISION_PATTERNS.items():
        if pattern.search(text):
            hits.append(label)
    if hits:
        score += 12
    if "decision" in guard_report.get("section_hits", []):
        score += 4
    markers = DELIVERABLE_MARKERS.get(deliverable_kind, ())
    if markers:
        marker_hits = sum(marker in lowered for marker in markers)
        score += min(8, marker_hits * 2)
    return min(20, score), hits


def score_grounding(guard_report: Dict[str, object]) -> int:
    counts = guard_report.get("counts", {})
    if not isinstance(counts, dict):
        return 0
    artifact_refs = int(counts.get("artifact_refs", 0) or 0)
    commands = int(counts.get("commands", 0) or 0)
    numbers = int(counts.get("numbers", 0) or 0)
    resolved_artifacts = int(counts.get("resolved_artifact_refs", 0) or 0)
    resolved_paths = int(counts.get("resolved_command_paths", 0) or 0)
    score = artifact_refs * 3 + commands * 5 + min(5, numbers) + resolved_artifacts * 2 + resolved_paths * 2
    return min(25, score)


def score_tradeoff_awareness(text: str, guard_report: Dict[str, object]) -> Tuple[int, int, int]:
    tradeoff_hits = len(TRADEOFF_PATTERN.findall(text))
    next_hits = len(NEXT_STEP_PATTERN.findall(text))
    section_hits = guard_report.get("section_hits", [])
    score = min(12, tradeoff_hits * 4) + min(4, next_hits * 2)
    if isinstance(section_hits, list):
        if "risk" in section_hits:
            score += 2
        if "next" in section_hits:
            score += 2
    return min(20, score), tradeoff_hits, next_hits


def score_structure(text: str) -> Tuple[int, int, int, int]:
    lines = [line.rstrip() for line in text.splitlines()]
    headings = sum(1 for line in lines if HEADING_PATTERN.match(line))
    bullets = sum(1 for line in lines if BULLET_PATTERN.match(line))
    labeled_lines = sum(1 for line in lines if LABELLED_LINE_PATTERN.match(line))
    paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    avg_paragraph_words = 0
    if paragraphs:
        avg_paragraph_words = round(
            sum(len(re.findall(r"\b[\w'-]+\b", chunk)) for chunk in paragraphs) / len(paragraphs)
        )

    score = 0
    if headings >= 1:
        score += 8
    elif labeled_lines >= 3:
        score += 8
    if bullets >= 2:
        score += 6
    elif bullets == 1:
        score += 4
    if 2 <= len(paragraphs) <= 8:
        score += 4
    if paragraphs and avg_paragraph_words <= 120:
        score += 2
    return min(20, score), headings, bullets, avg_paragraph_words


def score_tone(text: str, decision_score: int) -> Tuple[int, List[str], List[str]]:
    ai_speak_hits = normalize_hits(AI_SPEAK_PATTERNS, text)
    hedge_hits = normalize_hits(HEDGE_PATTERNS, text)
    score = 15
    score -= min(8, len(ai_speak_hits) * 4)
    score -= min(8, len(hedge_hits) * 2)
    if not ai_speak_hits and decision_score >= 12:
        score += 3
    return max(0, min(15, score)), ai_speak_hits, hedge_hits


def analyze_text(
    text: str,
    min_score: int = 65,
    deliverable_kind: str = "auto",
    repo_root: Path | None = None,
) -> Dict[str, object]:
    kind = infer_deliverable_kind(text, deliverable_kind)
    guard_report = output_guard.analyze_text(text, min_score=0, repo_root=repo_root)
    decision_score, decision_hits = score_decision_clarity(text, kind, guard_report)
    grounding_score = score_grounding(guard_report)
    tradeoff_score, tradeoff_hits, next_hits = score_tradeoff_awareness(text, guard_report)
    structure_score, headings, bullets, avg_paragraph_words = score_structure(text)
    tone_score, ai_speak_hits, hedge_hits = score_tone(text, decision_score)

    total_score = decision_score + grounding_score + tradeoff_score + structure_score + tone_score
    issues: List[str] = []
    suggestions: List[str] = []

    if decision_score < 10 and kind in {"plan", "review", "handoff"}:
        issues.append("Decision framing is weak for the deliverable type")
        suggestions.append("Name the chosen path, verdict, or current state explicitly near the top")
    if grounding_score < 10:
        issues.append("Grounding is too weak to feel decision-ready")
        suggestions.append("Cite exact files, commands, counts, or reproducible evidence")
    if tradeoff_score < 8:
        issues.append("Tradeoffs or follow-up conditions are under-specified")
        suggestions.append("Add at least one concrete risk, rollback, blocker, or next-step owner")
    if structure_score < 8:
        issues.append("Structure is too loose for quick human scanning")
        suggestions.append("Break the output into headings or short labeled sections")
    if ai_speak_hits or len(hedge_hits) >= 3:
        issues.append("Tone still reads like AI-safe prose")
        suggestions.append("Cut meta framing and replace hedges with direct recommendations")

    hard_fail = (
        total_score < min_score
        or (kind in {"plan", "review", "handoff"} and decision_score < 10)
        or grounding_score < 8
    )

    return {
        "status": "fail" if hard_fail else "pass",
        "score": total_score,
        "min_score": min_score,
        "deliverable_kind": kind,
        "rubric": {
            "decision_clarity": decision_score,
            "grounding": grounding_score,
            "tradeoff_awareness": tradeoff_score,
            "structure": structure_score,
            "editorial_tone": tone_score,
        },
        "counts": {
            "decision_markers": len(decision_hits),
            "tradeoff_markers": tradeoff_hits,
            "next_step_markers": next_hits,
            "headings": headings,
            "bullets": bullets,
            "avg_paragraph_words": avg_paragraph_words,
            "ai_speak_phrases": len(ai_speak_hits),
            "hedge_phrases": len(hedge_hits),
        },
        "decision_hits": decision_hits,
        "ai_speak_hits": ai_speak_hits,
        "hedge_hits": hedge_hits,
        "issues": issues,
        "suggestions": suggestions[:4],
        "output_guard": {
            "status": guard_report.get("status"),
            "score": guard_report.get("score"),
            "artifact_refs": guard_report.get("counts", {}).get("artifact_refs", 0) if isinstance(guard_report.get("counts"), dict) else 0,
            "commands": guard_report.get("counts", {}).get("commands", 0) if isinstance(guard_report.get("counts"), dict) else 0,
        },
    }


def format_table(report: Dict[str, object]) -> str:
    rubric = report.get("rubric", {})
    counts = report.get("counts", {})
    assert isinstance(rubric, dict)
    assert isinstance(counts, dict)
    lines = [
        f"status          : {report['status']}",
        f"score           : {report['score']}",
        f"min_score       : {report['min_score']}",
        f"kind            : {report['deliverable_kind']}",
        f"decision        : {rubric['decision_clarity']}",
        f"grounding       : {rubric['grounding']}",
        f"tradeoffs       : {rubric['tradeoff_awareness']}",
        f"structure       : {rubric['structure']}",
        f"tone            : {rubric['editorial_tone']}",
        f"headings        : {counts['headings']}",
        f"bullets         : {counts['bullets']}",
        f"hedges          : {counts['hedge_phrases']}",
        f"ai_speak        : {counts['ai_speak_phrases']}",
    ]
    issues = report.get("issues", [])
    if isinstance(issues, list):
        lines.extend(f"issue           : {item}" for item in issues)
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        text = load_text(args)
    except ValueError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else None
    report = analyze_text(
        text,
        min_score=args.min_score,
        deliverable_kind=args.deliverable_kind,
        repo_root=repo_root,
    )
    if args.format == "table":
        print(format_table(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
