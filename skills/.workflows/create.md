---
name: create
trigger: $create
loads: [codex-intent-context-analyzer, codex-workflow-autopilot, codex-execution-quality-gate, codex-project-memory]
---

# Workflow Alias: $create

## Trigger

Use for net-new features, scoped enhancements, or build-mode implementation requests.

## Step Outline

1. Confirm scope, users, and constraints before touching code.
2. Load `workflow-create.md` and run impact advisory for shared-module risk.
3. Break the change into small increments with explicit acceptance criteria.
4. Implement in narrow slices and keep cross-file blast radius visible.
5. Run pre-commit checks, focused tests, and post-task improvement suggestions.
6. Log architectural decisions when the feature introduces a lasting tradeoff.

## Exit Criteria

- Acceptance criteria are met.
- Relevant tests and gate checks pass.
- New tradeoffs are logged or explicitly rejected as unnecessary.
