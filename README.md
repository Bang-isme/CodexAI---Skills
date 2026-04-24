<img width="1536" height="1024" alt="CodexAI Skill Pack cover" src="https://github.com/user-attachments/assets/88afea81-e3a8-47ef-82f2-9dd7845f8cb4" />

# CodexAI Skill Pack

> Production-ready instruction framework for Codex - deterministic workflows, deliberate reasoning, domain routing, strict quality gates, and persistent project memory.

[![Version](https://img.shields.io/badge/version-14.3.0-blue)]() [![Tests](https://img.shields.io/badge/pytest-161%2F161%20passed-green)]() [![Smoke](https://img.shields.io/badge/smoke-55%2F55%20passed-green)]() [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

CodexAI Skill Pack turns Codex from an ad-hoc code assistant into a structured engineering partner.
Instead of relying on prompt luck, the pack enforces a repeatable flow:

`Intent -> Plan -> Route -> Implement -> Verify -> Persist -> Commit`

The pack is designed for 3 outcomes:

- less generic output
- stronger workflow discipline
- deliverables that read more like accountable human engineering work

### Current Stats

| Metric | Value |
| --- | --- |
| Core Skills | 24 |
| Entry-point Scripts | 53 |
| Shared Helpers | 2 |
| Reference Docs | 173+ |
| Starter Templates | 29 |
| Scrum Artifact Templates | 6 |
| Agent Personas | 8 |
| Workflow Aliases | 6 |
| Verification | 161 unit + 55 smoke = 216 tests |

---

## Why This Pack Is Different

| Weakness in default AI workflows | What this pack adds |
| --- | --- |
| Vague task interpretation | `codex-intent-context-analyzer` locks goal, scope, and ambiguity before code |
| Plans that sound good but do not guide execution | `codex-plan-writer` creates verifiable, dependency-aware task breakdowns |
| Design output drifts between sessions | `codex-design-system` plus `codex-design-md` turn design intent into reusable vocabulary and a lintable `DESIGN.md` contract |
| Generic output with no proof | `codex-reasoning-rigor` plus `output_guard.py` force evidence-backed deliverables |
| AI-safe writing that still feels synthetic | `editorial_review.py` scores tone, decision clarity, tradeoffs, and scanability |
| Documents that make readers infer too much | `codex-document-writer` forces purpose, audience, structure, complete sentences, and reliability wording |
| No final gate before declaring done | `codex-execution-quality-gate` runs lint, tests, security, output quality, editorial quality, UX, and trend tracking |
| Context lost between sessions | `codex-role-docs` preserves role-scoped project docs, while `codex-project-memory` stores decisions, summaries, genome, handoffs, and changelog inputs |
| Scrum roles live only in people's heads | `codex-scrum-subagents` installs project `.agent` kits and native `.codex/agents` custom agents |

---

## Public Pipeline

### Core Flow

1. `codex-master-instructions`
   Global operating rules, evidence policy, completion discipline.
2. `codex-intent-context-analyzer`
   Parse request -> classify intent -> confirm when risky or ambiguous.
3. `codex-plan-writer`
   Break medium/large work into small, verifiable steps.
4. `codex-workflow-autopilot`
   Route into build, fix, debug, review, docs, deploy, teach, or Scrum overlays.
5. Domain routing
   Load only relevant knowledge from domain and security packs.
6. Implementation
   Execute with bounded scope and explicit evidence.
7. `codex-execution-quality-gate`
   Enforce lint, tests, security, output rigor, editorial review, and trend logging.
8. `codex-role-docs` + `codex-project-memory` + `codex-git-autopilot`
   Persist what matters, then commit and ship with discipline.

## Agent System

The pack now supports additive agent routing without breaking the old flow:

1. `codex-intent-context-analyzer` classifies the request and may emit `suggested_agent`.
2. `codex-master-instructions` loads `skills/.agents/<agent>.md` when that file exists.
3. The loaded agent contributes behavioral rules plus `file_ownership` boundaries.
4. If the agent file or `.agents/` folder is missing, the pack falls back to legacy routing through `codex-domain-specialist`.
5. `codex-workflow-autopilot` then routes execution mode as usual, optionally loading a workflow alias file.

This keeps the pack fully backward compatible: if you never use agents or workflow aliases, the previous skill-only pipeline still works exactly the same way.

## Role Documentation System

`codex-role-docs` creates durable project-local docs under `.codex/project-docs/` so each specialist can preserve the context it owns:

- Frontend: UI/UX, design system, design tokens, reusable components, routing, accessibility, frontend tests.
- Backend: architecture, API contracts, database design, domain model, auth/security, integrations, logging, backend tests.
- DevOps: environments, CI/CD, deployment runbook, observability, incidents, secrets/config, rollback.
- Admin: scope, roles/permissions, admin flows, audit logs, data management, dashboards/reports.
- QA: test strategy, regression map, end-to-end flows.

The quality gate runs role-doc checks as advisory warnings in full/deploy mode. Missing docs never block unless a project explicitly makes documentation mandatory.

## Quick Aliases

| Alias | File | Equivalent |
| --- | --- | --- |
| `$plan` | `skills/.workflows/plan.md` | `$codex-plan-writer` + BMAD Phase 1-2 |
| `$debug` | `skills/.workflows/debug.md` | `workflow-debug.md` + 4-phase |
| `$create` | `skills/.workflows/create.md` | `workflow-create.md` |
| `$review` | `skills/.workflows/review.md` | `workflow-review.md` + output-guard + editorial |
| `$deploy` | `skills/.workflows/deploy.md` | `workflow-deploy.md` + full gate |
| `$handoff` | `skills/.workflows/handoff.md` | `workflow-handoff.md` + session summary |

Aliases are shortcuts, not replacements. All legacy triggers such as `$codex-plan-writer`, `$codex-workflow-autopilot`, and `$codex-execution-quality-gate` remain supported in parallel.

## Human-Quality Output Layer

This is the biggest differentiator of the pack today:

- `codex-reasoning-rigor` forces task contracts, evidence ladders, and monitoring loops.
- `codex-document-writer` turns reports, memos, guides, and Vietnamese documents into structured reader-first artifacts.
- `output_guard.py` rejects deliverables that are too generic or weakly grounded.
- `editorial_review.py` checks whether the writing sounds decisive, accountable, and scanable instead of model-safe.
- `benchmark_quality.py` now measures output score, editorial score, quality index, and expectation hit rate across a 12-case static corpus.
- Benchmark corpus loading returns structured JSON errors for invalid corpus files, so release measurement failures are easier to diagnose.
- `run_gate.py` now treats `plan`, `review`, and `handoff` as strict deliverables by default.
- `quality_trend.py` tracks gate pass rate, output score, and editorial score over time.

---

## Skill Inventory

### Core Pipeline

| Skill | What It Does |
| --- | --- |
| `codex-master-instructions` | Global behavior rules and evidence-based completion |
| `codex-intent-context-analyzer` | Structured intent parsing and confirmation gating |
| `codex-context-engine` | Project genome loading for large repos |
| `codex-plan-writer` | Verifiable plan generation |
| `codex-workflow-autopilot` | Workflow routing and mode selection |
| `codex-reasoning-rigor` | Anti-generic reasoning and output contracts |
| `codex-document-writer` | Professional documents, reports, memos, guides, Vietnamese style, and reliability tone |
| `codex-role-docs` | Project-local FE/BE/DevOps/Admin/QA docs that preserve role micro-context |
| `codex-scrum-subagents` | Scrum role kits, workflows, native custom agents, artifact generation |

### Knowledge Packs

| Skill | Coverage | Refs | Starters |
| --- | --- | ---: | ---: |
| `codex-design-system` | Premium UI vocabulary across palettes, typography, layout, motion, composition, trends, and anti-patterns | 7 | 0 |
| `codex-design-md` | Durable `DESIGN.md` contracts, lint/diff/export workflows, and design-token source of truth | 3 | 1 |
| `codex-domain-specialist` | Full-stack engineering | 66 | 19 |
| `codex-security-specialist` | Network, infra, AppSec, DevSecOps, compliance | 30 | 10 |

### Quality and Delivery

| Skill | What It Adds |
| --- | --- |
| `codex-execution-quality-gate` | Pre-commit checks, security scan, smart test selection, output guard, editorial review, UX/a11y, Lighthouse, quality trends |
| `codex-project-memory` | Decision logs, summaries, handoffs, genome, changelog, growth reporting |
| `codex-docs-change-sync` | Code diff to docs impact mapping |
| `codex-role-docs` | Role-scoped docs initialization, updates, indexing, and advisory coverage checks |
| `codex-git-autopilot` | Conventional commits, signing, and gate-aware commit flow |
| `codex-doc-renderer` | DOCX -> PDF -> PNG rendering helpers |

---

## Quick Start

### 1. Install

**Windows (PowerShell)**

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

**macOS / Linux**

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

### 2. Verify

```bash
# Unit tests
python -m pytest skills/tests -q

# Smoke checks
python skills/tests/smoke_test.py
```

### 3. Useful Commands

| Command | Purpose |
| --- | --- |
| `$codex-genome` | Build project context document |
| `$codex-intent-context-analyzer` | Parse a request into structured intent |
| `$codex-plan-writer` | Create an implementation plan |
| `$codex-workflow-autopilot` | Route work into the right execution flow |
| `$codex-reasoning-rigor` | Force deeper, less generic reasoning |
| `$role-docs` | Load role documentation workflow |
| `$init-docs` | Initialize `.codex/project-docs/` |
| `$check-docs` | Check role-doc coverage and suggested updates |
| `$design` | Load premium visual vocabulary before UI work |
| `$design-md` | Scaffold, lint, diff, and export `DESIGN.md` contracts |
| `$codex-execution-quality-gate` | Run verification before completion |
| `$output-guard` | Score specificity and evidence |
| `editorial_review.py` | Check whether a deliverable reads like a human-made artifact |
| `$scrum-install` | Install Scrum kit plus native `.codex/agents` |
| `$story-ready-check` | Validate user story readiness |
| `$release-readiness` | Run ship or no-ship release ceremony |
| `$log-decision` | Persist an architecture decision |
| `$session-summary` | Create end-of-session handoff summary |
| `$codex-doctor` | Check runtime installation health |

---

## Recommended Usage

### For implementation work

1. Parse intent.
2. Generate a plan when the task is not tiny.
3. Route only the needed domain context.
4. Implement in small verified slices.
5. Run the quality gate before saying "done".
6. Log decisions and generate a session summary when context matters.

### For reviews, plans, and handoffs

Use the full output-quality stack:

1. `codex-reasoning-rigor`
2. `output_guard.py`
3. `editorial_review.py`
4. `run_gate.py --strict-output`

This is the path that pushes outputs away from generic AI prose and toward human-grade engineering deliverables.

---

## Repository Layout

```text
CodexAI---Skills/
|-- README.md
|-- LICENSE
|-- docs/
|   `-- huong-dan-vi.md
`-- skills/
    |-- VERSION
    |-- CHANGELOG.md
    |-- README.md
    |-- pytest.ini
    |-- requirements.txt
    |-- .agents/
    |-- .workflows/
    |-- .system/
    |-- tests/
    |-- codex-master-instructions/
    |-- codex-intent-context-analyzer/
    |-- codex-context-engine/
    |-- codex-plan-writer/
    |-- codex-workflow-autopilot/
    |-- codex-reasoning-rigor/
    |-- codex-role-docs/
    |-- codex-design-system/
    |-- codex-design-md/
    |-- codex-domain-specialist/
    |-- codex-security-specialist/
    |-- codex-execution-quality-gate/
    |-- codex-project-memory/
    |-- codex-docs-change-sync/
    |-- codex-git-autopilot/
    |-- codex-doc-renderer/
    `-- codex-scrum-subagents/
```

---

## What To Read Next

- Public usage guide: [docs/huong-dan-vi.md](docs/huong-dan-vi.md)
- Technical internals: [skills/README.md](skills/README.md)
- Version history: [skills/CHANGELOG.md](skills/CHANGELOG.md)

---

## License

MIT
