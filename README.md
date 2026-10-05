<img width="1536" height="1024" alt="CodexAI Skill Pack cover" src="https://github.com/user-attachments/assets/88afea81-e3a8-47ef-82f2-9dd7845f8cb4" />

# CodexAI Skill Pack

> An AI agent workflow pack with host integrations for Codex, Claude Code, Cursor, and Antigravity: intent analysis, task routing, implementation guidance, quality checks, and project context.

[![Version](https://img.shields.io/badge/version-18.1.1-blue)](skills/VERSION) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

CodexAI Skill Pack gives an AI coding agent reusable, written workflows for engineering tasks.
Instead of relying on prompt luck, the pack guides the model through a repeatable flow when the task calls for it:

`Intent -> Spec -> Plan -> Route -> Implement -> Verify -> Persist -> Commit`

The pack is designed for 3 outcomes:

- less generic output
- stronger workflow discipline
- deliverables that read more like accountable human engineering work

## What's new in 18.1.1

18.1.1 improves the frontend workflow from experience planning through implementation and visual review. It adds context-led guidance for narrative scroll motion, scene lifecycle and reduced-motion behavior, and asks the visual gate to inspect important checkpoints that fall between capture slices. See [the changelog](skills/CHANGELOG.md) for the full release notes.

## What's new in 18.0.0

18.0.0 is a breaking cleanup. Its changes are listed below; see the changelog for the full version history.

**Breaking**

- Removed compatibility redirect skills `codex-design-system`, `codex-ui-ux-design`, and `codex-creative-direction`. Use `codex-frontend-design` (`$design` / `$ux` / `$direction`).
- Removed redirect agents `ui-ux-designer`, `creative-director`, and `creative-designer`. Use `design-lead`.
- Removed six frontend catalog stubs from `codex-domain-specialist/references/`. Load `codex-frontend-implementation/references/` instead.

**What got more reliable**

- `memory_status --strict` compares the `LANGUAGE_REGISTRY` subset of the codebase index. Indexer-only extras (`.md`, `Dockerfile`, tests the graph skipped) are `coherence.expected_extras`, not a false fail.

The 18.1.1 package and host setup are documented in [docs/INSTALL.md](docs/INSTALL.md). Common Codex entry points include `$plan`, `$design`, `$check`, and `$pipeline`. Full version notes: [skills/CHANGELOG.md](skills/CHANGELOG.md).

---

## Why This Pack Is Different

| Weakness in default AI workflows | What this pack adds |
| --- | --- |
| Vague task interpretation | `codex-intent-context-analyzer` helps make the goal, scope, and ambiguity explicit before code |
| Plans that sound good but do not guide execution | `codex-plan-writer` creates verifiable, dependency-aware task breakdowns |
| Design output drifts between sessions | `codex-frontend-design` plus `codex-design-md` turn design intent into a brief and a lintable `DESIGN.md`; product/surface context lives under `.codex/design/` |
| Vague “make it look great” UI prompts | `design-lead` + `codex-frontend-design` fast path, then `codex-frontend-implementation` and `$visual-gate` |
| Generic output with no proof | `codex-reasoning-rigor` and `output_guard.py` guide and check for evidence-backed deliverables when used |
| AI-safe writing that still feels synthetic | `editorial_review.py` scores tone, decision clarity, tradeoffs, and scanability |
| Documents that make readers infer too much | `codex-document-writer` guides purpose, audience, structure, complete sentences, and reliability wording |
| No final gate before declaring done | `codex-execution-quality-gate` can run lint, tests, security, output quality, editorial quality, UX, and trend checks |
| Context lost between sessions | `codex-role-docs` preserves role-scoped project docs, while `codex-project-memory` stores decisions, summaries, genome, handoffs, and changelog inputs |
| Tacit knowledge stays invisible | `build_knowledge_index.py` turns genome, role docs, decisions, commits, and configs into `.codex/knowledge/INDEX.md` |
| Fullstack prototypes start from vague prompts | `codex-spec-driven-development` provides a spec-first workflow with acceptance criteria before `$plan` and implementation |
| Scrum roles live only in people's heads | `codex-scrum-subagents` installs project `.agent` kits and native `.codex/agents` custom agents |
| Skills only work in one agent app | Host-specific manifests and adapters; see [docs/INSTALL.md](docs/INSTALL.md) for each host's package and verification status |

---

## Optional GitHub CLI

GitHub CLI (`gh`) is optional for normal skill use. Install and authenticate it only for workflows that interact with GitHub, such as PR automation:

```bash
gh auth login
gh auth status
```

Use GitHub CLI credential storage locally. Never commit tokens into plugin manifests, skill docs, generated artifacts, or source files.

---

## Local Quality Pipeline

The local pipeline runs the selected lint, contract, test, build, and doctor stages; it does not certify generated model behavior.

```bash
python skills/.system/scripts/pipeline.py --stage all --format text            # lint, contracts, test, build, doctor
python skills/.system/scripts/pipeline.py --stage lint,contracts --format text # fast pre-commit
python skills/.system/scripts/pipeline.py --stage all --report-path .codex/pipeline-report.json
```

See `skills/.system/OPERATION_RUNBOOK.md` for the operator workflow.

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
   Run configured lint, tests, security, output rigor, editorial review, and trend checks.
8. `codex-role-docs` + `codex-project-memory` + `codex-git-autopilot`
   Persist what matters, then commit and ship with discipline.

## Agent System

The pack now supports additive agent routing without breaking the old flow:

1. `codex-intent-context-analyzer` classifies the request and may emit `suggested_agent`.
2. `codex-master-instructions` loads `skills/.agents/<agent>.md` when that file exists.
3. The loaded agent contributes behavioral rules plus `file_ownership` boundaries.
4. If the agent file or `.agents/` folder is missing, the pack falls back to legacy routing through `codex-domain-specialist`.
5. `codex-workflow-autopilot` then routes execution mode as usual, optionally loading a workflow alias file.

Agents are optional. If you never set `suggested_agent`, routing still goes through `codex-domain-specialist`. 18.0.0 is **not** skill-name compatible with the three deleted design redirects: `$design` / `$ux` / `$direction` still resolve to `codex-frontend-design`.

## Role Documentation System

`codex-role-docs` can create durable project-local docs under `.codex/project-docs/` so each specialist can preserve the context it owns. By default, `$init-docs` creates a project brief and ADR template; role folders are created for selected roles:

- Frontend: UI/UX, design system, design tokens, reusable components, routing, accessibility, frontend tests.
- Backend: architecture, API contracts, database design, domain model, auth/security, integrations, logging, backend tests.
- DevOps: environments, CI/CD, deployment runbook, observability, incidents, secrets/config, rollback.
- Admin: scope, roles/permissions, admin flows, audit logs, data management, dashboards/reports.
- QA: test strategy, regression map, end-to-end flows.

`auto_gate.py` now runs a lightweight runtime preflight in quick/full/deploy modes, then runs role-doc checks as advisory warnings in full/deploy mode. Missing docs never block unless a project explicitly makes documentation mandatory.

## Spec-Driven Prototype Flow

For MVP, fullstack prototype, "from scratch", or "build whole app" requests, the pack now routes through `$prototype`:

`$hook -> $init-profile -> $genome -> $init-docs -> $spec -> $plan -> $sdd or inline -> $knowledge -> $check-full`

This makes requirements, acceptance criteria, FE/BE/data/QA impact, and verification visible before implementation. The spec layer is advisory in `auto_gate.py`, but `$prototype` treats spec-first work as mandatory.

## Quick Aliases

| Alias | File | Equivalent |
| --- | --- | --- |
| `$plan` | `skills/.workflows/plan.md` | `$codex-plan-writer` + BMAD Phase 1-2 |
| `$debug` | `skills/.workflows/debug.md` | `workflow-debug.md` + 4-phase |
| `$create` | `skills/.workflows/create.md` | `workflow-create.md` |
| `$prototype` | `skills/.workflows/prototype.md` | `$spec` + `$plan` + role docs + full gate |
| `$review` | `skills/.workflows/review.md` | `workflow-review.md` + output-guard + editorial |
| `$deploy` | `skills/.workflows/deploy.md` | `workflow-deploy.md` + full gate |
| `$handoff` | `skills/.workflows/handoff.md` | `workflow-handoff.md` + session summary |
| `$design` / `$ux` / `$direction` | `codex-frontend-design` | Fast for a page/component; prototype for multi-screen product flows; studio for requested alternatives or a new identity |
| `$check` | `auto_gate.py --mode quick` | Advisory pre-commit gate |
| `$pipeline` | `pipeline.py --stage all` | Lint, contracts, test, build, doctor |

Aliases are shortcuts, not replacements. All legacy triggers such as `$codex-plan-writer`, `$codex-workflow-autopilot`, and `$codex-execution-quality-gate` remain supported in parallel.

## Human-Quality Output Layer

The output-quality workflows include:

- `codex-reasoning-rigor` guides task contracts, evidence ladders, and monitoring loops.
- `codex-logical-decision-layer` guides compact option comparison before ambiguous decisions.
- `codex-document-writer` turns reports, memos, guides, and Vietnamese documents into structured reader-first artifacts.
- `output_guard.py` rejects deliverables that are too generic or weakly grounded.
- `editorial_review.py` checks whether the writing sounds decisive, accountable, and scanable instead of model-safe.
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
| `codex-runtime-hook` | One-command project preflight for domain detection and missing FE/BE readiness artifacts |
| `codex-reasoning-rigor` | Anti-generic reasoning and output contracts |
| `codex-logical-decision-layer` | Compact option comparison and decision contracts without hidden chain-of-thought |
| `codex-document-writer` | Professional documents, reports, memos, guides, Vietnamese style, and reliability tone |
| `codex-role-docs` | Project-local FE/BE/DevOps/Admin/QA docs that preserve role micro-context |
| `codex-spec-driven-development` | Spec-first requirements, acceptance criteria, traceability, and prototype workflow |
| `codex-scrum-subagents` | Scrum role kits, workflows, native custom agents, artifact generation |

### Knowledge Packs

| Skill | Coverage |
| --- | --- |
| `codex-frontend-design` | Fast path for a page/component, prototype workflow for multi-screen product flows, or studio path for requested alternatives/new identity; layout, type, states, anti-slop, and refinement guidance |
| `codex-frontend-implementation` | React/Next/Tailwind/shadcn/GSAP recipes, craft guidance with provenance, and implementation starters |
| `codex-design-md` | Durable `DESIGN.md` contracts, lint/diff/export workflows, and design-token source of truth |
| `codex-visual-quality-gate` | Mechanical UI source checks, optional Playwright stitched capture, fresh-eyes review with `DEGRADED` marking |
| `codex-domain-specialist` | Focused references for full-stack engineering |
| `codex-security-specialist` | Focused references for network, infrastructure, AppSec, DevSecOps, and compliance |

### Quality and Delivery

| Skill | What It Adds |
| --- | --- |
| `codex-execution-quality-gate` | Pre-commit checks, security scan, smart test selection, output guard, editorial review, UX/a11y, Lighthouse, quality trends |
| `codex-project-memory` | Decision logs, summaries, handoffs, genome, knowledge index, changelog, growth reporting |
| `codex-docs-change-sync` | Code diff to docs impact mapping |
| `codex-role-docs` | Role-scoped docs initialization, updates, indexing, and advisory coverage checks |
| `codex-git-autopilot` | Conventional commits, signing, and gate-aware commit flow |
| `codex-doc-renderer` | DOCX -> PDF -> PNG rendering helpers |

---

## Quick Start

1. **Install** for one host. This example uses Cursor; replace `cursor` with `codex`, `claude`, or `antigravity` when needed:

```powershell
python ".\skills\.system\scripts\install.py" --host cursor --scope user --apply --format text
```

2. **Verify** the selected host wiring after installation:

```powershell
python ".\skills\.system\scripts\install.py" doctor --host cursor --scope user --format text
```

3. **Use an alias** such as `$plan`, `$create`, `$design`, or `$check`. Load `codex-master-instructions` first.

Replace `cursor` with the host you use. Host installation steps and support limits are listed in [docs/INSTALL.md](docs/INSTALL.md). The doctor checks host wiring; it does not certify rendered UI or model behavior.

### 1. Install (advanced)

**Preferred: generic CLI/IDE trust harness**

Use this when you want a generic project adapter scaffold and a JSON report. The generated pre-prompt hook is a descriptor for a host integration; the host must support and run that hook for automatic routing to occur:

```powershell
python ".\skills\.system\scripts\trust_harness.py" --project-root "." --skills-root ".\skills" --setup generic --apply --evidence ".\.codexai\evidence\trust-harness.json" --format text
```

For a dry-run that does not write files, omit `--apply`. The generic setup creates `.codexai/skills`, merges a bounded `AGENTS.md` bridge, writes `.codexai/hooks/pre_prompt.json`, validates package contracts, runs the prompt-router corpus, the Python unit suite, responsive Node tests when Node.js is available, and a release-package dry run. Missing Node.js or skipped Node tests (for example, a browser fixture without Playwright/Chromium) are reported as warnings. These checks do not establish that an arbitrary IDE or CLI executes the hook.

**Preferred: Codex-native user install**

```powershell
python ".\skills\.system\scripts\install_codex_native.py" --source ".\skills" --scope user --dry-run --format text
python ".\skills\.system\scripts\install_codex_native.py" --source ".\skills" --scope user --apply --format text
```

**Repo-local install**

```powershell
python ".\skills\.system\scripts\install_codex_native.py" --source ".\skills" --scope repo --repo-root "." --apply --format text
```

The repo also ships a native plugin manifest at `.codex-plugin/plugin.json` and a local marketplace entry at `.agents/plugins/marketplace.json`.

**Claude Code user install**

```powershell
python ".\skills\.system\scripts\install_claude_native.py" --source ".\skills" --scope user --dry-run --format text
python ".\skills\.system\scripts\install_claude_native.py" --source ".\skills" --scope user --apply --format text
```

**Claude Code plugin mode**

```powershell
python ".\skills\.system\scripts\validate_claude_plugin.py" --plugin-root "." --format text
claude --plugin-dir .
```

Claude Code uses `.claude-plugin/plugin.json`, `skills/<skill>/SKILL.md`, and `hooks/hooks.json`. In plugin mode, skills are namespaced as `/codexai-agentic-workflow:<skill-name>`.

**Three runtime levels**

1. Python-only core: routers, design context, mechanical visual gate, quality gates. No Node required.
2. Python + local Impeccable detector: optional, never auto-installed. Doctor reports `available|skipped|failed`.
3. Antigravity IDE/CLI native package **candidate**:

```powershell
python ".\skills\.system\scripts\build_antigravity_plugin.py" --plugin-root "." --apply --format json
python ".\skills\.system\scripts\install_antigravity_native.py" --plugin-root "." --scope workspace --surface both --apply --format json
python ".\skills\.system\scripts\validate_antigravity_plugin.py" --package-dir ".\dist\antigravity-plugin" --format json
```

Workspace install lands in `.agents/plugins/codexai-agentic-workflow/`. User IDE uses `%USERPROFILE%\.gemini\config\plugins\`. User CLI uses `%USERPROFILE%\.gemini\antigravity-cli\plugins\`. If `agy` is missing, the validator records its CLI probe as skipped. A successful CLI probe does not establish that the plugin works in the IDE; keep this package labeled a candidate until both host surfaces are exercised.

See `docs/design-knowledge-provenance.md` and `THIRD_PARTY_NOTICES.md`.

**Windows (PowerShell)**

```powershell
python ".\skills\.system\scripts\sync_global_skills.py" --source-root ".\skills" --global-root "$env:USERPROFILE\.codex\skills" --dry-run --format text
python ".\skills\.system\scripts\sync_global_skills.py" --source-root ".\skills" --global-root "$env:USERPROFILE\.codex\skills" --apply --format text
```

**macOS / Linux**

```bash
python ./skills/.system/scripts/sync_global_skills.py --source-root ./skills --global-root "$HOME/.codex/skills" --dry-run --format text
python ./skills/.system/scripts/sync_global_skills.py --source-root ./skills --global-root "$HOME/.codex/skills" --apply --format text
```

The legacy sync commands copy dot directories such as `.system`, `.agents`, and `.workflows`. Sync is dry-run by default; use `--apply` only after reviewing the preview. Do not install with `skills/*`, because that can omit required runtime metadata on some systems.

### 2. Verify

```bash
# Everything in one command (lint, contracts, test, build, doctor)
python skills/.system/scripts/pipeline.py --stage all --format text

# Python unit tests
python -m unittest discover -s skills/tests -p "test_*.py"

# Responsive capture tests
node --test skills/tests/responsive_capture_stitch.test.mjs skills/tests/responsive_capture_core.test.mjs skills/tests/responsive_capture_browser.test.mjs

# Pack operation health
python skills/.system/scripts/check_pack_health.py --skills-root skills --format text
python skills/.system/scripts/validate_codex_plugin.py --plugin-root . --format text
python skills/.system/scripts/validate_claude_plugin.py --plugin-root . --format text
python skills/.system/scripts/trust_harness.py --project-root . --skills-root skills --setup generic --evidence .codexai/evidence/trust-harness.json --format text

# Clean release archive preview/build
python skills/.system/scripts/build_release_zip.py --project-root . --dry-run --format text
python skills/.system/scripts/build_release_zip.py --project-root . --apply --format text
```

### 3. Useful Commands

| Command | Purpose |
| --- | --- |
| `$codex-genome` | Build project context document |
| `$codex-intent-context-analyzer` | Parse a request into structured intent |
| `$codex-plan-writer` | Create an implementation plan |
| `$codex-workflow-autopilot` | Route work into the right execution flow |
| `$hook` / `$preflight` | Run one-command project readiness preflight |
| `$health` | Check pack manifest, registry, aliases, dot directories, global sync, and markdown encoding |
| `$init-profile` | Create `.codex/profile.json` for stable routing and user preferences |
| `$think` / `$decide` | Build compact multi-option decision surface |
| `$codex-reasoning-rigor` | Guide more specific, evidence-backed reasoning |
| `$role-docs` | Load role documentation workflow |
| `$init-docs` | Initialize `.codex/project-docs/` |
| `$check-docs` | Check role-doc coverage and suggested updates |
| `$spec` | Create or check `.codex/specs/<slug>/SPEC.md` |
| `$prototype` | Run the full spec-first prototype workflow |
| `$knowledge` | Build `.codex/knowledge/INDEX.md` from context, docs, decisions, commits, and config |
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
2. Run `$hook` / `$preflight` for medium or large work.
3. Generate a plan when the task is not tiny.
4. Route only the needed domain context.
5. Implement in small verified slices.
6. Run the quality gate before saying "done".
7. Log decisions and generate a session summary when context matters.

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
|-- .codex/hooks.json
|-- .codex-plugin/plugin.json
|-- .claude-plugin/plugin.json
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
    |   |-- OPERATION_RUNBOOK.md
    |   |-- REGISTRY.md
    |   `-- manifest.json
    |-- tests/
    |-- codex-master-instructions/
    |-- codex-intent-context-analyzer/
    |-- codex-context-engine/
    |-- codex-plan-writer/
    |-- codex-workflow-autopilot/
    |-- codex-reasoning-rigor/
    |-- codex-role-docs/
    |-- codex-frontend-design/
    |-- codex-frontend-implementation/
    |-- codex-visual-quality-gate/
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
- Operation runbook: [skills/.system/OPERATION_RUNBOOK.md](skills/.system/OPERATION_RUNBOOK.md)
- Version history: [skills/CHANGELOG.md](skills/CHANGELOG.md)

---

## License

MIT
