---
name: codex-frontend-design
description: Use when building or redesigning UI; pick fast path for a page/component or studio path for a new visual identity.
load_priority: on-demand
version: "18.0.0"
---

## TL;DR
Default is **fast**: 5-line brief -> tokens -> build -> anti-slop self-check. Use **studio** only for `$direction`, brand-new identity, or when the user asks for options. Precedence: product facts > anti-slop > catalog/wow.

# Frontend Design

## Activation
- `$design`, `$ux`, `$direction`, `$refine`, or prompts about landing pages, UI, visual identity, flows, or polish.
- After routing to `design-lead`.

Skip studio ceremony for "implement the approved design" and for one-page/one-component builds.

## Mode: fast (default)

When the user says build/make/implement, or the scope is one page or component:

1. Write a 5-line brief (audience, job, tone, one memorable detail, constraints). Template: `references/design-brief-template.md`.
2. Choose type, color (prefer OKLCH), spacing. Do not default to Inter or a purple gradient.
3. Build with `codex-frontend-implementation`.
4. Self-check `references/anti-slop.md`. Run `$visual-gate`.

Do not require `$spec` or `$init-docs` for this scope.

## Mode: studio

When the user asks for directions, a new brand, or `$direction`:

1. Ask at most 2 material questions.
2. Produce 3 directions (thesis, risk, implementation). See `references/directions.md`.
3. After a pick, write a short UX contract (`references/ux-contract.md`) and `DESIGN.md` via `codex-design-md`.
4. Then build.

## Precedence

1. Product facts and incumbent tokens win.
2. Anti-slop and originality beat decorative wow (glass, custom cursors, WebGL) unless the brief asks for them.
3. Catalogs (`palettes.md`, `typography.md`, craft recipes) are optional.

## Landing pages

Load `references/landing-page-anatomy.md` before coding a marketing or home page.

## Refinement

`$refine <dial>` or `$polish` `$critique` `$audit-ui` `$animate` — see `references/refinement-dials.md` and `.workflows/refine.md`. Each dial ends with `$visual-gate`.

## References
- `references/grammar.md`, `references/composition.md`, `references/anti-slop.md`
- `references/typography.md`, `references/color-oklch.md`, `references/palettes.md`
- `references/component-states.md`, `references/layout-adaptation.md`, `references/motion.md`
- `references/patterns.md`, `references/anti-patterns.md`
