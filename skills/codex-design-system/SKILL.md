---
name: codex-design-system
description: Inject modern design vocabulary, specific palettes, typography, and interaction patterns into UI generation. Prevents generic bootstrap-like output.
load_priority: on-demand
---

## TL;DR
Load before any UI/frontend task. Provide concrete design tokens, not abstract advice. Anti-generic rules: no default blue, no generic card layouts, no bootstrap look.

# Codex Design System

## Activation

1. Activate when task involves UI, frontend, styling, or component creation.
2. Activate on `$design` or "make it look premium".
3. Auto-load when `frontend-specialist` agent is active.

## Anti-Generic Rules (HARD RULES)

- NEVER use default blue (`#007bff`, `#2196F3`) or default purple (`#6C63FF`).
- NEVER use plain white cards with a basic shadow stack.
- NEVER use a generic sans-serif font without naming the exact family.
- NEVER use a symmetrical grid without clear visual hierarchy.
- When generating UI, ALWAYS specify exact hex colors, exact font names, exact spacing values in `px` or `rem`, exact border radii, and exact shadow values.
- Reference one concrete design direction such as glassmorphism, brutalism, bento grid, aurora gradients, editorial minimalism, or layered depth.

## Decision Tree

Task type -> What are we designing?
|- Marketing/site landing -> load `references/palettes.md` + `references/typography.md` + `references/patterns.md`
|- App/dashboard -> load `references/palettes.md` + `references/patterns.md` + `references/micro-interactions.md`
|- Component/system polish -> load `references/typography.md` + `references/micro-interactions.md`
`- Premium visual refresh -> load all 4 reference files before generating UI

## Rules

- Choose one palette and one typography pairing before proposing layout details.
- Tie layout choice to a named pattern from `references/patterns.md`.
- Use motion sparingly and intentionally; pick from `references/micro-interactions.md` instead of inventing vague animations.
- Keep output concrete enough that another engineer could implement the styling without guessing.

## Reference Files

- `references/palettes.md`: 20 curated palettes with exact hex tokens, use cases, and moods.
- `references/typography.md`: 15 font pairings with rationale and UI fit.
- `references/patterns.md`: 12 layout patterns with CSS snippets and anti-patterns.
- `references/micro-interactions.md`: 10 animation patterns with CSS snippets, use cases, and guardrails.
