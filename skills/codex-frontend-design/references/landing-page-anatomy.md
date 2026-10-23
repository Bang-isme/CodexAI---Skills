# Landing Page Anatomy

One offer per page. Hierarchy: proof of job-to-be-done, then action. Nav stays outside the story: identity, 3-5 links, and one primary CTA. Do not center every block. Vary span, media, and whitespace. See `patterns.md` and `anti-slop.md`.

## Four landing shapes

Pick one shape. Do not mix a long-form story into a minimal conversion page.

| Shape | When it fits | What changes |
| --- | --- | --- |
| `classic sections` | A product with distinct benefits, a method, and proof | Each beat is its own section, with uneven spans rather than a stack of identical cards |
| `long-form story` | A content-led launch, editorial, or onboarding narrative | Beats share one narrative spine and one signature mechanism; sections still follow the build order |
| `minimal conversion` | One offer, one action, little supporting catalog | Each beat stays short. The order does not collapse into a hero-only page |
| `comparison` | The reader is choosing between approaches or plans | The proof beat is a comparison the reader can scan. It is not a horizontal-scrolling table at `390px` |

## Strict build order

Build in this order, and do not reorder it:

`hero -> benefits -> how it works -> proof -> objections/FAQ -> final action`

A shape may shorten a beat. It may not skip the final action, hide the price, or move proof above the method. Nav and footer are chrome, not beats.

1. **Hero.** Specific promise, supporting line, one primary action, and real product proof (not a generic 3D blob). The hero claim must be source-matched to the brief, the product facts, or approved copy. Do not invent a metric, customer, or promise to fill the hero.
2. **Benefits.** The outcomes the reader can verify, tied to the claim. Uneven layout, not three identical cards.
3. **How it works.** 3-5 steps. Show the method before asking for trust.
4. **Proof.** Logos only if real; quotes with names; metrics that can be checked. If a number is not in the source, leave it out.
5. **Objections/FAQ.** The questions a skeptical buyer asks before acting. A pricing page fills this beat from `pricing-architecture.md`.
6. **Final action.** Repeat the same primary action. Place a risk reversal next to it: the trial, refund, cancellation, or guarantee the offer actually provides. Do not invent a guarantee the product does not honor.

## Indexing

An evergreen offer is indexable. A time-bound campaign is `noindex`.

Campaign pages include dated launches, seasonal discounts, private betas, and any offer that will be false after a deadline. Set the robots directive to `noindex` on those pages. Do not leave a campaign indexable because the layout looks like a permanent product page. An evergreen offer stays indexable so the durable claim can be found. Do not `noindex` it to hide an unfinished proof problem; fix the proof or mark the claim as a placeholder.
