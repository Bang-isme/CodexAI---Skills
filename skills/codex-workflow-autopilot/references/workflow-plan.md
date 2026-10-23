# Workflow: Plan

Use this workflow for plan-only requests or the planning stage of an explicitly authorized implementation task. Follow the shared confirmation policy in `references/workflow-routing-contract.json`. This is BMAD Phase 1-2.

## Steps

1. Run intent analysis to lock goal, constraints, missing info, and complexity.
2. Load 4-Tier Project Memory: check `.codex/profile.json`, `.codex/context/genome.md`, `.codex/knowledge/INDEX.md`, active `.codex/specs/`, and existing decisions in `.codex/decisions/`.
3. Inspect repo structure, patterns, and recent changes for context.
4. Run impact prediction for any files likely to change.
5. Apply reasoning rigor to define evidence needs, non-goals, risks, and quality bar.
6. Execute BMAD Phase 1 (Analysis): extract requirements from the user's request, resolve only material gaps under the shared policy, inspect patterns, lock cross-domain `SILC-###` integration seams, and capture decisions.
7. Execute BMAD Phase 2 (Planning): produce plan document with dependency-ordered tasks, `AC-###` / `SILC-###` links, and task-level input/output/verify.
8. For a plan-only request, present the plan and stop before implementation. For an implementation request, continue within the authorized scope when no material decision or risk remains open; otherwise pause only for the decision or authorization required by the shared policy.

## Exit Criteria

- Plan file exists with required sections and verifiable tasks.
- Each task has: scope, files affected, verification command, acceptance criteria.
- Risks, evidence needs, and success criteria are explicit.
- Dependencies and ordering constraints are documented.
- For a plan-only request, work is ready for BMAD Phase 3 only after the user approves the plan. For an implementation request, continue to the next phase within the authorized scope unless a new material decision or risk requires approval.

## Common Pitfalls

- Starting to code during planning — resist the urge, plan first.
- Writing tasks that are too vague to verify ("improve auth" vs "add JWT refresh token rotation to `src/auth/jwt.service.ts`").
- Not checking existing decisions — leading to contradictory architecture choices.
- Skipping impact prediction — underestimating blast radius.
- Planning without repo inspection — producing generic plans that don't match actual code structure.

## Example Sequence

1. `codex-intent-context-analyzer` → lock goal and complexity
2. Inspect `src/` structure, `package.json`, existing patterns
3. `predict_impact.py --project-root . --files <planned-changes>`
4. Draft plan with tasks, verification, dependencies
5. For plan-only requests, present the plan and wait for approval before later phases; for an implementation request, continue within its authorized scope.
6. Proceed to Phase 3 (solutioning) or Phase 4 (implementation) only when the request and any required material decisions authorize that phase.

## When to Escalate

- Scope is ambiguous after analysis → ask user to clarify before planning.
- Blast radius exceeds 15 files → suggest breaking into multiple plans.
- Plan contradicts existing decisions → surface the conflict and let user decide.
- Complexity is `simple` → skip formal plan, use direct execution via `$create`.
