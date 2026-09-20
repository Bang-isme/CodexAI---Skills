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

# Keep ROUTES as the catalog used by linkage tests. Scoring uses extra fields.
ROUTES: list[dict[str, Any]] = [
    {
        "intent": "review",
        "agent": "security-auditor",
        "workflow": "review",
        "skills": ["codex-security-specialist", "codex-execution-quality-gate"],
        "priority": 100,
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
        "negative_signals": [],
    },
    {
        "intent": "debug",
        "agent": "debugger",
        "workflow": "debug",
        "skills": ["codex-systematic-debugging", "codex-test-driven-development"],
        "priority": 90,
        "signals": ["bug", "debug", "fix", "crash", "error", "traceback", "broken", "lỗi", "sửa lỗi", "không chạy"],
        "negative_signals": [],
    },
    {
        "intent": "deploy",
        "agent": "devops-engineer",
        "workflow": "deploy",
        "skills": ["codex-execution-quality-gate", "codex-git-autopilot"],
        "priority": 80,
        "signals": ["deploy", "release", "publish", "ci", "cd", "pipeline", "docker", "kubernetes", "prod", "production"],
        "negative_signals": [],
    },
    {
        "intent": "review",
        "agent": "visual-quality-reviewer",
        "workflow": "review",
        "skills": ["codex-visual-quality-gate", "codex-design-system"],
        "priority": 55,
        "signals": [
            "visual review",
            "visual quality",
            "screenshot review",
            "screenshot",
            "ui review",
            "design critique",
            "critique",
            "xem lại giao diện",
            "đánh giá visual",
        ],
        "negative_signals": ["security", "vulnerability", "lỗ hổng"],
    },
    {
        "intent": "build",
        "agent": "ui-ux-designer",
        "workflow": "plan",
        "skills": ["codex-ui-ux-design", "codex-design-system"],
        "priority": 50,
        "signals": [
            "user flow",
            "user journey",
            "information architecture",
            "wireframe",
            "onboarding flow",
            "empty state",
            "cognitive load",
            "ia ",
            "ux flow",
            "luồng người dùng",
            "kiến trúc thông tin",
        ],
        "negative_signals": ["implement the approved", "react component", "css only"],
    },
    {
        "intent": "build",
        "agent": "creative-director",
        "workflow": "prototype",
        "skills": [
            "codex-creative-direction",
            "codex-ui-ux-design",
            "codex-design-system",
            "codex-visual-quality-gate",
        ],
        "priority": 48,
        "signals": [
            "beautiful",
            "stunning",
            "art direction",
            "creative direction",
            "visual identity",
            "redesign",
            "rebrand",
            "landing page",
            "marketing site",
            "make it look",
            "trang chủ",
            "landing",
            "đẹp",
            "sáng tạo",
            "nhận diện",
            "thiết kế lại",
            "portfolio",
            "immersive",
            "gallery",
        ],
        "negative_signals": [
            "implement the approved",
            "approved design",
            "only implement",
            "traceback",
            "endpoint",
            "without redesign",
            "no redesign",
            "không đổi",
        ],
    },
    {
        "intent": "build",
        "agent": "creative-designer",
        "workflow": "create",
        "skills": ["codex-design-system", "codex-design-md"],
        "priority": 46,
        "signals": [
            "visual system",
            "type ramp",
            "color system",
            "component grammar",
            "design tokens",
            "layout and type",
            "ngữ pháp component",
            "hệ thống visual",
        ],
        "negative_signals": ["implement the approved", "from scratch fullstack"],
    },
    {
        "intent": "build",
        "agent": "frontend-specialist",
        "workflow": "create",
        "skills": ["codex-domain-specialist", "codex-test-driven-development", "codex-design-system"],
        "priority": 44,
        "signals": [
            "frontend",
            "ui",
            "ux",
            "react",
            "vue",
            "page",
            "component",
            "css",
            "dashboard",
            "giao diện",
            "spacing",
            "padding",
            "cta",
            "motion",
        ],
        "negative_signals": [],
    },
    {
        "intent": "build",
        "agent": "backend-specialist",
        "workflow": "create",
        "skills": ["codex-domain-specialist", "codex-test-driven-development"],
        "priority": 44,
        "signals": ["backend", "api", "database", "server", "endpoint", "auth", "service", "worker"],
        "negative_signals": ["giao diện", "landing page", "react dashboard"],
    },
    {
        "intent": "test",
        "agent": "test-engineer",
        "workflow": "create",
        "skills": ["codex-test-driven-development", "codex-execution-quality-gate"],
        "priority": 72,
        "signals": [
            "tdd",
            "unit test",
            "unit tests",
            "write tests",
            "test coverage",
            "pytest",
            "jest",
            "vitest",
            "playwright",
            "regression test",
            "viết test",
            "phủ test",
            "kiểm thử",
            "$tdd",
            "$red-green",
        ],
        "negative_signals": ["deploy", "production", "lỗ hổng", "traceback"],
    },
    {
        "intent": "scrum",
        "agent": "scrum-master",
        "workflow": "plan",
        "skills": ["codex-scrum-subagents", "codex-workflow-autopilot"],
        "priority": 70,
        "signals": [
            "sprint planning",
            "daily scrum",
            "standup",
            "retrospective",
            "sprint review",
            "backlog refinement",
            "user story",
            "scrum master",
            "sprint goal",
            "lập kế hoạch sprint",
            "họp daily",
            "retrospect",
            "$sprint-plan",
            "$retro",
            "$scrum-install",
        ],
        "negative_signals": ["traceback", "vulnerability"],
    },
    {
        "intent": "pulse",
        "agent": "planner",
        "workflow": "plan",
        "skills": ["codex-project-pulse", "codex-workflow-autopilot"],
        "priority": 68,
        "signals": [
            "$today",
            "$pulse",
            "$daily",
            "$status",
            "$brief",
            "hôm nay thế nào",
            "what's next",
            "what should i work on",
            "project status",
            "project pulse",
            "daily brief",
        ],
        "negative_signals": ["traceback", "vulnerability", "deploy to production"],
    },
    {
        "intent": "docs",
        "agent": "planner",
        "workflow": "handoff",
        "skills": ["codex-document-writer", "codex-project-memory"],
        "priority": 42,
        "signals": ["docs", "document", "readme", "guide", "handoff", "tài liệu", "hướng dẫn"],
        "negative_signals": [],
    },
    {
        "intent": "refactor",
        "agent": "planner",
        "workflow": "refactor",
        "skills": ["codex-plan-writer", "codex-test-driven-development"],
        "priority": 40,
        "signals": ["refactor", "cleanup", "restructure", "optimize", "tối ưu", "cải thiện"],
        "negative_signals": [],
    },
    {
        "intent": "build",
        "agent": "planner",
        "workflow": "prototype",
        "skills": ["codex-spec-driven-development", "codex-plan-writer"],
        "priority": 20,
        "signals": ["prototype", "mvp", "from scratch", "fullstack"],
        "negative_signals": [
            "frontend",
            "ui",
            "ux",
            "react",
            "vue",
            "page",
            "component",
            "css",
            "giao diện",
            "backend",
            "api",
            "endpoint",
            "landing",
            "dashboard",
        ],
    },
]

