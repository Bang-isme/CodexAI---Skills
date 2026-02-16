---
name: codex-workflow-autopilot
description: Generate execution workflows from confirmed intent using behavioral modes, BMAD phases, checkpoints, and Phase X verification. Route build, fix, review, debug, and docs tasks into ordered steps with exit criteria.
---

# Workflow Autopilot

## Activation

1. Activate after intent analysis is confirmed.
2. Activate on explicit `$codex-workflow-autopilot`.

## Behavioral Modes

| Signals | Mode | Behavior |
| --- | --- | --- |
| what if, ideas, options | brainstorm | ask clarifying questions and present alternatives, no code |
| build, create, implement | implement | execute quickly with production-focused output |
| error, bug, broken | debug | reproduce, isolate, root-cause, fix, regression-test |
| review, audit, check | review | inspect and report findings by severity |
| explain, teach, learn | teach | explain progressively with examples |
| deploy, release, ship | ship | prioritize stability and complete checks |

## Intent to Workflow

| Intent | Steps | Exit Criteria |
| --- | --- | --- |
| build | analyze -> plan -> implement -> test -> docs -> gate | tests pass, docs checked, gate pass |
| fix | reproduce -> isolate -> root-cause -> fix -> regression-test -> docs -> gate | root cause identified, regression test pass, gate pass |
| review | inspect -> categorize findings -> recommend actions | findings documented with severity |
| debug | reproduce -> hypotheses -> verify/eliminate -> fix -> regression-test -> gate | verified fix with evidence, gate pass |
| docs | scope change -> update docs -> verify links/accuracy -> gate | docs updated and verified |

## BMAD for Complex Requests

Use BMAD when intent analysis marks `complexity: complex`.

### Phase 1: Analysis (no code)

- confirm requirements and constraints
- inspect existing patterns
- capture key decisions

### Phase 2: Planning (no code)

- create plan via `$codex-plan-writer`
- define task-level input/output/verify

Checkpoint: wait for explicit user approval before Phase 3.

### Phase 3: Solutioning (no code)

- finalize architecture and data flow decisions
- identify cross-file impacts

### Phase 4: Implementation (code)

- implement task by task
- run tests/docs as workflow requires

### Phase X: Verification (always last)

1. Run `$codex-execution-quality-gate`.
2. If gate fails, fix blockers and rerun.
3. Do not declare completion before gate decision.

## Overrides

- "skip test": remove test step and warn quality confidence is reduced.
- "no docs": remove docs step and warn maintainability confidence is reduced.
- "just do it": default to build workflow and still show brief step plan.
- "skip plan": allow for simple scope; for complex scope warn and reconfirm.

## Scope Heuristic

- small: 1-3 files, single concern
- medium: 4-10 files, multiple concerns
- large: 10+ files or architectural impact

## Output Contract

Return fenced JSON in conversation:

```json
{
  "mode": "brainstorm | implement | debug | review | teach | ship",
  "workflow_type": "build | fix | review | debug | docs",
  "steps": ["step1", "step2"],
  "exit_criteria": ["criterion1"],
  "estimated_scope": "small | medium | large",
  "phase": "analysis | planning | solutioning | implementation | verification"
}
```

Execution remains sequential for MVP.
