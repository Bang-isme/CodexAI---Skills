# Baseline Policy

Moved from `codex-master-instructions/SKILL.md` so the always-loaded skill stays short. Load this file for complex-code, refactor, or when a completion claim is in doubt.

## Decision Tree

| Type | Signals | Action |
| --- | --- | --- |
| question | explain, what is, how does | answer directly, no code edit flow |
| survey | analyze repo, list files, overview | inspect and report, do not modify files |
| simple-code | fix/add/change in small scope | implement with TDD (`$tdd`), run gate |
| complex-code | build/create/refactor multi-step | intent, plan (`$plan`), isolate (`$worktree`), TDD, gate |
| prototype | MVP, fullstack, from scratch | `$hook` -> `$init-profile` if needed -> `$genome`/`$init-docs` -> `$spec` -> `$plan` -> implement -> `$check-full` |
| debug | error, bug, broken | `$root-cause` then fix then regression test |
| review | review, audit | findings by severity |
| document | draft, report, guide | `codex-document-writer` then editorial review when quality matters |

Single page or component UI uses `codex-frontend-design` fast path. Do not require `$spec` or `$init-docs` for that scope.

## Design-Before-Code Gate

For `complex-code` and `refactor` (not a single UI page):

1. Explore project context.
2. Ask at most 2-3 material questions.
3. Propose 2-3 approaches with a recommendation.
4. Get approval, then write `$plan`.

A single-page or already-specified implementation may skip the interview and still must pass `$check`.

## Engineering Rules

- Keep output concise and action-oriented.
- Prefer repo-grounded evidence over reusable filler.
- Follow SRP, DRY, KISS, and YAGNI.
- Check inbound and outbound dependencies before editing a file.
- Reply in the user's language. Keep code identifiers in English.

## Completion Self-Check

No completion claims without fresh verification evidence. Identify the command, run it, read the output, then claim the result.

| Claim | Requires |
| --- | --- |
| Tests pass | Test command output: 0 failures |
| Linter clean | Linter output: 0 errors |
| Bug fixed | Reproduction test passes |
| Gate passes | `run_gate.py` output: `gate_passed: true` |

## Quality Gate Decision Tree

- New feature: `$tdd` + pre_commit_check
- Bug fix: `$root-cause` + `$tdd` + pre_commit_check
- UI change: ux_audit + accessibility_check + `$visual-gate`
- Deploy: security_scan + lighthouse/playwright when available

## Script Invocation

Always run `--help` first. Treat scripts as black-box CLIs.
