---
name: codex-intent-context-analyzer
description: Use before build, fix, debug, review, or docs implementation; converts prompts into structured intent JSON with goal, constraints, and routing.
load_priority: always
---

## TL;DR
Parse the request into structured intent JSON (goal, constraints, complexity). Treat a clear implementation request as authorization for its stated scope; ask only when a material decision has no safe default or a risk boundary needs authorization. A plan-only request stops after the plan. Follow the shared confirmation policy in `skills/codex-workflow-autopilot/references/workflow-routing-contract.json`. For large repos: read index files first, max 20 files deep-read per task.

# Intent and Context Analyzer

## Activation

1. Activate for any request that implies code or documentation changes.
2. Activate on explicit `$codex-intent-context-analyzer` or `$intent`.
3. Skip for purely informational questions with no requested edits.

## Output Contract

Always return a fenced JSON block in conversation:

```json
{
  "intent": "build | fix | review | debug | docs | refactor | deploy | handoff | other",
  "goal": "One-sentence description",
  "pain_points": ["Problems extracted from the prompt"],
  "constraints": ["Technical or business constraints"],
  "missing_info": ["Information needed but not provided"],
  "normalized_prompt": "Clean rewrite of the user request",
  "complexity": "simple | complex",
  "needs_confirmation": false,
  "suggested_agent": "design-lead | frontend-specialist | visual-quality-reviewer | backend-specialist | security-auditor | debugger | test-engineer | devops-engineer | planner | scrum-master | null",
  "design_operation": "extend | refine | redesign | new | null",
  "surface_mode": "persuade | operate | read | experience | null",
  "supporting_agents": [],
  "ambiguity_reasons": [],
  "required_evidence": []
}
```

Keep every existing field exactly as-is. Additive fields are `suggested_agent`, `design_operation`, `surface_mode`, `supporting_agents`, `ambiguity_reasons`, and `required_evidence`.
The example represents clear, authorized scope. Set `needs_confirmation` to true only for a condition in the shared confirmation policy.

## Auto-Agent Routing

After classifying intent, select the best primary agent from `skills/.agents/` and announce it in conversation:

`🤖 Routing to @[agent-name]...`

| Intent | Primary Agent | Secondary |
| --- | --- | --- |
| build (vague new/redesign UI) | `design-lead` | `frontend-specialist`, `visual-quality-reviewer` |
| build (flow/usability) | `design-lead` | `frontend-specialist` |
| build (visual execution of a chosen direction) | `design-lead` | `frontend-specialist` |
| build (implementation-only frontend) | `frontend-specialist` | `visual-quality-reviewer` |
| build (backend) | `backend-specialist` | `test-engineer` |
| review (visual) | `visual-quality-reviewer` | — |
| fix or debug | `debugger` | — |
| review or audit | `security-auditor` | — |
| deploy | `devops-engineer` | `security-auditor` |
| plan | `planner` | — |
| scrum | `scrum-master` | — |

Security, debug, and deploy routing still beat design routing.

### Routing Notes

- Keep the existing `intent` enum unchanged. `plan` and `scrum` are routing overlays, not new required JSON intent literals.
- For build requests, use domain signals to choose frontend vs backend primary ownership.
- Vague new/redesign UI loads `design-lead` (fast by default, studio for `$direction` or new identity). Implementation-only and CSS refine do not load `design-lead`.
- Separate product facts, visual authority, and art-direction choices. Do not treat missing accent color as missing product truth.
- When a strong secondary fit exists, list it in `supporting_agents` and mention it in prose after the routing line.
- If no confident route exists, set `suggested_agent` to `null` and continue with the normal clarification flow.

### Discipline Skill Notes

After routing to an agent, the following discipline skills activate automatically through agent behavioral rules:

| Agent | Auto-Loads Discipline Skills |
| --- | --- |
| `debugger` | `codex-systematic-debugging` (`$root-cause`) + `codex-test-driven-development` (`$tdd`) |
| `test-engineer` | `codex-test-driven-development` (`$tdd`) |
| `design-lead` | `codex-frontend-design` then `codex-frontend-implementation` |
| `visual-quality-reviewer` | `codex-visual-quality-gate` (must not approve its own implementation) |
| `frontend-specialist` | `codex-test-driven-development` (`$tdd`) via implement mode |
| `backend-specialist` | `codex-test-driven-development` (`$tdd`) via implement mode |
| `planner` | `codex-subagent-execution` (`$sdd`) available for execution handoff |

For `fix or debug` intents: Systematic debugging (4-phase root cause) activates BEFORE any fix attempt.
For all `build` intents: TDD (RED-GREEN-REFACTOR) activates as a behavioral constraint during implementation.

## Socratic Gate

Use Socratic clarification when material requirements are unresolved. Complexity alone does not require another confirmation when the user has clearly requested implementation and a safe, reversible default is available.

### HARD-GATE: Design Before Implementation (substantial UI or new systems)

```
Do NOT write substantial UI for a new identity until a brief exists. A single page or component uses the frontend fast path: 5-line brief then build. `$spec` and `$init-docs` are not required for that scope.
```