INJECTION_RE = re.compile(
    r"\b(ignore|bypass|override|forget|disable|jailbreak|system prompt|previous instructions)\b",
    re.IGNORECASE,
)

IMPLEMENTATION_ONLY_RE = re.compile(
    r"(implement the approved|approved design|implementation-only|chỉ implement|chỉ code|code the approved)",
    re.IGNORECASE,
)

REFINE_RE = re.compile(
    r"\b(tweak|refine|spacing|polish|microcopy|kerning|chỉnh|tinh chỉnh|spacing|padding)\b",
    re.IGNORECASE,
)

REDESIGN_RE = re.compile(
    r"\b(redesign|rebrand|thiết kế lại|làm lại giao diện|visual overhaul)\b",
    re.IGNORECASE,
)

NEW_SURFACE_RE = re.compile(
    r"\b(from scratch|new (site|app|landing|website)|make a|build a (beautiful|stunning)|tạo (một )?(trang|landing|website)|xây trang)\b",
    re.IGNORECASE,
)


def normalize_prompt(prompt: str) -> str:
    return " ".join(prompt.strip().split())


def detect_design_operation(lowered: str) -> str | None:
    if REDESIGN_RE.search(lowered):
        return "redesign"
    if REFINE_RE.search(lowered) and not REDESIGN_RE.search(lowered):
        return "refine"
    if NEW_SURFACE_RE.search(lowered) or "landing page" in lowered:
        return "new"
    if any(token in lowered for token in ("frontend", "ui", "giao diện", "component", "dashboard", "react", "vue")):
        return "extend"
    return None


def detect_surface_mode(lowered: str) -> str | None:
    if any(token in lowered for token in ("landing", "pricing", "marketing", "campaign", "trang chủ")):
        return "persuade"
    if any(token in lowered for token in ("dashboard", "admin", "settings", "operator", "app ui")):
        return "operate"
    if any(token in lowered for token in ("docs", "readme", "article", "blog", "tài liệu")):
        return "read"
    if any(token in lowered for token in ("portfolio", "immersive", "gallery", "experience")):
        return "experience"
    return None


