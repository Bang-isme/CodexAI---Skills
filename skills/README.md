# CodexAI Skill Pack — Technical Internals

> This document covers the runtime contents of `skills/`. For public overview, see [../README.md](../README.md). For Vietnamese guide, see [../docs/huong-dan-vi.md](../docs/huong-dan-vi.md).

## Current State

| Metric | Value |
| --- | --- |
| Version | `10.5.2` |
| Skills | 12 |
| Scripts | 30 + 1 shared module (`_js_parser.py`) |
| References | 127 |
| Starters | 29 |
| Pytest | 39/39 |
| Smoke | 32/32 |

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
- Task breakdown (domain, priority, dependencies, verify method, rollback)
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
| References | 9 (3 mode specs + 6 workflow templates) |

### 6. `codex-domain-specialist` — Full-Stack Knowledge

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
- 12 primary domains in detection table
- 45+ signal entries across 9 categories
- 10 common combo patterns (e.g. "Build new CRUD page" → 4 specific refs)
- 5 conflict resolution rules
- 30 feedback-driven supplemental loading categories
- 19 starter auto-routing patterns

**Starters:** 19 production-ready templates (Express API, React CRUD, Docker Compose, auth flow, etc.)

### 7. `codex-security-specialist` — Security Knowledge

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

### 8. `codex-execution-quality-gate` — Verification

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
| P6 | `quality_trend.py` | ℹ️ Advisory |
| P7 | `ux_audit.py` | ⚠️ Warning |
| P8 | `accessibility_check.py` | ⚠️ Warning |
| P9 | `lighthouse_audit.py` | ⚠️ Warning |
| — | `playwright_runner.py` | E2E helper |
| — | `with_server.py` | Server lifecycle |
| — | `doctor.py` | Installation health |
| — | `_js_parser.py` | Shared JS parser |

### 9. `codex-project-memory` — Knowledge Persistence

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

### 10. `codex-docs-change-sync` — Docs Impact Mapping

**Lazy.** Maps code diffs to potentially impacted documentation. Report-only by default.

### 11. `codex-git-autopilot` — Guarded Commits

**On-demand.** Pipeline: collect → stage → gate → message → sign → push.

Safety: **never** commits if gate fails, **never** force pushes, falls back to unsigned if GPG unavailable.

### 12. `codex-doc-renderer` — DOCX Rendering

**Lazy.** DOCX → PDF → PNG pipeline for visual document review.

---

## All Commands Reference

| Command | Skill | Action |
| --- | --- | --- |
| `$codex-intent-context-analyzer` | intent-context-analyzer | Parse request to intent JSON |
| `$codex-workflow-autopilot` | workflow-autopilot | Route to workflow + mode |
| `$codex-plan-writer` | plan-writer | Create implementation plan |
| `$codex-execution-quality-gate` | execution-quality-gate | Run verification suite |
| `$codex-doctor` | execution-quality-gate | Health check installation |
| `$setup-check` | execution-quality-gate | Verify dependencies |
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
├── VERSION                              ← 10.5.2
├── CHANGELOG.md                         ← v1.0 → v10.5.2 history
├── README.md                            ← This file
├── pytest.ini
├── requirements.txt
├── tests/
│   ├── conftest.py
│   ├── smoke_test.py                    ← 32 structural checks
│   └── test_parsing.py                  ← 39 unit tests
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
│   ├── references/ (9)
│   └── agents/
│
├── codex-domain-specialist/
│   ├── SKILL.md                         ← 22.5 KB, routing logic
│   ├── references/ (59)
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
│   ├── scripts/ (16)
│   ├── references/ (14)
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
└── codex-doc-renderer/
    ├── SKILL.md                         ← 3.2 KB
    ├── scripts/
    ├── assets/
    └── agents/
```
