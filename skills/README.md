# CodexAI Skill Pack — Technical Internals

> This document covers the runtime contents of `skills/`. For public overview, see [../README.md](../README.md). For Vietnamese guide, see [../docs/huong-dan-vi.md](../docs/huong-dan-vi.md).

## Current State

| Metric | Value |
| --- | --- |
| Version | `12.5.0` |
| Skills | 14 |
| Scripts | 36 + 2 shared modules (`_js_parser.py`, `_scrum_agent_kit.py`) |
| References | 146 |
| Starters | 29 |
| Pytest | 83/83 |
| Smoke | 47/47 |

---

## Runtime Pipeline

```
User Request
    │
    ▼
┌─ Intent Context Analyzer ──────────────────────────────────┐
│  Parse request → structured JSON {intent, goal, complexity} │
│  Socratic Gate for ambiguous → confirm before proceeding    │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─ Plan Writer ───────────────────────────────────────────────┐
│  (medium/large only) Break into 2-5 min verifiable tasks    │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─ Workflow Autopilot ────────────────────────────────────────┐
│  Route: build | fix | debug | review | docs | deploy | teach│
│  Modes: thinking-partner, devil's-advocate, ship            │
│  BMAD phases for complex: analysis → plan → solution → impl │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─ Domain / Security Routing ─────────────────────────────────┐
│  Domain: 12 primary domains, 45+ signal entries, 10 combos  │
│  Security: 24 domains, defense-in-depth, max 4 refs/pass    │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─ Implementation ────────────────────────────────────────────┐
│  Execute plan steps with domain context loaded              │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─ Execution Quality Gate ────────────────────────────────────┐
│  P0: pre_commit_check (lint, secret, debug)                 │
│  P1: smart_test_selector (run only relevant tests)          │
│  P2: run_gate (pass/fail orchestrator)                      │
│  P3: security_scan + bundle_check                           │
│  P4-P9: tech_debt, suggest, quality_trend, UX, a11y, LH    │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─ Post-Task ─────────────────────────────────────────────────┐
│  docs_change_sync → project_memory → git_autopilot          │
└─────────────────────────────────────────────────────────────┘
```

---

## Skill Inventory

### 1. `codex-master-instructions` — Global Behavior (P0)

**Always loaded.** Defines:
- Request classification (build/fix/debug/review/docs/refactor/deploy)
- Evidence-based completion ("Done" requires proof, not confidence)
- Circuit breaker: halt after 3 consecutive failures
- Complex task decomposition protocol (Master Plan → tickets)
- Script invocation discipline (--help first, black-box execution)

| Asset | Count |
| --- | --- |
| References | 3 (`defense-in-depth.md`, `root-cause-tracing.md`, `condition-based-waiting.md`) |

### 2. `codex-intent-context-analyzer` — Intent Parsing

**Always loaded.** Parses every code-change request into:
```json
{
  "intent": "build | fix | review | debug | docs | refactor | deploy",
  "goal": "One-sentence description",
  "complexity": "simple | complex",
  "missing_info": ["..."],
  "needs_confirmation": true
}
```

Socratic Gate triggers for complex/ambiguous → asks 3+ questions before code.

### 3. `codex-context-engine` — Project Genome

**Always loaded** (checks for genome existence). Generates `.codex/context/genome.md`:
- Tech stack, directory structure, entry points, data models
- API surface, coding conventions
- Token budget: genome (~2400 tokens) + max 3 module maps

Uses `codex-project-memory/scripts/generate_genome.py` for generation.

### 4. `codex-plan-writer` — Task Planning

**On-demand.** Creates `{task-slug}.md` with:
- Overview, success criteria, tech stack rationale
- Task breakdown (domain, priority, dependencies, verify method, rollback, evidence)
- Evidence and monitoring expectations for medium/high-risk work
- Phase X verification checklist

### 5. `codex-workflow-autopilot` — Workflow Routing

**On-demand.** Routes to workflow + behavioral mode:

