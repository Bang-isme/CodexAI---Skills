# Workflow: Create

Use this workflow for new feature implementation with moderate/high impact.

Follow the shared confirmation policy in `references/workflow-routing-contract.json`. Review the blast radius against the user's stated constraints; ask only when material scope, risk, or a missing decision requires authorization.

## Steps

1. Load 4-Tier Project Memory in order (`profile.json` / active session -> `genome.md` / `INDEX.md` -> active `SPEC.md` / `DESIGN.md` / `.codex/decisions/` -> active role doc).
2. Analyze scope, run `reuse_map.py` to inspect reusable helpers, and run impact advisory (`predict_impact.py`) for planned file changes.
3. Lock acceptance criteria (`AC-###`) and cross-module System Integration Contracts (`SILC-###`: API route/DTO, error envelope, DB schema, UI state mapping) before coding. Substantial UI needs a design blueprint/contract first; backend-only and tiny CSS fixes do not.
4. Walk `../../codex-reasoning-rigor/references/precision-ladder.md` (6-Rung Smallest-Complete-Change Decision Ladder), apply the **Caller-Grep Rule** on shared functions, and execute implementation in dependency-ordered slices (`Contract/Schema -> Producer -> Consumer`) using TDD (`$tdd`). Record any deliberate ceiling as `shortcut: <ceiling>, <when to upgrade>`.
5. Run `pre_commit_check.py` and `smart_test_selector.py` (plus `check_spec.py` when `.codex/specs/` exists and `$visual-gate` when UI changes).
6. Run `suggest_improvements.py` to surface nearby quality opportunities.
7. Execute Memory Write-Back: log new architecture/contract decisions (`decision_logger.py`), update touched role docs (`update_role_docs.py`), and update `SPEC.md` traceability.

## Exit Criteria

- Functional acceptance criteria (`AC-###`) and integration seams (`SILC-###`) are verified.
- Relevant unit and integration tests selected/executed and passing.
- No unresolved blocking findings.
- Decision journal, active spec traceability, and touched role docs updated when needed.

## Common Pitfalls

- Skipping impact prediction for "small" changes that still touch shared modules.
- Not logging architectural decisions made during implementation.
- Running quality checks only at the very end instead of incrementally.
- Treating advisory findings as noise and never converting them into follow-up tasks.
- Expanding scope during implementation without re-running impact prediction.
- Merging without documenting why a risky tradeoff was accepted.

## Example Sequence

1. Run impact prediction:
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/predict_impact.py" --project-root . --files "src/models/user.ts,src/api/users.ts"`
2. Review blast radius against the implementation scope and constraints already stated by the user.
3. Implement the planned changes in small commits.
4. Run staged quality checks:
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/pre_commit_check.py" --project-root .`
5. Select focused tests:
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/smart_test_selector.py" --project-root . --source staged`
6. Run post-task suggestions and decision logging:
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/suggest_improvements.py" --project-root . --source last-commit`
   then `python "<SKILLS_ROOT>/codex-project-memory/scripts/decision_logger.py" --project-root . --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>` if a tradeoff emerged.
7. Run full completion gate before final handoff:
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/run_gate.py" --project-root .`

## When to Escalate

- Escalate to review workflow when findings include cross-domain security and reliability risks.
- Escalate for human review when API contracts or data models change without clear downstream ownership.
- Escalate to planning workflow when blast radius expands beyond initial scope assumptions.
- Escalate to architecture review when repeated suggestions indicate structural decomposition issues.
