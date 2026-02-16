---
name: codex-project-memory
description: Tracks project knowledge, decisions, and patterns across sessions
---

# Codex Project Memory

## Activation

1. Activate after complex tasks involving architecture, design decisions, or refactors.
2. Activate on explicit command `$log-decision`.
3. Activate on `$handoff` or when user asks to generate handoff context.
4. Activate on `$session-summary` or when user asks to summarize a coding session.

## Behavior

### Decision Logger

1. Collect decision details:
   - `title`
   - `decision`
   - `alternatives`
   - `reasoning`
   - `context`
2. Run `scripts/decision_logger.py` to persist the record under project `.codex/decisions/`.
3. Return created file path and confirmation summary.
4. Before making similar decisions, review existing files in `.codex/decisions/`.

### Context Handoff Generator

1. Trigger when user needs portable project context for another AI or teammate.
2. Run `scripts/generate_handoff.py`.
3. Default output: `<project-root>/.codex/handoff.md`.
4. Return output path, section count, and file size from script JSON.

### Session Summary Generator

1. Trigger when user requests end-of-session summary.
2. Run `scripts/generate_session_summary.py`.
3. Default output directory: `<project-root>/.codex/sessions/`.
4. Return output path, commit count, and changed file count from script JSON.

## Execution Command

### Decision Logger

- Windows:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\decision_logger.py" --project-root <path> --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-project-memory/scripts/decision_logger.py" --project-root <path> --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>`

### Context Handoff Generator

- Windows:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\generate_handoff.py" --project-root <path>`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-project-memory/scripts/generate_handoff.py" --project-root <path>`

### Session Summary Generator

- Windows:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\generate_session_summary.py" --project-root <path> --since today`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-project-memory/scripts/generate_session_summary.py" --project-root <path> --since today`

## Output Contract

Success JSON:

```json
{
  "status": "logged",
  "path": "<project-root>/.codex/decisions/YYYY-MM-DD-<slug>.md",
  "title": "<title>"
}
```

Error JSON:

```json
{
  "status": "error",
  "path": "",
  "title": "<title>",
  "message": "<error details>"
}
```

## Reference

Read:
- `references/decision-journal-spec.md` for decision logging criteria and naming conventions.
- `references/handoff-spec.md` for handoff usage guidance.
- `references/session-summary-spec.md` for session summary workflow and retention guidance.
