# Unified Project Memory Architecture (4-Tier SSOT)

This specification defines how `codex-context-engine`, `codex-project-memory`, `codex-role-docs`, `codex-spec-driven-development`, and `codex-project-pulse` operate as one coherent memory system across long, multi-session engineering lifecycles.

---

## 1. The 4-Tier Memory Hierarchy (Read Order & Token Budget)

To prevent context-window bloat and conflicting instructions during long-horizon work, load project memory in this exact 4-tier order:

| Tier | Layer Name | Canonical Artifacts | Owning Skill | Load Policy & Budget |
| --- | --- | --- | --- | --- |
| **Tier 1 (L0)** | **Routing & Active Execution State** | `.codex/profile.json`, `.codex/pulse/sprint-state.json`, latest `.codex/sessions/*.md` | `codex-runtime-hook`, `codex-project-pulse`, `codex-project-memory` | **Always inspect first** when present (~500–1,000 tokens). Identifies primary domain, active story/spec, pending ACs, and exact resume point. |
| **Tier 2 (L1)** | **Macro Architecture & Tacit Index** | `.codex/context/genome.md`, `.codex/knowledge/INDEX.md` (`index.json`) | `codex-context-engine`, `codex-project-memory` | **Load at session start** for repo orientation (~1,500–2,500 tokens). Provides directory map, entrypoints, tacit conventions, risk hotspots, and verification commands. |
| **Tier 3 (L2)** | **Normative Contracts & Decisions** | `.codex/specs/<slug>/SPEC.md`, `DESIGN.md`, `.codex/design/surfaces/<slug>.md`, `.codex/decisions/*.md` | `codex-spec-driven-development`, `codex-design-md`, `codex-frontend-design`, `codex-project-memory` | **Load for the active feature/surface** (~1,000–2,500 tokens). Locks `AC-###`, `SILC-###` integration seams, `SEC-###`, visual tokens, and prior ADRs. |
| **Tier 4 (L3)** | **Role Micro-Context** | `.codex/project-docs/{frontend,backend,devops,qa,admin}/*.md`, `.codex/context/modules/*.md` | `codex-role-docs`, `codex-context-engine` | **Load on-demand for the active specialist role only** (max 2–3 files per task). Never bulk-load all roles. |

---

## 2. Single Source of Truth (SSOT) & Conflict Precedence

When two artifacts appear to disagree, resolve conflicts using this strict authority chain (highest to lowest):

1. **Verified Repository Code & Passing Tests** (ground truth of current runtime behavior).
2. **Active Normative Contracts (Tier 3):** Approved `.codex/specs/<slug>/SPEC.md`, `DESIGN.md`, `.codex/design/surfaces/<slug>.md`, and `.codex/decisions/*.md`.
3. **Human-Curated Role Docs (Tier 4):** `.codex/project-docs/<role>/*.md` and `.codex/profile.json`.
4. **Generated Synthesis Artifacts (Tier 2):** `.codex/knowledge/INDEX.md`, `.codex/context/genome.md`, and `.codex/handoff.md`.

**Hard Rule:** Never treat a generated Tier 2 summary (`genome.md` or `INDEX.md`) as overriding an explicit Tier 3 contract (`SPEC.md` or `DESIGN.md`). If Tier 2 is stale relative to git HEAD or the file tree (`memory_status.py` reports a staleness warning), regenerate Tier 2 with `generate_genome.py` or `build_knowledge_index.py`.

---

## 3. Deterministic Write-Back Protocol (Before Handoff or Completion)

Every non-trivial workflow (`$create`, `$prototype`, `$debug`, `$refactor`, `$deploy`, `$handoff`) must synchronize memory before claiming completion:

| Trigger Event in Workflow | Required Write-Back Action | Target Artifact |
| --- | --- | --- |
| New architectural, schema, API, or library tradeoff chosen | Run `decision_logger.py` | `.codex/decisions/YYYY-MM-DD-<slug>.md` |
| Feature slice implemented or contract changed | Update `SPEC.md` Traceability & SILC Seam status; run `check_spec.py` | `.codex/specs/<slug>/SPEC.md` |
| Frontend, Backend, DevOps, QA, or Security boundary modified | Run `update_role_docs.py` for the active role + `build_role_docs_index.py` | `.codex/project-docs/<role>/*.md` |
| Modules, entrypoints, dependencies, or configs added/removed | Run `generate_genome.py` and `build_knowledge_index.py`, then verify with `memory_status.py` | `.codex/context/genome.md`, `.codex/knowledge/INDEX.md` |
| Sprint story status, blocker, or priority changed | Update `.codex/pulse/` state files | `.codex/pulse/sprint-state.json`, `blockers.json` |
| Pausing multi-step work, compacting context, or ending session | Run `generate_session_summary.py`, fill all task-state & SILC seam fields, and run `generate_handoff.py` if transferring across sessions/tools | `.codex/sessions/*.md`, `.codex/handoff.md` |

---

## 4. Long-Horizon Continuity Contract (Zero Context Drift)

When an execution spans multiple sessions or subagents:

1. **Before pausing or handing off:** Never leave a raw Git snapshot with bracketed placeholders (`[Fill from the user request]`). Complete the checkpoint with:
   - **Active Spec & Plan Path:** e.g., `.codex/specs/2026-10-23-checkout/SPEC.md` and `./checkout-plan.md`
   - **Completed vs Pending Acceptance Criteria:** e.g., `Completed: AC-001, SILC-001 | Pending: AC-002, SILC-002`
   - **Integration Seam Status (SILC):** Which FE ↔ BE ↔ DB contracts are verified and which remain mocked or unverified
   - **Verified Commands:** Exact commands executed and their pass/fail output
   - **Exact Next Step:** The specific file, test, and ticket (`TICKET-###`) the next session must execute first
2. **When resuming a session:**
   - Read the latest completed checkpoint in `.codex/sessions/` matching the current branch and goal.
   - Verify `git status --short` and `HEAD` against the checkpoint's recorded `HEAD`.
   - Load only the active Tier 3 spec/plan and Tier 4 role doc required for the next ticket—do not re-interview the user on decisions already logged in `.codex/decisions/`.
