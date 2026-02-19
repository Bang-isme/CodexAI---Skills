# Workflow: Create

Use this workflow for new feature implementation with moderate/high impact.

## Steps

1. Analyze scope and identify expected user/system impact.
2. Check prior decisions (`.codex/decisions/`) for related architecture choices.
3. Run impact advisory (`predict_impact.py`) for planned file changes.
4. Plan implementation tasks and acceptance criteria.
5. Execute implementation in small, verifiable increments.
6. Run `pre_commit_check.py` and `smart_test_selector.py` before finalizing.
7. Run `suggest_improvements.py` to surface nearby quality opportunities.
8. Log a new decision when architecture or contract tradeoffs are introduced.

## Exit Criteria

- Functional acceptance criteria met.
- Relevant tests selected/executed.
- No unresolved blocking findings.
- Decision journal updated when needed.

## Common Pitfalls

- Skipping impact prediction for "small" changes that still touch shared modules.
- Not logging architectural decisions made during implementation.
- Running quality checks only at the very end instead of incrementally.
- Treating advisory findings as noise and never converting them into follow-up tasks.
- Expanding scope during implementation without re-running impact prediction.
- Merging without documenting why a risky tradeoff was accepted.

## Example Sequence

1. Run impact prediction:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\predict_impact.py" --project-root . --files "src/models/user.ts,src/api/users.ts"`
2. Review blast radius and confirm implementation scope with user constraints.
3. Implement the planned changes in small commits.
4. Run staged quality checks:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\pre_commit_check.py" --project-root .`
5. Select focused tests:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\smart_test_selector.py" --project-root . --source staged`
6. Run post-task suggestions and decision logging:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\suggest_improvements.py" --project-root . --source last-commit`
   then `python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\decision_logger.py" --project-root . --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>` if a tradeoff emerged.
7. Run full completion gate before final handoff:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\run_gate.py" --project-root .`

## When to Escalate

- Escalate to review workflow when findings include cross-domain security and reliability risks.
- Escalate for human review when API contracts or data models change without clear downstream ownership.
- Escalate to planning workflow when blast radius expands beyond initial scope assumptions.
- Escalate to architecture review when repeated suggestions indicate structural decomposition issues.
