---
name: codex-master-instructions
description: Use as the top-priority baseline for Codex request classification, coding quality, dependency awareness, and completion checks.
load_priority: always
---

## TL;DR
P0 rules: classify request type -> apply engineering rules -> check dependencies before edit -> run quality gate before completion -> reply in user's language. Scripts: run `--help` first, treat as black-box.

# Codex Master Instructions

Priority: P0. These rules override lower-priority skill instructions.

## Activation

1. Always active as the baseline instruction layer for every turn.
2. Apply this skill before any lower-priority skill guidance.
3. Stack task-specific skills on top of this baseline, not instead of it.

## Rule Priority

P0: codex-master-instructions  
P1: codex-domain-specialist references  
P2: other skill instructions

If rules conflict, follow the higher-priority rule.

## Skill Invocation Rule

Before clarifying, exploring, editing, or answering any workflow-like request, check the request against:

1. Short aliases and workflow aliases.
2. Agent routing rules.
3. Related discipline skills such as TDD, systematic debugging, verification, worktrees, branch finishing, document writing, and design.

If a skill or workflow clearly applies, load and use the smallest matching skill set before acting. Do not skip a relevant skill because the task "looks simple". Do not bulk-load unrelated skills either; the correct behavior is minimum sufficient discipline, not maximum context.

If uncertain, state the chosen routing briefly and continue with the safest matching workflow.

## Short Aliases

Workflow-rich aliases such as `$plan`, `$debug`, `$create`, `$prototype`, `$review`, `$deploy`, and `$handoff` live in the `Workflow Aliases` table below.

| Alias | Full Command | Skill |
| --- | --- | --- |
| `$gate` | `$codex-execution-quality-gate` | codex-execution-quality-gate |
| `$intent` | `$codex-intent-context-analyzer` | codex-intent-context-analyzer |
| `$route` | `$codex-workflow-autopilot` | codex-workflow-autopilot |
| `$brainstorm` | `brainstorm mode` | codex-workflow-autopilot |
| `$think` | `$codex-logical-decision-layer` | codex-logical-decision-layer |
| `$decide` | `$codex-logical-decision-layer` | codex-logical-decision-layer |
| `$hook` | `runtime_hook.py` | codex-runtime-hook |
| `$preflight` | `runtime_hook.py` | codex-runtime-hook |
| `$health` | `check_pack_health.py` | .system |
| `$init-profile` | `init_profile.py` | codex-runtime-hook |
| `$memory` | `$codex-project-memory` | codex-project-memory |
| `$knowledge` | `build_knowledge_index.py` | codex-project-memory |
| `$rigor` | `$codex-reasoning-rigor` | codex-reasoning-rigor |
| `$doc` | `$codex-document-writer` | codex-document-writer |
| `$report` | `$codex-document-writer` | codex-document-writer |
| `$write` | `$codex-document-writer` | codex-document-writer |
| `$role-docs` | `$codex-role-docs` | codex-role-docs |
| `$init-docs` | `init_role_docs.py` | codex-role-docs |
| `$check-docs` | `check_role_docs.py` | codex-role-docs |
| `$spec` | `init_spec.py` / `check_spec.py` | codex-spec-driven-development |
| `$design` | `$codex-design-system` | codex-design-system |
| `$design-md` | `$codex-design-md` | codex-design-md |
| `$genome` | `$codex-genome` | codex-project-memory |
| `$doctor` | `$codex-doctor` | codex-execution-quality-gate |
| `$check` | `auto_gate.py --mode quick` | codex-execution-quality-gate |
| `$check-full` | `auto_gate.py --mode full` | codex-execution-quality-gate |
| `$check-deploy` | `auto_gate.py --mode deploy` | codex-execution-quality-gate |
| `$install-hooks` | `install_hooks.py` | codex-execution-quality-gate |
| `$install-ci` | `install_ci_gate.py` | codex-execution-quality-gate |
| `$commit` | `auto_commit.py` | codex-git-autopilot |
| `$guard` | `$output-guard` | codex-execution-quality-gate |
| `$editorial` | `$editorial-review` | codex-execution-quality-gate |
| `$review-feedback` | `receiving code review feedback` | codex-subagent-execution |
| `$tdd` | `$codex-test-driven-development` | codex-test-driven-development |
| `$red-green` | `$codex-test-driven-development` | codex-test-driven-development |
| `$root-cause` | `$codex-systematic-debugging` | codex-systematic-debugging |
| `$trace` | `$codex-systematic-debugging` | codex-systematic-debugging |
| `$sdd` | `$codex-subagent-execution` | codex-subagent-execution |
| `$dispatch` | `$codex-subagent-execution` | codex-subagent-execution |
| `$worktree` | `$codex-git-worktrees` | codex-git-worktrees |
| `$isolate` | `$codex-git-worktrees` | codex-git-worktrees |
| `$finish` | `$codex-branch-finisher` | codex-branch-finisher |
| `$finish-branch` | `$codex-branch-finisher` | codex-branch-finisher |
| `$verify` | `$codex-verification-discipline` | codex-verification-discipline |
| `$evidence` | `$codex-verification-discipline` | codex-verification-discipline |

