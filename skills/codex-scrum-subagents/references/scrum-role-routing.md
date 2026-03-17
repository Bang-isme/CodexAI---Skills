# Scrum Role Routing

Use this table to pick the smallest role set that still gives the team a safe Scrum flow.

## Core Roles

| Role | Trigger Signals | Primary Outputs | Load These Pack Skills |
| --- | --- | --- | --- |
| `product-owner` | roadmap, backlog, user story, acceptance criteria, MVP, scope | prioritized backlog, user stories, acceptance criteria | `codex-intent-context-analyzer`, `codex-plan-writer`, `codex-project-memory` |
| `scrum-master` | sprint planning, blocker, facilitation, retro, daily scrum, dependency | sprint goal, risk board, impediment log, ceremony agenda | `codex-workflow-autopilot`, `codex-plan-writer`, `codex-project-memory` |
| `scrum-orchestrator` | multi-role, cross-functional, end-to-end delivery, large feature | role plan, execution order, delivery summary | `codex-workflow-autopilot`, `codex-execution-quality-gate`, `codex-project-memory` |

## Delivery Specialists

| Role | Trigger Signals | Primary Outputs | Load These Pack Skills |
| --- | --- | --- | --- |
| `solution-architect` | architecture, trade-off, system design, boundaries | architecture brief, module split, risk notes | `codex-context-engine`, `codex-domain-specialist`, `codex-security-specialist` |
| `frontend-developer` | UI, component, accessibility, responsive, dashboard | UI implementation plan, component changes, UI risks | `codex-domain-specialist`, `codex-execution-quality-gate` |
| `backend-developer` | API, service, worker, auth flow, integration | endpoint plan, schema touchpoints, backend risks | `codex-domain-specialist`, `codex-security-specialist`, `codex-execution-quality-gate` |
| `qa-engineer` | test coverage, regression, acceptance, e2e, flaky | test matrix, coverage gaps, release confidence | `codex-execution-quality-gate`, `codex-workflow-autopilot` |
| `security-engineer` | auth, vuln, secrets, compliance, threat model | threat notes, controls, release blockers | `codex-security-specialist`, `codex-execution-quality-gate` |
| `devops-engineer` | deploy, CI, observability, environment, rollback | deployment checklist, release gates, rollback plan | `codex-domain-specialist`, `codex-security-specialist`, `codex-execution-quality-gate` |
| `ux-researcher` | discovery, flow, usability, persona, friction | UX findings, edge cases, validation notes | `codex-domain-specialist`, `codex-project-memory` |

## Default Routing Patterns

| Request Pattern | Default Subagent Set |
| --- | --- |
| vague feature request | `product-owner` -> `scrum-master` -> `solution-architect` |
| sprint-ready story | `product-owner` -> `scrum-master` -> delivery specialists |
| large full-stack feature | `scrum-orchestrator` + `product-owner` + `scrum-master` + `solution-architect` + relevant delivery roles |
| bug found during sprint | `scrum-master` + impacted delivery role + `qa-engineer`, add `security-engineer` if auth or data is touched |
| release candidate | `scrum-master` + `qa-engineer` + `security-engineer` + `devops-engineer` |

## Escalation Rules

1. Pull in `product-owner` whenever scope, priority, or acceptance criteria are unclear.
2. Pull in `scrum-master` whenever dependencies, blockers, or ceremony output are needed.
3. Pull in `solution-architect` before editing multiple subsystems or when blast radius is unclear.
4. Pull in `qa-engineer` before calling a story done.
5. Pull in `security-engineer` for auth, secrets, external integrations, or compliance-sensitive data.
