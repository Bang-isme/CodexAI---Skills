# Workflow Cross Reference

## Cross-Reference Table

| Task Type | Preferred Workflow | Suggested Scripts |
| --- | --- | --- |
| new feature | `codex-workflow-autopilot/references/workflow-create.md` | `predict_impact.py`, `pre_commit_check.py`, `smart_test_selector.py`, `suggest_improvements.py` |
| bug fix | `codex-workflow-autopilot/references/workflow-debug.md` | `pre_commit_check.py`, `smart_test_selector.py`, `track_feedback.py` |
| code review or audit | `codex-workflow-autopilot/references/workflow-review.md` | `tech_debt_scan.py`, `quality_trend.py --report`, `security_scan.py` |
| refactor | `codex-workflow-autopilot/references/workflow-refactor.md` | `tech_debt_scan.py`, `predict_impact.py`, `pre_commit_check.py`, `smart_test_selector.py`, `suggest_improvements.py` |
| deploy or ship | `codex-workflow-autopilot/references/workflow-deploy.md` | `security_scan.py`, `bundle_check.py`, `lighthouse_audit.py`, `playwright_runner.py`, `generate_changelog.py`, `with_server.py` |
| environment check | pre-flight diagnostics | `doctor.py` |
| session handoff | `codex-workflow-autopilot/references/workflow-handoff.md` | `generate_session_summary.py`, `generate_handoff.py`, `decision_logger.py`, `generate_changelog.py`, `track_feedback.py` |
| docs sync | workflow docs phase | `map_changes_to_docs.py`, `generate_changelog.py` |
| release or pre-ship | quality gate + ship mode | `security_scan.py`, `lighthouse_audit.py`, `playwright_runner.py`, `with_server.py` |
| long-running project continuity | project-memory flow | `decision_logger.py`, `generate_session_summary.py`, `generate_handoff.py`, `generate_growth_report.py` |

## Two-Stage Review Protocol

When reviewing completed work against a plan or spec:

### Stage 1: Spec Compliance Review (Do First)

- Does the implementation match every requirement in the plan or spec?
- Is anything missing that was requested?
- Is anything extra that was not requested (YAGNI violation)?
- Are acceptance criteria met?

Do not proceed to Stage 2 until Stage 1 passes.

### Stage 2: Code Quality Review (Do Second)

- Does the code follow project conventions?
- Is error handling proper?
- Are there security concerns?
- Is test coverage adequate?
- Is there unnecessary complexity?

### Issue Severity

- **Critical** (must fix before completion): missing requirements, security holes, data loss risk
- **Important** (should fix): poor error handling, missing tests, convention violations
- **Suggestion** (nice to have): naming improvements, minor refactoring opportunities

## Workflow References

- `codex-workflow-autopilot/references/workflow-create.md`
- `codex-workflow-autopilot/references/workflow-debug.md`
- `codex-workflow-autopilot/references/workflow-review.md`
- `codex-workflow-autopilot/references/workflow-refactor.md`
- `codex-workflow-autopilot/references/workflow-deploy.md`
- `codex-workflow-autopilot/references/workflow-handoff.md`
