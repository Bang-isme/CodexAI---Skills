---
name: plan
trigger: $plan
loads: [codex-intent-context-analyzer, codex-plan-writer, codex-workflow-autopilot, codex-reasoning-rigor]
---

# Workflow Alias: $plan

## Trigger

Use when the user wants planning, scoping, or BMAD preparation before coding.

## Step Outline

1. Run intent analysis to lock goal, constraints, missing info, and complexity.
2. Review repo context, prior decisions, and any blast-radius hints before solutioning.
3. Apply reasoning rigor to define evidence, non-goals, risks, and quality bar.
4. Execute BMAD Phase 1-2 only: analysis first, then plan writing.
5. Produce a concrete plan file with verification, rollback, and dependency notes.
6. Stop before implementation and ask for approval to enter later phases.

## Exit Criteria

- Plan file exists with required sections and verifiable tasks.
- Risks, evidence needs, and success criteria are explicit.
- Work is ready for BMAD Phase 3 only after user approval.
