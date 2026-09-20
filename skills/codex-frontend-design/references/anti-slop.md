# Anti-Slop

Mechanical symptoms that usually mean generic UI. These are evidence categories, not taste scores.

## Card soup

Three or more sibling cards with the same heading size, padding, radius, and icon treatment. Fix by changing span, media, or hierarchy, or by not using cards.

## Missing hierarchy tokens

Headings skip levels, or body/label/caption all use the same size and color. Fix with a type ramp tied to tokens or explicit sizes.

## Arbitrary spacing and radius

Many unique `px`/`rem` values for gap, padding, or radius in one surface. Fix with a scale.

## Default-font and gradient clichés

System UI font only, or Inter/Roboto/Arial with a blue-to-purple hero gradient and a glassy card. Fix by choosing a strategy from `grammar.md` and an incumbent or authored pair.

## Competing CTAs

Two or more same-weight primary buttons in the first viewport. Fix by promoting one and demoting the rest.

## Absent responsive, reduced-motion, or state coverage

No breakpoint, no `prefers-reduced-motion`, or interactive components with only a default style. Fix in source before visual review.

## Category default

SaaS landing that could be any product: navy hero, three features, logo cloud, pricing toggle, footer. Originality requires a composition thesis that would be wrong for a different product.

## Extra DON'T fingerprints (from MengTo/Skills frontend-design)

- Overused fonts: Inter, Roboto, Arial, Open Sans, system defaults as the only type
- Identical card grids with icon + heading + text
- Center everything
- Glassmorphism, glow borders, or custom cursors used as decoration
- Bounce/elastic easing
- Gray text on colored backgrounds
- The 2024-2025 "AI palettes": cyan-on-dark, purple-to-blue gradients, neon on dark