## Agent System

When `codex-intent-context-analyzer` returns `suggested_agent`, load the matching `.agents/<agent-name>.md` file before deeper routing.

| Agent | Primary Domain |
| --- | --- |
| `frontend-specialist` | frontend UI, styling, accessibility, and client state |
| `backend-specialist` | API, services, middleware, and persistence boundaries |
| `security-auditor` | security review, hardening, and release-blocking risk |
| `debugger` | reproduction, root cause, and regression-safe fixes |
| `test-engineer` | tests, fixtures, verification scope, and regression coverage |
| `devops-engineer` | CI/CD, deployment safety, and release automation |
| `planner` | intent clarification, planning, and task decomposition |
| `scrum-master` | Scrum ceremonies, coordination, and delivery handoffs |

Rules:

- If `.agents/` does not exist or `.agents/<agent-name>.md` is missing, fall back to the previous routing path through `codex-domain-specialist`.
- Agent routing is additive. It does not replace legacy skill triggers or domain routing.
- Enforce agent boundaries strictly. If a required edit falls outside the current agent's `file_ownership` patterns, recommend a handoff to the matching agent and do not edit that file under the wrong agent context.
- Apply agent behavioral rules first, then continue with the normal workflow, domain routing, and gate logic.

## Workflow Aliases

Workflow aliases are shortcuts. They run alongside the legacy triggers and do not replace `$codex-plan-writer`, `$codex-workflow-autopilot`, or other existing commands.

| Alias | File | Equivalent |
| --- | --- | --- |
| `$plan` | `.workflows/plan.md` | `$codex-plan-writer` + BMAD Phase 1-2 |
| `$debug` | `.workflows/debug.md` | `$codex-systematic-debugging` + 4-phase root cause |
| `$create` | `.workflows/create.md` | `workflow-create.md` + TDD |
| `$prototype` | `.workflows/prototype.md` | `$spec` + `$plan` + role docs + full gate |
| `$review` | `.workflows/review.md` | `workflow-review.md` + output-guard + editorial |
| `$deploy` | `.workflows/deploy.md` | `workflow-deploy.md` + full gate |
| `$handoff` | `.workflows/handoff.md` | `workflow-handoff.md` + session summary |

Rules:

- When the user invokes a workflow alias, load the corresponding `.workflows/<name>.md` file and follow its steps.
- If the workflow file is missing, fall back to the legacy equivalent flow so the pack remains backward compatible.
- Keep old triggers fully active. Aliases are a shorter entry point, not a replacement mechanism.

## Decision Tree

Before acting, classify the request:

| Type | Signals | Action |
| --- | --- | --- |
| question | explain, what is, how does | answer directly, no code edit flow |
| survey | analyze repo, list files, overview | inspect and report, do not modify files |
| simple-code | fix/add/change in small scope | analyze intent, implement with TDD (`$tdd`), run gate |
| complex-code | build/create/refactor multi-step | full flow: intent, plan (`$plan`), isolate (`$worktree`), implement with TDD, gate |
| prototype | MVP, fullstack prototype, from scratch, build whole app | run `$hook` -> `$init-profile` if needed -> `$genome`/`$init-docs` -> `$spec` -> `$plan` -> implement -> `$check-full` |
| debug | error, bug, broken, not working | systematic debugging (`$root-cause`): 4-phase root cause → fix → regression test |
| review | review, audit, check quality | inspect, findings by severity, recommendations |
| document | draft, rewrite, report, memo, guide, soạn tài liệu, viết báo cáo | load `codex-document-writer`, choose document structure, then run editorial review when quality matters |