def ambiguity_reasons(normalized: str, design_operation: str | None) -> list[str]:
    lowered = normalized.lower()
    reasons: list[str] = []
    if not normalized:
        return ["empty_prompt"]
    if design_operation in {"new", "redesign"}:
        if not any(token in lowered for token in ("audience", "user", "customer", "khách", "người dùng")):
            reasons.append("missing_audience")
        if not any(token in lowered for token in ("brand", "reference", "screenshot", "incumbent", "DESIGN.md")):
            reasons.append("missing_visual_authority")
        if not any(token in lowered for token in ("proof", "metric", "claim", "offer", "sản phẩm")):
            reasons.append("missing_product_proof")
    return reasons


def supporting_agents_for(agent: str, design_operation: str | None, implementation_only: bool) -> list[str]:
    if implementation_only or agent in {
        "debugger",
        "security-auditor",
        "backend-specialist",
        "devops-engineer",
        "test-engineer",
        "scrum-master",
    }:
        return []
    if agent == "creative-director":
        return ["ui-ux-designer", "creative-designer", "frontend-specialist", "visual-quality-reviewer"]
    if agent == "ui-ux-designer":
        extras = ["frontend-specialist"]
        if design_operation in {"new", "redesign"}:
            extras = ["creative-designer", "frontend-specialist", "visual-quality-reviewer"]
        return extras
    if agent == "creative-designer":
        return ["frontend-specialist", "visual-quality-reviewer"]
    if agent == "frontend-specialist" and design_operation in {"new", "redesign"}:
        return ["visual-quality-reviewer"]
    if agent == "visual-quality-reviewer":
        return []
    return []


def required_evidence_for(agent: str, design_operation: str | None) -> list[str]:
    evidence: list[str] = []
    if agent in {"creative-director", "ui-ux-designer", "creative-designer", "frontend-specialist", "visual-quality-reviewer"}:
        if design_operation in {"new", "redesign"}:
            evidence.extend(["design_contract", "direction_or_ux_contract"])
        if agent in {"frontend-specialist", "visual-quality-reviewer"} or design_operation in {"new", "redesign"}:
            evidence.extend(["mechanical_visual_gate", "desktop_mobile_review"])
    return evidence


def signal_present(signal: str, lowered: str) -> bool:
    if signal == "redesign" and any(token in lowered for token in ("without redesign", "no redesign", "không redesign")):
        return False
    token = signal.strip().lower()
    if not token:
        return False
    if any(ord(char) > 127 for char in token) or " " in token:
        return token in lowered
    return re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", lowered) is not None


def score_route(route: dict[str, Any], lowered: str, injection_detected: bool) -> tuple[int, list[str]]:
    matches = [signal for signal in route["signals"] if signal_present(signal, lowered)]
    if route["workflow"] == "handoff" and ("tài liệu" in lowered or "hướng dẫn" in lowered):
        matches.append("vietnamese_docs")
    negatives = [signal for signal in route.get("negative_signals") or [] if signal in lowered]
    score = len(matches) * 3 - len(negatives) * 4
    score += int(route.get("priority") or 0)
    if route["agent"] == "security-auditor" and matches:
        score += 2
    if injection_detected and route["agent"] == "security-auditor":
        score += INJECTION_SECURITY_BOOST
        if "prompt_injection" not in matches:
            matches.append("prompt_injection")
    if score <= 0:
        return 0, matches
    return score, matches


def empty_payload(warnings: list[str]) -> dict[str, Any]:
    return {
        "intent": "other",
        "suggested_agent": None,
        "workflow": None,
        "required_skills": [],
        "confidence": 0.0,
        "matched_signals": [],
        "warnings": warnings,
        "normalized_prompt": "",
        "design_operation": None,
        "surface_mode": None,
        "supporting_agents": [],
        "ambiguity_reasons": ["empty_prompt"],
        "required_evidence": [],
    }


def fallback_payload(normalized: str, warnings: list[str]) -> dict[str, Any]:
    design_operation = detect_design_operation(normalized.lower())
    surface_mode = detect_surface_mode(normalized.lower())
    return {
        "intent": "other",
        "suggested_agent": None,
        "workflow": "plan",
        "required_skills": ["codex-intent-context-analyzer", "codex-plan-writer"],
        "confidence": 0.25,
        "matched_signals": [],
        "warnings": warnings + ["low_confidence_fallback"],
        "normalized_prompt": normalized,
        "design_operation": design_operation,
        "surface_mode": surface_mode,
        "supporting_agents": [],
        "ambiguity_reasons": ambiguity_reasons(normalized, design_operation),
        "required_evidence": [],
    }


