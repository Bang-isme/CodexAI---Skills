---
name: codex-frontend-implementation
description: Use when implementing web UI in React, Next.js, Tailwind, CSS, or GSAP against an approved design, fast-path brief, or prototype UX contract.
load_priority: on-demand
version: "18.1.0"
---

## TL;DR
Implement the selected brief. Honor incumbent tokens and `DESIGN.md`. Load stack recipes, then at most two craft files. Keep design exploration in `codex-frontend-design`; implement its selected direction faithfully.

# Frontend Implementation

## Activation
- After `codex-frontend-design` fast, prototype, or studio path.
- `$create` UI work routed to `frontend-specialist`.
- Prompts naming React, Next, Tailwind, shadcn, GSAP, CSS, components.

## Load order
1. `references/frontend-rules.md`
2. Stack recipe: `references/react-tailwind-shadcn.md` and/or `references/nextjs-app-router.md`
3. `references/accessibility-rules.md`
4. Optional craft file from `craft/` matching the requested effect
5. Starter tokens: `starters/design-system.css` (OKLCH, no Inter default)

For GSAP, ScrollTrigger, scrubbed, or pinned scenes, also load `references/gsap-mastery.md` and follow the scene intent in the approved UX contract. Do not treat its API examples as design defaults.

## Rules
- Match the brief. Do not swap palettes to look busy.
- “Do not invent a new art direction” applies after a direction has been selected. The design task may establish a distinctive, product-fit direction first; then carry it through implementation without quietly flattening or changing it.
- Treat the approved UX contract or audit findings as the implementation boundary. Preserve working routes, API/auth boundaries, data flow, and successful tasks; inspect consumers before changing a shared component and recheck affected consumers afterward.
- Preserve the repository's existing frontend architecture unless evidence shows it is causing maintenance problems. Before moving or extracting code, inspect ownership and import direction, then apply `references/frontend-rules.md` for proportionate structure, shared boundaries, and safe migration. A visual task does not justify a repository-wide architecture rewrite.
- For a material change to an existing product, use the audit's KEEP / REFINE / RECOMPOSE / REBUILD decision to preserve what works and target the evidenced root cause. A narrow fix does not need a redesign rationale or extra artifact.
- For a substantial layout change, follow the existing layout contract: keep the named task, content order, navigation, and control behavior stable while changing only the chosen creative direction. Prove the composition on a representative route with realistic long content before applying it to other shared consumers.
- Use intrinsic sizing where content must flex (`minmax(0, 1fr)` and `min-width: 0` where appropriate); avoid fixed height for variable text/data and absolute positioning for essential content. Keep intentional overflow local to the table or media region that needs it.
- Keep the change proportional: name the observable problem and expected outcome, explain why the current approach is insufficient for major refactors or dependencies, and record affected consumers, regression risk, verification, rollback, alternatives, and tradeoffs in the existing audit note. Prefer the simplest change that resolves the cause.
- Separate data, state, presentation, and behavior only when that improves clarity; reuse shared components for consistent product behavior, and avoid duplicate implementations or abstractions that only add configuration.
- Do not substitute static demo data for an existing working integration. If the requested artifact is a prototype and must mock a service, label the mock clearly and report that end-to-end behavior is unverified.
- Implement real control outcomes and the loading, empty, error, success, and disabled states required by the product. Do not leave visible controls inert or silently remove difficult functionality.
- Prefer transform/opacity when they fit the effect; honor `prefers-reduced-motion` with a content-equivalent state.
- When assets affect the page, follow `../codex-frontend-design/references/imagery.md`: keep controls, copy, and states semantic; implement the stated crop and responsive behavior; preserve a fallback; and review the asset at its actual rendered size in the component.
- Every control needs states from `../codex-frontend-design/references/component-states.md`.
- Product facts > anti-slop > wow recipes.
- Run project-native checks that apply to the changed behavior; distinguish checks run from assumptions. After substantial UI, run `$visual-gate` and inspect the captured render, not only source output.
- After each material iteration, compare expected and actual outcome, verify affected shared consumers, and update the same audit note. Do not add work once meaningful, actionable issues within scope are resolved or remaining issues are lower value, blocked, or out of scope.
- For structural changes, hand off the ownership or dependency changes, affected consumers, checks run, and any material remaining debt. Do not create an architecture document for a narrow UI change; use an existing project record for decisions that need to persist.

## Craft library
Curated technique skills live in `craft/`. See `craft/PROVENANCE.md`. Load one file, not the whole folder.
