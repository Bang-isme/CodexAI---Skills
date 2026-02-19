# Changelog Generator Spec

## When to Use

- Before publishing a release note.
- Before tagging a new version.
- When you need user-facing summaries from technical commits.

## How It Works

1. Reads commit history using `git log --oneline --no-merges`.
2. Resolves default range from latest tag; falls back to last 30 days.
3. Classifies commit subjects into:
   - Features
   - Bug Fixes
   - Breaking Changes
   - Improvements
   - Documentation
4. Filters out test-only and chore/merge/bump noise.
5. Produces markdown changelog section sorted by release impact.

## Output Format

- Markdown section:
  - Header with version/date
  - Categorized bullet lists
- JSON stdout:
  - `status`
  - `version`
  - `since`
  - `total_commits`
  - `categories`
  - `path`
  - `changelog_markdown`

## Integration

- Pair with `generate_session_summary.py` for sprint/session reporting.
- Pair with `decision_logger.py` to include major architecture decisions in release narratives.
- Use as input for release emails, app store notes, and CHANGELOG updates.
