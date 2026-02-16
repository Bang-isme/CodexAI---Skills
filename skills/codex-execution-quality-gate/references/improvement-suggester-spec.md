# Improvement Suggester

## Purpose

Generate practical, nearby improvements after task completion, even when the user did not explicitly request a refactor.

## When to Run

- After completing a feature
- After bug-fix stabilization
- After local refactor
- Before opening a PR for review

## Presentation Protocol

1. Show top 3 suggestions first, sorted by priority.
2. Keep each suggestion short and actionable.
3. Ask: "Do you want to fix any of these now?"
4. If user opts in, convert chosen items into next-step tasks.

## Integration Behavior

- Trigger explicitly via `$suggest` or "suggest improvements".
- Optional proactive trigger after complex tasks when proactive mode is enabled.
- Do not block completion based on suggestion output.

## Priority Mapping

- `high`: should do now, likely quality or regression risk
- `medium`: should consider in current change window
- `low`: nice-to-have cleanup

## Scope Boundaries

- Focus on changed files only.
- Skip `node_modules`, `.git`, `dist`, `build`, `__pycache__`, `.next`.
- Skip config-only and test-only files for suggestion generation.