| Mode | When |
| --- | --- |
| `thinking-partner` | "compare options", "help me decide" |
| `devil's-advocate` | "find blind spots", "red team this" |
| `teach` | "explain this", "walk me through" |
| `implement` | "build this", "create that" |
| `debug` | "error", "broken", "not working" |
| `review` | "audit", "check quality" |
| `ship` | "deploy", "release" |

| Asset | Count |
| --- | --- |
| Scripts | 1 (`explain_code.py`) |
| References | 11 (3 mode specs + 7 workflow templates + 1 routing contract) |

### 6. `codex-reasoning-rigor` — Anti-Generic Output Discipline

**On-demand.** Forces deliberate, evidence-backed output when shallow advice is not acceptable:

| Asset | Count |
| --- | --- |
| Scripts | 1 (`build_reasoning_brief.py`) |
| References | 4 |
| Assets | 3 templates |

Primary use case: activate when the user asks for deeper thinking, less generic output, stronger tradeoffs, monitoring loops, or repo-grounded reasoning instead of reusable best-practice language. The brief generator is now strict by default and only emits `_TODO_` scaffolds when `--allow-placeholders` is explicitly set.

### 7. `codex-domain-specialist` — Full-Stack Knowledge

**On-demand.** The largest knowledge pack:

| Category | References |
| --- | --- |
| Frontend (React, Next.js, CSS, forms, i18n, PWA) | 15 |
| Backend (API, validation, logging, background jobs, upload) | 12 |
| Database (aggregation, migration, caching, pagination) | 6 |
| Security & Auth (auth, OAuth, web security, payment) | 5 |
| Architecture & DevOps (deployment, K8s, observability, monorepo) | 12 |
| Cross-cutting (TypeScript, testing, Git, GraphQL, dates, export) | 9 |

**Routing system:**
- plus 7 creative/design-focused references currently present in the pack
- 12 primary domains in detection table
- 45+ signal entries across 9 categories
- 10 common combo patterns (e.g. "Build new CRUD page" → 4 specific refs)
- 5 conflict resolution rules
- 30 feedback-driven supplemental loading categories
- 19 starter auto-routing patterns

**Starters:** 19 production-ready templates (Express API, React CRUD, Docker Compose, auth flow, etc.)

### 8. `codex-security-specialist` — Security Knowledge

**On-demand.** Defense-in-depth across 6 layers:

| Layer | Version | References | Starters |
| --- | --- | ---: | ---: |
| Network (TCP/IP, firewall, VPN, DNS, SSL, segmentation) | v10.0 | 6 | 3 |
| Infrastructure (Linux, secrets, containers, cloud, API) | v10.1 | 5 | 2 |
| Offensive/Defensive (OWASP, pentest, vuln scan, IR, SIEM, threat) | v10.2 | 6 | 1 |
| DevSecOps (pipeline, SAST/DAST/SCA, IaC, supply chain) | v10.3 | 4 | 2 |
| Compliance (ISO 27001, GDPR, SOC 2, crypto, PKI) | v10.4 | 5 | 1 |
| Advanced (zero trust, DDoS, IDS/IPS, audit framework) | v10.5 | 4 | 1 |

**6 core principles:** defense-in-depth, least privilege, fail secure, zero trust, separation of duties, audit everything.

### 9. `codex-execution-quality-gate` — Verification

**On-demand.** 16 scripts organized by priority:

| Priority | Script | Blocking? |
| --- | --- | --- |
| P0 | `pre_commit_check.py` | ✅ Yes |
| P0 | `run_gate.py` | ✅ Yes |
| P1 | `smart_test_selector.py` | ✅ Yes |
| P2 | `security_scan.py` | ✅ Yes |
| P2 | `bundle_check.py` | ⚠️ Warning |
| P3 | `predict_impact.py` | ⚠️ Warning |
| P4 | `tech_debt_scan.py` | ℹ️ Advisory |
| P5 | `suggest_improvements.py` | ℹ️ Advisory |
| P6 | `output_guard.py` | ℹ️ Advisory |
| P7 | `quality_trend.py` | ℹ️ Advisory |
| P8 | `ux_audit.py` | ⚠️ Warning |
| P9 | `accessibility_check.py` | ⚠️ Warning |
| P10 | `lighthouse_audit.py` | ⚠️ Warning |
| — | `playwright_runner.py` | E2E helper |
| — | `with_server.py` | Server lifecycle |
| — | `doctor.py` | Installation health |
| — | `_js_parser.py` | Shared JS parser |

