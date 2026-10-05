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

## Narrative and scroll motion

Use scroll-linked motion only when the scroll represents a meaningful progression, comparison, spatial relationship, or reveal. Keep native scroll and semantic document order. A user must be able to scroll quickly or backward, use a direct section link, and reach essential information without waiting for an animation.

Avoid scroll hijacking, forced snap, and long pinned or horizontal sequences by default. Use one only when the content relationship needs it, users can leave it without friction, and the ordinary reading and navigation paths remain intact. Never hide price, safety, key product facts, controls, or task feedback behind a motion trigger.

For a complex sequence, storyboard the beats in the existing UX contract or direction file: intent, content/state change, user action, transition, and static fallback. Do not create a separate storyboard artifact. Reduced motion must preserve the same content, order, controls, and meaning in a stable static state; remove movement rather than removing the story.

Verify the sequence at normal pace, with fast and backward scrolling, direct anchor entry, refresh, browser back/forward, keyboard navigation, narrow viewports, and `prefers-reduced-motion`. Sticky navigation must not cover a target heading; account for it with a clear offset. A chapter/active-section indicator never moves keyboard focus. Check that entry at a restored or mid-page scroll position does not leave content hidden or stuck.

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
