---
name: prototype
trigger: $prototype
loads: [codex-runtime-hook, codex-spec-driven-development, codex-role-docs, codex-plan-writer, codex-workflow-autopilot, codex-execution-quality-gate]
---

# Workflow Alias: $prototype

## Trigger

Use for MVP, fullstack prototype, "from scratch", "build whole app", or multi-domain product build requests.

## Step Outline

1. Run `$hook` to detect domains, profile, context, role-doc, spec, and knowledge readiness.
2. If profile is missing, run `$init-profile` or create `.codex/profile.json`.
3. If context is missing, run `$genome`; if role docs are missing, run `$init-docs` with `--roles fullstack` (or the detected domain roles: `frontend,backend,devops,qa`).
4. Run `$spec` and create `.codex/specs/<slug>/SPEC.md` locking both functional requirements (`AC-###`) and **System Integration Contracts (`SILC-###`)** across FE ↔ BE ↔ Data ↔ Auth before implementation.
5. Run `$plan` and split work into dependency-ordered slices (`Schema/Contract -> Backend Producer -> Frontend Consumer -> E2E Seam Verification`) with explicit acceptance and SILC seam criteria.
6. For substantial UI, run `codex-frontend-design` (`/codex-frontend` / `$design`) to lock the UX contract and visual direction before frontend implementation; skip that chain for backend-only slices.
7. Execute with `$sdd` for independent tasks or inline for tightly coupled tasks, using TDD (`$tdd`) and verifying each SILC producer/consumer seam before advancing.
8. Execute Memory Write-Back: update `SPEC.md` traceability (`check_spec.py`), update touched role docs (`update_role_docs.py`), rebuild knowledge index (`build_knowledge_index.py`), and run `$check-full`.

## Exit Criteria

- Spec exists and maps the prototype requirements to acceptance criteria.
- Role docs capture FE/BE/data/QA decisions touched by the prototype.
- Prototype path works end to end in the existing repo.
- Working means the app boots locally, the main user path runs, FE can call BE when fullstack, at least one focused test or smoke check passes, and run commands are captured for handoff.
- Full gate passes or remaining advisory warnings are explicitly listed.