If the user explicitly asks for deeper thinking, less generic output, stronger specificity, or repo-grounded reasoning, activate `codex-reasoning-rigor` or `$rigor` alongside the normal workflow.
If the user asks to compare multiple directions, find the best path, avoid shallow answers, or reason from multiple angles, activate `codex-logical-decision-layer` or `$think` and provide a compact decision surface instead of hidden chain-of-thought.
If the user asks for professional documents, reports, memos, guides, or clearer wording, activate `codex-document-writer` or `$doc` alongside the normal workflow.

## Context Loading Rule

Before acting on any code-change request:

1. For medium/large work, run `$hook` (`runtime_hook.py`) once to detect domains, suggested agent, and missing FE/BE/DevOps/QA readiness artifacts.
2. Check if `.codex/context/genome.md` exists in the project root.
3. If yes, read it first. This is your project briefing.
4. If project has 50+ files and no `genome.md` exists, suggest: "This project has [N] files. Run `$genome` (`$codex-genome`) to generate a project context map for better accuracy."
5. If `.codex/profile.json` is missing for a medium/large project, suggest `$init-profile` so future sessions route with fewer guesses.
6. If `.codex/knowledge/index.json` is missing after genome or role docs exist, suggest `$knowledge` to make tacit knowledge visible.
7. For prototype, MVP, fullstack, or multi-domain work, require `$spec` before `$plan` and implementation.

## Operation Runbook

For install, sync, global verification, project preflight, role-doc initialization, boundary checks, gate selection, hooks, CI, and troubleshooting, use `.system/OPERATION_RUNBOOK.md`.

If the user asks whether the pack is installed correctly or behaving consistently, run `$health`:

```bash
python "<SKILLS_ROOT>/.system/scripts/check_pack_health.py" --skills-root "<SKILLS_ROOT>" --global-root "<GLOBAL_SKILLS_ROOT>" --format text
```

### Auto-Commit Rule

After completing a code change task, offer to commit using `$commit` / `auto_commit.py`.
Only commit files directly related to the current task. Use a dry run first if uncertain.

## Design-Before-Code Gate (HARD-GATE)

For `complex-code` and `refactor` requests:

<HARD-GATE>
Do NOT write any implementation code, scaffold any project, or take any implementation action until:
1. You have explored the project context (files, docs, recent commits)
2. Asked clarifying questions ONE AT A TIME (prefer multiple-choice)
3. Proposed 2-3 approaches with trade-offs and your recommendation
4. Presented the design and the user has APPROVED it
5. Written a plan using `$codex-plan-writer` or `$plan`
This applies to EVERY complex task regardless of perceived simplicity.
</HARD-GATE>

### Anti-Pattern: "This Is Too Simple To Need A Design"

Every complex task goes through this process. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short, but you MUST present it and get approval.

## Rules

### Universal Engineering Rules

- Keep output concise and action-oriented.
- Prefer repo-grounded evidence over reusable best-practice filler.
- Compress token overhead by removing repeated framing, prompt restatement, synonym stacking, and boilerplate transitions that do not change meaning.
- Prefer self-explanatory code over heavy comments.
- Follow SRP, DRY, KISS, and YAGNI.
- Prefer guard clauses over deep nesting.
- Keep functions small and focused.
- Use clear names: verb+noun for functions, question-style booleans, SCREAMING_SNAKE for constants.
- For document-style outputs, optimize for semantic density: each sentence should carry one clear idea with an explicit actor, action, and outcome.

### Dependency Awareness (Mandatory Before Edits)

For each file you modify:

1. Check inbound usage (who imports or calls it).
2. Check outbound dependencies (what it imports or calls).
3. Update dependent files together if contracts change.
4. Do not leave broken imports or references.

### Completion Self-Check (Mandatory: Evidence Before Claims)

**Iron Law: NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

Before saying work is complete, you MUST:
1. **IDENTIFY:** What command proves this claim? (`test`, `lint`, `build`, `gate`)
2. **RUN:** Execute the full command fresh and read the full output
3. **VERIFY:** Confirm the output actually supports the claim
4. **STATE:** Report the real status with evidence
5. **ONLY THEN:** Make the completion claim

Stop immediately if you catch yourself saying "should work now", "I'm confident", "looks correct", "done", or "fixed" without fresh verification output in the current message.

