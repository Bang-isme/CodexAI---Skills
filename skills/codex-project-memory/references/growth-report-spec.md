# Growth Report Spec

## When to Use

- Weekly developer retrospective.
- Sprint-end learning review.
- Coaching check-in for recurring issue categories.

## How It Works

1. Reads project feedback records from `.codex/feedback/`.
2. Reads session summaries from `.codex/sessions/`.
3. Reads skill usage analytics from `<skills-root>/.analytics/usage-log.jsonl`.
4. Cross-references recurring feedback categories with activity and skill outcomes.
5. Generates a prioritized markdown report with strengths and action items.

## Output Format

- Markdown report:
  - Activity summary
  - Improvement areas (prioritized)
  - Strengths observed
  - Skill effectiveness table
  - Action items
- JSON stdout:
  - `status`
  - `path`
  - `improvement_areas`
  - `sessions_analyzed`
  - optional `warnings`

## Integration

- Use with `track_feedback.py` for issue trend visibility.
- Use with `track_skill_usage.py --report` for skill effectiveness context.
- Use with `generate_session_summary.py` to tie improvement areas to actual delivery activity.
- Feed top action items into next planning cycle (`codex-plan-writer`).
