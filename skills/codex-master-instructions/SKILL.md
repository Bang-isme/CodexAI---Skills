---
name: codex-master-instructions
description: Use when starting any CodexAI task; load this baseline before routing, editing, or claiming work is done.
load_priority: always
---

## TL;DR
Classify the request, load the smallest matching skill, check dependencies before edits, run a quality gate before claiming done, and reply in the user's language. Scripts: `--help` first.

# Codex Master Instructions

P0 baseline. Stack other skills on top of this file; do not replace it.

## Skill Invocation Rule

Before clarifying, exploring, editing, or answering any workflow-like request, match aliases, agents, and workflows. Load only the smallest sufficient skill set. Do not skip a relevant skill because the task "looks simple". Do not bulk-load unrelated skills.

For a single page or component, use `codex-frontend-design` fast path. For prototype/fullstack, use spec-first `$prototype`. Documents, reports, and guides load `codex-document-writer`.

If the pack is not loaded, run `python skills/.system/scripts/install.py doctor --host all`.

## Featured Aliases

| Alias | Full Command | Skill |
| --- | --- | --- |
| `$plan` | `$codex-plan-writer` | codex-plan-writer |
| `$debug` | `$codex-systematic-debugging` | codex-systematic-debugging |
| `$create` | workflow-create + TDD | codex-workflow-autopilot |
| `$gate` | `$codex-execution-quality-gate` | codex-execution-quality-gate |
| `$check` | `auto_gate.py --mode quick` | codex-execution-quality-gate |
| `$design` | `$codex-frontend-design` | codex-frontend-design |
| `$ux` | `$codex-frontend-design` | codex-frontend-design |
| `$memory` | `$codex-project-memory` | codex-project-memory |
| `$today` | `codex-project-pulse` daily brief | codex-project-pulse |
| `$doctor` | `install.py doctor` | .system |
| `$doc` | `$codex-document-writer` | codex-document-writer |
| `$report` | `$codex-document-writer` | codex-document-writer |
| `$brainstorm` | `brainstorm mode` | codex-workflow-autopilot |
| `$review-feedback` | receiving code review feedback | codex-subagent-execution |

Critical aliases: `$hook` `$preflight` `$health` `$init-profile` `$knowledge` `$spec` `$prototype` `$think` `$decide` `$check` `$check-full` `$check-deploy` `$init-docs` `$check-docs` `$install-hooks` `$install-ci` `$today` `$pulse`.

Also: `$direction` `$refine` `$polish` `$fix` `$build` `$docs`. Full catalog: `../.system/references/aliases.json`.

Request types include question, survey, simple-code, complex-code, prototype, debug, review, and | document |.

## Agents

When routing returns `suggested_agent`, load `.agents/<name>.md`.

| Agent | Domain |
| --- | --- |
| `design-lead` | Brief, UX contract, visual direction |
| `frontend-specialist` | UI implementation |
| `visual-quality-reviewer` | Post-UI review |
| `backend-specialist` | API and persistence |
| `security-auditor` | Security review |
| `debugger` | Root cause |
| `test-engineer` | Tests |
| `devops-engineer` | CI/CD |
| `planner` | Planning |
| `scrum-master` | Scrum |

Missing agent files fall back to `codex-domain-specialist`. Honor `file_ownership`.

## Workflow Aliases

`$plan` `$debug` `$create` `$build` `$prototype` `$review` `$deploy` `$handoff` `$fix` `$docs` `$refine` load `.workflows/<name>.md`.

## Completion

No "done" without fresh evidence. Details: `references/baseline-policy.md`.

Also load: `references/debugging-and-recovery.md`, `references/scope-escalation.md`, `references/workflow-cross-reference.md`.
