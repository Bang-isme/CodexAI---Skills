# GSAP Mastery — Advanced Animation Engineering

## Scope and Triggers

Use this reference when:
- Building scroll-driven animations, page transitions, or interactive storytelling.
- Working with GSAP plugins: `ScrollTrigger`, `SplitText`, `ScrollSmoother`, `Observer`, `Flip`, `MotionPath`, `MorphSVG`, `DrawSVG`, `CustomEase`.
- Keywords: `gsap`, `scrolltrigger`, `splittext`, `scrollsmoother`, `timeline`, `tween`, `scrub`, `pin`, `stagger`.

**License**: GSAP's current Standard License permits no-charge commercial use in websites and apps, with restrictions for competing visual animation-builder products. Check the [current terms](https://gsap.com/community/standard-license/) for the product you are building.

**Relationship to the design brief**: `../../codex-frontend-design/references/motion.md` defines the user-facing reason, experience contract, and fallback. This reference covers implementation choices and lifecycle; it does not make a pin, horizontal section, or GSAP dependency a design default.

## Scroll-story implementation contract

Start from the mapped UX-contract scene. Keep native document flow and the semantic version as the source of essential content. If the scene does not need controlled progression, use ordinary CSS or no motion.

Treat motion as progressive enhancement: essential content is visible and controls work before the animation initializes and if it fails. Do not leave key copy hidden in baseline CSS waiting for JavaScript to reveal it.

- For one coordinated pinned/scrubbed scene, use a **single timeline or progress controller** as its source of truth. Drive child motion from that normalized progress and timeline labels; avoid unrelated ScrollTriggers that compete for the same elements or scene.
- Derive the pin span from meaningful mapped stages and the actual content. There is no default `300%` length. Prefer no pin when a simple reveal, sticky layout, or native sequence carries the same information.
- Scrub is directly linked when `scrub: true`; a numeric scrub intentionally adds catch-up lag. Select based on the scene and device, then verify it does not feel disconnected from the user's input. Scroll-linked tweens commonly use `ease: "none"` for predictable progress; ordinary time-based UI motion can use a purposeful easing curve.
- Snapping is opt-in. Keep it subtle and interruptible, and preserve ordinary scroll and direct navigation.
- Use `gsap.matchMedia()` when separate responsive or `prefers-reduced-motion` setups are needed. Keep the same story and controls in a stable reduced-motion mode; desktop choreography may be simplified or replaced on mobile. Avoid duplicating setup when only a small value changes.
- Give each component/scene local ownership. For component cleanup in React, use the project's supported `useGSAP()` or a scoped GSAP context; clean it up with `context.revert()` (or the hook's cleanup). Remove event listeners and custom render loops in the same owner. Do not kill every ScrollTrigger on route leave unless this module owns every instance.
- Refresh measurements after a layout/content change that affects trigger positions; do not call global refresh on every render. Keep development markers/debug progress out of production.

