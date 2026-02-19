# Pre Commit Check
## Purpose
Run targeted quality checks only on staged or changed files before commit.
It is designed for fast feedback without scanning the full repository.
## When to Run
- Before every local commit.
- As the first step of the quality gate in iterative development.
- On explicit `$pre-commit` invocation.
- After staging files for a risky bug fix or refactor.
## How AI Uses It
1. Run `pre_commit_check.py` with the project root.
2. Parse per-check and per-file results for warnings and failures.
3. Report blockers first, then ask whether to fix or proceed with warnings.
## Integration Behavior
- Trigger on `$pre-commit` or "check before commit".
- Auto-run before test selection in quick local verification flow.
- Blocking when a staged-file blocking rule fails; lighter than full gate.
## Output Intent
- Provide a fast feedback loop focused on changed files only.
- Caveat: unchanged files are not analyzed, so full-gate coverage is broader.
