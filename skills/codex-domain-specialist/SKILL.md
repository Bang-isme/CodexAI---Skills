---
name: codex-domain-specialist
description: Use when frontend, backend, mobile, data, DevOps, or security work needs domain routing and at most four focused references.
load_priority: on-demand
version: "18.0.0"
---

## TL;DR
Detect the primary domain, load at most 4 references from `references/INDEX.md`, and stay inside that domain. Frontend UI goes to `codex-frontend-implementation`. Do not announce this skill at start. Quality gates are loaded by the gate skills, not here.

# Domain Specialist

## Activation
- Domain-specific file edits or explicit `$codex-domain-specialist`.
- Check `.codex/profile.json` first (`references/project-profile-spec.md`). If missing, use detection in `references/INDEX.md`.

## Load budget
1. Max 4 references on the first pass. Declare `Loading:` and `Skipping:`.
2. Frontend/UI/React/Next/CSS/GSAP: load `codex-frontend-implementation`, not local frontend catalogs.
3. `references/output-quality-gates.md` is owned by `codex-execution-quality-gate` / `codex-visual-quality-gate`. Do not bulk-load it here.

## Routing
Use `references/INDEX.md` for the decision table, signal maps, combos, and starters. Compact detection:

| Signal | Domain |
| --- | --- |
| `.tsx` / components / styling | Frontend → implementation skill |
| `routes/`, `services/`, `api/` | Backend API |
| schema, migration, query | Database |
| auth, secrets, attack surface | Security |
| Docker, CI/CD, deploy | DevOps |
| prompt, RAG, embeddings | AI/LLM |

## Scope-fit enforcement
Prefer the smallest change that satisfies the task, tests, and existing project patterns.
Do not add a new dependency, service, worker, cache, queue, design system, or abstraction unless repo evidence shows the simpler path fails.
If adding complexity, state: `Why simpler option fails`, `What this complexity buys`, and `How we will verify it`.

## Tool-Aware Routing Overlay
Use this overlay after domain detection. It does not replace `references/INDEX.md`.

### Tool selection matrix
| Task Signal | Tool Action | Evidence To Record |
| --- | --- | --- |
| Unknown repo structure | Targeted `rg` and focused reads | Files inspected and why they matter |
| Helper script involved | Run `--help` first | CLI contract and limits |
| Auth, secrets, upload, deploy | Apply the Security overlay | Attacker-controlled input and closest control |

Rules:
1. Record explicit tool evidence when it affects the decision.
2. Pick the smallest tool that proves the routing decision.
3. Tool usage does not require full compliance unless the task or repo evidence calls for it.

### Security overlay
Apply when attacker-controlled input, secrets, auth, public APIs, uploads, or trust boundaries change. Name the closest existing control and choose proportional defenses.

### Implementation ticket trigger
Create tickets when more than one AC, domain, or phase is involved. Include `TICKET-###`, owner, linked AC, likely files, dependencies, security notes, and a validation check.

## Operating rules
Never bulk-load all references. Keep solutions project-specific. Frontend craft lives in `codex-frontend-implementation/craft/`.