These lifecycle APIs are documented by GSAP: [matchMedia](https://gsap.com/docs/v3/GSAP/gsap.matchMedia/), [context](https://gsap.com/docs/v3/GSAP/gsap.context/), and [ScrollTrigger](https://gsap.com/docs/v3/Plugins/ScrollTrigger/).

---

## 1. Core Architecture — Tweens & Timelines

### Tween Types

| Method | Behavior | Use Case |
| --- | --- | --- |
| `gsap.to()` | Animate FROM current state TO target | Most common; buttons, reveals |
| `gsap.from()` | Animate FROM target TO current state | Intro animations, load-in effects |
| `gsap.fromTo()` | Explicit start AND end values | When current state is unpredictable |
| `gsap.set()` | Instant property assignment (0 duration) | Reset state, prepare elements before animation |

### Timeline Architecture

Timelines (`gsap.timeline()`) are the backbone of complex animation sequences. **Never chain independent `gsap.to()` calls with delays.** Use timelines.

```javascript
// ❌ BAD: Fragile, impossible to adjust timing
gsap.to(".logo", { opacity: 1, duration: 0.5 });
gsap.to(".title", { y: 0, duration: 0.8, delay: 0.5 });
gsap.to(".subtitle", { y: 0, duration: 0.8, delay: 1.3 });
gsap.to(".cta", { scale: 1, duration: 0.6, delay: 2.1 });

// ✅ GOOD: Timeline with position parameter
const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
tl.to(".logo", { opacity: 1, duration: 0.5 })
  .to(".title", { y: 0, duration: 0.8 }, "-=0.2")      // overlap 0.2s
  .to(".subtitle", { y: 0, duration: 0.8 }, "-=0.4")    // overlap 0.4s
  .to(".cta", { scale: 1, duration: 0.6 }, "-=0.3");    // overlap 0.3s
```

### Position Parameter Cheatsheet

| Position | Meaning | Example |
| --- | --- | --- |
| `"+=0"` | After previous ends (default) | Sequential |
| `"-=0.3"` | 0.3s before previous ends | Overlap / cascade |
| `"+=0.5"` | 0.5s gap after previous | Pause between |
| `"<"` | Same start as previous | Parallel |
| `"<0.2"` | 0.2s after previous starts | Staggered parallel |
| `2` | Absolute time = 2s from timeline start | Pin to fixed point |
| `"myLabel"` | At named label position | Section marker |
| `"myLabel+=0.5"` | 0.5s after label | Relative to label |

### Timeline Defaults

Set shared properties once:

```javascript
const tl = gsap.timeline({
  defaults: {
    duration: 0.8,
    ease: "power3.out",
    stagger: 0.05,
  },
  paused: true,       // Don't auto-play (useful for ScrollTrigger or manual control)
  onComplete: () => { /* cleanup */ },
});
```

---

## 2. The Easing Bible

Easing is one craft choice among purpose, timing, distance, and hierarchy. Choose it for the motion goal; do not use a named curve as a substitute for a clear interaction.

### Easing Selection Matrix

| Context | Easing | Why |
| --- | --- | --- |
| Element entering viewport | `power3.out` or `power4.out` | Fast start, gentle settle → feels responsive |
| Element leaving viewport | `power2.in` or `power3.in` | Slow start, fast exit → feels natural |
| Hover / button press | `power2.out` | Quick response, professional snap |
| Elastic / playful bounce | `elastic.out(1, 0.3)` | Organic overshoot, playful UI |
| Smooth camera / scroll | `none` (linear) or `power1.inOut` | Constant speed, no jarring changes |
| Snapping to position | `power4.inOut` | Sharp deceleration into resting position |
| Magnetic / sticky feel | `expo.out` | Extreme deceleration, feels magnetic |
| Page transitions | `power3.inOut` or `circ.inOut` | Symmetric, cinematic feel |

### Custom Easing

```javascript
gsap.registerPlugin(CustomEase);

// Apple / Stripe signature ease
CustomEase.create("apple", "0.76, 0, 0.24, 1");

// Elastic settle (overshoot then settle)
CustomEase.create("elasticSettle", 
  "M0,0 C0.05,0 0.15,1.12 0.3,1.05 0.45,0.98 0.55,1.01 0.65,1 0.8,0.99 1,1");

// Slow-motion reveal
CustomEase.create("slowReveal", "0.22, 1, 0.36, 1");
```

### The Golden Rule of Easing

> Out easing often suits entrances, in easing often suits exits, and in-out easing often suits transitions. Linear is appropriate for direct scroll scrubbing or constant-rate motion. Treat these as starting points and verify against the actual interaction.

---

## 3. ScrollTrigger — Scroll-Driven Animation Engine

### Setup & Registration

```javascript
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
gsap.registerPlugin(ScrollTrigger);
```

### The 4 Core Modes

| Mode | Config | Use Case |
| --- | --- | --- |
| **Toggle** | `toggleActions: "play none none none"` | Play once when entering viewport |
| **Scrub** | `scrub: true` or `scrub: 1` (smoothed) | Animation progress = scroll position |
| **Pin** | `pin: true` | Lock element while animation plays |
| **Snap** | `snap: 1 / sectionCount` | Snap to discrete positions |

These are API modes, not a recipe to combine them. In particular, do not add pinning or snapping unless the scene contract explains the user benefit and how users can leave or bypass it.

### ScrollTrigger Patterns

#### Pattern A: Reveal on Scroll (Most Common)

```javascript
gsap.utils.toArray(".reveal").forEach((el) => {
  gsap.from(el, {
    y: 60,
    opacity: 0,
    duration: 1,
    ease: "power3.out",
    scrollTrigger: {
      trigger: el,
      start: "top 85%",   // trigger when top of el hits 85% of viewport
      toggleActions: "play none none none",
    },
  });
});
```

#### Pattern B: Parallax Layers

```javascript
gsap.to(".bg-layer", {
  yPercent: -30,
  ease: "none",
  scrollTrigger: {
    trigger: ".parallax-section",
    start: "top bottom",
    end: "bottom top",
    scrub: true,         // Tie directly to scroll position
  },
});
```

#### Pattern C: Horizontal Scroll Section (only for spatial/sequence content)

```javascript
const sections = gsap.utils.toArray(".horizontal-panel");

gsap.to(sections, {
  xPercent: -100 * (sections.length - 1),
  ease: "none",
  scrollTrigger: {
    trigger: ".horizontal-container",
    pin: true,
    scrub: 1,
    // Add snap only if the sequence needs discrete stopping points and remains interruptible.
    end: () => "+=" + document.querySelector(".horizontal-container").offsetWidth,
  },
});
```

#### Pattern D: Pinned Storytelling (only when the mapped stages earn a pin)

```javascript
const storytl = gsap.timeline({
  scrollTrigger: {
    trigger: ".story-section",
    pin: true,
    scrub: 0.5,
    start: "top top",
    end: "bottom top",    // derive the scene's span from its real layout; avoid copied 300% durations
  },
});

storytl
  .to(".story-text-1", { opacity: 1, y: 0 })
  .to(".story-image-1", { scale: 1.1 }, "<")
  .to(".story-text-1", { opacity: 0, y: -50 })
  .to(".story-text-2", { opacity: 1, y: 0 })
  .to(".story-image-1", { opacity: 0 }, "<")
  .to(".story-image-2", { opacity: 1, scale: 1 }, "<");
```

#### Pattern E: Progress Bar / Scroll Indicator

```javascript
gsap.to(".progress-bar", {
  scaleX: 1,
  transformOrigin: "left center",
  ease: "none",
  scrollTrigger: {
    trigger: "body",
    start: "top top",
    end: "bottom bottom",
    scrub: true,
  },
});
```

### ScrollTrigger `start` / `end` Cheatsheet

Format: `"<trigger position> <scroller position>"`

| Value | Meaning |
| --- | --- |
| `"top top"` | Trigger's top hits viewport top |
| `"top 80%"` | Trigger's top hits 80% down the viewport |
| `"top bottom"` | Trigger's top enters viewport bottom |
| `"center center"` | Trigger's center hits viewport center |
| `"bottom top"` | Trigger's bottom reaches viewport top (fully passed) |
| `"+=300%"` | 300% of trigger height after start (for `end`) |

### `clamp()` for Above-the-Fold Elements

Prevents elements from starting in a partially scrubbed state when they are already visible on load:

```javascript
scrollTrigger: {
  trigger: ".hero-element",
  start: "clamp(top bottom)",  // Clamp: don't start before page load
  end: "clamp(bottom top)",
  scrub: true,
}
```

---

## 4. SplitText — Text Animation Engine

### Modern SplitText (v3.13+ Rewrite)

```javascript
import { SplitText } from "gsap/SplitText";
gsap.registerPlugin(SplitText);

// Split into lines, words, and characters
const split = new SplitText(".hero-title", {
  type: "lines, words, chars",
  autoSplit: true,           // Re-split on resize / font load
  mask: "lines",             // Add overflow:hidden mask wrapper per line
  onSplit: (self) => {
    // Re-run animation after re-split
    animateText(self);
  },
  aria: true,                // Accessibility: auto aria-label + aria-hidden
});
```

### Text Reveal Patterns

#### The Mask Reveal (Characters rise into view)

```javascript
function animateText(split) {
  gsap.from(split.chars, {
    yPercent: 100,           // Rise from below the mask
    opacity: 0,
    stagger: 0.02,           // 20ms between each character
    duration: 0.8,
    ease: "power3.out",
    scrollTrigger: {
      trigger: split.elements[0],
      start: "top 80%",
    },
  });
}
```

#### The Word-by-Word Fade

```javascript
gsap.from(split.words, {
  opacity: 0,
  y: 20,
  filter: "blur(4px)",
  stagger: 0.04,
  duration: 0.6,
  ease: "power2.out",
});
```

#### The Line-by-Line Wipe

```javascript
gsap.from(split.lines, {
  yPercent: 100,             // Each line slides up
  stagger: 0.08,
  duration: 1,
  ease: "power4.out",
});
```

#### The Typewriter Effect

```javascript
gsap.from(split.chars, {
  opacity: 0,
  stagger: 0.03,            // Each char appears sequentially
  duration: 0.01,            // Near-instant per char
  ease: "none",
});
```

### SplitText Cleanup

Always revert SplitText when the component unmounts (important in React/SPA):

```javascript
// Revert to original HTML
split.revert();
```

---

## 5. ScrollSmoother — Lenis Alternative (GSAP Native)

```javascript
import { ScrollSmoother } from "gsap/ScrollSmoother";
gsap.registerPlugin(ScrollTrigger, ScrollSmoother);

const smoother = ScrollSmoother.create({
  wrapper: "#smooth-wrapper",
  content: "#smooth-content",
  smooth: 1.5,              // Seconds of smoothing (higher = more lag)
  effects: true,            // Enable data-speed and data-lag attributes
  smoothTouch: 0.1,         // Light smoothing on touch devices (0 = off)
});
```

### Data Attributes for Parallax

```html
<!-- Slow element (parallax background) -->
<div data-speed="0.5">Moves at half scroll speed</div>

<!-- Fast element (foreground accent) -->
<div data-speed="1.5">Moves at 1.5x scroll speed</div>

<!-- Lagging element (follows with delay) -->
<div data-lag="0.3">Follows scroll with 0.3s delay</div>
```

### Clamp for Above-the-Fold

```html
<!-- Prevent parallax offset before user scrolls -->
<div data-speed="0.8" data-speed-clamp="true">Hero background</div>
```

---

## 6. Observer — Universal Input Detection

Detects mouse wheel, touch swipe, pointer drag, and scroll in a unified API:

Using `preventDefault` to replace native page scrolling is a high-friction pattern, not a default. Reserve it for a requested, genuinely spatial full-screen interface with a clear way to navigate, keyboard support, reduced-motion behavior, and an ordinary content path.

```javascript
import { Observer } from "gsap/Observer";
gsap.registerPlugin(Observer);

// Full-screen section navigation (like Apple keynote)
let currentIndex = 0;
const sections = document.querySelectorAll(".section");

Observer.create({
  type: "wheel, touch, pointer",
  wheelSpeed: -1,           // Invert wheel direction if needed
  tolerance: 50,            // Minimum distance to trigger
  preventDefault: true,
  onUp: () => goToSection(currentIndex - 1),
  onDown: () => goToSection(currentIndex + 1),
});

function goToSection(index) {
  index = gsap.utils.clamp(0, sections.length - 1, index);
  if (index === currentIndex) return;
  currentIndex = index;
  gsap.to(sections[index], {
    scrollIntoView: true,   // GSAP native scrollIntoView
    duration: 1,
    ease: "power3.inOut",
  });
}
```

---

## 7. Flip — Layout Animations

Animate between two layout states seamlessly (FLIP = First, Last, Invert, Play):

```javascript
import { Flip } from "gsap/Flip";
gsap.registerPlugin(Flip);

// Save current state
const state = Flip.getState(".card");

// Mutate the DOM (reorder, move to different container, change class)
container.classList.toggle("grid-view");

// Animate from old state to new state
Flip.from(state, {
  duration: 0.7,
  ease: "power2.inOut",
  stagger: 0.05,
  absolute: true,           // Use absolute positioning during animation
  onEnter: (elements) => gsap.fromTo(elements, { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1 }),
  onLeave: (elements) => gsap.to(elements, { opacity: 0, scale: 0.8 }),
});
```

**Use cases**: Grid ↔ List toggle, filtering/sorting, drag-and-drop reorder, expanding cards.

---

## 8. MorphSVG & DrawSVG

### MorphSVG — Shape Morphing

```javascript
import { MorphSVGPlugin } from "gsap/MorphSVGPlugin";
gsap.registerPlugin(MorphSVGPlugin);

// Morph circle into star
gsap.to("#circle", {
  morphSVG: "#star",
  duration: 1.5,
  ease: "power2.inOut",
});

// Convert non-path elements (rect, circle, polygon) to path data
MorphSVGPlugin.convertToPath("circle, rect, polygon");
```

### DrawSVG — Line Drawing Animation

```javascript
import { DrawSVGPlugin } from "gsap/DrawSVGPlugin";
gsap.registerPlugin(DrawSVGPlugin);

// Draw from 0% to 100%
gsap.from(".svg-path", {
  drawSVG: "0%",
  duration: 2,
  ease: "power2.inOut",
  stagger: 0.2,
});

// Partial draw (10% to 60%)
gsap.to(".svg-path", {
  drawSVG: "10% 60%",
  duration: 1.5,
});
```

---

## 9. MotionPath — Animate Along a Path

```javascript
import { MotionPathPlugin } from "gsap/MotionPathPlugin";
gsap.registerPlugin(MotionPathPlugin);

gsap.to(".rocket", {
  motionPath: {
    path: "#flight-path",      // SVG path element
    align: "#flight-path",
    autoRotate: true,          // Element rotates to follow the path
    alignOrigin: [0.5, 0.5],   // Center of element aligns to path
  },
  duration: 5,
  ease: "power1.inOut",
});
```

---

## 10. Performance & Optimization

### Performance and property cost

Transform and opacity are often good starting points because they can avoid layout. They are not a blanket law, and `filter`, large layers, image sequences, canvas, and WebGL can still be expensive. Profile the actual scene on representative devices; animate layout-affecting properties only when the intended effect warrants the cost and layout remains stable.

Typical tendency only: compositor promotion varies by browser and device, so inspect actual layout/paint work when performance matters.

| Property | GSAP Shorthand | Typical cost |
| --- | --- | --- |
| `transform: translateX/Y` | `x`, `y` | ✅ Composited |
| `transform: scale` | `scale`, `scaleX`, `scaleY` | ✅ Composited |
| `transform: rotate` | `rotation` | ✅ Composited |
| `opacity` | `opacity` | ✅ Composited |
| `filter: blur()` | `filter` | ⚠️ Expensive but composited |
| `width`, `height` | — | ❌ Layout thrash |
| `top`, `left`, `right`, `bottom` | — | ❌ Layout thrash |
| `margin`, `padding` | — | ❌ Layout thrash |
| `border-radius` | — | ❌ Paint only |
| `background-color` | — | ❌ Paint only |

Prefer `x`, `y`, `scale`, `rotation`, and `opacity` for continuous motion when they preserve the desired visual result. There is no universally safe property list; inspect paint/layout cost and visual quality for the actual effect.

### `will-change` Management

```javascript
// Use will-change only when profiling shows a benefit; avoid promoting many layers.
gsap.set(".animated-el", { willChange: "transform, opacity" });

// Remove will-change when the temporary optimization is no longer needed.
tl.eventCallback("onComplete", () => {
  gsap.set(".animated-el", { willChange: "auto" });
});
```

### `gsap.ticker` for Custom Render Loops

```javascript
// Sync with GSAP's rAF ticker instead of your own requestAnimationFrame
gsap.ticker.add((time, deltaTime, frame) => {
  // Custom per-frame logic (cursor follower, parallax, etc.)
  cursor.x += (mouseX - cursor.x) * 0.1;
  cursor.y += (mouseY - cursor.y) * 0.1;
});

// Use gsap.ticker.fps(30) to limit FPS on low-power devices
gsap.ticker.lagSmoothing(500, 33); // Prevent lag spike catch-up
```

### ScrollTrigger Performance

```javascript
// Batch multiple reveals (more efficient than individual ScrollTriggers)
ScrollTrigger.batch(".reveal-item", {
  onEnter: (batch) => gsap.to(batch, {
    opacity: 1,
    y: 0,
    stagger: 0.05,
    ease: "power3.out",
  }),
  start: "top 85%",
});

// Refresh after dynamic content load
ScrollTrigger.refresh();

// On route leave, revert the owning component/route context.
// Avoid a global kill when other components own their own ScrollTriggers.
```

---

## 11. GSAP + React Integration

### The `useGSAP` Hook (Official)

```javascript
import { useGSAP } from "@gsap/react";

function HeroSection() {
  const container = useRef();

  useGSAP(() => {
    // All GSAP code here is auto-scoped to container
    // Auto-reverts on unmount (no manual cleanup needed)
    const tl = gsap.timeline();
    tl.from(".title", { y: 100, opacity: 0, duration: 1 })
      .from(".subtitle", { y: 50, opacity: 0, duration: 0.8 }, "-=0.5");
  }, { scope: container }); // Scope all selectors to this ref

  return (
    <section ref={container}>
      <h1 className="title">Hello</h1>
      <p className="subtitle">World</p>
    </section>
  );
}
```

### Context Cleanup (Manual Alternative)

```javascript
useEffect(() => {
  const ctx = gsap.context(() => {
    // All animations created here are tracked
    gsap.from(".box", { x: -100 });
    ScrollTrigger.create({ /* ... */ });
  }, containerRef);

  return () => ctx.revert(); // Kills ALL animations + ScrollTriggers in context
}, []);
```

In React, scope animations with the project's supported `useGSAP` hook or a `gsap.context()` and clean them up on teardown. Keep DOM event listeners and non-GSAP resources in the same component lifecycle; an animation created later by an event handler must also be added to the owning context when needed.

---

## 12. Creative Recipe Book

### Recipe: Hero Load Sequence

```javascript
const heroTl = gsap.timeline({ delay: 0.3 });

// 1. Preloader counter transitions into heading
heroTl
  .set(".hero", { visibility: "visible" })
  .from(".hero-bg", { scale: 1.3, opacity: 0, duration: 1.5, ease: "power3.out" })
  .from(".hero-title", {
    yPercent: 100,
    duration: 1.2,
    ease: "power4.out",
    stagger: 0.08,  // If SplitText lines
  }, "-=0.8")
  .from(".hero-subtitle", { opacity: 0, y: 30, duration: 0.8 }, "-=0.5")
  .from(".hero-cta", { opacity: 0, scale: 0.9, duration: 0.6, ease: "back.out(1.7)" }, "-=0.3")
  .from(".hero-scroll-hint", { opacity: 0, y: -10, duration: 0.5 }, "-=0.2");
```

### Recipe: Staggered Grid Reveal

```javascript
ScrollTrigger.batch(".grid-item", {
  onEnter: (batch) => gsap.fromTo(batch, 
    { y: 60, opacity: 0, scale: 0.95 },
    { y: 0, opacity: 1, scale: 1, stagger: 0.08, duration: 0.8, ease: "power3.out" }
  ),
  start: "top 90%",
});
```

### Recipe: Cursor Follower (Smooth)

```javascript
const cursor = document.querySelector(".custom-cursor");
let mouseX = 0, mouseY = 0;

window.addEventListener("mousemove", (e) => {
  mouseX = e.clientX;
  mouseY = e.clientY;
});

gsap.ticker.add(() => {
  gsap.set(cursor, {
    x: mouseX,
    y: mouseY,
    xPercent: -50,
    yPercent: -50,
  });
});

// For smooth lag: use gsap.quickTo
const xTo = gsap.quickTo(cursor, "x", { duration: 0.4, ease: "power3.out" });
const yTo = gsap.quickTo(cursor, "y", { duration: 0.4, ease: "power3.out" });

window.addEventListener("mousemove", (e) => {
  xTo(e.clientX);
  yTo(e.clientY);
});
```

### Recipe: Number Counter Animation

```javascript
const counter = { value: 0 };
gsap.to(counter, {
  value: 12500,
  duration: 2,
  ease: "power2.out",
  snap: { value: 1 },          // Round to integer
  onUpdate: () => {
    document.querySelector(".counter").textContent = 
      new Intl.NumberFormat().format(Math.round(counter.value));
  },
  scrollTrigger: {
    trigger: ".counter-section",
    start: "top 70%",
  },
});
```

### Recipe: Image Sequence on Scroll (Apple-style)

```javascript
const frameCount = 120;
const canvas = document.querySelector("#sequence-canvas");
const ctx = canvas.getContext("2d");
const images = [];
const currentFrame = { index: 0 };

// Preload all frames
for (let i = 0; i < frameCount; i++) {
  const img = new Image();
  img.src = `/frames/frame-${String(i).padStart(4, "0")}.webp`;
  images.push(img);
}

gsap.to(currentFrame, {
  index: frameCount - 1,
  snap: "index",
  ease: "none",
  scrollTrigger: {
    trigger: ".sequence-section",
    pin: true,
    scrub: 0.5,
    start: "top top",
    end: "+=500%",
  },
  onUpdate: () => {
    const img = images[Math.round(currentFrame.index)];
    if (img.complete) ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  },
});
```

---

## 13. Utility Functions

### `gsap.utils` Essentials

```javascript
// Map a value from one range to another
gsap.utils.mapRange(0, 1, 100, 500, 0.5); // → 300

// Clamp a value within bounds
gsap.utils.clamp(0, 100, 150); // → 100

// Wrap around (useful for infinite loops)
gsap.utils.wrap(0, 5, 7); // → 2

// Distribute values across elements
gsap.utils.distribute({ base: 0, amount: 1.5, from: "center" });

// Convert NodeList to Array
const elements = gsap.utils.toArray(".item");

// Random value
gsap.utils.random(1, 10, 0.5); // Random between 1–10, snapped to 0.5

// Interpolate between two values
const interp = gsap.utils.interpolate(0, 100);
interp(0.5); // → 50
```

### `gsap.quickTo` & `gsap.quickSetter`

For high-frequency updates (mousemove, scroll), avoid creating new tweens:

```javascript
// quickTo: creates a reusable tween (with easing)
const moveX = gsap.quickTo(".dot", "x", { duration: 0.5, ease: "power3.out" });
const moveY = gsap.quickTo(".dot", "y", { duration: 0.5, ease: "power3.out" });
window.addEventListener("mousemove", (e) => { moveX(e.clientX); moveY(e.clientY); });

// quickSetter: instant set (no easing, maximum performance)
const setX = gsap.quickSetter(".dot", "x", "px");
const setY = gsap.quickSetter(".dot", "y", "px");
```

---

## 14. Anti-Patterns

1. ❌ **Bad**: Chaining `gsap.to()` calls with `delay` instead of timelines.
   ✅ **Good**: Use `gsap.timeline()` with position parameters (`"-=0.3"`, `"<"`).

2. ❌ **Bad**: Creating new tweens on every `mousemove` event.
   ✅ **Good**: Use `gsap.quickTo()` or `gsap.quickSetter()` for high-frequency updates.

3. ❌ **Bad**: Bare `gsap.to()` in React `useEffect` without cleanup.
   ✅ **Good**: Use `useGSAP()` hook or `gsap.context()` with `.revert()` on unmount.

4. ❌ **Bad**: Repeatedly animating layout-affecting properties without checking reflow cost or content stability.
   ✅ **Good**: Prefer transforms/opacity for continuous movement when they preserve the intended result; profile other effects instead of forbidding them categorically.

5. ❌ **Bad**: Treating numeric `scrub` as automatically smoother or better.
   ✅ **Good**: Use `scrub: true` for direct mapping or numeric scrub only when intentional catch-up lag fits the scene; verify both fast and slow input.

6. ❌ **Bad**: Leaving `will-change` on elements permanently.
   ✅ **Good**: Set `willChange: "auto"` in `onComplete` callback after animation finishes.

7. ❌ **Bad**: Leaving stale measurements after a layout/content change or globally killing triggers owned elsewhere.
   ✅ **Good**: Refresh after changes that affect start/end positions; use local component cleanup on route leave.

8. ❌ **Bad**: Assuming split lines remain valid after relevant font or width changes.
   ✅ **Good**: For responsive SplitText layouts, re-split after those changes and clean up/rebuild the associated animation.

---

## Cross-References

- `../../codex-frontend-design/references/motion.md` for user-facing motion intent and fallback.
- `../../codex-frontend-design/references/prototype-pipeline.md` for the UX contract and scene map.
- `../../codex-frontend-design/references/responsive-evidence.md` for route/state/viewport capture and review.
- `frontend-rules.md` for component ownership and dependency direction.
