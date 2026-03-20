#!/usr/bin/env python3
"""Score text outputs for specificity, evidence, and generic filler."""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_MAX_TOKENS = 500
DEFAULT_LLM_COST_ESTIMATE_USD = 0.001
LLM_JUDGE_TIMEOUT_SECONDS = 20
LLM_JUDGE_MAX_INPUT_CHARS = 8000
LLM_TRUNCATION_MARKER = "...[truncated]..."

GENERIC_PHRASES = (
    "best practice",
    "best practices",
    "ensure scalability",
    "improve performance",
    "enhance maintainability",
    "robust solution",
    "seamless workflow",
    "optimize the process",
    "improve quality",
    "user-friendly",
    "production-ready",
)
SECTION_PATTERNS = {
    "decision": re.compile(r"\b(decision|recommended path|chosen path)\b", re.IGNORECASE),
    "evidence": re.compile(r"\b(evidence|verification|validate|proof)\b", re.IGNORECASE),
    "risk": re.compile(r"\b(risk|failure mode|uncertainty|open question)\b", re.IGNORECASE),
    "next": re.compile(r"\b(next step|exit criteria|follow-up|action)\b", re.IGNORECASE),
}
COMMAND_WORDS = ("python", "pytest", "git", "npm", "pnpm", "robocopy", "copy-item", "get-content")
COMMAND_START_PATTERN = re.compile(rf"^(?:{'|'.join(re.escape(word) for word in COMMAND_WORDS)})\b", re.IGNORECASE)
COMMAND_LINE_PATTERN = re.compile(
    rf"^\s*(?:[-*]\s+|\d+\.\s+|>\s+|[$#]\s+)?(?P<command>(?:{'|'.join(re.escape(word) for word in COMMAND_WORDS)})\b[^\n`]*)",
    re.IGNORECASE,
)
INLINE_CODE_PATTERN = re.compile(r"`([^`\n]+)`")
FILE_PATTERN = re.compile(r"\b(?:[A-Za-z]:[\\/][^\s`]+|[\w./-]+\.(?:py|js|jsx|ts|tsx|md|json|yaml|yml|toml|ini))\b")
NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")
PATH_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".yaml", ".yml", ".toml", ".ini"}
GENERIC_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = tuple(
    (
        phrase,
        re.compile(
            rf"(?<!\w){re.escape(phrase).replace(r'\ ', r'\s+')}(?!\w)",
            re.IGNORECASE,
        ),
    )
    for phrase in sorted(GENERIC_PHRASES, key=len, reverse=True)
)
JUDGE_PROMPT = """You are an output quality judge. Evaluate the following deliverable on a scale of 0-100.
Criteria:
1. Specificity (0-25): Does it reference specific files, commands, numbers, or concrete artifacts? Or is it generic advice?
2. Evidence (0-25): Does it include proof, verification commands, test results, or measurable conditions?
3. Actionability (0-25): Can someone execute the recommendations immediately? Or are they vague?
4. Completeness (0-25): Does it cover decision, evidence, risks, and next steps?
Respond with JSON only:
{{"score": <0-100>, "specificity": <0-25>, "evidence": <0-25>, "actionability": <0-25>, "completeness": <0-25>, "issues": ["..."], "suggestions": ["..."]}}
Deliverable to evaluate:
---
{text}
---"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate whether a text output is specific and evidence-backed instead of generic.",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", help="Path to a text or markdown file")
    source.add_argument("--text", help="Inline text to score")
    parser.add_argument("--repo-root", help="Optional repo root used to verify file and command path grounding")
    parser.add_argument("--min-score", type=int, default=60, help="Minimum passing score (default: 60)")
    parser.add_argument("--format", choices=("json", "table"), default="json", help="Output format")
    parser.add_argument("--llm-judge", action="store_true", help="Use LLM judging when API credentials are available")
    parser.add_argument("--model", default=DEFAULT_LLM_MODEL, help=f"LLM judge model (default: {DEFAULT_LLM_MODEL})")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum response tokens for LLM judge mode (default: {DEFAULT_MAX_TOKENS})",
    )
    return parser.parse_args()


def load_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file:
        return Path(args.file).expanduser().read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("Provide --file, --text, or pipe text via stdin")


def find_generic_phrases(text: str) -> List[str]:
    found: List[str] = []
    occupied_spans: List[Tuple[int, int]] = []
    for phrase, pattern in GENERIC_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            if any(start < existing_end and end > existing_start for existing_start, existing_end in occupied_spans):
                continue
            occupied_spans.append((start, end))
            found.append(phrase)
            break
    return found


def collect_command_hits(text: str) -> List[str]:
    hits: List[str] = []
    seen = set()

    def record(candidate: str) -> None:
        normalized = candidate.strip()
        key = normalized.lower()
        if not normalized or key in seen:
            return
        seen.add(key)
        hits.append(normalized)

    for match in INLINE_CODE_PATTERN.finditer(text):
        snippet = match.group(1).strip()
        if COMMAND_START_PATTERN.match(snippet):
            record(snippet)

    for line in text.splitlines():
        match = COMMAND_LINE_PATTERN.match(line)
        if match:
            record(match.group("command"))

    return hits


def normalize_reference(value: str) -> str:
    return value.strip().strip(".,;:()[]{}").strip("\"'")


def looks_like_path_token(value: str) -> bool:
    candidate = normalize_reference(value)
    if not candidate or candidate in {"-", "."}:
        return False
    if candidate.startswith("-"):
        return False
    path = Path(candidate)
    return bool(path.is_absolute() or "/" in candidate or "\\" in candidate or path.suffix.lower() in PATH_SUFFIXES)


def resolve_reference_path(value: str, repo_root: Path) -> Path:
    candidate = normalize_reference(value)
    path = Path(candidate).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (repo_root / candidate).resolve()


def collect_artifact_refs(backtick_refs: Sequence[str], file_refs: Sequence[str], command_hits: Sequence[str]) -> List[str]:
    artifacts: List[str] = []
    seen = set()
    command_set = {item.strip().lower() for item in command_hits}
    for ref in list(file_refs) + list(backtick_refs):
        normalized = normalize_reference(ref)
        if not normalized:
            continue
        if normalized.lower() in command_set:
            continue
        if normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        artifacts.append(normalized)
    return artifacts


def validate_artifact_refs(artifact_refs: Sequence[str], repo_root: Path | None) -> Tuple[List[str], List[str]]:
    if repo_root is None:
        return [], []
    resolved: List[str] = []
    missing: List[str] = []
    for ref in artifact_refs:
        try:
            target = resolve_reference_path(ref, repo_root)
        except OSError:
            missing.append(ref)
            continue
        if target.exists():
            resolved.append(ref)
        else:
            missing.append(ref)
    return resolved, missing


def split_command(command: str) -> List[str]:
    try:
        return shlex.split(command, posix=False)
    except ValueError:
        return command.split()


def validate_command_paths(command_hits: Sequence[str], repo_root: Path | None) -> Tuple[List[str], List[str]]:
    if repo_root is None:
        return [], []

    resolved: List[str] = []
    missing: List[str] = []
    seen_resolved = set()
    seen_missing = set()

    for command in command_hits:
        tokens = [token.strip("\"'") for token in split_command(command)]
        if not tokens:
            continue
        tool = tokens[0].lower()
        if tool not in {"python", "pytest", "copy-item", "get-content"}:
            continue
        for token in tokens[1:]:
            if token in {"-m", "-c", "-", "."}:
                continue
            if token.startswith("-") and not looks_like_path_token(token):
                continue
            if not looks_like_path_token(token):
                continue
            try:
                target = resolve_reference_path(token, repo_root)
            except OSError:
                key = normalize_reference(token).lower()
                if key not in seen_missing:
                    seen_missing.add(key)
                    missing.append(normalize_reference(token))
                continue
            normalized = normalize_reference(token)
            key = normalized.lower()
            if target.exists():
                if key not in seen_resolved:
                    seen_resolved.add(key)
                    resolved.append(normalized)
            elif key not in seen_missing:
                seen_missing.add(key)
                missing.append(normalized)
    return resolved, missing


def merge_unique_strings(*groups: Sequence[str]) -> List[str]:
    merged: List[str] = []
    seen = set()
    for group in groups:
        for item in group:
            normalized = str(item).strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(normalized)
    return merged


def truncate_for_judge(text: str, max_chars: int = LLM_JUDGE_MAX_INPUT_CHARS) -> Tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    marker = LLM_TRUNCATION_MARKER
    remaining = max_chars - len(marker)
    if remaining <= 0:
        return text[:max_chars], True
    head = remaining // 2
    tail = remaining - head
    return f"{text[:head]}{marker}{text[-tail:]}", True


def get_judge_api_key() -> str:
    return os.environ.get("CODEX_JUDGE_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""


def judge_api_url() -> str:
    base_url = os.environ.get("CODEX_JUDGE_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    return base_url.rstrip("/") + "/chat/completions"


def unwrap_json_response(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
        if match:
            return match.group(1)
    return stripped


def extract_choice_content(payload: Dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Judge response did not include choices")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise ValueError("Judge response choice is invalid")
    message = choice.get("message")
    if not isinstance(message, dict):
        raise ValueError("Judge response message is invalid")
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        if parts:
            return "\n".join(parts)
    raise ValueError("Judge response content is missing")


def coerce_score(value: Any, minimum: int, maximum: int) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid judge score: {value!r}") from exc
    return max(minimum, min(maximum, score))


def request_llm_judgment(prompt: str, model: str, max_tokens: int, api_key: str) -> Dict[str, Any]:
    if max_tokens <= 0:
        raise ValueError("--max-tokens must be a positive integer")
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Return valid JSON only. Do not include markdown fences."},
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        judge_api_url(),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=LLM_JUDGE_TIMEOUT_SECONDS) as response:
            raw_payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Judge API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Judge API unavailable: {exc.reason}") from exc
    payload_json = json.loads(raw_payload)
    content = extract_choice_content(payload_json)
    parsed = json.loads(unwrap_json_response(content))
    if not isinstance(parsed, dict):
        raise ValueError("Judge response JSON must be an object")
    return parsed


def evaluate_with_llm(
    text: str,
    prompt_template: str,
    breakdown_keys: Sequence[str],
    *,
    model: str = DEFAULT_LLM_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    api_key: str | None = None,
) -> Dict[str, Any]:
    key = api_key or get_judge_api_key()
    if not key:
        raise RuntimeError("No CODEX_JUDGE_API_KEY or OPENAI_API_KEY was found")
    judged_text, truncated = truncate_for_judge(text)
    prompt = prompt_template.format(text=judged_text)
    payload = request_llm_judgment(prompt, model=model, max_tokens=max_tokens, api_key=key)
    score = coerce_score(payload.get("score"), 0, 100)
    breakdown = {key_name: coerce_score(payload.get(key_name), 0, 25) for key_name in breakdown_keys}
    issues = [str(item).strip() for item in payload.get("issues", []) if str(item).strip()]
    suggestions = [str(item).strip() for item in payload.get("suggestions", []) if str(item).strip()]
    return {
        "score": score,
        "breakdown": breakdown,
        "issues": issues,
        "suggestions": suggestions,
        "truncated": truncated,
        "judged_chars": len(judged_text),
        "estimated_cost_usd": DEFAULT_LLM_COST_ESTIMATE_USD,
        "model": model,
    }


def maybe_run_llm_judge(
    text: str,
    prompt_template: str,
    breakdown_keys: Sequence[str],
    *,
    llm_judge: bool,
    model: str = DEFAULT_LLM_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> Tuple[Dict[str, Any] | None, List[str]]:
    if not llm_judge:
        return None, []
    api_key = get_judge_api_key()
    if not api_key:
        return None, [
            "LLM judge requested but no CODEX_JUDGE_API_KEY or OPENAI_API_KEY was found; falling back to heuristic mode."
        ]
    try:
        return (
            evaluate_with_llm(
                text,
                prompt_template,
                breakdown_keys,
                model=model,
                max_tokens=max_tokens,
                api_key=api_key,
            ),
            [],
        )
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        return None, [f"LLM judge unavailable ({exc}); falling back to heuristic mode."]


def analyze_text_heuristic(text: str, min_score: int = 60, repo_root: Path | None = None) -> Dict[str, Any]:
    generic_hits = find_generic_phrases(text)
    backtick_refs = INLINE_CODE_PATTERN.findall(text)
    file_refs = FILE_PATTERN.findall(text)
    command_hits = collect_command_hits(text)
    number_hits = NUMBER_PATTERN.findall(text)
    section_hits = [name for name, pattern in SECTION_PATTERNS.items() if pattern.search(text)]
    artifact_refs = collect_artifact_refs(backtick_refs, file_refs, command_hits)
    resolved_artifact_refs, missing_artifact_refs = validate_artifact_refs(artifact_refs, repo_root)
    resolved_command_paths, missing_command_paths = validate_command_paths(command_hits, repo_root)

    score = 45
    score += min(20, len(artifact_refs) * 3)
    score += min(12, len(command_hits) * 4)
    score += min(10, len(number_hits))
    score += len(section_hits) * 5
    score += min(10, len(resolved_artifact_refs) * 2)
    score += min(6, len(resolved_command_paths) * 2)
    score -= len(generic_hits) * 8
    score -= min(12, len(missing_artifact_refs) * 4)
    score -= min(8, len(missing_command_paths) * 4)
    if not artifact_refs:
        score -= 15
    if not command_hits:
        score -= 8
    if len(section_hits) < 2:
        score -= 8
    score = max(0, min(100, score))

    issues: List[str] = []
    suggestions: List[str] = []
    if generic_hits:
        issues.append("Generic filler language detected")
        suggestions.append("Replace filler phrases with named files, commands, or measurable conditions")
    if not artifact_refs:
        issues.append("No concrete code, file, or artifact references detected")
        suggestions.append("Add exact file paths, scripts, commands, or identifiers")
    if not command_hits:
        issues.append("No verification or command evidence detected")
        suggestions.append("Include at least one runnable command or validator invocation that proves the claim")
    if len(section_hits) < 2:
        issues.append("Weak delivery structure")
        suggestions.append("Add explicit sections for decision, evidence, risks, or next steps")
    if repo_root is not None and missing_artifact_refs:
        issues.append("Some referenced files or artifacts were not found under repo root")
        suggestions.append("Replace stale file references with paths that exist under the target repo root")
    if repo_root is not None and missing_command_paths:
        issues.append("Some command path arguments were not found under repo root")
        suggestions.append("Point commands at real files or directories so the evidence can be reproduced")

    status = "pass"
    if (
        score < min_score
        or len(generic_hits) >= 2
        or not command_hits
        or (repo_root is not None and missing_artifact_refs and not resolved_artifact_refs)
        or (repo_root is not None and missing_command_paths and not resolved_command_paths and not resolved_artifact_refs)
        or (not artifact_refs and not command_hits)
    ):
        status = "fail"

    return {
        "status": status,
        "score": score,
        "min_score": min_score,
        "repo_root": repo_root.as_posix() if repo_root is not None else "",
        "counts": {
            "generic_phrases": len(generic_hits),
            "artifact_refs": len(artifact_refs),
            "commands": len(command_hits),
            "numbers": len(number_hits),
            "sections": len(section_hits),
            "resolved_artifact_refs": len(resolved_artifact_refs),
            "missing_artifact_refs": len(missing_artifact_refs),
            "resolved_command_paths": len(resolved_command_paths),
            "missing_command_paths": len(missing_command_paths),
        },
        "generic_hits": generic_hits,
        "section_hits": section_hits,
        "artifact_refs": artifact_refs,
        "resolved_artifact_refs": resolved_artifact_refs,
        "missing_artifact_refs": missing_artifact_refs,
        "resolved_command_paths": resolved_command_paths,
        "missing_command_paths": missing_command_paths,
        "issues": issues,
        "suggestions": suggestions[:4],
    }


def analyze_text(
    text: str,
    min_score: int = 60,
    repo_root: Path | None = None,
    llm_judge: bool = False,
    model: str = DEFAULT_LLM_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> Dict[str, Any]:
    report = analyze_text_heuristic(text, min_score=min_score, repo_root=repo_root)
    heuristic_score = int(report["score"])
    report["evaluation_mode"] = "heuristic"
    report["llm_score"] = None
    report["heuristic_score"] = heuristic_score
    report["estimated_cost_usd"] = 0.0
    report["warnings"] = []

    llm_result, warnings = maybe_run_llm_judge(
        text,
        JUDGE_PROMPT,
        ("specificity", "evidence", "actionability", "completeness"),
        llm_judge=llm_judge,
        model=model,
        max_tokens=max_tokens,
    )
    report["warnings"] = warnings
    if llm_result is None:
        return report

    llm_score = int(llm_result["score"])
    final_score = int(round((llm_score * 0.7) + (heuristic_score * 0.3)))
    report["status"] = "pass" if final_score >= min_score else "fail"
    report["score"] = final_score
    report["evaluation_mode"] = "llm"
    report["llm_score"] = llm_score
    report["heuristic_score"] = heuristic_score
    report["estimated_cost_usd"] = llm_result["estimated_cost_usd"]
    report["llm_breakdown"] = llm_result["breakdown"]
    report["judged_chars"] = llm_result["judged_chars"]
    report["input_truncated"] = llm_result["truncated"]
    report["model"] = llm_result["model"]
    report["issues"] = merge_unique_strings(report.get("issues", []), llm_result["issues"])
    report["suggestions"] = merge_unique_strings(report.get("suggestions", []), llm_result["suggestions"])[:6]
    return report


def format_table(report: Dict[str, Any]) -> str:
    counts = report["counts"]
    assert isinstance(counts, dict)
    lines = [
        f"status       : {report['status']}",
        f"score        : {report['score']}",
        f"min_score    : {report['min_score']}",
        f"mode         : {report.get('evaluation_mode', 'heuristic')}",
        f"generic      : {counts['generic_phrases']}",
        f"artifacts    : {counts['artifact_refs']}",
        f"resolved art : {counts.get('resolved_artifact_refs', 0)}",
        f"missing art  : {counts.get('missing_artifact_refs', 0)}",
        f"commands     : {counts['commands']}",
        f"resolved cmd : {counts.get('resolved_command_paths', 0)}",
        f"missing cmd  : {counts.get('missing_command_paths', 0)}",
        f"numbers      : {counts['numbers']}",
        f"sections     : {counts['sections']}",
    ]
    if report.get("llm_score") is not None:
        lines.append(f"llm_score    : {report['llm_score']}")
        lines.append(f"heuristic    : {report['heuristic_score']}")
    warnings = report.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.extend(f"warning      : {item}" for item in warnings)
    issues = report.get("issues", [])
    if isinstance(issues, list) and issues:
        lines.append("issues       : " + "; ".join(str(item) for item in issues))
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        text = load_text(args)
        repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else None
        report = analyze_text(
            text,
            min_score=args.min_score,
            repo_root=repo_root,
            llm_judge=args.llm_judge,
            model=args.model,
            max_tokens=args.max_tokens,
        )
    except (OSError, ValueError) as exc:
        payload = {"status": "error", "message": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(f"status       : error\nmessage      : {exc}")
        return 1

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_table(report))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
