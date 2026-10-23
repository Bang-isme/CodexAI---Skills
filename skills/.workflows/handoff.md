---
name: handoff
trigger: $handoff
loads: [codex-project-memory, codex-workflow-autopilot, codex-execution-quality-gate]
---

# Workflow Alias: $handoff

## Trigger

Use when ending a session, transferring work, or packaging project state for another teammate or AI.

## Step Outline

1. Synchronize active Tier 3/Tier 4 memory (log decisions via `decision_logger.py`, update `SPEC.md` traceability & `SILC-###` seam status, update touched role docs).
2. Load `workflow-handoff.md`, run `generate_session_summary.py`, and replace all bracketed prompts with the active spec/plan, completed vs pending `AC-###` / `SILC-###` seams, verified commands, and exact next step.
3. Export a fresh portable handoff document (`generate_handoff.py`) with current state, open issues, and next steps.
4. Generate a recent changelog slice and review aggregated feedback for recurring risks.
5. Run the written deliverable through strict output checks (`output_guard.py` + `editorial_review.py`) before sign-off.

## Exit Criteria

- Session summary (`.codex/sessions/*.md` with all prompts filled) and handoff (`.codex/handoff.md`) artifacts both exist.
- Active spec, pending ACs, SILC integration seams, and recurring risks are visible.
- The receiving agent can continue from the exact next ticket/file without rediscovering basic context.
