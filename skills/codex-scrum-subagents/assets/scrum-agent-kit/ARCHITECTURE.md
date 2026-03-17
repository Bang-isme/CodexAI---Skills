# Scrum Agent Architecture

```
USER REQUEST
    |
    v
PRODUCT OWNER ---------------------> SPRINT REVIEW
    |                                      ^
    v                                      |
SCRUM MASTER -----> DAILY SCRUM ---------- |
    |                                      |
    v                                      |
SOLUTION ARCHITECT                         |
    |                                      |
    +----> FRONTEND DEVELOPER -----+       |
    |                              |       |
    +----> BACKEND DEVELOPER ------+-----> QA ENGINEER
    |                              |       |
    +----> UX RESEARCHER ----------+       |
    |                                      |
    +----> SECURITY ENGINEER ------------- |
    |                                      |
    +----> DEVOPS ENGINEER --------------- RELEASE READINESS
    |
    +----> RETROSPECTIVE
```

## Core Principles

- Product Owner owns value and acceptance criteria.
- Scrum Master owns cadence, facilitation, and blocker management.
- Specialists own implementation and discipline-specific risk assessment.
- QA, security, and release checks happen per story, not only at the end of the sprint.

## Skill Mapping

| Role | Preferred CodexAI Skills |
| --- | --- |
| Product Owner | `codex-intent-context-analyzer`, `codex-plan-writer`, `codex-project-memory` |
| Scrum Master | `codex-workflow-autopilot`, `codex-plan-writer`, `codex-project-memory` |
| Architect | `codex-context-engine`, `codex-domain-specialist`, `codex-security-specialist` |
| Developers | `codex-domain-specialist`, optional `codex-security-specialist`, `codex-execution-quality-gate` |
| QA / Security / DevOps | `codex-execution-quality-gate`, `codex-security-specialist`, `codex-domain-specialist` |

## Native Codex Agents

The installer also materializes a companion `.codex/agents/` directory with one TOML file per Scrum role.
Those files follow the official Codex custom-agent discovery path so the Codex app and CLI can surface subagent activity when these roles are selected.
