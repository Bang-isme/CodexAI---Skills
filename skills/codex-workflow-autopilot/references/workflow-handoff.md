# Workflow: Handoff
Use this workflow at end of session or when transferring project context to another developer or future AI session. Follow the Long-Horizon Continuity Contract in `../codex-project-memory/references/unified-memory-architecture.md`.

## Steps
1. Synchronize active artifacts per the Write-Back Protocol:
   - Log any new architecture/contract tradeoff via `decision_logger.py`.
   - Update active `SPEC.md` traceability and `SILC-###` integration seam status (`check_spec.py` when `.codex/specs/` exists).
   - Update touched role docs via `update_role_docs.py` when `.codex/project-docs/` exists.
2. Run `generate_session_summary.py --project-root . --since last-session` (or `--since today` for first session) to capture the Git and working-tree snapshot.
3. Complete **every** prompt marker in the generated `.codex/sessions/*.md` file before treating it as a valid checkpoint:
   - **Goal & Status:** `in_progress | completed | blocked`
   - **Active Spec & Plan:** exact `.codex/specs/<slug>/SPEC.md` and `./<plan>.md` paths when applicable
   - **Completed vs Pending ACs & SILC Seams:** e.g., `Completed: AC-001, SILC-001 | Pending: AC-002, SILC-002`
   - **Commands Verified:** exact commands run and observed pass/fail outputs
   - **Exact Next Step:** specific `TICKET-###`, file path, and verification command to run first on resume
4. Run `generate_handoff.py` to export a self-contained portable project handoff (`.codex/handoff.md`).
5. Run `generate_changelog.py --since today` and `track_feedback.py --aggregate` to surface recent changes and recurring risk patterns.

## Exit Criteria
- Session summary file exists in `.codex/sessions/` with zero unresolved bracketed placeholders (`[Fill from the user request]`, etc.).
- Active spec, pending ACs, SILC integration seams, verified commands, and exact next step are recorded.
- Handoff document exported with current project state.
- No undocumented architectural decisions from the session.
## Common Pitfalls
- Skipping handoff because session was "short" - even small sessions produce decisions worth capturing.
- Not aggregating feedback - recurring patterns get lost between sessions.
- Generating handoff without session summary - handoff lacks activity context.
## Example Sequence
1. `generate_session_summary.py --project-root . --since today`
2. `generate_handoff.py --project-root .`
3. `decision_logger.py --project-root . --title "api-pagination-strategy" --decision "cursor-based" --alternatives "offset-based" --reasoning "better for large datasets" --context "users endpoint"`
4. `generate_changelog.py --project-root . --since today`
5. `track_feedback.py --project-root . --aggregate`
## When to Escalate
- Multiple unresolved decisions accumulating -> schedule dedicated architecture review.
- Feedback aggregate shows 5+ issues in same category -> prioritize fix before next feature work.
