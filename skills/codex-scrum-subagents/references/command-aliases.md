# Scrum Command Aliases

Use these aliases as short, repeatable entry points for the Scrum kit.

## Installer Aliases

| Alias | Purpose | Maps To |
| --- | --- | --- |
| `$scrum-install` | install the project-local `.agent` Scrum kit plus native `.codex/agents` custom agents | `codex-scrum-subagents.install` |
| `$scrum-diff` | compare the installed `.agent` and `.codex/agents` trees with the source bundle | `codex-scrum-subagents.diff` |
| `$scrum-update` | update only missing or changed kit files across both install surfaces and keep backups | `codex-scrum-subagents.update` |
| `$scrum-validate` | validate the bundle or an installed `.agent` plus `.codex/agents` tree | `codex-scrum-subagents.validate` |

## Ceremony Aliases

| Alias | Purpose | Maps To |
| --- | --- | --- |
| `$backlog-refinement` | turn a rough request into sprint-ready stories | `backlog-refinement` |
| `$sprint-plan` | create sprint goal, sprint backlog, and ownership plan | `sprint-planning` |
| `$daily-scrum` | surface progress, blockers, and replanning needs | `daily-scrum` |
| `$story-ready-check` | decide whether a story is ready to build or needs refinement first | `backlog-refinement` |
| `$story-delivery` | move one story through implementation and verification | `story-delivery` |
| `$sprint-review` | review the increment and capture feedback | `sprint-review` |
| `$retro` | run a retrospective and log improvements | `retrospective` |
| `$release-readiness` | decide ship/no-ship with rollback evidence | `release-readiness` |

## Usage Pattern

1. Use installer aliases when the project still needs the `.agent` kit and the native `.codex/agents` Codex custom agents.
2. Use ceremony aliases when the team already has the kit and needs a faster trigger vocabulary.
3. Pair `$story-ready-check` with Product Owner or Scrum Master behavior before coding.
4. Pair `$release-readiness` with QA, security, and DevOps checks before ship.
