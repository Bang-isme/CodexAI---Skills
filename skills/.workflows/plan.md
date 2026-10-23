---
name: plan
trigger: $plan
loads: [codex-intent-context-analyzer, codex-plan-writer, codex-workflow-autopilot, codex-reasoning-rigor]
---

# Workflow Alias: $plan

## Trigger

Use when the user wants planning, scoping, or BMAD preparation before coding.

## Step Outline

This alias is for plan-only requests. Follow `skills/codex-workflow-autopilot/references/workflow-routing-contract.json`; present the plan and stop before implementation. When a plan is used internally for an explicit implementation request, the implementation workflow may continue within the authorized scope.

1. Run intent analysis to lock goal, constraints, missing info, and complexity.
2. Load 4-Tier Project Memory (`profile.json` -> `genome.md` / `INDEX.md` -> active `SPEC.md` / `decisions/` -> active role doc) and review any blast-radius hints before solutioning.
3. Apply reasoning rigor to define evidence, non-goals, risks, and quality bar.
4. Execute BMAD Phase 1-2 only: analysis (including cross-domain `SILC-###` integration seams) first, then plan writing.
5. Produce a concrete plan file with dependency-ordered tasks, `AC-###` / `SILC-###` links, verification, rollback, and dependency notes.
6. Stop before implementation and ask for approval to enter later phases.

## Exit Criteria

- Plan file exists with required sections and verifiable tasks.
- Risks, evidence needs, and success criteria are explicit.
- Work is ready for BMAD Phase 3 only after user approval.
