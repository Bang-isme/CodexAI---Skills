#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Sequence


SKILLS_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_VERSION = "1.0"
MIN_SCORE = 60


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
                "Task breakdown:",
                "1. Add semantic tokens in `src/styles/tokens.css` for background, text, border, and accent colors.",
                "2. Add persisted theme state in `src/context/theme.tsx` and wire a toggle into `src/components/Header.tsx`.",
                "3. Update high-risk surfaces first: dashboard, settings, and auth screens.",
                "Dependencies: token work must land before component rewrites, and the toggle depends on `ThemeProvider` being mounted in `src/App.tsx`.",
                "Verification: run `npm test -- theme-toggle.spec.ts`, review the dark-mode stories in Storybook, and manually verify contrast on login and settings pages.",
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


def percentage_improvement(with_pack: float, without_pack: float) -> float:
    if without_pack <= 0:
        return 100.0 if with_pack > 0 else 0.0
    return round(((with_pack - without_pack) / without_pack) * 100, 1)


def benchmark_case(case: Dict[str, object]) -> Dict[str, object]:
    with_pack_text = str(case["sample_with_pack"])
    without_pack_text = str(case["sample_without_pack"])
    expectations = dict(case["expectations"])

    with_pack_report = score_text(with_pack_text)
    without_pack_report = score_text(without_pack_text)

    with_pack_expectations = evaluate_expectations(with_pack_text, expectations)
    without_pack_expectations = evaluate_expectations(without_pack_text, expectations)

    with_pack_score = int(with_pack_report["score"])
    without_pack_score = int(without_pack_report["score"])

    return {
        "name": case["name"],
        "input_prompt": case["input_prompt"],
        "with_pack": {
            "score": with_pack_score,
            "status": with_pack_report["status"],
            "issues": with_pack_report["issues"],
            "suggestions": with_pack_report["suggestions"],
            "expectation_hits": with_pack_expectations,
        },
        "without_pack": {
            "score": without_pack_score,
            "status": without_pack_report["status"],
            "issues": without_pack_report["issues"],
            "suggestions": without_pack_report["suggestions"],
            "expectation_hits": without_pack_expectations,
        },
        "delta": with_pack_score - without_pack_score,
        "improvement_percentage": percentage_improvement(with_pack_score, without_pack_score),
    }


def main() -> int:
    per_case = [benchmark_case(case) for case in TEST_CASES]
    avg_with_pack = round(sum(int(case["with_pack"]["score"]) for case in per_case) / len(per_case), 1)
    avg_without_pack = round(sum(int(case["without_pack"]["score"]) for case in per_case) / len(per_case), 1)

    payload = {
        "benchmark_version": BENCHMARK_VERSION,
        "test_cases": len(TEST_CASES),
        "avg_score_with_pack": avg_with_pack,
        "avg_score_without_pack": avg_without_pack,
        "improvement_percentage": percentage_improvement(avg_with_pack, avg_without_pack),
        "per_case": per_case,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
