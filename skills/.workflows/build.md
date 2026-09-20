---
name: build
trigger: $build
loads: [codex-intent-context-analyzer, codex-workflow-autopilot, codex-execution-quality-gate, codex-project-memory]
---

# Workflow Alias: $build

## Trigger

Alias of `$create`. Use for net-new features and scoped implementation requests.

## Step Outline

Follow `.workflows/create.md`. `$build` and `$create` are the same implementation workflow.

## Exit Criteria

Same as `$create`.