Highlights:
- `output_guard.py` is now repo-aware when `--repo-root` is supplied, so stale file references can be caught instead of rewarded.
- `run_gate.py` can now auto-enforce strict output for plans, reviews, and handoffs, or fail on weak deliverables explicitly via `--strict-output --output-file/--output-text`.
- `quality_trend.py` now reports gate pass rate, strict-output failures, and average output-guard score in addition to code-shape trends.

### 10. `codex-project-memory` — Knowledge Persistence

**On-demand.** 11 scripts for cross-session memory:

| Script | Command | Purpose |
| --- | --- | --- |
| `decision_logger.py` | `$log-decision` | Record architecture decisions |
| `generate_session_summary.py` | `$session-summary` | End-of-session report |
| `generate_handoff.py` | `$handoff` | Portable context for transfer |
| `generate_changelog.py` | `$changelog` | Release-oriented commit summary |
| `generate_growth_report.py` | `$growth-report` | Developer skill tracking |
| `generate_genome.py` | `$codex-genome` | Project context doc |
| `build_knowledge_graph.py` | `$knowledge-graph` | Deep architecture mapping |
| `compact_context.py` | `$compact-context` | Clean old session data |
| `track_feedback.py` | `$feedback` | AI correction tracking |
| `track_skill_usage.py` | — | Skill effectiveness analytics |
| `analyze_patterns.py` | — | Recurring pattern detection |

### 11. `codex-docs-change-sync` — Docs Impact Mapping

**Lazy.** Maps code diffs to potentially impacted documentation. Report-only by default.

### 12. `codex-git-autopilot` — Guarded Commits

**On-demand.** Pipeline: collect → stage → gate → message → sign → push.

Safety: **never** commits if gate fails, **never** force pushes, falls back to unsigned if GPG unavailable.

### 13. `codex-doc-renderer` — DOCX Rendering

**Lazy.** DOCX → PDF → PNG pipeline for visual document review.

### 14. `codex-scrum-subagents` — Scrum Delivery Kit

**On-demand.** Installs a project-local `.agent` bundle plus native `.codex/agents` custom agents for Scrum delivery:

| Asset | Count |
| --- | --- |
| Scripts | 4 entry points + 1 shared helper (`install_scrum_subagents.py`, `validate_scrum_agent_kit.py`, `generate_scrum_artifact.py`, `run_scrum_alias.py`, `_scrum_agent_kit.py`) |
| References | 6 |
| Installed Role Briefs | 10 |
| Installed Native Codex Agents | 10 |
| Installed Workflows | 7 |
| Installed Manifests | 3 |
| Installed Aliases | 12 |
| Artifact Templates | 6 |

Primary use case: add explicit Product Owner, Scrum Master, architect, developer, QA, security, DevOps, and UX subagent templates to projects that need ceremony-driven coordination and repeatable handoffs.
The installer now supports `--diff`, `--update`, and backup creation across both `.agent` and `.codex/agents`, plus `--native-scope project|personal|both` for first-class personal-agent installs. `validate_scrum_agent_kit.py` can now verify bundled, project, and personal native Codex custom agents, and the bundle also ships a `commands.json` manifest so shorthand triggers like `$scrum-install`, `$story-ready-check`, `$retro`, and `$release-readiness` are documented and testable. The artifact generator still rejects placeholder-only ceremony outputs unless `--allow-placeholders` is explicitly requested.

---

## All Commands Reference

