---
name: create
trigger: $create
loads: [codex-intent-context-analyzer, codex-workflow-autopilot, codex-execution-quality-gate, codex-project-memory]
---

# Workflow Alias: $create

## Trigger

Use for net-new features, scoped enhancements, or build-mode implementation requests.

## Step Outline

Confirmation follows `skills/codex-workflow-autopilot/references/workflow-routing-contract.json`: a clear request authorizes its stated scope. Resolve only material gaps without safe defaults, unapproved risk boundaries, or scope expansion before implementation.

1. Review the user's stated scope, users, and constraints; ask only about material information that could change the outcome and has no safe default.
2. Run `$hook` and load 4-Tier Project Memory; if the feature spans multiple domains or prototype/MVP scope, route to `$prototype` and create `$spec` (`AC-###` + `SILC-###` integration seams) first.
3. For substantial UI (new surface or redesign), produce a design contract and role chain before code. Backend-only work and one-line CSS fixes skip the studio.
4. Load `workflow-create.md`, run `reuse_map.py` to discover existing project helpers, and run impact advisory (`predict_impact.py`) for shared-module risk.
5. Walk `../codex-reasoning-rigor/references/precision-ladder.md` (6-Rung Smallest-Complete-Change Decision Ladder) and break the change into small, dependency-ordered increments (`Contract/Schema -> Producer -> Consumer`) with explicit acceptance and SILC seam criteria.
6. Implement in narrow slices with TDD (`$tdd`), applying the **Caller-Grep Rule** before changing shared signatures, and marking any intentional capacity limit with `shortcut: <ceiling>, <when to upgrade>`.
7. Run pre-commit checks, focused tests, spec traceability (`check_spec.py`), and post-task improvement suggestions.
8. Execute Memory Write-Back: log architectural decisions (`decision_logger.py`) and update touched role docs when lasting tradeoffs or contracts change.

## Exit Criteria

- Acceptance criteria are met.
- Relevant tests and gate checks pass.
- New tradeoffs are logged or explicitly rejected as unnecessary.
