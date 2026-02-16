# Gate Policy

## Verification Sequence

1. `security_scan.py`
2. `run_gate.py` (lint + tests)
3. `bundle_check.py` (optional, warning-only)

## Blocking Rules

- Block when security scan reports critical findings.
- Block when detected lint exits with code `1`.
- Block when detected tests exit with code `1`.

## Warning Rules

- No tool detected.
- Timeout or command failure with exit code `>= 2`.
- Bundle/dependency concerns.
- Missing lock files or missing dependency installation artifacts.

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
