---
name: codex-intent-context-analyzer
description: Analyze code-change prompts into structured intent JSON with goal, constraints, missing info, normalized prompt, complexity, and confirmation gating. Use before implementation for build, fix, debug, review, and docs tasks.
load_priority: always
---

## TL;DR
Parse user request into structured intent JSON (goal, constraints, complexity). Trigger Socratic Gate for complex or ambiguous scope. Suggest an agent route after classification. Wait for explicit confirmation before implementation. For large repos: read index files first, max 20 files deep-read per task.

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
  "needs_confirmation": true,
  "suggested_agent": "frontend-specialist | backend-specialist | security-auditor | debugger | test-engineer | devops-engineer | planner | scrum-master | null"
}
```

Keep every existing field exactly as-is. The only additive extension is `suggested_agent`.

## Auto-Agent Routing

After classifying intent, select the best primary agent from `skills/.agents/` and announce it in conversation:

`🤖 Routing to @[agent-name]...`

| Intent | Primary Agent | Secondary |
| --- | --- | --- |
| build (frontend) | `frontend-specialist` | `test-engineer` |
| build (backend) | `backend-specialist` | `test-engineer` |
| fix or debug | `debugger` | — |
| review or audit | `security-auditor` | — |
| deploy | `devops-engineer` | `security-auditor` |
| plan | `planner` | — |
| scrum | `scrum-master` | — |

### Routing Notes

- Keep the existing `intent` enum unchanged. `plan` and `scrum` are routing overlays, not new required JSON intent literals.
- For build requests, use domain signals to choose frontend vs backend primary ownership.
- When a strong secondary fit exists, mention it in prose after the routing line instead of adding another JSON field.
- If no confident route exists, set `suggested_agent` to `null` and continue with the normal clarification flow.

### Discipline Skill Notes

After routing to an agent, the following discipline skills activate automatically through agent behavioral rules:

| Agent | Auto-Loads Discipline Skills |
| --- | --- |
| `debugger` | `codex-systematic-debugging` (`$root-cause`) + `codex-test-driven-development` (`$tdd`) |
| `test-engineer` | `codex-test-driven-development` (`$tdd`) |
| `frontend-specialist` | `codex-test-driven-development` (`$tdd`) via implement mode |
| `backend-specialist` | `codex-test-driven-development` (`$tdd`) via implement mode |
| `planner` | `codex-subagent-execution` (`$sdd`) available for execution handoff |

For `fix or debug` intents: Systematic debugging (4-phase root cause) activates BEFORE any fix attempt.
For all `build` intents: TDD (RED-GREEN-REFACTOR) activates as a behavioral constraint during implementation.

## Socratic Gate

Trigger Socratic Gate for `complexity: complex` or ambiguous scope.

### HARD-GATE: Design Before Implementation

```
Do NOT write any code, scaffold any project, or take any implementation
action until you have presented a design and the user has approved it.
This applies to EVERY project regardless of perceived simplicity.
```

### Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.

### Trigger Conditions

- Build/create requests with vague requirements.
- Multi-file or architecture-level work.
- Requests with missing constraints or success criteria.
- "Just do it" requests with unclear scope.

### Mandatory Questions

Ask questions **one at a time** — do not overwhelm with multiple questions per message.

Ask at least 3 questions covering:

1. Purpose: what problem is being solved.
2. Users: who is affected.
3. Scope: must-have vs nice-to-have.

Prefer **multiple choice** questions when possible — easier to answer than open-ended.

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

Before settling on a design, **propose 2-3 approaches with trade-offs:**

- Lead with your recommended option and explain why.
- Present options conversationally, not as a wall of text.
- Include: approach name, key benefit, key trade-off, your recommendation.

### Design Presentation

Scale each section to its complexity:
- A few sentences if straightforward
- Up to 200-300 words if nuanced
- Ask after each section whether it looks right so far
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
- If user says "just do it", still ask 2 short boundary questions.
- If scope covers multiple independent subsystems, help decompose into sub-projects first.

## Confirmation Rule

- Keep `needs_confirmation` true by default.
- Present analysis first and wait for explicit confirmation.
- Do not start implementation until confirmed.

## Fallback

If `intent` is `other`, ask user to rephrase or choose one of:
`build`, `fix`, `review`, `debug`, `docs`, `refactor`, `deploy`, `handoff`.

## Script Invocation Discipline

1. When this workflow calls helper scripts from other skills, run `--help` first.
2. Treat helper scripts as black-box tools and execute by contract before reading source.
3. Read script source only when customization or bug-fixing is required.

## Repo Comprehension Protocol

For repositories with more than 50 files:

1. Read index files first: `ARCHITECTURE.md`, `CODEBASE.md`, `README.md`.
2. Build a lightweight map:
   - top-level directories (depth <= 2)
   - likely entry points (`main`, `index`, `app`, `server`)
   - config files (`package.json`, `tsconfig.json`, `pyproject.toml`, etc.)
3. Load by scope, not globally:
   - fix: target module + related tests/docs
   - build: target area + nearby tests/docs
4. Use progressive disclosure:
   - outline first (exports/functions/classes)
   - deep-read only directly relevant files
5. Deep-read budget: max 20 files per task unless user approves expansion.
6. If uncertain scope, ask user before broad exploration.
