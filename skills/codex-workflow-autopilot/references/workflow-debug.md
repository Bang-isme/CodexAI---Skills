# Workflow: Debug

Use this workflow for bug investigations and production issue resolution.

## Steps

1. Reproduce the issue with exact steps and expected vs actual behavior.
2. Check feedback logs for similar recurring failure patterns.
3. Analyze relevant code paths and dependency relationships.
4. Apply minimal fix targeting root cause.
5. Run targeted tests/regression checks.
6. Log feedback entry when AI-generated code contributed to the issue.

## Exit Criteria

- Root cause documented.
- Reproduction no longer fails.
- Regression path covered by tests or explicit verification steps.
- Feedback log updated when applicable.

## Common Pitfalls

- Fixing symptoms without proving the root cause.
- Not checking feedback logs for recurring bug patterns.
- Skipping targeted regression testing after the fix.
- Mixing multiple unrelated fixes in one debug cycle.
- Ignoring environment or configuration drift when reproduction is inconsistent.
- Closing the bug after a local-only check without verifying target runtime conditions.

## Example Sequence

1. Reproduce the issue and document expected versus actual behavior.
2. Check prior feedback signals:
   `python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\track_feedback.py" --project-root . --aggregate`
3. Analyze the code path and isolate the root cause before editing.
4. Apply the minimal fix and run staged checks:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\pre_commit_check.py" --project-root .`
5. Run targeted tests only:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\smart_test_selector.py" --project-root . --source staged`
6. If AI-generated code caused the bug, log a feedback entry:
   `python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\track_feedback.py" --project-root . --file <file> --ai-version <text> --user-fix <text> --category logic`
7. If issue scope expands across modules, re-run impact advisory:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\predict_impact.py" --project-root . --files "<changed-file-1>,<changed-file-2>" --depth 2`

## When to Escalate

- Escalate to security review when debug findings expose auth, secret, or validation weaknesses.
- Escalate to planning workflow when the fix requires multi-module refactor instead of targeted patching.
- Request human review when reproduction is intermittent and cannot be stabilized with current evidence.
- Escalate to review workflow when recurring failures persist after verified regression checks.
- Escalate for release rollback discussion when production impact remains high after the patch.
