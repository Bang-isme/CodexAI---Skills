# Composition and Optical Balance

These are observable gates, not a fake balance score.

## Hierarchy / squint test

Squint or shrink the viewport. The primary task or claim must remain the only loud object. If two regions shout, reduce one. Size, weight, contrast, and position beat extra color.

## Grouping

Related controls share a cluster: same inset, same background, one heading. Unrelated actions do not share a card. Lists of “features” need a reason to be a list; otherwise use a narrative block or a comparison.

## Spacing rhythm

Use a small spacing scale (for example 4/8/12/16/24/40/64) and repeat it. Arbitrary values (`13px`, `37px`, mixed `gap` and `margin` with no scale) fail the mechanical gate. Adjacent clusters should differ by at least one scale step so groups read as groups.

## Optical alignment

Align to a grid and then correct optically: hanging punctuation, icon optical center, text that looks centered but is not because of uneven glyph bounds. Edges of cards, rules, and columns should share a line unless a break is the thesis.

## Density

`operate` surfaces may be dense if grouping is strong. `persuade` surfaces need air around the claim. Repeated cards are useful for genuinely parallel items; if items have different importance, vary hierarchy or choose a more suitable grouping instead of forcing equal tiles.

## Distinctiveness without visual clutter

For a substantial redesign, give the page one product-fit signature: for example, a data visualization that explains change, an editorial split that pairs a decision with its evidence, or a workspace arrangement that keeps a frequent task in reach. State what it helps the user notice or do. Let the rest of the composition support that move with a clear hierarchy and familiar interaction patterns. Creative structure can come from scale, alignment, negative space, grouping, or information geometry; it does not need extra cards, gradients, shadows, or motion. Keep any device whose product job is clear, and simplify the rest.

Before accepting a new composition, check the same hierarchy in realistic short and long content. Long labels, controls, data, and media must reflow or use a deliberate local scroll/crop behavior; they must not overlap neighboring content or hide the primary task. See `layout-decision-framework.md` for the layout contract and `layout-adaptation.md` for content-safe responsive behavior.

## Narrative sequence when it serves the user

Use narrative structure for content-led experiences when staged understanding improves the task: a launch story, editorial explanation, learning flow, onboarding, or a product journey with meaningful discovery. Before arranging sections, write a compact spine in the existing brief or UX contract:

`user question → essential context/proof → discovery or decision → useful next action`

Expand that spine into only the beats the product needs. Each beat should answer a distinct user question, contribute new evidence or meaning, and make the next step easier to anticipate. Connect sections through information and visual continuity when that relationship helps comprehension. Use contrast and breathing room to pace attention; resolve any question the page raises, and keep essential details such as safety, price, or caveats visible rather than hiding them for suspense.

If a user skips to a later section, the heading and nearby context should still orient them. If the experience is primarily operational, use its task sequence, current state, feedback, and next action as the structure. Do not force an emotional arc or a cinematic climax onto a utility-heavy surface.

## Responsive reflow

Desktop and a narrow viewport are both first-class. Reflow must preserve hierarchy: the primary action stays reachable; secondary nav collapses; tables get a stacked or scroll plan. Do not hide the only CTA behind a hamburger without a visible substitute.

## Focus order

DOM order matches visual reading order. Skip links or landmarks exist on long pages. Modals trap focus and restore it.

## Contrast

Text and essential icons meet WCAG contrast for the chosen surface. Large decorative type may be quieter only if a readable counterpart exists.

## States

Every interactive control documents default, hover, focus-visible, disabled, loading, error, and empty. `operate` flows also need success and permission-denied.

## Reduced motion

Transforms and fades have a reduced-motion alternative: instant state change or opacity only, no large movement.
