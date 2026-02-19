# Docs Change Sync
## Purpose
Map code changes to candidate documentation updates using git diff analysis and configurable mapping rules.
## When to Run
- During workflow docs steps after code implementation.
- After modifying public API signatures or contracts.
- After renaming or moving files referenced in docs.
- Before PR when README or API docs may be stale.
## How AI Uses It
1. Run `map_changes_to_docs.py` with `--diff-scope auto` to detect changed files.
2. Parse JSON output for candidate doc files with confidence scores.
3. Present candidates to user and ask which docs to update.
4. If user approves, proceed to update listed documentation files.
## Integration Behavior
- Trigger on `$codex-docs-change-sync` or during workflow docs phase.
- Report-only by default; do not auto-edit docs unless user requests it.
- If script unavailable, fall back to manual diff inspection targeting `docs/`, `README.md`, `CHANGELOG.md`.
## Output Intent
- Surface likely-stale documentation before it becomes a maintenance burden.
- Provide confidence-ranked candidates so AI prioritizes high-impact doc updates.
