# Mapping Rules (MVP)

## Default Mapping Conventions

- `src/<module>/` -> `docs/<module>.md` or `docs/<module>/`
- `lib/<module>/` -> `docs/api/<module>.md`
- `src/index.*` or `src/main.*` -> `README.md`
- Public API related changes -> include `README.md`
- Schema/model changes -> include `docs/database.md` and/or `docs/schema.md` if present

## Reference Search Patterns

1. Search markdown files under `docs/` and root `README.md` for:
   - changed file paths
   - module names from changed paths
   - changed file stem tokens
2. Add matching docs as medium-confidence candidates.

## Always-Include Rules

1. Include `README.md` when public API files change.
2. Include `CHANGELOG.md` when it exists and there are code changes.

## Notes

- This MVP is report-only: it suggests docs candidates and reasons, but does not edit docs.
- Default diff scope should be `auto`:
  - staged -> unstaged -> last-commit
  - report which scope was used
- Confidence levels:
  - `high`: convention match or exact rule hit
  - `medium`: reference search hit
  - `low`: heuristic fallback
