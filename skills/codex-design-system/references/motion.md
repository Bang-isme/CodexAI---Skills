# Motion and Interaction

Motion is a sentence about change. If you cannot say what the user should understand, do not animate.

## Purpose tests

Allowed purposes:

- Feedback: press, save, error, success
- Continuity: shared-element or panel replace so the user knows what changed
- Hierarchy: a primary panel enters; secondary stays still
- Orientation: a drawer or modal origin

Forbidden purposes:

- “Make it feel premium”
- Looping hero decoration that competes with the claim
- Staggered card entrance on every page load for an `operate` surface

## Duration and easing

Keep feedback under 200ms. Panel movement 200–400ms. Use ease-out for entry, ease-in for exit. Do not bounce unless the brand thesis is playful and the surface is `experience` or `persuade`.

## Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Prefer a project token override over this blunt reset when the codebase already has motion tokens.

## Interaction grammar

- Hover is not the only affordance; keyboard and touch need the same information.
- Loading replaces the control or shows progress on the same layout; do not jump the page.
- Destructive actions confirm in place when possible.

Catalog snippets in `micro-interactions.md` are optional examples after purpose is chosen. Do not add two interactions because a list exists.
