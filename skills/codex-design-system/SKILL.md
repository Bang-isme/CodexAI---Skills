---
name: codex-design-system
description: Use for UI, frontend, styling, landing page, or component work; applies grammar (surface mode, change mode, composition, motion) instead of mandatory palettes.
load_priority: on-demand
---

## TL;DR
Load before substantial UI work. Brief, incumbent system, and visitor/surface mode win over catalogs. Palettes and font pairings are optional after a color strategy and composition thesis exist. Do not add two micro-interactions by default.

## Activation
1. Activate for UI, frontend, styling, component, or marketing-surface work.
2. Activate on `$design` or when the user asks for a distinctive or balanced visual result.
3. Auto-load with `creative-director`, `creative-designer`, `ui-ux-designer`, or `frontend-specialist` when the task is visual.
4. Pair with `codex-design-md` for `DESIGN.md`. Pair with `codex-ui-ux-design` for flows. Pair with `codex-creative-direction` when the prompt is a new or redesign surface.

Skip the full studio when the change is a one-line CSS fix, copy tweak, or backend-only work.

## Decision order
1. Read product facts and visual authority (`PRODUCT.md`, `DESIGN.md`, incumbent tokens).
2. Choose surface mode and change mode from `references/grammar.md`.
3. Write a one-sentence composition thesis.
4. Only then choose type, color strategy, imagery, and motion purpose.
5. Optional: consult `palettes.md` / `typography.md` if no incumbent tokens exist.
6. Check `references/anti-slop.md` and `references/composition.md` before code.

## Hard rules
- Do not always pick a palette preset or always add two micro-interactions.
- Do not use default bootstrap blue/purple or generic white card stacks unless the incumbent system already does.
- Do not invent product claims to fill a layout.
- Substantial UI work needs desktop and mobile evidence in one review pass.

## Reference Files
- `references/grammar.md` — surface mode, change mode, color strategy, originality.
- `references/composition.md` — hierarchy, grouping, rhythm, optical alignment, density, reflow, focus, contrast, states, reduced motion.
- `references/color-material.md` — strategy before hex; one material model.
- `references/typography.md` — optional pairings after strategy is chosen.
- `references/palettes.md` — optional catalogs after color strategy is chosen.
- `references/patterns.md` — optional layout primitives.
- `references/motion.md` — purpose-first motion.
- `references/layout-adaptation.md` — desktop plus mobile in one pass.
- `references/imagery.md` — asset provenance and icon grammar.
- `references/anti-slop.md` — mechanical slop categories.
- `references/anti-patterns.md` — additional developer-UI mistakes.
- `references/micro-interactions.md` — optional snippets after purpose is chosen.
- `references/trends.md` — fit heuristics, not year-dated fashion.
