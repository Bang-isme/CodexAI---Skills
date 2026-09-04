---
name: codex-creative-direction
description: Use for vague new or redesign UI prompts; decode the brief, pick visual authority, and produce three distinct directions before implementation.
load_priority: on-demand
version: "16.0.0"
---

## TL;DR
Do not code first. Separate product facts from visual authority. Produce three directions with thesis, risk, and implementation consequence. Fight category default. User or brief picks one direction before `creative-designer`.

## Activation
1. Vague “make a site / app / landing page look great” prompts.
2. Explicit redesign or new visual identity.
3. `$direction` or routing to `creative-director`.

Do not activate for implementation-only work or CSS refinements.

## Product truth vs visual truth
- Product truth: who it is for, what it claims, proof, constraints. Missing facts become 2–3 material questions, not a long interview.
- Visual truth: references, incumbent UI, photography, type, material. If none exist, say so and invent a thesis rather than a template SaaS look.

## Three directions
Each direction must differ in composition thesis, not just accent color:

1. Name and one-sentence thesis
2. Surface mode and color strategy
3. Type and material attitude
4. Risk (legibility, build cost, brand mismatch)
5. Implementation consequence (tokens, layout, motion budget)

Do not offer three flavors of the same card grid.

## Originality
Reject Inter-on-white plus blue gradient plus three feature cards unless the product *is* that category and the user confirmed refine-not-redesign. Direction DNA must be wrong for a generic competitor.

## Output
Direction contract in conversation and, when applying design context, `.codex/design/directions/`. Chosen direction is the only input `creative-designer` may execute.

## References
- `../codex-design-system/references/grammar.md`
- `../codex-design-system/references/composition.md`
- `../codex-design-system/references/anti-slop.md`
