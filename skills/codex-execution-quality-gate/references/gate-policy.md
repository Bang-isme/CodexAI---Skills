# Gate Policy

## Verification Sequence

1. `security_scan.py`
2. `run_gate.py` (lint + tests)
3. `bundle_check.py` (optional, warning-only)
4. `tech_debt_scan.py` (optional, warning-only)
5. `suggest_improvements.py` (post-task, optional, warning-only)

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
