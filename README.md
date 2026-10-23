<img width="1536" height="1024" alt="CodexAI Skill Pack cover" src="https://github.com/user-attachments/assets/88afea81-e3a8-47ef-82f2-9dd7845f8cb4" />

# CodexAI Skill Pack

> A 100% proprietary, production-grade AI agent engineering system with native host integrations for **Codex**, **Claude Code**, **Cursor**, and **Antigravity**: 7-Stage SDLC + SILC closed-loop workflows, 4-Tier Unified Project Memory, `/codex-frontend` anti-slop UI/UX engineering, 6-Rung Precision Mode, 10 Specialist Agent Playbooks, and deterministic verification gates.

[![Version](https://img.shields.io/badge/version-18.1.0-blue)](skills/VERSION) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

**CodexAI Skill Pack** transforms a general-purpose coding agent into a disciplined, context-aware software engineering system. Instead of relying on prompt luck or producing generic "AI slop", the pack guides the model through a repeatable **7-Stage SDLC + SILC Closed-Loop Pipeline** whenever the task calls for it:

```text
Stage 1: Preflight & 4-Tier Memory Read ($hook -> L0 State -> L1 Genome/Index -> L2 Specs/DESIGN.md -> L3 Role Docs)
  -> Stage 2: Intent & Boundary Classification ($intent / $think)
  -> Stage 3: Normative Contract Lock ($spec for AC-### + SILC-### Seams | /codex-frontend for 7-Point UI Blueprint)
  -> Stage 4: Dependency & Seam-Ordered Planning ($plan: Schema/Contract -> Producer -> Consumer -> E2E Seam Test)
  -> Stage 5: 6-Rung Precision + TDD + SILC Seam Execution ($create / $tdd / $sdd / $root-cause)
  -> Stage 6: Multi-Gate Verification ($check / $check-full / $check-deploy / $visual-gate / safety_selftest)
  -> Stage 7: Deterministic Memory Write-Back ($role-docs / $knowledge / $handoff / $commit)
```

The pack is **100% proprietary to CodexAI**—with zero third-party skill clones and zero external CLI dependencies required for core operation—and is engineered for four outcomes:

1. **Zero AI UI/UX Slop & Gimmicks:** Enforces a mandatory 7-Point Frontend Design Blueprint, Spatial Layout Mathematics, perceptual OKLCH color tokens, a 6-State Interactive Matrix, numeric motion bands, and a 12-Point Anti-Slop Rejection Matrix via `/codex-frontend`.
2. **Rock-Solid Cross-Domain Integration (SDLC + SILC):** Locks **System Integration Contracts (`SILC-001` FE ↔ BE, `SILC-002` BE ↔ DB/Infra)** before coding so Frontend, Backend, Database, and DevOps slices never drift apart.
3. **Long-Horizon Memory & Living Source of Truth (SSOT):** Tracks projects from **Stage 0 (`From-Scratch Bootstrap`)** through **Stage 4 (`Maintenance & Handoff`)** across a 4-Tier Memory Architecture so context is never lost across long sessions.
4. **Executable Verification Over Vague Claims:** Replaces "should work" claims with 266+ automated unit/edge-case tests, a 12-pair executable `safety_selftest.py`, a 4-Part Review Finding Contract (`finding_contract.py`), and deterministic quality gates (`auto_gate.py`).

Full installation details per host are in [docs/INSTALL.md](docs/INSTALL.md), the Vietnamese guide is in [docs/huong-dan-vi.md](docs/huong-dan-vi.md), and version history is in [skills/CHANGELOG.md](skills/CHANGELOG.md).

---

## Why This Pack Is Different

| Weakness in Default AI Coding | What CodexAI Skill Pack Enforces |
| --- | --- |
| **Jumps straight into generic UI code ("AI slop")** | `/codex-frontend` (`codex-frontend-design` + `codex-design-md`) locks a **7-Point Frontend Design Blueprint**, asymmetric layout ratios (`7:5`, `8:4`, Split Workbench), OKLCH tokens, a 6-State Matrix, and rejects 12 AI slop/gimmick patterns before any `.tsx/.css` is written |
| **FE and BE code drift apart on DTOs, status codes, or errors** | `codex-spec-driven-development` locks **`SILC-001` (FE ↔ BE)** and **`SILC-002` (BE ↔ DB/Infra)** contracts with RFC 9457 `fieldErrors`, `Idempotency-Key`, and keyset cursor pagination before `$plan` and implementation |
| **Over-engineered code or missed callers during bug fixes** | `codex-reasoning-rigor` enforces the **6-Rung Smallest-Complete-Change Decision Ladder**, the **Caller-Grep Rule** (grep every caller before changing a shared function), a sanitized `< 2000` char **Reuse Map** (`reuse_map.py`), and the **Never-Cut List** |
| **Vague code reviews with hypothetical worries** | `$review` and `finding_contract.py` enforce the **4-Part Finding Contract**: every finding requires a **concrete failing input/case**, `file:line`, smallest fix, impact if skipped, continuous numbering across `Must-Fix / Should-Fix / Nice-to-Have`, and respects documented `# shortcut: <ceiling>, <when to upgrade>` comments |
| **Context lost or contradicted across multi-day projects** | **4-Tier Unified Project Memory** (`L0 Active State -> L1 Genome/Knowledge Index -> L2 Normative Specs/DESIGN.md/ADRs -> L3 Role Docs`) with strict SSOT conflict precedence and automatic Write-Back |
| **No living documentation when starting from scratch** | `codex-role-docs` (`$init-docs --roles fullstack`) scaffolds domain-specific matrices for FE, BE, DevOps, QA, and Admin, tracks maturity from `Stage 0` to `Stage 4`, detects unpopulated `stub` docs, and exports a complete `.codex/handoff.md` |
| **Claiming "done" without real verification** | `codex-execution-quality-gate` runs `auto_gate.py` (`quick`, `full`, `deploy`), `safety_selftest.py` (12 good/bad security & correctness pairs), `visual_quality_gate.py`, `verify_live_assets.py`, `output_guard.py`, and `editorial_review.py` |

---

## Practical Usage Guide: How To Use the Pack in Real Scenarios

### Scenario 1: Starting a Fullstack / MVP Project from Scratch (`$prototype`)

When building a new product, MVP, or multi-domain feature from scratch, invoke `$prototype`:

```text
$prototype Build a multi-tenant B2B subscription & invoicing workspace with React, Express/TypeScript, and PostgreSQL.
```

**What happens automatically:**
1. **Preflight & Profile (`$hook` + `$init-profile`):** Detects or initializes `.codex/profile.json`, active `precision_mode`, and the project `reuse_map`.
2. **Living Documentation Bootstrap (`$init-docs --roles fullstack`):** Creates `.codex/project-docs/PROJECT-BRIEF.md` (at `Stage 0: From-Scratch Bootstrap`) plus domain-specific role docs (`FE-00..07`, `BE-00..07`, `DO-00..07`, `QA-00..02`).
3. **SDLC + SILC Specification (`$spec`):** Creates `.codex/specs/<slug>/SPEC.md` locking functional `AC-###` criteria, `SILC-001` (API routes, Zod DTOs, RFC 9457 `fieldErrors`, cursor pagination), `SILC-002` (DB schema, integer cents, Expand-and-Contract migration), and `SEC-001`.
4. **Dependency-Ordered Plan (`$plan`):** Breaks work into verifiable tasks ordered strictly as `Schema/Contract -> Backend Producer -> Frontend Consumer -> E2E Seam Verification`.
5. **TDD & Seam Implementation (`$sdd` / `$tdd`):** Implements each slice with RED-GREEN-REFACTOR and verifies each `SILC-###` seam.
6. **Full Quality Gate & Write-Back (`$check-full`):** Updates Role Docs to `populated`, rebuilds `.codex/knowledge/INDEX.md`, and runs `auto_gate.py --mode full`.

---

### Scenario 2: Designing & Implementing Breakthrough UI Without AI Slop (`/codex-frontend`)

When creating or redesigning a web page, component, dashboard, landing page, or multi-screen flow, invoke `/codex-frontend` (or `$codex-frontend` / `$design` / `$ux`):

```text
/codex-frontend Design and implement an operational analytics workbench and 3-tier pricing page.
```

**What happens automatically:**
1. **Scope Selection:**
   - **Fast Path** (single page/component): Completes the **7-Point Frontend Design Blueprint** before writing code.
   - **Prototype Path** (multi-route flow): Writes `.codex/design/surfaces/<slug>.md` (with the 6-State Matrix mapped to `SILC-001` status/error codes) and `.codex/design/direction.md`.
   - **Studio Path** (`$direction` or explicit alternatives): Presents 3 structurally distinct directions, then locks the chosen contract in `DESIGN.md`.
2. **Spatial, Typographic, Color & Motion Discipline:**
   - **Layout Mathematics:** Uses purposeful asymmetric grids (`7:5`, `8:4`, `260px + minmax(0, 1fr)` workbench) with `min-width: 0` overflow protection across `320px–2560px`.
   - **Perceptual OKLCH & Tabular Rhythm:** Uses tinted OKLCH neutral surfaces (`--surface-canvas`, `--surface-1`, `--surface-2`), `|ΔL| >= 0.65` body contrast, and `font-variant-numeric: tabular-nums` on all numbers/prices/metrics.
   - **Numeric Motion & Scroll-State Math:** Enforces concrete timing bands (`120–220ms` control feedback, `180–320ms` popovers, `400–800ms` entrances), pure scroll progress `scrollY / (scrollHeight - innerHeight)`, `0.39` chapter flip threshold, `inert` on hidden chapters, and a **designed still frame** for `prefers-reduced-motion`.
   - **12-Point Anti-Slop Rejection:** Strips out 3-equal-card Bento soup, neon purple/cyan dark-mode clichés, icon-in-a-rounded-box above every heading, gradient text on metrics, custom cursor hijacking, forced `100vh` section clipping, and fabricated metrics/logos.
3. **Visual Quality Gate (`$visual-gate`):** Runs `visual_quality_gate.py`, `ux_audit.py`, and `accessibility_check.py` (plus Playwright responsive capture matrix when available; discloses `DEGRADED` honestly if browser capture is absent).

---

### Scenario 3: Feature Implementation, Bug Fixing & Refactoring (`$create`, `$debug`, `$refactor`)

- **Build a Feature (`$create`):**
  Loads 4-Tier Memory, runs `reuse_map.py` and `predict_impact.py`, walks the **6-Rung Precision Ladder** (`precision-ladder.md`), applies the **Caller-Grep Rule**, implements with TDD (`$tdd`), and verifies with `$check`.
- **Debug a Bug (`$debug` / `$root-cause`):**
  Enforces the 4-Phase Systematic Debugging Iron Law (`NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST`): traces data flow backward across `SILC-###` boundaries, greps every caller of the broken function, writes a failing reproduction test (`RED`), applies the minimal root-cause fix at the shared function (`GREEN`), and updates `QA-01-regression-map.md`.
- **Code Review & Audit (`$review`):**
  Runs `tech_debt_scan.py`, `shortcut_ledger.py`, and `security_scan.py`, then authors a review strictly following the **4-Part Finding Contract** (validated by `finding_contract.py`).

---

### Scenario 4: Session Checkpoints, Living Docs Maintenance & Handoff (`$handoff`, `$today`)

- **Check Daily Project Pulse (`$today` / `$pulse`):** Reads `.codex/pulse/` sprint state, priority queue, stale blockers, upcoming milestones, and recent git/quality signals to generate `.codex/pulse/daily-brief.md`.
- **Package a Complete Handoff (`$handoff`):**
  1. Logs architectural tradeoffs via `decision_logger.py`.
  2. Updates touched Role Docs via `update_role_docs.py` (advancing `Stage 0..4` and marking `Population: populated|locked|production`).
  3. Generates a Git & working-tree checkpoint via `generate_session_summary.py --since last-session`.
  4. Exports `.codex/handoff.md` via `generate_handoff.py`—automatically embedding Tech Stack, Key Files, **Living Source of Truth (Lifecycle Stage, Active `SPEC.md` `AC-###` & `SILC-###` status, `DESIGN.md`, UX Surfaces, Role Doc coverage, and Latest Session Checkpoint)**, Active Decisions, and Conventions.

---

## Public Pipeline

### Core Flow

1. `codex-master-instructions`
   Global operating rules, 4-Tier Memory hierarchy, 7-Stage SDLC + SILC pipeline, and evidence policy.
2. `codex-runtime-hook` + `codex-context-engine`
   One-command preflight (`runtime_hook.py`), active `precision_mode` resolution, `< 2000` char sanitized `reuse_map`, and macro project `genome.md`.
3. `codex-intent-context-analyzer` + `codex-logical-decision-layer`
   Structured intent JSON, confirmation policy gating, and 2–4 option tradeoff matrices (`$think`).
4. `codex-spec-driven-development` + `codex-plan-writer`
   Lock `SPEC.md` (`AC-###`, `SILC-001`, `SILC-002`, `SEC-001`) and decompose into bite-sized, dependency-ordered TDD tasks (`$plan`).
5. `codex-workflow-autopilot` + Specialist Agents (`.agents/*.md`)
   Route into `build`, `prototype`, `fix`, `debug`, `review`, `refactor`, `deploy`, `handoff`, or Scrum ceremonies with strict `file_ownership`.
6. Domain & Frontend Implementation (`codex-frontend-design`, `codex-frontend-implementation`, `codex-domain-specialist`, `codex-security-specialist`)
   Execute with the 6-Rung Precision Ladder, Caller-Grep Rule, and modern TypeScript/Python/SQL/OKLCH production patterns.
7. `codex-execution-quality-gate` + `codex-visual-quality-gate`
   Run `auto_gate.py`, `run_gate.py`, `safety_selftest.py`, `finding_contract.py`, `shortcut_ledger.py`, `visual_quality_gate.py`, `verify_live_assets.py`, `output_guard.py`, and `editorial_review.py`.
8. `codex-role-docs` + `codex-project-memory` + `codex-git-autopilot`
   Write back decisions, update role docs, rebuild `.codex/knowledge/INDEX.md`, export `.codex/handoff.md`, and commit safely.

---

## 4-Tier Unified Project Memory Architecture (SSOT)

To prevent context drift across long-running projects, the pack reads and writes project memory in a strict 4-tier order (`skills/codex-project-memory/references/unified-memory-architecture.md`):

| Tier | Layer Name | Canonical Artifacts | Authority & Role |
| --- | --- | --- | --- |
| **Tier 1 (L0)** | **Routing & Active Execution State** | `.codex/profile.json`, `.codex/precision.json`, `.codex/pulse/sprint-state.json`, latest `.codex/sessions/*.md` | **Inspect first (~500–1,000 tokens):** Identifies primary domain, precision level, active story/spec, pending ACs, and exact resume point. |
| **Tier 2 (L1)** | **Macro Architecture & Tacit Index** | `.codex/context/genome.md`, `.codex/knowledge/INDEX.md` (`index.json`, `knowledge-graph.json`), `reuse_map` | **Load at session start (~1,500–2,500 tokens):** Directory map, entrypoints, reusable helpers, tacit conventions, risk hotspots, and verification commands. |
| **Tier 3 (L2)** | **Normative Contracts & Decisions** | `.codex/specs/<slug>/SPEC.md`, `DESIGN.md`, `.codex/design/surfaces/<slug>.md`, `.codex/decisions/*.md` | **Highest Documentation Authority:** Locks `AC-###`, `SILC-###` integration seams, `SEC-###`, visual tokens, and Architecture Decision Records. |
| **Tier 4 (L3)** | **Role Micro-Context** | `.codex/project-docs/{frontend,backend,devops,qa,admin}/*.md`, `.codex/context/modules/*.md` | **Load on-demand for active role only:** Preserves specialist tables, runbooks, and test plans across `Stage 0` → `Stage 4`. |

**Conflict Precedence (Highest to Lowest):**
`Verified Repository Code & Passing Tests > Tier 3 Normative Contracts (SPEC.md / DESIGN.md / ADRs) > Tier 4 Human-Curated Role Docs > Tier 2 Generated Summaries`.

---

## Agent System (10 Deep Execution Playbooks)

When `codex-intent-context-analyzer` or `prompt_router.py` emits `suggested_agent`, `codex-master-instructions` loads `skills/.agents/<agent>.md`. Each agent persona is a full execution playbook with explicit `file_ownership`, 4-Tier Memory & SILC Seam checks, Non-Negotiable Engineering Standards, and a Pre-Handoff Verification Gate:

| Agent | Primary Domain & Ownership | Key Enforcement |
| --- | --- | --- |
| `design-lead` | `.codex/design/**/*`, `DESIGN.md` | Runs `/codex-frontend` (`fast`, `prototype`, `studio`), locks 7-Point Blueprint, Layout Mathematics, OKLCH tokens, and 6-State Matrix |
| `frontend-specialist` | `app/`, `src/`, `components/`, `pages/`, `styles/`, `FE-*` docs | Implements overflow-safe `minmax(0, 1fr)` layouts, `tabular-nums`, 6 interactive states, `SILC-001` `fieldErrors` binding, and WCAG AA |
| `visual-quality-reviewer` | `.codex/design/reviews/**/*` | Runs `visual_quality_gate.py`, `ux_audit.py`, `accessibility_check.py`, 7-viewport responsive capture review, and `narrative-runtime-qa.md` |
| `backend-specialist` | `api/`, `server/`, `services/`, `controllers/`, `routes/`, `db/`, `migrations/`, `BE-*` docs | Enforces Zod `.strict()` boundary parsing, DTO mapping, RFC 9457 error envelopes, `Idempotency-Key`, Transactional Outbox, and Expand-and-Contract migrations |
| `security-auditor` | `security/`, infra/CI configs, `BE-04`, `AD-01`, `AD-03`, `DO-05`, `DO-06` | Audits STRIDE trust boundaries, BOLA/IDOR tenant isolation, secret hygiene, and validates reviews with `finding_contract.py` |
| `debugger` | Implicated source paths + tests + `QA-01-regression-map.md` | Enforces 4-phase root-cause investigation, `reuse_map.py`, Caller-Grep Rule, and failing reproduction test (`$tdd`) before any fix |
| `test-engineer` | `tests/`, `__tests__/`, `e2e/`, test configs, `QA-*`, `FE-07`, `BE-07` | Enforces the Testing Trophy, real DB integration tests (no ORM mock chains), MSW v2 network boundary tests, and 5-Dimension Boundary Matrix |
| `devops-engineer` | `.github/workflows/`, `infra/`, `deploy/`, `Dockerfile*`, `docker-compose*`, `DO-*` docs | Enforces multi-stage non-root (`USER 10001`) containers, separate `/health/live` vs `/health/ready` probes, graceful `SIGTERM` drain, OpenTelemetry JSON logs, and `< 2 min` rollback runbooks |
| `planner` | `.codex/**/*`, `docs/**/*`, `*plan*.md`, `PROJECT-BRIEF.md`, `decisions/` | Authors `SPEC.md` (`AC-###` + `SILC-###`) and zero-placeholder, dependency-ordered implementation plans (`$plan`) |
| `scrum-master` | `.agent/**/*`, `.codex/agents/**/*`, `.codex/pulse/**/*`, ceremony artifacts | Facilitates Scrum ceremonies, enforces Definition of Ready (`AC` + `SILC` locked) and Definition of Done, and updates `.codex/pulse/` |

---

## Role Documentation System (From-Scratch to Production-Ready)

`codex-role-docs` creates durable project-local documentation under `.codex/project-docs/` so teams and agents have a trustworthy Single Source of Truth from initial bootstrap to final handoff:

```bash
# Minimal init (PROJECT-BRIEF.md + ADR template only)
python skills/codex-role-docs/scripts/init_role_docs.py --project-root .

# Fullstack preset (PROJECT-BRIEF + frontend, backend, devops, qa role docs with domain matrices)
python skills/codex-role-docs/scripts/init_role_docs.py --project-root . --roles fullstack

# Update a role doc with decisions, SILC contracts, verification evidence, and maturity stage
python skills/codex-role-docs/scripts/update_role_docs.py --project-root . --role backend --doc BE-01 \
  --summary "Locked POST /api/v1/orders contract" --files "src/routes/orders.ts" \
  --decision "Require Idempotency-Key UUID on order creation" \
  --contract "SILC-001: 201 Created + 422 fieldErrors" \
  --verification "npm test" --stage "Stage 2: MVP Implementation" --population populated

# Check coverage, stale docs, and unpopulated template stubs
python skills/codex-role-docs/scripts/check_role_docs.py --project-root . --changed-files "src/routes/orders.ts"

# Rebuild .codex/project-docs/index.json (tracks populated vs stub counts and project stage)
python skills/codex-role-docs/scripts/build_role_docs_index.py --project-root .
```

---

## Quick Aliases

| Alias | File / Target | Equivalent Workflow |
| --- | --- | --- |
| `/codex-frontend` / `$codex-frontend` / `$design` / `$ux` | `codex-frontend-design` | Lock 7-Point Frontend Design Blueprint + 12-Point Anti-Slop Gate (`fast`, `prototype`, or `studio`) |
| `$direction` | `codex-frontend-design` | Studio mode: 3 structurally distinct visual directions before build |
| `$refine` / `$polish` / `$critique` / `$audit-ui` | `skills/.workflows/refine.md` | Targeted UI refinement dial (`refinement-dials.md`) + `$visual-gate` |
| `$prototype` | `skills/.workflows/prototype.md` | `$hook -> $init-profile -> $genome -> $init-docs (--roles fullstack) -> $spec (AC + SILC) -> $plan -> TDD + Seam Verify -> $check-full` |
| `$spec` | `codex-spec-driven-development` | `init_spec.py` / `check_spec.py` (`AC-###`, `SILC-###`, `SEC-###`, `TICKET-###`) |
| `$plan` | `skills/.workflows/plan.md` | `$codex-plan-writer` + BMAD Phase 1–2 + SILC Seam Mapping |
| `$create` / `$build` | `skills/.workflows/create.md` | `workflow-create.md` + `reuse_map.py` + 6-Rung Precision Ladder + TDD |
| `$debug` / `$fix` / `$root-cause` | `skills/.workflows/debug.md` | 4-Phase Systematic Debugging + Caller-Grep Rule + Regression TDD |
| `$refactor` | `skills/.workflows/refactor.md` | `tech_debt_scan.py` + `shortcut_ledger.py` + `predict_impact.py` + incremental TDD |
| `$review` | `skills/.workflows/review.md` | 4-Part Finding Contract (`finding_contract.py`) + `shortcut_ledger.py` + `output_guard.py` + `editorial_review.py` |
| `$deploy` | `skills/.workflows/deploy.md` | `workflow-deploy.md` + `auto_gate.py --mode deploy` + `safety_selftest.py` + `verify_live_assets.py` |
| `$handoff` / `$docs` | `skills/.workflows/handoff.md` | 4-Tier Memory Write-Back + `generate_session_summary.py` + `generate_handoff.py` |
| `$check` / `$check-full` / `$check-deploy` | `codex-execution-quality-gate` | `auto_gate.py --mode quick|full|deploy` |
| `$today` / `$pulse` | `codex-project-pulse` | Sprint state, priority queue, blockers, milestones, and daily brief |
| `$pipeline` / `$release-gate` | `skills/.system/scripts/` | `pipeline.py --stage all` / `local_release_gate.py` |

---

## Skill Inventory (30 Canonical Skills)

### 1. Core Pipeline, Routing & Reasoning (11 Skills)

| Skill | What It Does |
| --- | --- |
| `codex-master-instructions` | P0 baseline rules, 4-Tier Memory hierarchy, 7-Stage SDLC + SILC flow, and completion discipline |
| `codex-runtime-hook` | One-command preflight (`runtime_hook.py`), profile initializer (`init_profile.py`), `precision_mode.py`, and `reuse_map.py` |
| `codex-intent-context-analyzer` | Structured intent JSON parser, agent router, confirmation policy, and Socratic gate |
| `codex-context-engine` | Multi-layer project context generator (`genome.md` and per-module maps) |
| `codex-logical-decision-layer` | Compact 2–4 option decision matrices (`build_decision_matrix.py`) with cost, risk, reversibility, and stop conditions |
| `codex-reasoning-rigor` | 6-Rung Precision Ladder (`precision-ladder.md`), Caller-Grep Rule, Never-Cut List, task contracts, and monitoring loops |
| `codex-spec-driven-development` | Normative `SPEC.md` authoring and traceability checker (`init_spec.py`, `check_spec.py`) with `AC-###`, `SILC-###`, and `SEC-###` |
| `codex-plan-writer` | Zero-placeholder, dependency-ordered implementation plans (`{task-slug}.md`) with TDD and SILC seam steps |
| `codex-workflow-autopilot` | Behavioral mode router (`implement`, `prototype`, `debug`, `review`, `thinking-partner`, `devils-advocate`, `teach`, `ship`) |
| `codex-subagent-execution` | Fresh subagent dispatch per task with two-stage review (`spec-reviewer` -> `code-quality-reviewer`) |
| `codex-scrum-subagents` | Project-local `.agent/` Scrum kit and native `.codex/agents/*.toml` custom agents for 10 Scrum/delivery roles |

### 2. Frontend, UI/UX, Backend, DevOps & Security Knowledge Packs (6 Skills)

| Skill | Coverage |
| --- | --- |
| `codex-frontend-design` | `/codex-frontend` (`fast`, `prototype`, `studio`), 7-Point Design Blueprint, Layout Mathematics, OKLCH color system, Optical Typography, 6-State Matrix, Numeric Motion/Scroll-State Math, Landing/Pricing Architecture, Originality Evidence Ladder, and 12-Point Anti-Slop Audit |
| `codex-frontend-implementation` | React, Next.js App Router, Tailwind, shadcn, GSAP/ScrollTrigger mastery, native `craft-recipes.md`, and canonical OKLCH `design-system.css` starter |
| `codex-design-md` | Native Python `DESIGN.md` contract engine (`design_contract.py`: `doctor`, `scaffold`, `lint`, `diff`, `export tailwind|dtcg`, `spec`) and `.codex/design/` surface scaffold (`design_context.py`) |
| `codex-visual-quality-gate` | Mechanical UI source & contract evaluators (`visual_quality_gate.py`), Playwright 7-viewport + `320px–2560px` responsive capture (`capture_responsive_matrix.mjs`), `anchored-craft-rubric.md`, and `narrative-runtime-qa.md` |
| `codex-domain-specialist` | 58 focused engineering references + 21 modernized production starters across Backend, REST/tRPC/GraphQL, Zod Validation, RFC 9457 Error Handling, PostgreSQL/Prisma/Mongoose/Sequelize, Expand-and-Contract Migrations, Singleflight Caching, Testing Trophy, OpenTelemetry, Docker, and Nginx |
| `codex-security-specialist` | 30 focused security references + 10 starters across OWASP Top 10, STRIDE Threat Modeling, Auth/RBAC/OAuth, API Security, Container/Linux/SSH Hardening, DevSecOps SAST/DAST/SCA, Supply Chain, and ISO 27001 / SOC 2 / GDPR |

### 3. Quality Gates, Engineering Discipline, Memory & Delivery (13 Skills)

| Skill | What It Adds |
| --- | --- |
| `codex-execution-quality-gate` | 21 verification scripts: `auto_gate.py`, `run_gate.py`, `security_scan.py`, `pre_commit_check.py`, `smart_test_selector.py`, `predict_impact.py`, `tech_debt_scan.py`, `shortcut_ledger.py`, `finding_contract.py`, `safety_selftest.py`, `verify_live_assets.py`, `output_guard.py`, `editorial_review.py`, `ux_audit.py`, `accessibility_check.py`, `lighthouse_audit.py`, `playwright_runner.py`, `bundle_check.py`, `quality_trend.py`, `install_hooks.py`, `install_ci_gate.py` |
| `codex-test-driven-development` | Iron Law RED-GREEN-REFACTOR enforcement (`$tdd`) and testing anti-patterns guard |
| `codex-systematic-debugging` | 4-Phase root-cause investigation (`$root-cause`), backward data-flow tracing, and 3-failure architectural circuit breaker |
| `codex-verification-discipline` | Iron Law evidence-before-claims behavioral constraint (`$verify`) |
| `codex-project-memory` | 4-Tier Unified Memory (`unified-memory-architecture.md`), `decision_logger.py`, `generate_session_summary.py`, `generate_handoff.py`, `build_knowledge_index.py`, `build_knowledge_graph.py`, `memory_status.py`, `generate_genome.py`, `generate_changelog.py`, `analyze_patterns.py`, `track_feedback.py`, `compact_context.py` |
| `codex-role-docs` | 5-Stage Lifecycle (`Stage 0..4`) & domain-specific role docs (`init_role_docs.py`, `update_role_docs.py`, `check_role_docs.py`, `build_role_docs_index.py`) |
| `codex-project-pulse` | Persistent sprint state, priority queue, blocker aging, risk register, milestones, and `$today` daily brief |
| `codex-docs-change-sync` | Git diff to documentation, `SPEC.md`, `DESIGN.md`, and Role Docs impact mapper (`map_changes_to_docs.py`) |
| `codex-document-writer` | Reader-first reports, proposals, postmortems, Mermaid diagrams, and natural UTF-8 Vietnamese technical writing |
| `codex-doc-renderer` | DOCX creation, visual layout inspection, and PDF/PNG rendering (`render_docx.py`) |
| `codex-git-worktrees` | Isolated `.worktrees/` workspace setup with gitignore safety check and baseline test verification (`$worktree`) |
| `codex-branch-finisher` | Structured 4-option branch completion (`merge`, `PR`, `keep`, `discard`) with worktree cleanup (`$finish`) |
| `codex-git-autopilot` | Gate-aware conventional commit and GPG signing automation (`auto_commit.py`) |

---

## Quick Start

1. **Install** for your host (`cursor`, `codex`, `claude`, or `antigravity`):

```powershell
python ".\skills\.system\scripts\install.py" --host cursor --scope user --apply --format text
```

2. **Verify** the installed host wiring:

```powershell
python ".\skills\.system\scripts\install.py" doctor --host cursor --scope user --format text
```

3. **Start using aliases** in your AI coding session:
   - `/codex-frontend` or `$design` — Design & implement high-craft UI with the 7-Point Blueprint
   - `$prototype` — Build a fullstack feature or MVP from scratch with `SPEC.md` (`AC-###` + `SILC-###`) and Role Docs
   - `$plan` — Create a dependency-ordered implementation plan
   - `$create` — Implement a feature with the 6-Rung Precision Ladder & TDD
   - `$debug` — Run 4-phase systematic root-cause debugging
   - `$review` — Run a 4-Part Finding Contract review
   - `$check-full` — Run the full execution quality gate
   - `$handoff` — Update living documentation and export `.codex/handoff.md`

Host-specific marketplace and local installation options are documented in [docs/INSTALL.md](docs/INSTALL.md).

### 1. Advanced Host Installation Commands

**Codex-native user or repo install:**

```powershell
python ".\skills\.system\scripts\install_codex_native.py" --source ".\skills" --scope user --apply --format text
python ".\skills\.system\scripts\install_codex_native.py" --source ".\skills" --scope repo --repo-root "." --apply --format text
```

**Claude Code user install or plugin mode:**

```powershell
python ".\skills\.system\scripts\install_claude_native.py" --source ".\skills" --scope user --apply --format text
python ".\skills\.system\scripts\validate_claude_plugin.py" --plugin-root "." --format text
claude --plugin-dir .
```

**Cursor native user or repo install:**

```powershell
python ".\skills\.system\scripts\install_cursor_native.py" --source ".\skills" --scope user --apply --format text
python ".\skills\.system\scripts\validate_cursor_plugin.py" --plugin-root "." --format text
```

**Antigravity native package candidate:**

```powershell
python ".\skills\.system\scripts\build_antigravity_plugin.py" --plugin-root "." --apply --format json
python ".\skills\.system\scripts\install_antigravity_native.py" --plugin-root "." --scope workspace --surface both --apply --format json
python ".\skills\.system\scripts\validate_antigravity_plugin.py" --package-dir ".\dist\antigravity-plugin" --format json
```

**Generic CLI/IDE trust harness:**

```powershell
python ".\skills\.system\scripts\trust_harness.py" --project-root "." --skills-root ".\skills" --setup generic --apply --evidence ".\.codexai\evidence\trust-harness.json" --format text
```

### 2. Local Quality Pipeline & Release Verification

```bash
# Run the unified pipeline (lint, contracts, test, build, doctor)
python skills/.system/scripts/pipeline.py --stage all --format text

# Run fast pre-commit lint + contract + 12-pair safety selftest
python skills/.system/scripts/pipeline.py --stage lint,contracts --format text

# Run full Python unittest suite (266 tests)
python -m unittest discover -s skills/tests -p "test_*.py"

# Run Node responsive capture tests
node --test skills/tests/responsive_capture_stitch.test.mjs skills/tests/responsive_capture_core.test.mjs skills/tests/responsive_capture_browser.test.mjs

# Run executable 12-pair good/bad safety selftest directly
python skills/codex-execution-quality-gate/scripts/safety_selftest.py --format text

# Run pre-tag release gate and build clean release ZIP
python skills/.system/scripts/local_release_gate.py --format text
python skills/.system/scripts/build_release_zip.py --project-root . --exclude-tests --apply --format text
```

### 3. Optional GitHub CLI

GitHub CLI (`gh`) is optional and only used for workflows that interact with GitHub (such as PR creation in `$finish`):

```bash
gh auth login
gh auth status
```

Never commit credentials or tokens into plugin manifests, skill docs, generated artifacts, or source files.

---

## Repository Layout

```text
CodexAI---Skills/
|-- README.md
|-- LICENSE
|-- AGENTS.md
|-- CLAUDE.md
|-- .cursor/rules/codexai-core.mdc
|-- .codex-plugin/plugin.json
|-- .claude-plugin/
|   |-- plugin.json
|   `-- marketplace.json
|-- .cursor-plugin/
|   |-- plugin.json
|   `-- marketplace.json
|-- .agents/plugins/marketplace.json
|-- antigravity/
|   |-- plugin.json
|   |-- hooks.json
|   |-- rules/codexai-core.md
|   `-- scripts/pre_tool_use.py
|-- hooks/hooks.json
|-- docs/
|   |-- INSTALL.md
|   |-- huong-dan-vi.md
|   `-- project-artifact-layout.md
`-- skills/
    |-- VERSION
    |-- CHANGELOG.md
    |-- README.md
    |-- pytest.ini
    |-- requirements.txt
    |-- .agents/                  # 10 Deep Specialist Agent Playbooks
    |-- .workflows/               # 12 Workflow Alias Definitions
    |-- .system/                  # Pack Registry, Manifest, Validators, Pipeline & Installers
    |   |-- OPERATION_RUNBOOK.md
    |   |-- REGISTRY.md
    |   |-- manifest.json
    |   `-- skill-capabilities.json
    |-- tests/                    # 266 Python Unit/Edge-Case Tests + 3 Node Test Suites
    `-- codex-*/                  # 30 Canonical CodexAI Skills
```

---

## What To Read Next

- Host installation guide: [docs/INSTALL.md](docs/INSTALL.md)
- Vietnamese usage guide: [docs/huong-dan-vi.md](docs/huong-dan-vi.md)
- Project artifact layout & 4-Tier Memory map: [docs/project-artifact-layout.md](docs/project-artifact-layout.md)
- Technical internals: [skills/README.md](skills/README.md)
- Operator runbook: [skills/.system/OPERATION_RUNBOOK.md](skills/.system/OPERATION_RUNBOOK.md)
- Version history: [skills/CHANGELOG.md](skills/CHANGELOG.md)

---

## License

MIT
