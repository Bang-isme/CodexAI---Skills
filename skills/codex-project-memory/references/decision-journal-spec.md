# Decision Journal Spec

## When To Log

Log decisions for:
- architecture choices
- dependency selection or replacement
- pattern changes (state management, data flow, routing, etc.)
- trade-off resolutions with long-term impact

## When Not To Log

Do not log:
- simple bug fixes
- formatting-only changes
- routine implementation tasks with no meaningful trade-off

## How To Reference Existing Decisions

Before making a similar decision:
1. Read files in `<project-root>/.codex/decisions/`.
2. Reuse confirmed patterns when context is equivalent.
3. If context differs, log a new decision and reference prior rationale.

## File Naming Convention

Use:
- `YYYY-MM-DD-<slug>.md`

If the same date and slug already exist:
- append numeric suffix: `YYYY-MM-DD-<slug>-2.md`, `-3.md`, ...

## Decision Record Format

```markdown
# Decision: <title>
Date: YYYY-MM-DD
Status: accepted
## Context
<context>
## Decision
<decision>
## Alternatives Considered
<alternatives>
## Reasoning
<reasoning>
## Consequences
(to be filled after implementation)
```
