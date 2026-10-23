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

| Mode | Meaning | Decision boundary |
| --- | --- | --- |
| `extend` | Add a surface that must belong to the current system | Preserve tokens unless a documented product need requires an addition |
| `refine` | Tighten spacing, type, states, or copy | Keep the approved visual thesis and user task |
| `redesign` | Replace the visual system with an explicit thesis | State what changes and why before silently replacing tokens |
| `new` | No incumbent system; invent one and write it down | Explain how the system fits this product rather than relying on category defaults |

Refinement requests must not become redesigns. Redesigns must produce a direction contract before code.

## Color strategy

Choose a strategy, then tokens:

- `incumbent`: keep existing tokens; only add missing states.
- `restrained`: one accent, mostly neutrals, contrast from type and space.
- `expressive`: color carries brand, still one primary action color.
- `editorial`: ink, paper, and one ink-red or gold accent; photos do the rest.

Do not pick a palette only because it is in a list. Palettes in `palettes.md` are optional starting points after strategy is chosen.

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

Check familiar category patterns in context: ask what the typography, hero treatment, card repetition, or dashboard chrome helps this product communicate or do. A familiar pattern becomes a quality concern when a cluster has no product rationale or weakens the user task. Originality means a specific thesis for *this* product, not a named aesthetic from a preset list.

## Originality Evidence Ladder

Judge copying from the strongest evidence downward. A higher rung is sufficient. Do not launder a match by changing a detail on a lower rung.

1. Identical bytes/assets. The same file bytes or the same asset identifiers.
2. Verbatim copy/claims. A contiguous phrase of 8 or more words that is not a generic control label.
3. Brand names & unusual numbers. A distinctive name or a non-generic figure carried over from the reference.
4. Distinctive crop/frame sequence. The same ordered crop or frame sequence, when it is not just hero then FAQ.
5. Multi-trait layout+motion cluster. Two or more specific layout traits together with two or more specific motion traits.

### False-Positive Exclusions

These are not plagiarism findings, alone or together: a black-and-white palette, a single accent, hero+FAQ order, or a standard fade. The label "Learn more" is a generic control, not a copied claim.

Do not fix copied numbers by nudging `$49` to `$47` or `$48`. A small price delta on a copied structure is the same claim. Change the offer, the proof, or the layout for real, or keep the source number and cite it.

## 3-Level Reference Similarity Dial

Set the dial before looking at a reference, and record it in the direction notes.

| Dial | Allowed resemblance |
| --- | --- |
| `distant` | Only the category is shared: both are pricing pages, or both are docs. Hierarchy, crop, motion, and proof are this product's. |
| `recognizable` | A viewer can name the reference family. Type, layout, motion mechanism, and proof are still specific to this product. |
| `close-but-four-elements-changed` | The reference is close, so at least four elements must change before the work is acceptable: hierarchy, crop or frame, motion mechanism, and proof, type, or section structure. A nudged price does not count as one of the four. |
