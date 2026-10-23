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

### Scroll choreography when it serves the story

Use scroll-linked motion only when it helps the user understand meaningful progression, comparison, spatial relationship, reveal, or transformation. If scroll adds no user-facing meaning, keep the content in ordinary document flow; utility-heavy surfaces do not need a story arc.

For a content-led experience that benefits from choreography, choose **one signature mechanism** and let supporting effects reinforce it. Define the purpose and visual hierarchy of each effect, vary intensity, and leave a quiet section when the story needs room to land. A payoff should answer or deepen the user's question; do not stretch a page or tease without delivering useful content.

After a scene's peak, reduce intensity and resolve with context, a useful action, or closure. Choose one product-appropriate idea or visual detail that the experience should leave in the user's memory; do not force emotional beats onto task-focused screens.

For each substantial scroll scene, extend the existing UX contract with: user question and intended discovery; content/state change and user action; visual anchor; signature and supporting effects; progress beats from entry/orientation through exploration/build and reveal/peak to release; the information or action payoff and next question; mobile adaptation; reduced-motion/static fallback; performance/lifecycle owner; and a concrete verification method. Percentages are optional aids, not a required formula. Do not create a separate storyboard artifact.

Earn pinned duration with distinct, meaningful stages and release the user back to normal reading. Use horizontal travel only when the content is a sequence, collection, timeline, journey, or other spatial relationship. One short reveal is not a reason for a long pin. Prefer an existing CSS/native transition over GSAP, canvas, WebGL, or generated assets when it communicates the same idea with less cost.

Keep native scroll and semantic document order. A user must be able to scroll quickly or backward, use a direct section link, and reach essential information without waiting for an animation.

Avoid scroll hijacking, forced snap, and long pinned or horizontal sequences by default. Use one only when the content relationship needs it, users can leave it without friction, and the ordinary reading and navigation paths remain intact. Never hide price, safety, key product facts, controls, or task feedback behind a motion trigger.

Reduced motion must preserve the same content, order, controls, and meaning in a designed still frame, which is a stable static state, not a `0.01ms` animation of a hidden initial state; remove movement rather than removing the story.

Verify the sequence at normal pace, with fast and backward scrolling, direct anchor entry, refresh, browser back/forward, keyboard navigation, narrow viewports, and `prefers-reduced-motion`. Sticky navigation must not cover a target heading; account for it with a clear offset. A chapter/active-section indicator never moves keyboard focus. Check that entry at a restored or mid-page scroll position does not leave content hidden or stuck.

## Horizontal & Pinned Chapter Scroll-State Contract

Scroll position is the sole state source. Compute it with a pure function of the live viewport, not a cached height and not the direction the user arrived from:

```javascript
function scrollProgress(scrollY, scrollHeight, innerHeight) {
  const travel = scrollHeight - innerHeight;
  if (travel <= 0) return 0;
  return Math.min(1, Math.max(0, scrollY / travel));
}
```

`progress = scrollY / (scrollHeight - innerHeight)`, normalized by the live viewport height. Recompute when `innerHeight` changes so a mobile URL-bar show or hide cannot leave progress drifted against a stale viewport.

Default scene cadence, when a chapter does not document a different earned span: dwell `1.15` screens, move `0.85` screens. Track length is `(span + 1) * 100vh`. Scene weight stays inside `0.7–1.8` viewport heights unless the brief records an exception.

With two chapters, the active chapter index flips at progress `0.39`, not `0.50`. A midpoint rule keeps the previous chapter marked current after the reader has already entered the next one. With more chapters, each handoff uses that same fraction of the gap between anchors: `threshold(i) = (i - 1 + 0.39) / (chapter_count - 1)` for `i` starting at 1.

Hidden chapters must set `inert`, not only `opacity: 0`, so offscreen controls cannot trap keyboard focus. `aria-hidden` is not a substitute.

Disable `scroll-behavior: smooth` on `html` during programmatic jumps and capture jumps. A smoothed jump lands screenshots mid-transition. Set `scroll-behavior: auto` for that jump, then restore the page's normal behavior.

Fast-skip across multiple scenes plays only the final transition. Do not queue the skipped scenes behind it. Forward scroll, reverse scroll, direct anchor jump, and reload at depth must produce the identical scene signature, because the signature is a pure function of scroll progress, the active index, and chapter identity. Navigation direction is not an input.

## Numerical duration and travel bands

