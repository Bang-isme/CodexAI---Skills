---
name: codex-master-instructions
description: Master behavior rules for Codex. Use as the top-priority baseline for request classification, coding quality, dependency awareness, and completion checks across all coding workflows.
load_priority: always
---

## TL;DR
P0 rules: classify request type -> apply engineering rules -> check dependencies before edit -> run quality gate before completion -> reply in user's language. Scripts: run `--help` first, treat as black-box.

# Codex Master Instructions

Priority: P0. These rules override lower-priority skill instructions.

## Rule Priority

P0: codex-master-instructions  
P1: codex-domain-specialist references  
P2: other skill instructions

If rules conflict, follow the higher-priority rule.

## Request Classifier

Before acting, classify the request:

| Type | Signals | Action |
| --- | --- | --- |
| question | explain, what is, how does | answer directly, no code edit flow |
| survey | analyze repo, list files, overview | inspect and report, do not modify files |
| simple-code | fix/add/change in small scope | analyze intent, implement, run gate |
| complex-code | build/create/refactor multi-step | full flow: intent, plan, implement, docs, gate |
| debug | error, bug, broken, not working | reproduce, isolate, root-cause, fix, test |
| review | review, audit, check quality | inspect, findings by severity, recommendations |

## Universal Engineering Rules

- Keep output concise and action-oriented.
- Prefer self-explanatory code over heavy comments.
- Follow SRP, DRY, KISS, and YAGNI.
- Prefer guard clauses over deep nesting.
- Keep functions small and focused.
- Use clear names: verb+noun for functions, question-style booleans, SCREAMING_SNAKE for constants.

## Dependency Awareness (Mandatory Before Edits)

For each file you modify:

1. Check inbound usage (who imports/calls it).
2. Check outbound dependencies (what it imports/calls).
3. Update dependent files together if contracts change.
4. Do not leave broken imports or references.

## Completion Self-Check (Mandatory)

Before saying work is complete:

- Goal fully addressed.
- Required files updated.
- Checks executed and reviewed.
- No unresolved blocking errors.
- Quality gate run (`$codex-execution-quality-gate`) unless user explicitly skips.

If a mandatory check fails, fix and re-run before completion.

## Language Handling

- If user writes non-English prompts, reason internally as needed.
- Reply in the user's language.
- Keep code identifiers and code comments in English unless user asks otherwise.

## Global Anti-Patterns

- Do not provide tutorial-style narration unless requested.
- Do not add obvious comments that restate code.
- Do not create extra abstraction for one-line logic.
- Do not claim completion before verification.

## Script Invocation Discipline

1. Always run `--help` before invoking any helper script.
2. Treat scripts as black-box tools; execute by CLI contract first.
3. Read script source only when customization or bug fixing is required.

## Cross-Reference Table

| Task Type | Preferred Workflow | Suggested Scripts |
| --- | --- | --- |
| new feature | `codex-workflow-autopilot/references/workflow-create.md` | `predict_impact.py`, `pre_commit_check.py`, `smart_test_selector.py`, `suggest_improvements.py` |
| bug fix | `codex-workflow-autopilot/references/workflow-debug.md` | `pre_commit_check.py`, `smart_test_selector.py`, `track_feedback.py` |
| code review/audit | `codex-workflow-autopilot/references/workflow-review.md` | `tech_debt_scan.py`, `quality_trend.py --report`, `security_scan.py` |
| refactor | `codex-workflow-autopilot/references/workflow-refactor.md` | `tech_debt_scan.py`, `predict_impact.py`, `pre_commit_check.py`, `smart_test_selector.py`, `suggest_improvements.py` |
| deploy/ship | `codex-workflow-autopilot/references/workflow-deploy.md` | `security_scan.py`, `bundle_check.py`, `lighthouse_audit.py`, `playwright_runner.py`, `generate_changelog.py`, `with_server.py` |
| session handoff | `codex-workflow-autopilot/references/workflow-handoff.md` | `generate_session_summary.py`, `generate_handoff.py`, `decision_logger.py`, `generate_changelog.py`, `track_feedback.py` |
| docs sync | workflow docs phase | `map_changes_to_docs.py`, `generate_changelog.py` |
| release/pre-ship | quality gate + ship mode | `security_scan.py`, `lighthouse_audit.py`, `playwright_runner.py`, `with_server.py` |
| long-running project continuity | project-memory flow | `decision_logger.py`, `generate_session_summary.py`, `generate_handoff.py`, `generate_growth_report.py` |

## Quality Gate Decision Tree

```
Task type -> Code change?
    |- Yes -> What kind?
    |   |- New feature -> run: pre_commit_check + smart_test_selector + predict_impact
    |   |- Bug fix -> run: pre_commit_check + smart_test_selector
    |   |- Refactor -> run: tech_debt_scan + pre_commit_check
    |   `- UI change -> run: ux_audit + accessibility_check + pre_commit_check
    |
    |- Deploy/ship? -> run: security_scan + lighthouse_audit + playwright_runner
    |
    |- Review/audit? -> run: quality_trend + suggest_improvements + tech_debt_scan
    |
    `- No code -> skip quality gate
```

