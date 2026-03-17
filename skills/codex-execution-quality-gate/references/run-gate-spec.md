# Run Gate
## Purpose
Orchestrate lint and test execution, then evaluate pass or fail in a single gate decision.
It provides one consolidated status used before completion.
## When to Run
- At the final gate step before declaring work done.
- Before creating a commit when quality status is uncertain.
- Before opening or updating a pull request.
- After significant code changes across multiple files.
## How AI Uses It
1. Run `run_gate.py` with the target project root.
2. Parse lint and test status, including exit codes and summaries.
3. Decide blocking pass or fail and report required next actions.
## Integration Behavior
- Trigger on `$codex-execution-quality-gate` or "run quality gate".
- Auto-run at the end of implementation workflows unless explicitly skipped.
- Blocking behavior: non-zero lint/test failure blocks completion.
- Strict-output behavior:
  - when `--strict-output` is supplied with `--output-file` or `--output-text`, output-guard failures block completion
  - when the deliverable looks like a `plan`, `review`, or `handoff`, strict-output should auto-enable by default
  - `--advisory-output` is the explicit escape hatch when the caller wants those deliverables treated as advisory-only
## Output Intent
- Provide aggregated lint, test, and optional output-quality status for completion decisions.
- Caveat: if tooling is not detected, output may contain warnings instead of strict failures.