| Command | Skill | Action |
| --- | --- | --- |
| `$codex-intent-context-analyzer` | intent-context-analyzer | Parse request to intent JSON |
| `$codex-workflow-autopilot` | workflow-autopilot | Route to workflow + mode |
| `$codex-reasoning-rigor` | reasoning-rigor | Force deeper, non-generic reasoning |
| `$codex-plan-writer` | plan-writer | Create implementation plan |
| `$codex-execution-quality-gate` | execution-quality-gate | Run verification suite |
| `$codex-doctor` | execution-quality-gate | Health check installation |
| `$setup-check` | execution-quality-gate | Verify dependencies |
| `$output-guard` | execution-quality-gate | Score deliverables for generic filler and weak evidence |
| `$codex-genome` | context-engine / project-memory | Generate project context |
| `$codex-genome --force` | context-engine / project-memory | Force regenerate |
| `$log-decision` | project-memory | Record architecture decision |
| `$session-summary` | project-memory | Generate session report |
| `$handoff` | project-memory | Create portable context |
| `$changelog` | project-memory | Generate release changelog |
| `$growth-report` | project-memory | Developer growth report |
| `$knowledge-graph` | project-memory | Build architecture map |
| `$compact-context` | project-memory | Clean old session data |
| `$feedback` | project-memory | Log AI correction |
| `$codex-docs-change-sync` | docs-change-sync | Map code changes to docs |
| `$teach` | workflow-autopilot | Enter teaching mode |
| `$e2e check` | execution-quality-gate | Run Playwright checks |
| `$lighthouse <url>` | execution-quality-gate | Run Lighthouse audit |
| `$scrum-install` | scrum-subagents | Install the local Scrum `.agent` kit plus native `.codex/agents` custom agents |
| `$scrum-diff` | scrum-subagents | Compare installed `.agent` and `.codex/agents` files vs source bundle |
| `$scrum-update` | scrum-subagents | Refresh missing or changed kit files across both install surfaces |
| `$scrum-validate` | scrum-subagents | Validate the bundled or installed Scrum kit across `.agent` and `.codex/agents` |
| `$backlog-refinement` | scrum-subagents | Turn a request into sprint-ready backlog |
| `$sprint-plan` | scrum-subagents | Build sprint goal, scope, and ownership |
| `$daily-scrum` | scrum-subagents | Run blocker and progress sync |
| `$story-ready-check` | scrum-subagents | Check whether a story is ready to implement |
| `$story-delivery` | scrum-subagents | Drive one story through delivery and verification |
| `$sprint-review` | scrum-subagents | Review increment outcomes and feedback |
| `$retro` | scrum-subagents | Capture process improvements |
| `$release-readiness` | scrum-subagents | Decide ship or no-ship with evidence |

Script-style entry point for the Scrum kit:

```bash
python codex-scrum-subagents/scripts/install_scrum_subagents.py --target-root <project-root>
python codex-scrum-subagents/scripts/install_scrum_subagents.py --target-root <project-root> --diff --format json
python codex-scrum-subagents/scripts/install_scrum_subagents.py --target-root <project-root> --update
python codex-scrum-subagents/scripts/validate_scrum_agent_kit.py --install-root <project-root>/.agent
python codex-scrum-subagents/scripts/run_scrum_alias.py --alias \$story-ready-check --artifact-output .codex/story.md --field title="Checkout validation" --field persona="Store admin" --field need="Validate address input before order creation" --field outcome="Reject invalid orders before payment" --field acceptance_criteria="- invalid addresses block submission" --field notes="- QA covers edge cases"
python codex-scrum-subagents/scripts/generate_scrum_artifact.py --template retrospective --field title="Sprint 8 retrospective" --field sprint_name="Sprint 8" --field wins="- Release stabilized" --field pain_points="- QA joined late" --field actions="- Pull QA into story delivery earlier" --field owners="- scrum-master" --output .codex/retro.md
```

Shorthand alias reference for the Scrum kit:

- `references/command-aliases.md`
- `assets/scrum-agent-kit/services/commands.json`

---

## Customization Points

| What to Customize | Location | How |
| --- | --- | --- |
| Domain knowledge | `codex-domain-specialist/references/` | Add/edit `.md` files + update routing in SKILL.md |
| Security knowledge | `codex-security-specialist/references/` | Add/edit `.md` files + update routing in SKILL.md |
| Gate policy (pass/fail rules) | `codex-execution-quality-gate/references/gate-policy.md` | Edit thresholds and blocking rules |
| Workflow templates | `codex-workflow-autopilot/references/workflow-*.md` | Edit step sequences and exit criteria |
| Starter templates | `codex-*/starters/` | Add project-specific boilerplate |
| Feedback categories | `codex-domain-specialist/SKILL.md` (line 39-72) | Add new feedback→reference mappings |

