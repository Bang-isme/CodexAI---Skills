#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import argparse
import json
import re
import sys
from pathlib import Path
from json import JSONDecodeError
from typing import Dict, List, Sequence


SKILLS_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_VERSION = "1.2"
MIN_SCORE = 60
EDITORIAL_MIN_SCORE = 65
DEFAULT_CORPUS_DIR = Path(__file__).resolve().parent / "quality_corpus"


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


output_guard = load_script_module(
    "skills_output_guard_benchmark",
    "codex-execution-quality-gate/scripts/output_guard.py",
)
editorial_review = load_script_module(
    "skills_editorial_review_benchmark",
    "codex-execution-quality-gate/scripts/editorial_review.py",
)


TEST_CASES: List[Dict[str, object]] = [
    {
        "name": "jwt_auth_express",
        "input_prompt": "Add JWT auth to Express app",
        "expectations": {
            "specific_files": ["src/routes/auth.ts", "src/middleware/requireAuth.ts", "src/services/token_service.ts"],
            "commands": ["npm install", "npm test", "curl"],
            "test_plan": ["test", "verify", "next step"],
        },
        "sample_with_pack": "\n".join(
            [
                "Decision: implement JWT auth by updating `src/routes/auth.ts`, adding `src/middleware/requireAuth.ts`, and extracting token signing into `src/services/token_service.ts`.",
                "Evidence: run `npm install jsonwebtoken bcryptjs`, then `npm test -- auth.routes.test.ts` and `curl -X POST http://localhost:3000/api/login -d '{\"email\":\"demo@example.com\",\"password\":\"secret\"}'` to verify the token contract.",
                "Risk: token expiry and refresh semantics can drift if `.env.example` is not updated with `JWT_SECRET` and `JWT_TTL`.",
                "Next step: add a regression test for protected routes and document the middleware order in `src/app.ts`.",
            ]
        ),
        "sample_without_pack": "\n".join(
            [
                "Add JWT authentication using best practices.",
                "Secure the login flow, protect routes, and make sure the app scales well.",
                "Test the feature thoroughly before shipping.",
            ]
        ),
    },
    {
        "name": "fix_login_500",
        "input_prompt": "Fix login returning 500",
        "expectations": {
            "reproduction": ["reproduce", "post /api/login", "npm run dev"],
            "root_cause": ["root cause", "null guard", "login_controller.ts"],
            "regression_test": ["regression", "auth.routes.test.ts", "npm test"],
        },
        "sample_with_pack": "\n".join(
            [
                "Reproduction: start the app with `npm run dev`, then POST `/api/login` with a disabled user payload to trigger the current 500 path.",
                "Root cause: `src/controllers/login_controller.ts:48` reads `user.password_hash` before the null guard, so missing users fall into the generic exception handler.",
                "Decision: add the early 401 return in `src/controllers/login_controller.ts`, keep password comparison inside `src/services/auth_service.ts`, and log the rejected branch with the existing auth logger.",
                "Regression test: run `npm test -- auth.routes.test.ts -t \"returns 401 for unknown user\"` and verify the route no longer returns 500.",
            ]
        ),
        "sample_without_pack": "\n".join(
            [
                "The login error could be caused by the backend, the database, or validation logic.",
                "Check the logs, improve error handling, and retry the request.",
                "After that, add some tests so the problem does not happen again.",
            ]
        ),
    },
    {
        "name": "review_registration_security",
        "input_prompt": "Review security of user registration",
        "expectations": {
            "findings": ["finding", "severity", "evidence"],
            "specificity": ["src/routes/register.ts", "web/src/pages/Register.tsx", "curl"],
            "severity_labels": ["high", "medium", "low"],
        },
        "sample_with_pack": "\n".join(
            [
                "# Findings",
                "High: `src/routes/register.ts:72` trusts the inbound `role` field, so a client can self-assign elevated roles during registration.",
                "High evidence: reproduce with `python scripts/repro_register_role.py` or `pytest tests/security/test_registration.py -k role_escalation` and inspect the created record.",
                "Medium: password strength is enforced only in `web/src/pages/Register.tsx`; the API route still accepts weak passwords shorter than the UI policy.",
                "Medium evidence: server-side validation in `src/routes/register.ts` only checks non-empty values.",
                "Next step: remove `role` from the accepted payload, add server-side password policy checks, and rate-limit the endpoint before the next review.",
            ]
        ),
        "sample_without_pack": "\n".join(
            [
                "Make sure registration follows OWASP guidance.",
                "Validate inputs, hash passwords, use HTTPS, and think about abuse protection.",
                "A security review should cover common risks and best practices.",
            ]
        ),
    },
    {
        "name": "plan_dark_mode",
        "input_prompt": "Create implementation plan for dark mode",
        "expectations": {
            "task_breakdown": ["task breakdown", "phase", "step"],
            "dependencies": ["dependency", "depends", "tokens.css"],
            "verification": ["verify", "npm test", "storybook"],
        },
        "sample_with_pack": "\n".join(
            [
                "# Implementation Plan",
                "Decision: implement dark mode through semantic tokens first, then migrate the highest-traffic surfaces after the token contract is stable.",
                "Task breakdown:",
                "1. Add semantic tokens in `src/styles/tokens.css` for background, text, border, and accent colors.",
                "2. Add persisted theme state in `src/context/theme.tsx` and wire a toggle into `src/components/Header.tsx`.",
                "3. Update high-risk surfaces first: dashboard, settings, and auth screens.",
                "Dependencies: token work must land before component rewrites, and the toggle depends on `ThemeProvider` being mounted in `src/App.tsx`.",
                "Risk: contrast regressions are most likely in dense forms and chart legends, so those screens need manual visual QA before release.",
                "Verification: run `npm test -- theme-toggle.spec.ts`, review the dark-mode stories in Storybook, and manually verify contrast on login and settings pages.",
                "Next step: assign one owner for token review and one owner for visual QA before implementation starts.",
            ]
        ),
        "sample_without_pack": "\n".join(
            [
                "Plan the dark mode work in a few steps.",
                "Add a toggle, update styles, and test everything after implementation.",
                "Be mindful of dependencies and user experience.",
            ]
        ),
    },
    {
        "name": "session_summary",
        "input_prompt": "Summarize what was done this session",
        "expectations": {
            "file_list": ["skills/codex-execution-quality-gate/scripts/auto_gate.py", "skills/.system/REGISTRY.md"],
            "decision_log": ["decision", "deploy only", "registry"],
            "verification": ["pytest", "smoke_test.py", "validation"],
        },
        "sample_with_pack": "\n".join(
            [
                "Current state: added `skills/codex-execution-quality-gate/scripts/auto_gate.py`, updated `skills/.system/REGISTRY.md`, and wired the new aliases into `skills/codex-master-instructions/SKILL.md`.",
                "Decision: keep `suggest_improvements.py` marked as deploy-only in the registry so `auto_gate.py --mode deploy` stays truthful without pretending it runs in quick mode.",
                "Evidence: ran `python -m pytest skills/tests -q`, `python skills/tests/smoke_test.py`, and validated `python skills/codex-execution-quality-gate/scripts/auto_gate.py --project-root D:\\CodexAI---Skills --mode quick`.",
                "Next step: fix the repo security findings before relying on quick mode as a passing release check.",
            ]
        ),
        "sample_without_pack": "\n".join(
            [
                "We made several improvements during this session.",
                "A number of files were updated and the workflow is now better organized.",
                "Testing was done and there are some follow-up items left.",
            ]
        ),
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run static output quality benchmark cases.")
    parser.add_argument(
        "--corpus-dir",
        default=str(DEFAULT_CORPUS_DIR),
        help="Directory containing additional JSON benchmark cases",
    )
    return parser.parse_args()


def normalize_sample(value: object, field: str, source: Path) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    raise ValueError(f"{source}: {field} must be a string or list of strings")


def normalize_expectation_needles(value: object, source: Path, case_name: str, expectation_name: str) -> List[str]:
    if isinstance(value, str):
        needles = [value]
    elif isinstance(value, list):
        needles = [str(item) for item in value]
    else:
        raise ValueError(f"{source}: {case_name}.{expectation_name} must be a string or list of strings")
    needles = [needle for needle in needles if needle.strip()]
    if not needles:
        raise ValueError(f"{source}: {case_name}.{expectation_name} must contain at least one non-empty matcher")
    return needles


def validate_case(case: object, source: Path) -> Dict[str, object]:
    if not isinstance(case, dict):
        raise ValueError(f"{source}: benchmark case must be an object")
    required = {"name", "input_prompt", "expectations", "sample_with_pack", "sample_without_pack"}
    missing = sorted(required - set(case))
    if missing:
        raise ValueError(f"{source}: benchmark case is missing {', '.join(missing)}")
    expectations = case["expectations"]
    if not isinstance(expectations, dict):
        raise ValueError(f"{source}: expectations must be an object")
    case_name = str(case["name"])
    normalized_expectations = {
        str(name): normalize_expectation_needles(value, source, case_name, str(name))
        for name, value in expectations.items()
    }
    normalized = dict(case)
    normalized["expectations"] = normalized_expectations
    normalized["sample_with_pack"] = normalize_sample(case["sample_with_pack"], "sample_with_pack", source)
    normalized["sample_without_pack"] = normalize_sample(case["sample_without_pack"], "sample_without_pack", source)
    normalized["source"] = source.as_posix()
    return normalized


def load_corpus_cases(corpus_dir: Path) -> List[Dict[str, object]]:
    if not corpus_dir.exists():
        return []
    cases: List[Dict[str, object]] = []
    for path in sorted(corpus_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except JSONDecodeError as exc:
            raise ValueError(f"{path}: invalid JSON: {exc.msg}") from exc
        if isinstance(payload, list):
            entries = payload
        elif isinstance(payload, dict) and "cases" in payload:
            entries = payload["cases"]
        else:
            raise ValueError(f"{path}: corpus payload must be a list or contain a cases list")
        if not isinstance(entries, list):
            raise ValueError(f"{path}: corpus payload must be a list or contain a cases list")
        cases.extend(validate_case(entry, path) for entry in entries)
    return cases


def needle_matches(text: str, needle: str) -> bool:
    if re.fullmatch(r"[A-Za-z0-9 _-]+", needle):
        pattern = re.compile(rf"\b{re.escape(needle).replace(r'\ ', r'\s+')}\b", re.IGNORECASE)
        return bool(pattern.search(text))
    return needle.lower() in text.lower()


def contains_any(text: str, needles: Sequence[str]) -> bool:
    return any(needle_matches(text, needle) for needle in needles)


def evaluate_expectations(text: str, expectations: Dict[str, Sequence[str]]) -> Dict[str, bool]:
    return {
        name: contains_any(text, needles)
        for name, needles in expectations.items()
    }


def score_text(text: str) -> Dict[str, object]:
    return output_guard.analyze_text(text, min_score=MIN_SCORE)


def score_editorial_text(text: str, deliverable_kind: str = "auto") -> Dict[str, object]:
    return editorial_review.analyze_text(
        text,
        min_score=EDITORIAL_MIN_SCORE,
        deliverable_kind=deliverable_kind,
    )


def expectation_hit_rate(hits: Dict[str, bool]) -> float:
    if not hits:
        return 0.0
    return round((sum(1 for value in hits.values() if value) / len(hits)) * 100, 1)


def percentage_improvement(with_pack: float, without_pack: float) -> float:
    if without_pack <= 0:
        return 100.0 if with_pack > 0 else 0.0
    return round(((with_pack - without_pack) / without_pack) * 100, 1)


def benchmark_case(case: Dict[str, object]) -> Dict[str, object]:
    with_pack_text = str(case["sample_with_pack"])
    without_pack_text = str(case["sample_without_pack"])
    expectations = dict(case["expectations"])
    deliverable_kind = str(case.get("deliverable_kind", "auto"))

    with_pack_report = score_text(with_pack_text)
    without_pack_report = score_text(without_pack_text)
    with_pack_editorial = score_editorial_text(with_pack_text, deliverable_kind)
    without_pack_editorial = score_editorial_text(without_pack_text, deliverable_kind)

    with_pack_expectations = evaluate_expectations(with_pack_text, expectations)
    without_pack_expectations = evaluate_expectations(without_pack_text, expectations)

    with_pack_score = int(with_pack_report["score"])
    without_pack_score = int(without_pack_report["score"])
    with_pack_editorial_score = int(with_pack_editorial["score"])
    without_pack_editorial_score = int(without_pack_editorial["score"])
    with_pack_quality_index = round((with_pack_score + with_pack_editorial_score) / 2, 1)
    without_pack_quality_index = round((without_pack_score + without_pack_editorial_score) / 2, 1)

    return {
        "name": case["name"],
        "input_prompt": case["input_prompt"],
        "deliverable_kind": deliverable_kind,
        "source": case.get("source", "built-in"),
        "with_pack": {
            "score": with_pack_score,
            "status": with_pack_report["status"],
            "editorial_score": with_pack_editorial_score,
            "editorial_status": with_pack_editorial["status"],
            "quality_index": with_pack_quality_index,
            "issues": with_pack_report["issues"],
            "suggestions": with_pack_report["suggestions"],
            "expectation_hits": with_pack_expectations,
            "expectation_hit_rate": expectation_hit_rate(with_pack_expectations),
        },
        "without_pack": {
            "score": without_pack_score,
            "status": without_pack_report["status"],
            "editorial_score": without_pack_editorial_score,
            "editorial_status": without_pack_editorial["status"],
            "quality_index": without_pack_quality_index,
            "issues": without_pack_report["issues"],
            "suggestions": without_pack_report["suggestions"],
            "expectation_hits": without_pack_expectations,
            "expectation_hit_rate": expectation_hit_rate(without_pack_expectations),
        },
        "delta": with_pack_score - without_pack_score,
        "editorial_delta": with_pack_editorial_score - without_pack_editorial_score,
        "quality_index_delta": round(with_pack_quality_index - without_pack_quality_index, 1),
        "improvement_percentage": percentage_improvement(with_pack_score, without_pack_score),
        "quality_index_improvement_percentage": percentage_improvement(
            with_pack_quality_index,
            without_pack_quality_index,
        ),
    }


def main() -> int:
    output_guard.configure_utf8_stdio()
    args = parse_args()
    corpus_dir = Path(args.corpus_dir).expanduser().resolve()
    try:
        corpus_cases = load_corpus_cases(corpus_dir)
    except ValueError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    all_cases = [*TEST_CASES, *corpus_cases]
    per_case = [benchmark_case(case) for case in all_cases]
    avg_with_pack = round(sum(int(case["with_pack"]["score"]) for case in per_case) / len(per_case), 1)
    avg_without_pack = round(sum(int(case["without_pack"]["score"]) for case in per_case) / len(per_case), 1)
    avg_editorial_with_pack = round(sum(int(case["with_pack"]["editorial_score"]) for case in per_case) / len(per_case), 1)
    avg_editorial_without_pack = round(sum(int(case["without_pack"]["editorial_score"]) for case in per_case) / len(per_case), 1)
    avg_quality_index_with_pack = round(sum(float(case["with_pack"]["quality_index"]) for case in per_case) / len(per_case), 1)
    avg_quality_index_without_pack = round(sum(float(case["without_pack"]["quality_index"]) for case in per_case) / len(per_case), 1)
    avg_expectation_hit_rate_with_pack = round(sum(float(case["with_pack"]["expectation_hit_rate"]) for case in per_case) / len(per_case), 1)
    avg_expectation_hit_rate_without_pack = round(sum(float(case["without_pack"]["expectation_hit_rate"]) for case in per_case) / len(per_case), 1)

    payload = {
        "status": "pass",
        "benchmark_version": BENCHMARK_VERSION,
        "test_cases": len(all_cases),
        "built_in_cases": len(TEST_CASES),
        "corpus_cases": len(corpus_cases),
        "corpus_dir": corpus_dir.as_posix(),
        "avg_score_with_pack": avg_with_pack,
        "avg_score_without_pack": avg_without_pack,
        "avg_editorial_score_with_pack": avg_editorial_with_pack,
        "avg_editorial_score_without_pack": avg_editorial_without_pack,
        "avg_quality_index_with_pack": avg_quality_index_with_pack,
        "avg_quality_index_without_pack": avg_quality_index_without_pack,
        "avg_expectation_hit_rate_with_pack": avg_expectation_hit_rate_with_pack,
        "avg_expectation_hit_rate_without_pack": avg_expectation_hit_rate_without_pack,
        "improvement_percentage": percentage_improvement(avg_with_pack, avg_without_pack),
        "editorial_improvement_percentage": percentage_improvement(avg_editorial_with_pack, avg_editorial_without_pack),
        "quality_index_improvement_percentage": percentage_improvement(
            avg_quality_index_with_pack,
            avg_quality_index_without_pack,
        ),
        "per_case": per_case,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
