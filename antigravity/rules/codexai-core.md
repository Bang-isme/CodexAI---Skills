# CodexAI Antigravity Core

This rule is a native package candidate for Antigravity IDE and CLI. Canonical source is the CodexAI `skills/` tree. Do not assume undocumented plugin-root variables.

## Routing

Security, debug, and deploy still beat design. Vague new or redesign UI loads creative director, then UI/UX, then creative designer, then frontend, then visual quality. Implementation-only work does not load the full studio.

## Tools

Prefer documented tools: `view_file`, `replace_file_content`, `run_command`. Stay inside the project root. Python scripts default to dry-run unless `--apply`.

## Visual quality

Mechanical checks are source evidence, not taste scores. Independent visual review must not approve UI it just authored. Missing browser or subagent is `DEGRADED`, not a silent pass.

## Hooks

Pre-tool hooks remind on UI writes and fail open if Python is missing. They must not freeze the IDE.