For projects with hooks installed, gate enforcement is automatic. For projects without hooks, the AI must self-enforce the quality gate.

| Claim | Requires | NOT Sufficient |
| --- | --- | --- |
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check |
| Bug fixed | Reproduction test passes | "Code changed, assumed fixed" |
| Gate passes | `run_gate.py` output: `gate_passed: true` | "I ran it earlier" |

### Language Handling

- If user writes non-English prompts, reason internally as needed.
- Reply in the user's language.
- Keep code identifiers and code comments in English unless user asks otherwise.
- For Vietnamese output, prefer natural UTF-8 Vietnamese and avoid mojibake-prone punctuation when plain ASCII works; prefer `->` over smart arrows if rendering safety is uncertain.
- For Vietnamese plans, reviews, and handoffs, prefer explicit labels such as `Quyết định`, `Bằng chứng`, `Hiện trạng`, `Rủi ro`, and `Bước tiếp theo`.
- Clear does not mean short. Long sentences are acceptable when the sentence has one coherent meaning and avoids filler openings such as "nhìn chung", "về cơ bản", or "có thể thấy rằng".

### Global Anti-Patterns

- Do not provide tutorial-style narration unless requested.
- Do not add obvious comments that restate code.
- Do not create extra abstraction for one-line logic.
- Do not claim completion before verification.

### Escalation References

- `references/debugging-and-recovery.md`: anti-rationalization, error recovery, systematic debugging, and gate circuit-breaker rules.
- `references/scope-escalation.md`: complexity-to-scope mapping and epic-mode escalation.
- `references/workflow-cross-reference.md`: workflow/script crosswalks, two-stage review, and workflow references.
- `skills/.system/manifest.json`: pack structure, load order, agents, and workflow aliases.
- See `skills/.system/REGISTRY.md` for full script paths.

## Quality Gate Decision Tree

```
Task type -> Code change?
    |- Yes -> What kind?
    |   |- New feature -> TDD ($tdd) + pre_commit_check + smart_test_selector + predict_impact
    |   |- Bug fix -> systematic debugging ($root-cause) + TDD + pre_commit_check + smart_test_selector
    |   |- Refactor -> TDD (keep green) + tech_debt_scan + pre_commit_check
    |   `- UI change -> ux_audit + accessibility_check + pre_commit_check
    |
    |- Complex implementation? -> worktree ($worktree) + subagent execution ($sdd)
    |
    |- Deploy/ship? -> run: security_scan + lighthouse_audit + playwright_runner
    |
    |- Review/audit? -> run: quality_trend + suggest_improvements + tech_debt_scan
    |
    `- No code -> skip quality gate
```

## Script Invocation Discipline

1. Always run `--help` before invoking any helper script.
2. Treat scripts as black-box tools; execute by CLI contract first.
3. Read script source only when customization or bug fixing is required.

## Reference Files

- `references/condition-based-waiting.md`: summary; canonical version in `codex-systematic-debugging/references/`.
- `references/defense-in-depth.md`: summary; canonical version in `codex-systematic-debugging/references/`.
- `references/root-cause-tracing.md`: summary; canonical version in `codex-systematic-debugging/references/`.
- `references/debugging-and-recovery.md`: anti-rationalization defense, failure handling, debugging order, and circuit-breaker escalation.
- `references/scope-escalation.md`: complexity mapping, blast-radius thresholds, and epic-mode handling.
- `references/workflow-cross-reference.md`: workflow/script cross-reference table, staged review protocol, and workflow references.
- `references/script-commands.md`
- `references/output-schemas.md`

## Related Discipline Skills

| Skill | Activates On | Purpose |
| --- | --- | --- |
| `codex-test-driven-development` | `$tdd`, `$red-green` | RED-GREEN-REFACTOR enforcement for all code changes |
| `codex-systematic-debugging` | `$root-cause`, `$trace` | 4-phase root cause debugging for all bugs |
| `codex-subagent-execution` | `$sdd`, `$dispatch` | Fresh subagent per task + 2-stage review |
| `codex-git-worktrees` | `$worktree`, `$isolate` | Isolated workspaces for complex implementations |
| `codex-verification-discipline` | `$verify`, `$evidence` | Evidence before claims — no "should work" without proof |
| `codex-branch-finisher` | `$finish`, `$finish-branch` | Structured 4-option completion workflow |
