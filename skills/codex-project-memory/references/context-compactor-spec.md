# Context Compactor Spec

Use `compact_context.py` to reduce memory-file sprawl while preserving long-term signal.

## Trigger

- Use when session/feedback history grows large.
- User cues: "clean up old sessions", "$compact-context", "reduce context bloat".

## Retention Policy

### Sessions (`.codex/sessions/*.md`)

- Keep latest `N` files (`--keep-latest`, default `5`) regardless of age.
- Archive older files only when file age is greater than `--max-age-days` (default `90`).
- Archive target: `.codex/sessions/archive/YYYY-summary.md`.
- Archive content should keep:
  - session date
  - commit count
  - files changed
  - key change bullets (compact view)

### Feedback (`.codex/feedback/*.md`)

- If total entries exceed `50`, aggregate all current entries by month.
- Archive target: `.codex/feedback/archive/YYYY-MM-summary.md`.
- Preserve:
  - per-category counts
  - top recurring patterns/lessons
- After successful archive write, originals can be removed.

### Decisions (`.codex/decisions/*.md`)

- Never delete decision records.
- Only report count in compact result.

## Dry Run

- `--dry-run` must not write, move, or delete files.
- It should report what would be archived and estimated bytes freed.

## Output Contract

```json
{
  "status": "compacted",
  "sessions_archived": 12,
  "feedback_archived": 45,
  "decisions_kept": 8,
  "bytes_freed": 24500
}
```
