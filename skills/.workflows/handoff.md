---
name: handoff
trigger: $handoff
loads: [codex-project-memory, codex-workflow-autopilot, codex-execution-quality-gate]
---

# Workflow Alias: $handoff

## Trigger

Use when ending a session, transferring work, or packaging project state for another teammate or AI.

## Step Outline

1. Load `workflow-handoff.md` and generate the latest session summary.
2. Export a fresh handoff document with current state, open issues, and next steps.
3. Log unresolved architectural decisions instead of leaving them implicit.
4. Generate a recent changelog slice and review aggregated feedback for recurring risks.
5. Run the written deliverable through strict output checks before sign-off.

## Exit Criteria

- Session summary and handoff artifacts both exist.
- Open decisions and recurring risks are visible.
- The receiving agent can continue without rediscovering basic context.
