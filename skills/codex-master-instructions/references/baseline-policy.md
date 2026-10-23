# Baseline Policy

Moved from `codex-master-instructions/SKILL.md` so the always-loaded skill stays short. Load this file for complex-code, refactor, or when a completion claim is in doubt.

## Decision Tree (SDLC + SILC Routing)

| Type | Signals | Action |
| --- | --- | --- |
| question | explain, what is, how does | answer directly, no code edit flow |
| survey | analyze repo, list files, overview | inspect and report, do not modify files |
| simple-code | fix/add/change in small scope (1-3 files, single domain) | load L0/L1 context, implement with TDD (`$tdd`), run `$check` |
| complex-code | build/create/refactor multi-step or cross-module | 4-Tier Memory Read -> intent -> spec/contract if cross-domain -> plan (`$plan`) -> isolate (`$worktree`) -> TDD + SILC seam verification -> gate -> Memory Write-Back |
| prototype | MVP, fullstack, from scratch | `$hook` -> `$init-profile` if needed -> `$genome`/`$init-docs` -> `$spec` (lock `AC-###` + `SILC-###` contracts) -> `$plan` -> implement + verify seams -> `$check-full` -> Memory Write-Back |
| debug | error, bug, broken | `$root-cause` (4-phase trace across component boundaries) -> failing reproduction test (`$tdd`) -> minimal fix -> regression gate |
| review | review, audit | findings by severity + spec/SILC contract compliance |
| document | draft, report, guide | `codex-document-writer` then editorial review when quality matters |

Single page or component UI uses `codex-frontend-design` fast path. Do not require `$spec` or `$init-docs` for that scope.

## 7-Stage SDLC + SILC Closed-Loop Pipeline

For multi-file, cross-domain, or long-horizon engineering tasks, execute these 7 stages in order without skipping seams:

1. **Stage 1 — Preflight & 4-Tier Memory Read:** Inspect Tier 1 (`.codex/profile.json`, active session/pulse), Tier 2 (`genome.md`, `INDEX.md`), Tier 3 (`SPEC.md`, `DESIGN.md`, `decisions/`), and Tier 4 (active role doc only).
2. **Stage 2 — Intent & Boundary Classification:** Parse goal, constraints, primary/supporting agents, and confirmation conditions via `codex-intent-context-analyzer`.
3. **Stage 3 — Normative Contract Lock (SDLC + SILC):** Before writing multi-domain code, lock functional requirements (`AC-###`), System Integration Contracts (`SILC-###`: API route/DTO, error envelope, DB schema/migration, UI state mapping), and security controls (`SEC-###`).
4. **Stage 4 — Dependency & Seam-Ordered Planning:** Decompose into bite-sized tasks ordered from shared contract/schema -> producer -> consumer -> integration test.
5. **Stage 5 — TDD + SILC Seam Execution:** Run RED-GREEN-REFACTOR for each task and verify the producer/consumer contract seam before starting dependent tasks.
6. **Stage 6 — Multi-Gate Verification:** Run `auto_gate.py` (`quick`, `full`, or `deploy`), `check_spec.py`, and `$visual-gate` when UI changes.
7. **Stage 7 — Deterministic Memory Write-Back:** Log new decisions (`decision_logger.py`), update active `SPEC.md` traceability and role docs (`update_role_docs.py`), and checkpoint session state (`generate_session_summary.py`).

## Design-Before-Code Gate

For `complex-code` and `refactor` (not a single UI page):

1. Explore project context.
2. Ask up to 2-3 questions only when a material requirement has no safe default.
3. Present competing approaches when a material choice remains open; recommend a reversible default when it does not.
4. If the user requested a plan only, write `$plan` and stop. If the user explicitly requested implementation and scope is clear, use a plan internally and proceed without asking the user to approve that same scope again.

Follow `skills/codex-workflow-autopilot/references/workflow-routing-contract.json` for confirmation conditions. Pause before unrequested destructive, irreversible, high-impact, or external actions, and before material scope expansion. Preserve a required spec or design review when it presents a new artifact or material decision.

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
