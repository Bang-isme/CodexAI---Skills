---
name: codex-spec-driven-development
description: Use for prototype, MVP, fullstack feature, from-scratch feature, or multi-domain work that needs a SPEC.md with SDLC + SILC contracts before planning or implementation. Do not use for tiny one-file edits.
load_priority: on-demand
---

## TL;DR
Use before `$prototype`, MVP, fullstack, or high-ambiguity feature work. Write `.codex/specs/<slug>/SPEC.md` first to lock both **SDLC requirements (`AC-###`)** and **SILC System Integration Contracts (`SILC-###`)** across FE ↔ BE ↔ Data ↔ Auth/Infra, then plan, implement with TDD + seam verification, and validate against traceability.

## Activation
1. Activate on `$spec`, `$prototype`, "spec-driven", "MVP", "fullstack prototype", "from scratch", or "build whole app".
2. Activate when a task spans frontend + backend, data, QA, or deployment concerns.
3. Activate when requirements or cross-module integration seams are ambiguous enough that coding first would create rework.

## Hard Rules (SDLC + SILC Discipline)
- Do not implement prototype/fullstack/multi-domain work before `.codex/specs/<slug>/SPEC.md` exists.
- Specs are **Tier 3 (L2) Normative Contracts** in the Unified Memory Architecture (`../codex-project-memory/references/unified-memory-architecture.md`).
- Every spec must include:
  1. **Requirements & Non-Goals**
  2. **System Integration Contracts (`SILC-001`, `SILC-002`, ...)** locking producer/consumer seams:
     - **FE ↔ BE Seam:** Exact endpoint route/method, request payload, response DTO shape, HTTP status codes, and deterministic error envelope (`code`, `message`, `fieldErrors`).
     - **BE ↔ Data/Runtime Seam:** Schema/table changes, constraints, indexes, idempotency/transaction boundaries, and required environment variables.
     - **UI State ↔ Async Seam:** How `loading`, `empty`, `error`, `success`, and `retry` states map to the API contract.
  3. **Acceptance Criteria (`AC-001`, ...)** and **Security Criteria (`SEC-001`, ...)**
  4. **Implementation Tickets (`TICKET-001`, ...)** linking `AC-###` and `SILC-###` to owned files and validation commands
  5. **Traceability Table** mapping changed files to `AC-###` / `SILC-###` IDs and verification commands
- Keep specs project-local under `.codex/specs/`; load only the active spec for the current feature.
- Run `check_spec.py` after code changes when `.codex/specs/` exists.

## Commands

```bash
python "<SKILLS_ROOT>/codex-spec-driven-development/scripts/init_spec.py" --project-root <path> --title "<title>"
python "<SKILLS_ROOT>/codex-spec-driven-development/scripts/check_spec.py" --project-root <path> --changed-files <csv>
```

## Output Contract
- `init_spec.py` returns JSON with `status`, `spec_path`, and `slug`.
- `check_spec.py` returns JSON with `schema_version`, `overall`, `matched_specs`, `matched_acceptance_criteria`, `matched_silc_contracts`, `matched_implementation_tickets`, `unmapped_files`, and `suggested_actions`.

## End-to-End SDLC + SILC Prototype Flow
1. **Preflight & Memory Boot (`$hook`):** Detect domains, profile (`.codex/profile.json`), genome (`.codex/context/genome.md`), and role docs (`.codex/project-docs/`).
2. **Contract Specification (`$spec`):** Lock `AC-###`, `SILC-###` integration seams, and `SEC-###` in `.codex/specs/<slug>/SPEC.md`.
3. **Architecture & Task Planning (`$plan`):** Break work into dependency-ordered slices (`DB/Contract -> Backend API -> Frontend UI -> E2E Seam Verification`).
4. **Execution & SILC Seam Verification (`$sdd` or inline `$tdd`):** Implement each slice with Red-Green-Refactor AND verify the producer/consumer seam before moving to the next layer.
5. **Memory Write-Back & Full Gate (`$check-full`):** Update `SPEC.md` traceability, update touched role docs, rebuild `.codex/knowledge/INDEX.md`, and run `auto_gate.py --mode full`.

## Reference Files
- `references/spec.schema.json`: required spec markdown contract, `SILC-###` integration contract fields, and traceability schema.
