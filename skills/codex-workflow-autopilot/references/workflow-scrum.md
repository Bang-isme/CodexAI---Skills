# Workflow: Scrum Overlay

Use this workflow when the user request depends on Scrum ceremony output, role handoffs, or sprint governance.

## Trigger Signals

- backlog, story, acceptance criteria, MVP
- refinement, sprint planning, sprint goal, daily scrum
- sprint review, retrospective, release readiness
- Product Owner, Scrum Master, QA handoff, release gate

## Decision Rules

1. If the story is vague or not sprint-ready, route to `backlog-refinement` first.
2. If the request is about scope, blockers, or forecasting, route through `scrum-master` before implementation.
3. If the request is an in-sprint implementation story, keep the engineering workflow but attach Scrum handoffs and verification.
4. If the request is about shipping, attach `release-readiness` before the final deploy workflow.

## Ceremony Mapping

| Situation | Ceremony | Outcome |
| --- | --- | --- |
| idea is vague | backlog-refinement | story packet with acceptance criteria |
| sprint commitment needed | sprint-planning | sprint goal and ownership |
| blocker surfaced mid-sprint | daily-scrum | replan and unblock |
| one story moving to done | story-delivery | verified story increment |
| stakeholder wants demo and feedback | sprint-review | accepted work plus backlog updates |
| team wants process improvement | retrospective | action items for next sprint |
| team wants to decide if it is safe to ship | release-readiness | ship/no-ship plus rollback notes |

## Recommended Action

- If the project lacks a local `.agent` kit, recommend `codex-scrum-subagents`.
- If a local `.agent` kit already exists, map the request to the matching ceremony workflow and role set.
- Never let Scrum overlay replace the underlying engineering quality gate.