---

## Validation

```bash
# Full test suite
python -m pytest tests -v

# Smoke test (SKILL.md presence, script imports, ref counts)
python tests/smoke_test.py --verbose

# Doctor check (runtime health)
python codex-execution-quality-gate/scripts/doctor.py --skills-root . --format table
```

---

## File Structure

```
skills/
├── VERSION                              ← 12.5.0
├── CHANGELOG.md                         ← v1.0 → v12.5.0 history
├── README.md                            ← This file
├── pytest.ini
├── requirements.txt
├── tests/
│   ├── conftest.py
│   ├── smoke_test.py                    ← 47 CLI and structural checks
│   ├── test_output_rigor.py             ← 10 output rigor / reasoning tests
│   ├── test_parsing.py                  ← 41 unit tests
│   └── test_scrum_subagents.py          ← 28 scrum installer/validator tests
│
├── codex-master-instructions/
│   ├── SKILL.md                         ← 18.8 KB, always loaded
│   ├── agents/openai.yaml
│   └── references/ (3)
│
├── codex-intent-context-analyzer/
│   ├── SKILL.md                         ← 3.6 KB, always loaded
│   └── agents/
│
├── codex-context-engine/
│   └── SKILL.md                         ← 3.2 KB, always loaded
│
├── codex-plan-writer/
│   ├── SKILL.md                         ← 2.7 KB
│   └── agents/
│
├── codex-workflow-autopilot/
│   ├── SKILL.md                         ← 7.4 KB
│   ├── scripts/explain_code.py
│   ├── references/ (10)
│   └── agents/
│
├── codex-reasoning-rigor/
│   ├── SKILL.md                         ← Anti-generic reasoning protocol
│   ├── scripts/build_reasoning_brief.py
│   ├── references/ (4)
│   ├── assets/ (3)
│   └── agents/
│
├── codex-domain-specialist/
│   ├── SKILL.md                         ← 22.5 KB, routing logic
│   ├── references/ (66)
│   ├── starters/ (19)
│   └── agents/
│
├── codex-security-specialist/
│   ├── SKILL.md                         ← 11.4 KB, security routing
│   ├── references/ (30)
│   └── starters/ (10)
│
├── codex-execution-quality-gate/
│   ├── SKILL.md                         ← 10.1 KB
│   ├── scripts/ (16 + helper)           ← includes output_guard.py and run_gate.py
│   ├── references/ (15)
│   └── agents/
│
├── codex-project-memory/
│   ├── SKILL.md                         ← 14.9 KB
│   ├── scripts/ (11)
│   ├── references/ (10)
│   └── agents/
│
├── codex-docs-change-sync/
│   ├── SKILL.md                         ← 1.9 KB
│   ├── scripts/map_changes_to_docs.py
│   ├── references/ (2)
│   └── agents/
│
├── codex-git-autopilot/
│   ├── SKILL.md                         ← 2.0 KB
│   └── scripts/auto_commit.py
│
├── codex-doc-renderer/
│   ├── SKILL.md                         ← 3.2 KB
│   ├── scripts/
│   ├── assets/
│   └── agents/
│
└── codex-scrum-subagents/
    ├── SKILL.md                         ← Scrum subagent routing + native Codex agent install
    ├── scripts/install_scrum_subagents.py
    ├── scripts/validate_scrum_agent_kit.py
    ├── scripts/generate_scrum_artifact.py
    ├── scripts/run_scrum_alias.py
    ├── scripts/_scrum_agent_kit.py
    ├── references/ (6)
    ├── assets/scrum-agent-kit/          ← 10 role briefs + 7 workflows + 3 manifests + 12 aliases
    └── assets/artifact-templates/       ← 6 repeatable Scrum artifacts
```