Each band is inclusive at its endpoints. A value outside the band fails unless the brief records an exception. Caps are strict: a value equal to the cap fails. Use ease-out for entry and ease-in for exit. Do not bounce unless the brand thesis is playful and the surface is `experience` or `persuade`.

| Job | Band | Bug this band prevents |
| --- | --- | --- |
| Control feedback | `120–220ms` | Under 120ms the press feels dropped. Over 220ms the control still feels busy after the pointer is released. |
| Toggle, popover, toast | `180–320ms` | Under 180ms the surface appears or vanishes before the eye acquires it. Over 320ms it lags the gesture and blocks the next action. |
| Section entrance | `400–800ms` | Under 400ms the entrance reads as a flash cut. Over 800ms it delays reading. |
| Editorial masks | `500–760ms` | A shorter mask clips the type reveal. A longer mask holds the headline hostage. |
| Hero sequence | `800–1600ms` with internal beats | One undifferentiated fade, or a sequence longer than 1600ms, loses the claim before the first action. Use at least two beats inside the total. |
| Scroll scrub lag | `0.8–1.4` | Below 0.8 the scene jitters with the scrollbar. Above 1.4 the scene feels disconnected from input. `scrub: true` is direct linkage, not a lag value. |
| Word stagger | `0.035–0.07s` | Tighter than 0.035s reads as a block fade. Wider than 0.07s becomes a typewriter. |
| Line stagger | `0.08–0.14s` | Outside this band, lines either pop together or stack into a slow waterfall. |
| Card stagger | `0.06–0.10s` | Outside this band, cards either flash as a grid or cascade long enough to delay scanning. |
| Product reveal travel | `12–24px` | Under 12px the motion is invisible at product density. Over 24px the UI slides in from offstage. |
| Narrative reveal travel | `24–48px` | Under 24px a story beat has no travel. Over 48px it becomes a scene change. Masked wipes may move inside a clipping mask; the visible unmasked travel still uses this band. |
| Text blur reveal | `4–10px` resolving to `0px` | Under 4px blur does no work. Over 10px the type is illegible. A non-zero end blur leaves the headline soft. |
| Magnetic or interactive hover | scale `< 1.03`, tilt `< 4deg`, travel `< 16px` | Larger hover transforms shift the perceived layout and chase the pointer. |
| Parallax | `< 5%` of viewport travel | Larger parallax disconnects layers from scroll and induces vection. |
| Reveal trigger | `20–30%` visible, or top at `82%` of the viewport | An earlier trigger animates offscreen. A later trigger fires after the reader has already parsed the block. |

A utility or `operate` surface that staggers every card fails even when the card interval sits inside `0.06–0.10s`. Stagger a focal cluster, not the whole task grid. Scroll-linked motion must not animate layout properties (`width`, `height`, `top`, `left`, `right`, `bottom`, margin, or padding). Those properties reflow on every frame.

## Reduced motion

Render the designed still frame. Content, controls, and the resolved transform are already visible: opacity `1`, blur `0`, and no offscreen waiting state. Do not collapse a hidden initial keyframe to `0.01ms` and call that reduced motion. A near-zero tween that starts at `opacity: 0` still captures and flashes the hidden frame.

```css
@media (prefers-reduced-motion: reduce) {
  .scene-chapter {
    animation: none;
    transition: none;
    opacity: 1;
    transform: none;
    filter: none;
  }
}
```

Rejected when the pre-motion state is hidden:

```css
/* 0.01ms does not repair a hidden initial state. */
.scene-chapter { animation-duration: 0.01ms; }
```

Prefer a project token that selects the still frame when the codebase already has motion tokens.

## Runtime and WebGL safeguards

Clamp the integration step to `dt <= 1/30s` so a resumed tab cannot teleport a scene. Cap `devicePixelRatio <= 2`. Pause rendering when `document.hidden` or the canvas is offscreen, and keep `offscreen running animations == 0`.

When a scene misses frame budget, ablate in this order and stop at the first step that recovers: lower DPR -> disable post-processing -> freeze shadows -> disable particles -> hide groups -> swap LOD -> replace materials. Do not skip ahead to a material swap while post-processing is still the cost.

## Interaction grammar

- Hover is not the only affordance; keyboard and touch need the same information.
- Loading replaces the control or shows progress on the same layout; do not jump the page.
- Destructive actions confirm in place when possible.

Catalog snippets in `micro-interactions.md` are optional examples after purpose is chosen. Do not add two interactions because a list exists.
