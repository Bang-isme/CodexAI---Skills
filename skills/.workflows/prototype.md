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
3. If context is missing, run `$genome`; if role docs are missing, run `$init-docs`.
4. Run `$spec` and create `.codex/specs/<slug>/SPEC.md` before implementation.
5. Run `$plan` and split work into FE/BE/data/QA/DevOps slices with acceptance criteria.
6. Execute with `$sdd` for independent tasks or inline for tightly coupled tasks, using TDD.
7. Update role docs, rebuild knowledge index, and run `$check-full`.

## Exit Criteria

- Spec exists and maps the prototype requirements to acceptance criteria.
- Role docs capture FE/BE/data/QA decisions touched by the prototype.
- Prototype path works end to end in the existing repo.
- Working means the app boots locally, the main user path runs, FE can call BE when fullstack, at least one focused test or smoke check passes, and run commands are captured for handoff.
- Full gate passes or remaining advisory warnings are explicitly listed.