### Anti-Pattern: Over-interviewing a narrow task

A one-line CSS refine, an approved-design implementation, or a backend-only fix must not be forced through a long Socratic interview. Ask zero or one boundary question, then execute.

### Trigger Conditions

- Build/create requests with a material requirement that remains unclear.
- Multi-file or architecture-level work.
- Requests with missing constraints or success criteria that change the user-visible outcome.
- "Just do it" requests where a material choice or risk boundary remains unresolved.
- Vague new/redesign UI with no audience, proof, or visual authority.

### Mandatory Questions

When material ambiguity has no safe default, ask up to **2–3 questions in one round**, not an endless one-at-a-time interview. Each question must change the design or implementation. Skip questions whose answers would not change the outcome.

Cover only what is missing:

1. Product facts: who it is for and what it claims.
2. Visual authority: incumbent UI, references, or freedom to invent.
3. Change mode: extend, refine, redesign, or new.

Prefer **multiple choice** questions when possible — easier to answer than open-ended.

Do not ask accent-color trivia when the user already named a framework and an approved mock.

### Question Quality Rules

- Generate questions dynamically for this task (do not reuse static boilerplate).
- Tie each question to an implementation decision.
- Present trade-offs and a default assumption.

Format:

- Question: ...
- Why it matters: ...
- Options: A vs B ...
- Default if unspecified: ...

### Explore Approaches

When the user asks for design options or a material design choice is unresolved, **propose 2-3 approaches with trade-offs:**

- Lead with your recommended option and explain why.
- Present options conversationally, not as a wall of text.
- Include: approach name, key benefit, key trade-off, your recommendation.

### Design Presentation

Scale each section to its complexity:
- A few sentences if straightforward
- Up to 200-300 words if nuanced
- Ask for feedback at a material decision checkpoint or when the user requests collaborative review; otherwise continue within the authorized scope.
- Cover: architecture, components, data flow, error handling, testing

### Design Self-Review

After presenting the design, run a quick self-check:

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections? Fix them.
2. **Internal consistency:** Do sections contradict each other?
3. **Scope check:** Focused enough for a single plan?
4. **Ambiguity check:** Could any requirement be interpreted two ways? Pick one.

Fix issues inline. No need to re-review — just fix and move on.

### Special Cases

- If user already gave stack/tooling, ask edge-case and trade-off questions.
- If the user says "just do it", proceed within the stated scope using a safe, reversible default. Ask only for a material missing decision or required risk authorization.
- If scope covers multiple independent subsystems, help decompose into sub-projects first.

## Confirmation Rule

Follow `confirmation_policy` in `skills/codex-workflow-autopilot/references/workflow-routing-contract.json`. Set `needs_confirmation` only when that policy requires a decision. A clear request authorizes its stated scope, so do not ask the user to confirm the same scope again. Ask before unrequested destructive, irreversible, high-impact, or external actions, and before expanding scope. A plan-only request ends after the plan; an implementation request may use an internal plan and continue within its authorized scope. Keep required spec or design reviews when they present a new artifact or material decision.

## Fallback

If `intent` is `other`, ask user to rephrase or choose one of:
`build`, `fix`, `review`, `debug`, `docs`, `refactor`, `deploy`, `handoff`.

## Script Invocation Discipline

1. When this workflow calls helper scripts from other skills, run `--help` first.
2. Treat helper scripts as black-box tools and execute by contract before reading source.
3. Read script source only when customization or bug-fixing is required.

## Repo Comprehension Protocol (4-Tier Memory First)

For repositories with more than 50 files or existing `.codex/` context:

1. Read the 4-Tier Unified Project Memory first (`../codex-project-memory/references/unified-memory-architecture.md`):
   - **Tier 1 (L0):** `.codex/profile.json`, `.codex/pulse/sprint-state.json`, latest `.codex/sessions/*.md`
   - **Tier 2 (L1):** `.codex/context/genome.md`, `.codex/knowledge/INDEX.md`
   - **Tier 3 (L2):** active `.codex/specs/<slug>/SPEC.md`, `DESIGN.md`, `.codex/decisions/*.md`
   - **Tier 4 (L3):** active `.codex/project-docs/<role>/*.md`
2. If no `.codex/` memory exists yet, read repository index files first: `ARCHITECTURE.md`, `CODEBASE.md`, `README.md`.
3. Build a lightweight map:
   - top-level directories (depth <= 2)
   - likely entry points (`main`, `index`, `app`, `server`)
   - config files (`package.json`, `tsconfig.json`, `pyproject.toml`, etc.)
4. Load by scope, not globally:
   - fix: target module + related tests/docs
   - build: target area + nearby tests/docs + cross-module `SILC-###` seam files
5. Use progressive disclosure:
   - outline first (exports/functions/classes)
   - deep-read only directly relevant files
6. Deep-read budget: max 20 files per task unless user approves expansion.
7. If uncertain scope, ask user before broad exploration.
