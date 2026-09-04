---
name: codex-ui-ux-design
description: Use for flows, IA, cognitive load, empty/error/loading states, content ranges, and responsive accessibility before visual decoration.
load_priority: on-demand
version: "16.0.0"
---

## TL;DR
Produce a UX contract: jobs, flows, information architecture, states, copy, and responsive/a11y behavior. Do not invent visual direction. Hand off to `creative-designer` or `frontend-specialist`.

## Activation
1. New or changed user journeys, onboarding, forms, navigation, or empty states.
2. `$ux` or prompts about usability, IA, or cognitive load.
3. After `creative-director` when the chosen direction still needs flow structure.

Skip when the user only asks to implement an already approved UX contract.

## Output: UX contract
Write under `.codex/design/surfaces/<slug>.md` when `--apply` is used via `design_context.py`. Include:

- Job and success metric
- Happy path and failure path
- IA: pages, nav, grouping
- Content ranges (shortest and longest realistic copy)
- States: empty, loading, error, success, permission denied
- Responsive behavior and keyboard/focus order
- Accessibility notes that are requirements, not suggestions

## Rules
- Reduce cognitive load: one primary decision per view when possible.
- Copy is part of UX. Do not leave “lorem” on a primary CTA.
- Do not change product claims.
- Do not pick palettes or motion language here.

## References
- `../codex-design-system/references/grammar.md`
- `../codex-design-system/references/layout-adaptation.md`
- `../codex-design-system/references/composition.md`
