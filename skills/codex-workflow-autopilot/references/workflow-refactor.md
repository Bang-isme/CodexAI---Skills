# Workflow: Refactor
Use this workflow for restructuring, renaming, or simplifying existing code without changing behavior.
## Steps
1. Analyze scope and identify refactor boundaries (files, modules, layers).
2. Run `tech_debt_scan.py` to baseline current debt signals.
3. Run `predict_impact.py` to map blast radius of planned changes.
4. Implement refactor in small, verifiable increments.
5. Run `pre_commit_check.py` after each increment.
6. Run `smart_test_selector.py` to verify no behavior changes.
7. Run `suggest_improvements.py` as final quality pass.
## Exit Criteria
- All existing tests pass without modification (behavior preserved).
- Tech debt count reduced or unchanged (not increased).
- No broken imports or dangling references.
## Common Pitfalls
- Refactoring too many things at once instead of incremental steps.
- Skipping blast-radius analysis on "obvious" renames that touch shared exports.
- Not running tests after each increment, discovering failures only at the end.
## Example Sequence
1. `tech_debt_scan.py --project-root .` -> baseline: 23 signals
2. `predict_impact.py --project-root . --files src/utils/helpers.ts` -> 8 dependents found
3. Rename and update imports in batches of 2-3 files
4. `pre_commit_check.py --project-root .` -> pass
5. `smart_test_selector.py --project-root . --source staged` -> 4 tests selected, all pass
6. `tech_debt_scan.py --project-root .` -> reduced to 19 signals
7. `suggest_improvements.py --project-root . --source last-commit`
## When to Escalate
- Blast radius exceeds 15 files -> break into multiple smaller refactor sessions.
- Refactor reveals architectural issues -> switch to workflow-create for redesign.
- Test failures after refactor -> switch to workflow-debug for root-cause analysis.
