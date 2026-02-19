# Gate Policy

## Verification Sequence

1. `security_scan.py`
2. `run_gate.py` (lint + tests)
3. `bundle_check.py` (optional, warning-only)
4. `tech_debt_scan.py` (optional, warning-only)
5. `suggest_improvements.py` (post-task, optional, warning-only)
6. `predict_impact.py` (pre-edit, optional, warning-only)
7. `quality_trend.py` (periodic, optional, warning-only)
8. `ux_audit.py` (pre-UI delivery, optional, warning-only)
9. `accessibility_check.py` (public-facing pages, optional, warning-only)
10. `lighthouse_audit.py` (pre-production URL audit, optional, warning-only)
11. `playwright_runner.py` (E2E setup/execution helper, optional, warning-only)
12. `with_server.py` (runtime server lifecycle helper, optional, warning-only)

## Blocking Rules

- Block when security scan reports critical findings.
- Block when detected lint exits with code `1`.
- Block when detected tests exit with code `1`.

## Warning Rules

- No tool detected.
- Timeout or command failure with exit code `>= 2`.
- Bundle/dependency concerns.
- Missing lock files or missing dependency installation artifacts.
- Tech debt findings (TODO/FIXME/HACK, long functions/files, duplicates, unused exports).
- Tech debt parse or git-blame fallback warnings.
- Improvement suggestions (long functions/files, missing tests, magic numbers, deep nesting, debug leftovers).
- Impact predictor blast-radius alerts.
- Quality trend health-score degradation signals.
- UX static audit findings.
- Accessibility static WCAG findings.
- Lighthouse CLI not installed, URL not reachable, or Lighthouse run warnings.
- Playwright not installed/setup incomplete or E2E inventory gaps.
- Runtime helper setup failures from `with_server.py` (server command, port wait timeout, command wiring).

## Lint Detection Order (run_gate.py)

1. `package.json` script `lint`
2. ESLint config
3. Biome config
4. Ruff in `pyproject.toml`
5. Flake8 config
6. `golangci-lint` config

## Test Detection Order (run_gate.py)

1. `package.json` script `test` (skip placeholder script)
2. Jest config
3. Vitest config
4. Pytest config
5. Cargo manifest
6. Go modules

## Timeout Defaults

- Lint: 120 seconds
- Tests: 300 seconds

Timeouts are warnings in MVP and do not block completion by themselves.

## Tech Debt Scan Policy

- `tech_debt_scan.py` is advisory in MVP.
- Findings are reported with priorities but do not block completion.
- Parse failures in specific files must be reported as warnings, then continue scanning.
- If git blame is unavailable, TODO age scoring falls back gracefully and remains warning-only.

## Pre-Commit Intelligence Policy

- `pre_commit_check.py` is optional but recommended before local commits.
- It evaluates staged files only (`git diff --cached`) instead of scanning the full repository.
- Secret detection is always blocking.
- Lint/test/tooling warnings remain warning-level unless strict mode is enabled.

## Smart Test Selector Policy

- `smart_test_selector.py` is the default fast-feedback strategy for local iteration.
- Prefer selecting related tests over running the entire suite when developer feedback speed matters.
- If related tests cannot be identified, warn and suggest running full suite.

## Improvement Suggester Policy

- `suggest_improvements.py` runs after task completion as an optional quality enhancer.
- Findings are advisory and never block completion in MVP.
- Prioritize top 3 findings when presenting to users, sorted by `high > medium > low`.
- In proactive mode, auto-run is allowed after complex tasks if context budget permits.

## Impact Predictor Policy

- `predict_impact.py` is a pre-edit advisory check.
- Use before model/interface/shared utility updates to estimate blast radius.
- Output must be communicated before implementation for risk-aware planning.
- Results are non-blocking in MVP.

## Quality Trend Policy

- `quality_trend.py --record` stores periodic quality snapshots in `.codex/quality/snapshots/`.
- `quality_trend.py --report` compares historical snapshots and surfaces trajectory.
- Trend insights are advisory and intended for sprint planning/tech-debt prioritization.
- Results are non-blocking in MVP.

## UX Audit Policy

- `ux_audit.py` is optional and recommended before UI delivery.
- Findings are advisory in MVP and do not block completion.
- Use score and issue severity to prioritize remediation.

## Accessibility Check Policy

- `accessibility_check.py` is optional and recommended for public-facing pages.
- WCAG issues are advisory in MVP and should be prioritized for user-critical flows.
- Compliance score trend can be used as a pre-release signal.

## Lighthouse Audit Policy

- `lighthouse_audit.py` is optional and recommended before production deploy.
- Requires a reachable running server URL.
- Missing Lighthouse tool or run preconditions must return actionable guidance, not crashes.
- Results are advisory and non-blocking in MVP.

## Playwright Runner Policy

- `playwright_runner.py` is optional and recommended for critical user journeys.
- `check` mode verifies setup; `generate` bootstraps tests; `run` executes E2E.
- Missing Playwright setup must return installation steps as warnings/advice.
- Results are advisory and non-blocking in MVP.

## With Server Helper Policy

- `with_server.py` is a helper-only utility for runtime audits that need controlled startup/shutdown.
- Use it before `lighthouse_audit.py` or `playwright_runner.py` when local services must be bootstrapped.
- Failures are advisory in MVP and should return actionable command/port guidance.
