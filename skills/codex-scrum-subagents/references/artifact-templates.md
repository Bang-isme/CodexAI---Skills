# Scrum Artifact Templates

Use the bundled artifact templates when a ceremony should produce a repeatable output instead of free-form notes.

## Template Mapping

- `user-story`: backlog refinement, story-ready check
- `sprint-goal`: sprint planning, sprint review recap
- `daily-scrum`: daily progress + blocker capture
- `retrospective`: wins, pain points, actions, owners
- `release-readiness`: ship decision, risks, rollback, signoff
- `story-delivery`: implementation notes, verification, handoff

## Generator

Use `scripts/generate_scrum_artifact.py` when you need a concrete markdown artifact.

Example:

```bash
python scripts/generate_scrum_artifact.py --template user-story --field title="Checkout address validation" --field persona="Store admin" --field need="Validate shipping input" --field outcome="Reject invalid checkout data before payment" --field acceptance_criteria="- invalid addresses block submission" --field notes="- QA covers edge cases" --output .codex/story.md
```

If you only want a scaffold, add `--allow-placeholders` explicitly.

## Dispatcher

Use `scripts/run_scrum_alias.py` when the user prefers shorthand commands like `$story-ready-check` or `$release-readiness`.
When `--artifact-output` is provided, the alias runner also enforces complete fields unless `--allow-placeholders` is set.
