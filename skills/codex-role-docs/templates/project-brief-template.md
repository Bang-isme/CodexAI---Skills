# Project Brief & Living Source of Truth: {{project_name}}

Generated: {{generated_at}}
Owner: planner
Stage: Stage 0: From-Scratch Bootstrap
Population: stub

## Lifecycle Stages (From-Scratch to Production-Ready)

Track the project's maturity progression across these 5 stages:
- [x] `Stage 0: From-Scratch Bootstrap` — Project brief, profile, and initial role docs initialized
- [ ] `Stage 1: Architecture & SILC Contract Lock` — `SPEC.md` (`AC-###`, `SILC-001`, `SILC-002`, `SEC-001`) and `DESIGN.md` / Frontend Blueprint locked
- [ ] `Stage 2: MVP Implementation` — Core FE/BE/Data slices implemented with TDD and verified across `SILC-###` seams
- [ ] `Stage 3: Production-Ready Hardening` — Security scan, accessibility/visual gate, observability, and rollback runbook verified
- [ ] `Stage 4: Maintenance & Handoff` — Role docs populated (`locked`/`production`), `shortcut:` ledger audited, and `.codex/handoff.md` exported

## Purpose

Describe the product goal, target users, and the measurable outcome this codebase delivers.

## Current Scope

- In scope: Not recorded
- Out of scope: Not recorded

## System Map & Stack Lock

| Layer | Technology / Stack | Entrypoint / Key Path | Linked Contract |
| --- | --- | --- | --- |
| Frontend | Not recorded | Not recorded | `DESIGN.md`, `SILC-001` |
| Backend | Not recorded | Not recorded | `SILC-001`, `SILC-002` |
| Data / Persistence | Not recorded | Not recorded | `SILC-002` |
| Runtime / Deployment | Not recorded | Not recorded | `DO-03-deployment-runbook.md` |

## Normative Contracts & Traceability Index

- Active Spec(s): `.codex/specs/<slug>/SPEC.md`
- Visual Identity Contract: `DESIGN.md` / `.codex/design/PRODUCT.md`
- Architecture Decisions: `.codex/decisions/` and `.codex/project-docs/decisions/`
- Active `AC-###` / `SILC-###` / `SEC-###` IDs: Not recorded

## Production-Readiness Gate Checklist

- [ ] Application boots cleanly with fail-fast environment validation (`env-config`)
- [ ] Database migrations follow Expand-and-Contract and have a verified rollback path (`BE-02`, `DO-07`)
- [ ] `/health/live` and `/health/ready` probes are separated and verified (`DO-03`, `DO-04`)
- [ ] All `SILC-001` (FE ↔ BE) and `SILC-002` (BE ↔ DB) contracts have automated integration tests (`QA-00`)
- [ ] Security scan (`security_scan.py`) and full quality gate (`auto_gate.py --mode full`) pass

## Key Decisions

- Not recorded

## Active Risks & Shortcut Debt

- Not recorded

## Role Docs

Run `build_role_docs_index.py` to refresh `.codex/project-docs/index.json`.

## Update Log

- {{date}}: Initialized project role documentation (`Stage 0: From-Scratch Bootstrap`).
