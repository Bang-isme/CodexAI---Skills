#!/usr/bin/env python3
"""Portable prompt routing for CodexAI generic CLI/IDE harnesses."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

INJECTION_SECURITY_BOOST = 3


ROUTES: list[dict[str, Any]] = [
    {
        "intent": "review",
        "agent": "security-auditor",
        "workflow": "review",
        "skills": ["codex-security-specialist", "codex-execution-quality-gate"],
        "signals": [
            "security",
            "secure",
            "vulnerability",
            "vulnerable",
            "exploit",
            "audit",
            "threat",
            "hardening",
            "harden",
            "secret",
            "lỗ hổng",
            "bao mat",
            "bảo mật",
            "an toàn",
        ],
    },
    {
        "intent": "debug",
        "agent": "debugger",
        "workflow": "debug",
        "skills": ["codex-systematic-debugging", "codex-test-driven-development"],
        "signals": ["bug", "debug", "fix", "crash", "error", "traceback", "broken", "lỗi", "sửa lỗi", "không chạy"],
    },
    {
        "intent": "deploy",
        "agent": "devops-engineer",
        "workflow": "deploy",
        "skills": ["codex-execution-quality-gate", "codex-git-autopilot"],
        "signals": ["deploy", "release", "publish", "ci", "cd", "pipeline", "docker", "kubernetes", "prod", "production"],
    },
    {
        "intent": "build",
        "agent": "frontend-specialist",
        "workflow": "create",
        "skills": ["codex-domain-specialist", "codex-test-driven-development"],
        "signals": ["frontend", "ui", "ux", "react", "vue", "page", "component", "css", "giao diện"],
    },
    {
        "intent": "build",
        "agent": "backend-specialist",
        "workflow": "create",
        "skills": ["codex-domain-specialist", "codex-test-driven-development"],
        "signals": ["backend", "api", "database", "server", "endpoint", "auth", "service", "worker"],
    },
    {
        "intent": "docs",
        "agent": "planner",
        "workflow": "handoff",
        "skills": ["codex-document-writer", "codex-project-memory"],
        "signals": ["docs", "document", "readme", "guide", "handoff", "tài liệu", "hướng dẫn"],
    },
    {
        "intent": "refactor",
        "agent": "planner",
        "workflow": "refactor",
        "skills": ["codex-plan-writer", "codex-test-driven-development"],
        "signals": ["refactor", "cleanup", "restructure", "optimize", "tối ưu", "cải thiện"],
    },
    {
        "intent": "build",
        "agent": "planner",
        "workflow": "prototype",
        "skills": ["codex-spec-driven-development", "codex-plan-writer"],
        "signals": ["prototype", "mvp", "from scratch", "fullstack", "build", "create", "xây", "tạo"],
    },
]

INJECTION_RE = re.compile(
    r"\b(ignore|bypass|override|forget|disable|jailbreak|system prompt|previous instructions)\b",
    re.IGNORECASE,
)


def normalize_prompt(prompt: str) -> str:
    return " ".join(prompt.strip().split())


def route_prompt(prompt: str) -> dict[str, Any]:
    normalized = normalize_prompt(prompt)
    warnings: list[str] = []
    if not normalized:
        return {
            "intent": "other",
            "suggested_agent": None,
            "workflow": None,
            "required_skills": [],
            "confidence": 0.0,
            "matched_signals": [],
            "warnings": ["empty_prompt"],
            "normalized_prompt": "",
        }

    injection_detected = bool(INJECTION_RE.search(normalized))
    if injection_detected:
        warnings.append("prompt_injection_signal")

    lowered = normalized.lower()
    best: dict[str, Any] | None = None
    best_matches: list[str] = []
    best_score = 0
    for route in ROUTES:
        matches = [signal for signal in route["signals"] if signal in lowered]
        if route["workflow"] == "handoff" and ("tài liệu" in lowered or "hướng dẫn" in lowered):
            matches.append("vietnamese_docs")
        score = len(matches)
        if route["agent"] == "security-auditor" and matches:
            score += 2
        if injection_detected and route["agent"] == "security-auditor":
            score += INJECTION_SECURITY_BOOST
            if "prompt_injection" not in matches:
                matches.append("prompt_injection")
        if score > best_score:
            best = route
            best_matches = matches
            best_score = score

    if not best:
        return {
            "intent": "other",
            "suggested_agent": None,
            "workflow": "plan",
            "required_skills": ["codex-intent-context-analyzer", "codex-plan-writer"],
            "confidence": 0.25,
            "matched_signals": [],
            "warnings": warnings + ["low_confidence_fallback"],
            "normalized_prompt": normalized,
        }

    confidence = min(0.95, 0.45 + (0.15 * len(best_matches)))
    return {
        "intent": best["intent"],
        "suggested_agent": best["agent"],
        "workflow": best["workflow"],
        "required_skills": best["skills"],
        "confidence": round(confidence, 2),
        "matched_signals": best_matches,
        "warnings": warnings,
        "normalized_prompt": normalized,
    }


def load_corpus(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        raise ValueError("corpus must be a JSON object with a cases list")
    cases: list[dict[str, Any]] = []
    for index, item in enumerate(payload["cases"]):
        if not isinstance(item, dict):
            raise ValueError(f"case {index} must be an object")
        if "prompt" not in item or "intent" not in item:
            raise ValueError(f"case {index} must include prompt and intent")
        cases.append(item)
    return cases


def validate_corpus(path: Path) -> dict[str, Any]:
    cases = load_corpus(path)
    failures: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for index, item in enumerate(cases):
        routed = route_prompt(str(item.get("prompt", "")))
        expected_agent = item.get("suggested_agent")
        expected_intent = item.get("intent")
        expected_workflow = item.get("workflow")
        failed = routed["intent"] != expected_intent or routed["suggested_agent"] != expected_agent
        if expected_workflow is not None and routed["workflow"] != expected_workflow:
            failed = True
        result = {"index": index, "expected": item, "actual": routed}
        results.append(result)
        if failed:
            failures.append(result)
    return {
        "status": "pass" if not failures else "fail",
        "total": len(cases),
        "passed": len(cases) - len(failures),
        "failed": len(failures),
        "failures": failures,
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Route a user prompt to CodexAI workflow, agent, and skills.")
    parser.add_argument("--prompt", default="", help="Prompt text to classify")
    parser.add_argument("--corpus", default="", help="Validate a JSON corpus of expected prompt routes")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        payload = validate_corpus(Path(args.corpus).expanduser().resolve()) if args.corpus else route_prompt(args.prompt)
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "text":
        if "intent" in payload:
            print(
                f"{payload['intent']}: agent={payload['suggested_agent']} "
                f"workflow={payload['workflow']} confidence={payload['confidence']}"
            )
        else:
            print(f"{payload['status']}: {payload.get('passed', 0)}/{payload.get('total', 0)} corpus cases passed")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status", "pass") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
