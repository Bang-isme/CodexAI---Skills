# Workflow: Handoff
Use this workflow at end of session or when transferring project context to another developer or future AI session.
## Steps
1. Run `generate_session_summary.py` to capture session activity.
2. Run `generate_handoff.py` to create portable project context export.
3. Log any open decisions via `decision_logger.py` (if architectural tradeoffs remain unresolved).
4. Run `generate_changelog.py --since today` to capture today's changes.
5. Run `track_feedback.py --aggregate` to surface any recurring issues.
## Exit Criteria
- Session summary file exists in `.codex/sessions/`.
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
