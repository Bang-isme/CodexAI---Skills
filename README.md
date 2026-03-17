<img width="1536" height="1024" alt="ChatGPT Image Feb 25, 2026, 03_25_19 AM" src="https://github.com/user-attachments/assets/88afea81-e3a8-47ef-82f2-9dd7845f8cb4" />
# CodexAI Skill Pack

> **Production-ready instruction framework for Codex** — deterministic workflows, intelligent domain routing, pre-delivery quality gates, and persistent project memory across sessions.

[![Version](https://img.shields.io/badge/version-12.5.0-blue)]() [![Tests](https://img.shields.io/badge/pytest-83%2F83%20passed-green)]() [![Smoke](https://img.shields.io/badge/smoke-47%2F47%20passed-green)]() [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

CodexAI Skill Pack transforms Codex from an ad-hoc code assistant into a **structured engineering partner**. Instead of relying on prompt quality, the pack enforces a repeatable pipeline: understand intent → plan → route to domain expertise → implement → verify → persist knowledge.

### Key Stats

| Metric | Value |
| --- | --- |
| Core Skills | 14 |
| CLI Scripts | 36 |
| Reference Docs | 146 (66 fullstack + 30 security + 50 other) |
| Starter Templates | 29 (19 fullstack + 10 security) |
| Scrum Delivery Kit | 10 role briefs + 10 native Codex agents + 7 workflows + 12 aliases + 6 artifact templates |
| Test Coverage | 83 unit + 47 smoke = 130 tests |

---

## Why It Matters

| Problem Without Pack | Solution With Pack |
| --- | --- |
| AI drifts from requirements mid-task | **Intent Analyzer** locks goal + constraints before code |
| No pre-delivery verification | **Quality Gate** enforces lint, tests, security, a11y checks plus auto-strict validation for plans, reviews, and handoffs |
| Knowledge lost between sessions | **Project Memory** persists decisions, context, handoff docs |
| Generic advice and shallow reasoning | **Reasoning Rigor + Output Guard** force evidence-backed, repo-specific output contracts |
| Generic advice, no domain depth | **Domain Specialist** routes to 66 focused references |
| Security as afterthought | **Security Specialist** applies defense-in-depth from 30 references |
| Inconsistent commit quality | **Git Autopilot** enforces conventional commits + GPG signing |
| Scrum roles live only in people's heads | **Scrum Subagents** installs project-local role/workflow kits plus native Codex custom agents and reusable artifacts |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    codex-master-instructions (P0)            │
│        Global behavior rules, completion policy, evidence    │
└──────────────┬──────────────────────────────────┬───────────┘
               │                                  │
     ┌─────────▼─────────┐             ┌─────────▼──────────┐
     │  Intent Analyzer   │             │  Context Engine     │
     │  Parse → Confirm   │             │  genome.md loader   │
     └─────────┬─────────┘             └─────────────────────┘
               │
     ┌─────────▼─────────┐
     │  Plan Writer       │  (medium/large tasks only)
     └─────────┬─────────┘
               │
     ┌─────────▼─────────────────────────────────────────────┐
     │             Workflow Autopilot                          │
     │  build │ fix │ debug │ review │ docs │ deploy │ teach  │
     └──┬──────────┬──────────┬──────────┬───────────────────┘
        │          │          │          │
  ┌─────▼────┐ ┌──▼────────┐│    ┌─────▼──────────┐
  │ Domain   │ │ Security  ││    │ Doc Renderer    │
  │Specialist│ │Specialist ││    │ (DOCX/PDF)      │
  │ 59 refs  │ │ 30 refs   ││    └────────────────-┘
  │ 19 start │ │ 10 start  ││
  └──────────┘ └───────────┘│
                             │
     ┌───────────────────────▼───────────────────────────────┐
     │              Execution Quality Gate                    │
     │  lint │ test │ security │ a11y │ UX │ Lighthouse       │
     └──────────────┬────────────────────────────────────────┘
                    │
     ┌──────────────▼──────┐     ┌──────────────────────┐
     │  Docs Change Sync   │     │  Project Memory       │
     │  code→docs mapping  │     │  decisions, genome,   │
     └─────────────────────┘     │  summaries, handoff   │
                                 └──────────┬───────────┘
                                            │
                               ┌────────────▼───────────┐
                               │    Git Autopilot        │
                               │  stage→gate→sign→push   │
                               └─────────────────────────┘
```

---

## Skills Detail

### Core Pipeline

| Skill | What It Does | Key Feature |
| --- | --- | --- |
| **master-instructions** | Global behavior rules loaded on every session | Evidence-based completion policy, circuit breaker on 3 consecutive failures |
| **intent-context-analyzer** | Parses user request into structured JSON | Socratic Gate for ambiguous requests — asks before coding |
| **context-engine** | Loads `.codex/context/genome.md` for project awareness | Auto-suggests genome generation for repos with 50+ files |
| **plan-writer** | Creates bite-sized implementation plans | Each task: 2-5 min, with files/code/commands/verification |
| **workflow-autopilot** | Routes to the right workflow (build, fix, debug, review, docs) | 8 behavioral modes including thinking-partner and devil's-advocate |
| **reasoning-rigor** | Forces deliberate, non-generic, evidence-backed outputs | Adds task contracts, evidence ladders, and monitoring loops |
| **scrum-subagents** | Installs a project-local `.agent` Scrum kit plus native `.codex/agents` custom agents | 10 role briefs + 10 native agents + 7 ceremony workflows + 12 aliases |

### Knowledge Packs

| Skill | Scope | Refs | Starters | Routing |
| --- | --- | ---: | ---: | --- |
| **domain-specialist** | Full-stack development | 66 | 19 | 12 domains, 45+ signals, 10 combos |
| **security-specialist** | Network → Infra → AppSec → DevSecOps → Compliance | 30 | 10 | 24 domains, defense-in-depth principles |

### Quality & Delivery

| Skill | What It Does | Scripts |
| --- | --- | ---: |
| **execution-quality-gate** | Pre-commit checks, test selection, security scan, repo-aware output guard, auto-strict deliverable gate, UX/a11y audit, Lighthouse, quality trends | 16 |
| **project-memory** | Decision log, session summary, handoff doc, genome, changelog, growth report | 11 |
| **docs-change-sync** | Maps code diffs to impacted documentation | 1 |
| **git-autopilot** | Conventional commits + GPG signing + pre-commit gate | 1 |
| **doc-renderer** | DOCX → PDF → PNG rendering pipeline | 1 |
| **scrum-subagents** | Installs Scrum-focused subagents, validates them, and supports diff/update workflows plus artifact generation for `.agent/` | 4 |

---

## Quick Start

### 1. Install

**Windows (PowerShell):**
```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

**macOS / Linux:**
```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

### 2. Verify

```bash
# Smoke test (47 checks: SKILL.md exists, entry-point scripts respond, key JSON CLIs work)
python skills/tests/smoke_test.py --verbose

# Unit tests (82 tests: parsing, output guard, auto-strict gate, reasoning brief, Scrum native-agent installer/validator, workflow routing contract, security scan, impact prediction, etc.)
python -m pytest skills/tests -v
```

### 3. First Commands

| Command | What It Does |
| --- | --- |
| `$codex-genome` | Generate project context document |
| `$codex-intent-context-analyzer` | Parse your request into structured intent |
| `$codex-workflow-autopilot` | Route to the right workflow |
| `$codex-reasoning-rigor` | Force deeper, less generic, more evidence-backed output |
| `$codex-execution-quality-gate` | Run all verification checks |
| `$output-guard` | Check whether a deliverable is too generic or weakly evidenced |
| `$scrum-install` | Install the Scrum `.agent` kit plus native `.codex/agents` custom agents into a project |
| `$story-ready-check` | Check whether a story is ready before coding |
| `$release-readiness` | Run a ship or no-ship ceremony with evidence |
| `$log-decision` | Record an architecture decision |
| `$session-summary` | Generate end-of-session summary |
| `$codex-doctor` | Health check for skills installation |

---

## Recommended Workflow

```
1. 🎯 INTENT      →  $codex-intent-context-analyzer
                      Lock goal, constraints, and complexity.

2. 📋 PLAN        →  $codex-plan-writer  (medium/large tasks)
                      Break into bite-sized, verifiable steps.

3. 🔀 ROUTE       →  Automatic domain/security routing
                      Load only relevant references (max 4).

4. 💻 IMPLEMENT   →  Code with bounded scope
                      Follow plan steps, one at a time.

5. ✅ VERIFY      →  $codex-execution-quality-gate
                      Lint + tests + security + a11y.

6. 📄 DOCS        →  Auto-detected docs candidates
                      Review impacted documentation.

7. 💾 PERSIST     →  $log-decision / $session-summary
                      Preserve knowledge for next session.

8. 🚀 COMMIT      →  Git Autopilot
                      Conventional commit + sign + push.
```

---

## Repository Layout

```
CodexAI---Skills/
├── README.md                    ← You are here
├── LICENSE                      ← MIT
├── docs/
│   └── huong-dan-vi.md          ← Hướng dẫn sử dụng (Tiếng Việt)
└── skills/
    ├── VERSION                  ← 12.5.0
    ├── CHANGELOG.md             ← Full version history
    ├── README.md                ← Technical internals
    ├── pytest.ini
    ├── requirements.txt
    ├── tests/                   ← 83 unit + 47 smoke tests
    ├── templates/               ← Shared templates
    ├── codex-master-instructions/
    ├── codex-intent-context-analyzer/
    ├── codex-context-engine/
    ├── codex-plan-writer/
    ├── codex-workflow-autopilot/
    ├── codex-reasoning-rigor/
    ├── codex-domain-specialist/
    │   ├── SKILL.md             ← Routing logic (22 KB)
    │   ├── references/          ← 59 .md files
    │   └── starters/            ← 19 template files
    ├── codex-security-specialist/
    │   ├── SKILL.md             ← Security routing (11 KB)
    │   ├── references/          ← 30 .md files
    │   └── starters/            ← 10 template files
    ├── codex-execution-quality-gate/
    │   ├── scripts/             ← 16 Python scripts + 1 shared helper
    │   └── references/          ← 15 spec files
    ├── codex-project-memory/
    │   ├── scripts/             ← 11 Python scripts
    │   └── references/          ← 10 spec files
    ├── codex-docs-change-sync/
    ├── codex-git-autopilot/
    ├── codex-doc-renderer/
    └── codex-scrum-subagents/   ← Scrum `.agent` installer + native Codex agents + role/workflow kit
```

---

## Dependencies

### Required

- **Python 3.10+** — all scripts use Python
- **Git** — git-autopilot, genome, changelog, docs-sync

### Optional

| Dependency | Used By | Install |
| --- | --- | --- |
| Node.js / npm | Lighthouse, Playwright wrappers | [nodejs.org](https://nodejs.org) |
| GPG | Signed commits (Verified badge) | `winget install GnuPG.GnuPG` |
| pdf2image + Poppler | Doc renderer | `pip install pdf2image` |

---

## Documentation

| Document | Language | Purpose |
| --- | --- | --- |
| `README.md` (this file) | English | Public overview and quick start |
| `skills/README.md` | English | Technical internals, customization, all commands |
| `docs/huong-dan-vi.md` | Tiếng Việt | Hướng dẫn sử dụng chi tiết |
| `skills/CHANGELOG.md` | English | Complete version history (v1.0 → v12.5.0) |

---

## License

MIT — see [LICENSE](LICENSE).
