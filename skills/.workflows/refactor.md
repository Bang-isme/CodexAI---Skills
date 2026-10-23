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
2. Load `workflow-refactor.md`, run `reuse_map.py` to index existing shared helpers, and run `tech_debt_scan.py` + `shortcut_ledger.py` to baseline current debt signals.
3. Run impact prediction (`predict_impact.py`) and apply the **Caller-Grep Rule** (`../codex-reasoning-rigor/references/precision-ladder.md`) to map every caller of the refactored symbols.
4. Walk the 6-Rung Precision Ladder and implement the refactor in small, verifiable increments — preserving existing validation at every moved boundary.
5. Run pre-commit checks and focused tests after each increment.
6. Verify behavior is preserved (all existing tests pass without modification).
7. Run improvement suggestions as final quality pass.

## Exit Criteria

- All existing tests pass without modification (behavior preserved).
- Tech debt count reduced or unchanged (not increased).
- No broken imports or dangling references.
- Blast radius was predicted and confirmed within bounds.