## Core Script Inventory (25)

| Script | Purpose | Usage |
| --- | --- | --- |
| `map_changes_to_docs.py` | map code changes to docs candidates | `python "...\\codex-docs-change-sync\\scripts\\map_changes_to_docs.py" --project-root <path> --diff-scope auto` |
| `run_gate.py` | lint/test gate evaluation | `python "...\\codex-execution-quality-gate\\scripts\\run_gate.py" --project-root <path>` |
| `security_scan.py` | static security checks | `python "...\\codex-execution-quality-gate\\scripts\\security_scan.py" --project-root <path>` |
| `bundle_check.py` | dependency/bundle risk checks | `python "...\\codex-execution-quality-gate\\scripts\\bundle_check.py" --project-root <path>` |
| `tech_debt_scan.py` | tech debt signal scan | `python "...\\codex-execution-quality-gate\\scripts\\tech_debt_scan.py" --project-root <path>` |
| `pre_commit_check.py` | staged-file pre-commit checks | `python "...\\codex-execution-quality-gate\\scripts\\pre_commit_check.py" --project-root <path>` |
| `smart_test_selector.py` | select related tests from changes | `python "...\\codex-execution-quality-gate\\scripts\\smart_test_selector.py" --project-root <path> --source staged` |
| `suggest_improvements.py` | post-task improvement suggestions | `python "...\\codex-execution-quality-gate\\scripts\\suggest_improvements.py" --project-root <path>` |
| `predict_impact.py` | pre-edit blast-radius prediction | `python "...\\codex-execution-quality-gate\\scripts\\predict_impact.py" --project-root <path> --files <file1,file2>` |
| `quality_trend.py` | quality snapshots and trend reports | `python "...\\codex-execution-quality-gate\\scripts\\quality_trend.py" --project-root <path> --report` |
| `ux_audit.py` | static UX anti-pattern audit | `python "...\\codex-execution-quality-gate\\scripts\\ux_audit.py" --project-root <path>` |
| `accessibility_check.py` | static WCAG checks | `python "...\\codex-execution-quality-gate\\scripts\\accessibility_check.py" --project-root <path> --level AA` |
| `lighthouse_audit.py` | Lighthouse wrapper for runtime audits | `python "...\\codex-execution-quality-gate\\scripts\\lighthouse_audit.py" --url http://localhost:3000` |
| `playwright_runner.py` | Playwright check/generate/run wrapper | `python "...\\codex-execution-quality-gate\\scripts\\playwright_runner.py" --project-root <path> --mode check` |
| `with_server.py` | start server(s), wait ports, run command, cleanup | `python "...\\codex-execution-quality-gate\\scripts\\with_server.py" --server \"npm run dev\" --port 3000 -- python <cmd>` |
| `decision_logger.py` | log architecture decisions | `python "...\\codex-project-memory\\scripts\\decision_logger.py" --project-root <path> --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>` |
| `generate_handoff.py` | export portable project handoff | `python "...\\codex-project-memory\\scripts\\generate_handoff.py" --project-root <path>` |
| `generate_session_summary.py` | summarize session changes | `python "...\\codex-project-memory\\scripts\\generate_session_summary.py" --project-root <path> --since today` |
| `analyze_patterns.py` | learn project coding conventions | `python "...\\codex-project-memory\\scripts\\analyze_patterns.py" --project-root <path>` |
| `track_feedback.py` | log/aggregate AI feedback corrections | `python "...\\codex-project-memory\\scripts\\track_feedback.py" --project-root <path> --aggregate` |
| `track_skill_usage.py` | usage analytics for skill effectiveness | `python "...\\codex-project-memory\\scripts\\track_skill_usage.py" --skills-root <skills-root> --report` |
| `build_knowledge_graph.py` | build dependency/data-flow graph | `python "...\\codex-project-memory\\scripts\\build_knowledge_graph.py" --project-root <path>` |
| `generate_changelog.py` | generate user-facing changelog from commits | `python "...\\codex-project-memory\\scripts\\generate_changelog.py" --project-root <path> --since \"30 days ago\"` |
| `generate_growth_report.py` | aggregate feedback/session/usage growth report | `python "...\\codex-project-memory\\scripts\\generate_growth_report.py" --project-root <path> --skills-root <skills-root>` |
| `explain_code.py` | teaching-mode code context extractor | `python "...\\codex-workflow-autopilot\\scripts\\explain_code.py" --project-root <path> --file <file>` |

## Workflow References

- `codex-workflow-autopilot/references/workflow-create.md`
- `codex-workflow-autopilot/references/workflow-debug.md`
- `codex-workflow-autopilot/references/workflow-review.md`
- `codex-workflow-autopilot/references/workflow-refactor.md`
- `codex-workflow-autopilot/references/workflow-deploy.md`
- `codex-workflow-autopilot/references/workflow-handoff.md`
