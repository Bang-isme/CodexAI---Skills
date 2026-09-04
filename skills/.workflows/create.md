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
2. Run `$hook`; if the feature spans multiple domains or prototype/MVP scope, route to `$prototype` and create `$spec` first.
3. For substantial UI (new surface or redesign), produce a design contract and role chain before code. Backend-only work and one-line CSS fixes skip the studio.
4. Load `workflow-create.md` and run impact advisory for shared-module risk.
5. Break the change into small increments with explicit acceptance criteria.
6. Implement in narrow slices and keep cross-file blast radius visible.
7. Run pre-commit checks, focused tests, and post-task improvement suggestions.
8. Log architectural decisions when the feature introduces a lasting tradeoff.

## Exit Criteria

- Acceptance criteria are met.
- Relevant tests and gate checks pass.
- New tradeoffs are logged or explicitly rejected as unnecessary.
