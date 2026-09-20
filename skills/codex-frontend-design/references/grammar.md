# Design Grammar

Use this grammar instead of a style catalog. Brief, incumbent system, and surface mode win over palettes and font pairings.

## Surface mode

| Mode | Visitor job | Visual consequence |
| --- | --- | --- |
| `persuade` | Decide and act (landing, campaign, pricing) | One dominant claim, one primary CTA, proof near the ask |
| `operate` | Complete a work task (app, dashboard, admin) | Dense but grouped; status first; decoration last |
| `read` | Understand (docs, article, changelog) | Measure line length, type contrast, quiet chrome |
| `experience` | Feel a place (portfolio, brand moment) | Atmosphere allowed only if navigation stays obvious |

If the prompt does not name a mode, infer it from the surface. Do not mix `persuade` hero theater into an `operate` settings page.

## Change mode

| Mode | Meaning | Forbidden smuggle |
| --- | --- | --- |
| `extend` | Add a surface that must belong to the current system | New visual language |
| `refine` | Tighten spacing, type, states, or copy | Rebrand or new layout thesis |
| `redesign` | Replace the visual system with an explicit thesis | Silent “refresh” of tokens |
| `new` | No incumbent system; invent one and write it down | Category-default SaaS look |

Refinement requests must not become redesigns. Redesigns must produce a direction contract before code.

## Color strategy

Choose a strategy, then tokens:

- `incumbent`: keep existing tokens; only add missing states.
- `restrained`: one accent, mostly neutrals, contrast from type and space.
- `expressive`: color carries brand, still one primary action color.
- `editorial`: ink, paper, and one ink-red or gold accent; photos do the rest.

Never pick a palette because it is in a list. Palettes in `palettes.md` are optional starting points after strategy is chosen.

## Composition thesis

State one sentence the layout must prove, for example:

- “The product is a calm operator console; the chart is the hero.”
- “The offer is a single claim; proof sits under the CTA, not beside it.”

Then choose grouping, rhythm, and optical alignment to serve that sentence. See `composition.md`.

## Content and proof

Visual craft cannot invent product claims. If the brief lacks audience, offer, or proof, ask or mark the claim as placeholder. Marketing surfaces need proof placement (quote, metric, logo, or demo) near the primary action.

## Asset provenance

Every image, icon set, and illustration needs a source: generated under project license, user-supplied, or named public domain/open font. Do not paste stock watermarks or unmarked third-party UI kits.

## Motion purpose

Motion exists to explain change, hierarchy, or feedback. If it does not change a decision or a state, omit it. Honor `prefers-reduced-motion`. See `motion.md`.

## Originality boundary

Reject category defaults: Inter-on-white, blue gradient hero, three identical feature cards, generic dashboard chrome. Originality means a specific thesis for *this* product, not a named aesthetic from a preset list.
