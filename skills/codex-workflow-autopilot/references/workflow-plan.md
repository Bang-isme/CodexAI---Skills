# Workflow: Plan

Use this workflow for scoping, analysis, and implementation planning before any code is written. This is BMAD Phase 1-2.

## Steps

1. Run intent analysis to lock goal, constraints, missing info, and complexity.
2. Check existing decisions in `.codex/decisions/` for related prior choices.
3. Inspect repo structure, patterns, and recent changes for context.
4. Run impact prediction for any files likely to change.
5. Apply reasoning rigor to define evidence needs, non-goals, risks, and quality bar.
6. Execute BMAD Phase 1 (Analysis): confirm requirements, inspect patterns, capture decisions.
7. Execute BMAD Phase 2 (Planning): produce plan document with task-level input/output/verify.
8. Stop before implementation and ask for explicit approval to proceed.

## Exit Criteria

- Plan file exists with required sections and verifiable tasks.
- Each task has: scope, files affected, verification command, acceptance criteria.
- Risks, evidence needs, and success criteria are explicit.
- Dependencies and ordering constraints are documented.
- Work is ready for BMAD Phase 3 only after user approval.

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
5. Present plan → wait for user approval
6. Only then proceed to Phase 3 (solutioning) or Phase 4 (implementation)

## When to Escalate

- Scope is ambiguous after analysis → ask user to clarify before planning.
- Blast radius exceeds 15 files → suggest breaking into multiple plans.
- Plan contradicts existing decisions → surface the conflict and let user decide.
- Complexity is `simple` → skip formal plan, use direct execution via `$create`.
