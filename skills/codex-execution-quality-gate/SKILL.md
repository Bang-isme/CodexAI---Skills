---
name: codex-execution-quality-gate
description: Run verification checks before completion using lint/test, security scanning, and optional bundle analysis. Use at final gate steps and block completion when mandatory failures are detected.
---

# Execution Quality Gate

## Activation

1. Activate during final `gate` steps.
2. Activate on explicit `$codex-execution-quality-gate`.
3. Run before saying work is complete.

## Phase X Verification Order

| Priority | Check | Script | Blocking |
| --- | --- | --- | --- |
| P0 | security scan | `scripts/security_scan.py` | yes for critical findings |
| P1 | lint | `scripts/run_gate.py` | yes when detected lint exits 1 |
| P2 | tests | `scripts/run_gate.py` | yes when detected tests exit 1 |
| P3 | bundle/dependency check | `scripts/bundle_check.py` | warning only |

## Execution

1. Run `run_gate.py` with project root.
2. Run `security_scan.py` with project root.
3. Optionally run `bundle_check.py` with project root.
4. Merge results and decide pass/fail.

### Decision Rules

- Completion allowed only if no blocking failures remain.
- Blocking failures must be fixed, then checks rerun.
- Warning-only outcomes may proceed with explicit warning to user.

## Script Paths

- Windows:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\<script>.py" --project-root <path>`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-execution-quality-gate/scripts/<script>.py" --project-root <path>`

## Override

If user says `skip gate` or `force complete`, comply and warn:
"Quality gate skipped. Lint/test/security status is unknown."

## Output Handling

For each script:

1. capture output
2. summarize errors/warnings/passes
3. ask whether to fix blocking errors when present
4. rerun after fixes to verify
