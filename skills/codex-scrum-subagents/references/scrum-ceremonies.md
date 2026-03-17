# Scrum Ceremonies

Use these playbooks to turn the installed subagents into a repeatable Scrum operating rhythm.

## Ceremony Matrix

| Ceremony | Goal | Lead Role | Support Roles | Required Outputs |
| --- | --- | --- | --- | --- |
| Backlog Refinement | turn vague work into sprint-ready stories | `product-owner` | `scrum-master`, `solution-architect`, optional specialists | story list, acceptance criteria, open risks |
| Sprint Planning | agree sprint goal and forecast | `scrum-master` | `product-owner`, all delivery roles | sprint goal, sprint backlog, risks, owners |
| Daily Scrum | surface progress and blockers | `scrum-master` | current delivery roles | progress notes, blockers, replanned tasks |
| Story Delivery | move one story through implementation safely | `scrum-orchestrator` or lead specialist | impacted specialists, `qa-engineer`, optional `security-engineer` | implementation notes, test evidence, docs impact |
| Sprint Review | inspect increment with stakeholders | `product-owner` | `scrum-master`, `qa-engineer`, delivery leads | accepted increment, feedback list, follow-up backlog |
| Retrospective | improve team process | `scrum-master` | full squad | keep/start/stop actions, ownership, next-sprint experiments |
| Release Readiness | decide ship / no-ship | `scrum-master` | `qa-engineer`, `security-engineer`, `devops-engineer`, `product-owner` | ship decision, rollback plan, release notes |

## Minimal Checklists

### Backlog Refinement

- Confirm user value, business outcome, and acceptance criteria.
- Split stories until each one can be owned by one lead specialist.
- Identify dependencies, security concerns, and test expectations before sprint planning.

### Sprint Planning

- State one sprint goal in a single sentence.
- Forecast only work with clear acceptance criteria and known dependencies.
- Record who leads each story and what verification is required.

### Daily Scrum

- Capture yesterday, today, blocker.
- Re-route blocked work within the same session.
- Escalate scope or priority changes to `product-owner`.

### Story Delivery

- Start from the story artifact, not raw chat fragments.
- Keep implementation, testing, and review evidence tied to the same story.
- Run quality gates before declaring the story done.

### Sprint Review

- Demo only tested increments.
- Capture feedback as backlog items, not side comments.
- Separate "accepted now" from "future enhancement".

### Retrospective

- Focus on system changes the team controls.
- Limit to three concrete experiments for the next sprint.
- Assign an owner and a review date for each action.

### Release Readiness

- Confirm quality, security, and rollback evidence.
- Check docs or handoff artifacts for external-facing changes.
- Make ship/no-ship decision explicit and timestamped.