def route_prompt(prompt: str) -> dict[str, Any]:
    normalized = normalize_prompt(prompt)
    warnings: list[str] = []
    if not normalized:
        return empty_payload(["empty_prompt"])

    injection_detected = bool(INJECTION_RE.search(normalized))
    if injection_detected:
        warnings.append("prompt_injection_signal")

    lowered = normalized.lower()
    implementation_only = bool(IMPLEMENTATION_ONLY_RE.search(lowered))
    design_operation = detect_design_operation(lowered)
    surface_mode = detect_surface_mode(lowered)

    best: dict[str, Any] | None = None
    best_matches: list[str] = []
    best_score = 0
    for route in ROUTES:
        if implementation_only and route["agent"] in {"creative-director", "ui-ux-designer", "creative-designer"}:
            continue
        if design_operation == "refine" and route["agent"] == "creative-director":
            continue
        score, matches = score_route(route, lowered, injection_detected)
        if not matches and not (injection_detected and route["agent"] == "security-auditor"):
            continue
        if score > best_score:
            best = route
            best_matches = matches
            best_score = score

    if not best:
        return fallback_payload(normalized, warnings)

    supporting = supporting_agents_for(best["agent"], design_operation, implementation_only)
    if implementation_only:
        supporting = [name for name in supporting if name == "visual-quality-reviewer"]
        supporting = []

    required_skills = list(best["skills"])
    if best["agent"] == "creative-director":
        required_skills = [
            "codex-creative-direction",
            "codex-ui-ux-design",
            "codex-design-system",
            "codex-visual-quality-gate",
        ]
    elif best["agent"] == "frontend-specialist" and not implementation_only and design_operation in {"new", "redesign"}:
        if "codex-visual-quality-gate" not in required_skills:
            required_skills.append("codex-visual-quality-gate")

    confidence = min(0.95, 0.45 + (0.15 * len(best_matches)))
    return {
        "intent": best["intent"],
        "suggested_agent": best["agent"],
        "workflow": best["workflow"],
        "required_skills": required_skills,
        "confidence": round(confidence, 2),
        "matched_signals": best_matches,
        "warnings": warnings,
        "normalized_prompt": normalized,
        "design_operation": design_operation,
        "surface_mode": surface_mode,
        "supporting_agents": supporting,
        "ambiguity_reasons": ambiguity_reasons(normalized, design_operation),
        "required_evidence": required_evidence_for(best["agent"], design_operation),
    }


def merge_routing(prompt_route: dict[str, Any], repo_report: dict[str, Any] | None = None) -> dict[str, Any]:
    """Prompt-router user intent wins; runtime-hook repo state fills gaps only."""
    merged = dict(prompt_route)
    repo = repo_report if isinstance(repo_report, dict) else {}
    repo_agent = repo.get("suggested_agent")
    repo_workflow = repo.get("workflow_recommendation") if isinstance(repo.get("workflow_recommendation"), dict) else {}
    merged["repo_suggested_agent"] = repo_agent
    merged["repo_workflow"] = repo_workflow.get("workflow")
    intent = merged.get("intent")
    agent = merged.get("suggested_agent")
    if intent not in {None, "other"} and agent:
        merged["precedence"] = "prompt_router"
        return merged
    if repo_agent:
        merged["suggested_agent"] = repo_agent
        if not merged.get("workflow") and repo_workflow.get("alias"):
            alias = str(repo_workflow.get("alias", "")).lstrip("$")
            merged["workflow"] = alias or merged.get("workflow")
        merged["precedence"] = "runtime_hook"
        merged["warnings"] = list(merged.get("warnings") or []) + ["repo_state_fallback"]
        return merged
    merged["precedence"] = "prompt_router"
    return merged


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
        for field in ("design_operation", "surface_mode"):
            if field in item and routed.get(field) != item.get(field):
                failed = True
        if "supporting_agents" in item:
            expected_support = item.get("supporting_agents") or []
            actual_support = routed.get("supporting_agents") or []
            if list(expected_support) != list(actual_support):
                failed = True
        if "must_include_skills" in item:
            required = item.get("must_include_skills") or []
            actual_skills = routed.get("required_skills") or []
            if any(skill not in actual_skills for skill in required):
                failed = True
        if "must_not_include_agents" in item:
            forbidden = set(item.get("must_not_include_agents") or [])
            loaded = {routed.get("suggested_agent"), *(routed.get("supporting_agents") or [])}
            if loaded & forbidden:
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
