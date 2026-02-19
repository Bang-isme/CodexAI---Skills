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
