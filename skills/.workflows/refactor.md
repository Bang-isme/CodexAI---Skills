---
name: refactor
trigger: $refactor
loads: [codex-intent-context-analyzer, codex-workflow-autopilot, codex-execution-quality-gate, codex-project-memory]
---

# Workflow Alias: $refactor

## Trigger

Use for restructuring, renaming, extracting, or simplifying existing code without changing behavior.

## Step Outline

1. Analyze current structure and identify refactor boundaries (files, modules, layers).
2. Load `workflow-refactor.md` and run tech debt scan to baseline current signals.
3. Run impact prediction to map blast radius of planned changes.
4. Implement refactor in small, verifiable increments — never all at once.
5. Run pre-commit checks and focused tests after each increment.
6. Verify behavior is preserved (all existing tests pass without modification).
7. Run improvement suggestions as final quality pass.

## Exit Criteria

- All existing tests pass without modification (behavior preserved).
- Tech debt count reduced or unchanged (not increased).
- No broken imports or dangling references.
- Blast radius was predicted and confirmed within bounds.
