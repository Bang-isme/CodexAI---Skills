## Summary

- What changed and why

## Scope

- [ ] Skill code only
- [ ] Plugin metadata (Codex/Claude/marketplace)
- [ ] Project-memory tooling
- [ ] CI/CD workflows
- [ ] Documentation only

## Test plan

- [ ] `python -m pytest skills/tests -q -k "not test_project_traversal_does_not_follow_symlinks_outside_root"` (Windows) or `python -m pytest skills/tests -q` (Linux)
- [ ] `python skills/.system/scripts/check_pack_health.py --skills-root skills --strict --format json`
- [ ] Plugin validators (`validate_codex_plugin.py`, `validate_claude_plugin.py`) when plugin metadata changes
- [ ] Project-memory contract tests when memory tooling changes

## Risk and rollback

- Risk:
- Rollback: revert this PR; no runtime state changes outside generated `.codex/` artifacts.

## Notes

- Did not commit generated `.codex/` artifacts (see `skills/codex-project-memory/references/artifact-lifecycle-policy.md`).
- Did not commit local IDE state (`.cursor/`, `.commandcode/`).
- Did not store secrets or tokens.
