# Plugin Routing and Spec Framework Upgrade Design

## Goal
Upgrade the CodexAI Skill Pack so domain routing, tool usage, security reasoning, and spec output become more explicit, evidence-driven, and actionable without turning the pack into a heavyweight compliance system.

## Scope
This design targets the strong compatibility-preserving path. It changes skill contracts, spec template generation, schema expectations, spec checking, and tests. It does not introduce a new runtime service, external dependency, or agent orchestration engine.

## Architecture
The upgrade keeps the existing skill-pack structure:

- `codex-domain-specialist` remains the primary routing surface for domain-specific engineering work.
- `codex-security-specialist` remains the security reference pack, while spec-driven development receives a lightweight security layer inspired by Codex Security threat modeling.
- `codex-spec-driven-development` remains the spec-first workflow and owns `init_spec.py`, `check_spec.py`, and `spec.schema.json`.
- `codex-scrum-subagents` remains the source of Scrum-style ticket language, but spec tickets are generated inside SPEC.md rather than requiring a separate Scrum install.

## Domain Routing Design
`codex-domain-specialist/SKILL.md` will gain a Tool-Aware Routing Overlay. The overlay requires the agent to classify which tools are needed before implementation:

- File discovery and repo evidence: `rg`, `rg --files`, targeted file reads.
- Script-backed behavior: run helper scripts with `--help` first.
- Spec work: use `init_spec.py` and `check_spec.py` when a task is prototype, MVP, fullstack, multi-domain, or high ambiguity.
- Security work: load security references or Codex Security phases when the task changes trust boundaries, attacker-controlled input, auth, secrets, deployment exposure, or CI/package integrity.
- Ticket work: create implementation tickets when the spec spans multiple files, domains, acceptance criteria, or delivery roles.

The routing table will stay bounded. The first pass still avoids bulk-loading references, but it will explicitly explain when a tool, starter template, or security reference is chosen.

## Spec Framework Design
`init_spec.py` will render a longer SPEC.md with sections that help an AI gather evidence through tools before drafting decisions:

- Context Summary
- Evidence and Source Log
- Assumptions
- Constraints
- User Workflow
- Requirements
- Acceptance Criteria
- Implementation Tickets
- Domain Impact
- Security Model
- Tool Research Plan
- Validation Matrix
- Risk Matrix
- Open Questions
- Traceability

The template will avoid empty placeholders such as "TBD". It will use concrete prompts that tell the agent what evidence to collect and how to record it. This makes the spec longer by default while keeping the fields practical.

## Multi-Ticket Design
Specs will support `TICKET-001` style implementation tickets. Each ticket will include:

- title
- domain or owner
- linked acceptance criteria
- intent
- likely files or areas
- dependencies
- security notes
- validation command or manual check

`check_spec.py` will parse ticket IDs and expose them in its JSON report. The schema will document ticket requirements so downstream tools and agents can rely on them.

## Security Design
The spec template will add a lightweight security model:

- assets and sensitive data
- trust boundaries
- attacker-controlled inputs
- abuse cases
- security acceptance criteria
- security validation

This is not a mandatory full security scan. It is a proportional security reasoning layer. If a feature has no meaningful security surface, the spec says why. If it touches auth, secrets, file upload, deployment, CI, dependency supply chain, or user-controlled data, the spec requires stronger evidence.

## Tests
Implementation will follow TDD. Tests will be added before production edits for:

- rendering richer spec sections
- rendering implementation tickets
- schema documenting ticket/security fields
- `check_spec.py` parsing ticket IDs
- domain specialist documenting tool-aware routing and security overlay

## Verification
Focused verification will run the relevant pytest files:

```powershell
python -m pytest skills/tests/test_spec_driven_development.py skills/tests/test_domain_specialist_integrity.py
```

If broader changes are made, run the full skills test suite:

```powershell
python -m pytest skills/tests
```
