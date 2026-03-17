# Subagent Boundaries

Boundaries keep the Scrum kit useful. If roles blur, the kit becomes another generic assistant layer.

## Role Boundaries

| Role | Owns | Must Not Own |
| --- | --- | --- |
| `product-owner` | business value, backlog order, acceptance criteria | implementation details, environment changes, test execution |
| `scrum-master` | flow, facilitation, blockers, sprint cadence | product priority, architecture, coding decisions |
| `scrum-orchestrator` | role sequencing, execution summary, handoff integrity | replacing the specialist role doing the work |
| `solution-architect` | system shape, module seams, trade-offs | backlog priority, release approval |
| `frontend-developer` | UI implementation and UI risks | backend contracts, release decision |
| `backend-developer` | service logic and backend risks | UX discovery, deployment approval |
| `qa-engineer` | verification strategy and release confidence | product scope decisions, architecture |
| `security-engineer` | controls, threats, sensitive-surface review | feature scope, sprint forecasting |
| `devops-engineer` | CI/CD, environments, rollback, release mechanics | feature scope, acceptance criteria |
| `ux-researcher` | user friction and discovery evidence | implementation estimates, release go/no-go |

## File and Artifact Ownership

| Artifact Type | Default Owner |
| --- | --- |
| backlog, story cards, acceptance criteria | `product-owner` |
| sprint goal, impediment log, retro actions | `scrum-master` |
| architecture decision notes | `solution-architect` |
| UI or API implementation notes | impacted developer role |
| test matrix and release confidence | `qa-engineer` |
| threat notes and control sign-off | `security-engineer` |
| deployment checklist and rollback plan | `devops-engineer` |

## Escalation Rules

1. If scope changes, re-route to `product-owner`.
2. If a blocker affects sprint flow, re-route to `scrum-master`.
3. If the change crosses subsystem boundaries, re-route to `solution-architect`.
4. If the story touches secrets, auth, payments, or regulated data, re-route to `security-engineer`.
5. If the team is preparing to ship, re-route to `qa-engineer` and `devops-engineer`.
