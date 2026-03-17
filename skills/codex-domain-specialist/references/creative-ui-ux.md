# Creative UI/UX & Interactive Design

## Scope and Triggers

Use this reference when building **high-impact, agency-level websites, landing pages, or portfolios**. 
Primary triggers:
- Keywords: `GSAP`, `Three.js`, `WebGL`, `Framer Motion`, `Awwwards`, `FWA`, `Creative`, `ScrollTrigger`.
- Requests for "wow factor", "smooth animations", "storytelling", or "premium feel".
- Building marketing pages, immersive experiences, or product showcases.

**Crucial Mindset Shift**: When this context is loaded, stop thinking like an "Enterprise Dashboard Developer". Stop thinking in default Bootstrap/Tailwind columns. Start thinking like a **Creative Developer**. Prioritize emotional impact, motion fluidity, typographic rhythm, and spatial design.

---

## 1. The Storytelling Flow (Narrative UI)

A creative landing page is an interactive story. Do not stack generic sections. Connect them.

### Structure of an Immersive Page:

> **CRITICAL: Each step below = exactly ONE viewport (100vh).** No section should require scrolling within itself. If content overflows, it means there is too much content — split or simplify. See `ui-ux-design-principles.md` section 6 for the Content Budget Table.

1. **The Hook (Hero)**: Needs a jaw-dropping visual (3D, kinetic typography, or WebGL particle system) and a master animation sequence on load. **Content budget**: 1 heading + 1 subtitle + 1 CTA + 1 visual. NO stats, NO bullet lists, NO tag badges.
2. **The Descent (Scroll Start)**: As the user scrolls, the hero should gracefully fade, scale, or mask out. Use `ScrollTrigger` to pin the background and transition narrative text.
3. **The Proof (Value Prop)**: Horizontal scrolling sections or sticky-stacked cards. Do not use standard 3-column grids. Break the grid. **Max 4 cards per viewport.**
4. **The Climax (Interactive Feature)**: A draggable WebGL slider, a 3D model that rotates on scroll, or a cursor-reveal masking effect.
5. **The Resolution (Footer/CTA)**: A massive, magnetic typographic CTA that feels satisfying to click.

---

## 2. Animation Orchestration (GSAP & Motion)

Janky animations ruin the illusion. Motion must be purposeful, easing must be refined.

### The "Agency" Easing Signature
Never use `linear` or default `ease-in-out` for UI elements.
```javascript
// GSAP Custom Ease for premium feel
gsap.registerPlugin(CustomEase);
CustomEase.create("premium", "0.76, 0, 0.24, 1"); // Apple/Stripe-esque snap
CustomEase.create("fluid", "0.25, 1, 0.5, 1"); // Smooth, floating deceleration
```

### Staggering & Text Reveal
Text should never just "appear". It should reveal.
```javascript
// The classic SplitText + mask reveal
const lines = new SplitText(".title", { type: "lines" });
gsap.from(lines.lines, {
  yPercent: 100,
  opacity: 0,
  stagger: 0.05,
  ease: "premium",
  duration: 1.2,
  scrollTrigger: {
    trigger: ".title",
    start: "top 80%",
  }
});
```
*Note: Always set `overflow: hidden` on the text wrapper to create the masking effect.*

### ScrollTrigger Golden Rules
1. **Don't animate everything at once.** Tie animations to the exact scroll position (`scrub: true` or `scrub: 1` for smoothing).
2. **Pinning**: Use `pin: true` for storytelling blocks where the user reads while the background evolves (e.g., Apple product pages).
3. **Always use Lenis or Locomotive Scroll**. Smooth scrolling is mandatory for a premium feel. Avoid native janky scrolling for heavy animated pages.

---

## 3. Typography & Micro-Interactions

Typography is the interface. Make it massive, make it kinetic.

### Typographic Rhythm
- **Scale**: Don't use standard `h1` sizes (32px). Use viewport units (`10vw`, `12vw`). Text should bleed off the screen or wrap tightly.
- **Contrast**: Mix a massive, bold Sans-serif (e.g., `Clash Display`, `Oswald`) with a delicate, italic Serif (e.g., `Playfair Display`, `PP Editorial New`).

### The Custom Cursor & Magnetic Button
Hide the default cursor. Create a fluid, lagging custom cursor that reacts to elements.
```javascript
// Magnetic Button Logic
button.addEventListener("mousemove", (e) => {
  const rect = button.getBoundingClientRect();
  const x = e.clientX - rect.left - rect.width / 2;
  const y = e.clientY - rect.top - rect.height / 2;
  
  gsap.to(button, { x: x * 0.3, y: y * 0.3, duration: 0.4, ease: "power2.out" });
  gsap.to(cursor, { scale: 1.5, mixBlendMode: 'difference' }); // React to button
});

button.addEventListener("mouseleave", () => {
  gsap.to(button, { x: 0, y: 0, duration: 0.7, ease: "elastic.out(1, 0.3)" });
  gsap.to(cursor, { scale: 1, mixBlendMode: 'normal' });
});
```

---

## 4. Advanced CSS Techniques

Rely on CSS for rendering performance before reaching for JS.

### Glassmorphism & Depth
```css
.glass-panel {
  background: rgba(255, 255, 255, 0.05); /* Barely visible */
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 30px 60px rgba(0,0,0,0.12); /* Deep, soft shadow */
}
```

### Clip-Path & Mask Image Reveal
Used for image transitions and hover reveals.
```css
.image-reveal {
  clip-path: polygon(0 100%, 100% 100%, 100% 100%, 0 100%);
  transition: clip-path 1.2s cubic-bezier(0.76, 0, 0.24, 1);
}
.image-reveal.is-in-view {
  clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%);
}
```

---

## 5. WebGL & Three.js Integration

3D elevates a site from "good" to "world-class".

### Architecture Rules for React Three Fiber (R3F)
1. **Never render multiple canvases**. Use a single full-screen `<Canvas>` fixed to the background. Use the `<View>` component (drei) to map 3D scenes to DOM elements.
2. **HTML Overlay**: Keep UI (text, buttons) strictly in the HTML DOM. Do not build UI in WebGL. Sync HTML scroll position with the 3D camera.
3. **Performance Budget**: Keep draw calls under 100. Limit lights (use baked lighting/matcaps where possible). Always use `dpr={[1, 2]}` to prevent lag on retina displays.

### Example: Scroll-Driven 3D Model
```jsx
// R3F sync with GSAP ScrollTrigger
useFrame(() => {
  // Map scroll progress (0 to 1) to model rotation
  const scrollValue = document.documentElement.scrollTop / (document.documentElement.scrollHeight - window.innerHeight);
  modelGroup.current.rotation.y = THREE.MathUtils.lerp(
    modelGroup.current.rotation.y, 
    scrollValue * Math.PI * 2, 
    0.1 // Smooth interpolation
  );
});
```

---

## 6. Anti-Patterns (The "Agency Taboo" List)

1. ❌ **Bad**: Using standard Bootstrap/Tailwind shadows (`shadow-md`).
   ✅ **Good**: Use layered, soft, colored shadows. Provide depth, not just a border.
2. ❌ **Bad**: Animating `top`, `left`, `width`, `height`.
   ✅ **Good**: Animate ONLY `transform` (translate, scale, rotate) and `opacity` to avoid layout thrashing and keep 60fps.
3. ❌ **Bad**: Forcing users to wait for a 5-second generic spinner.
   ✅ **Good**: Animate the preloader as part of the story. The preloader should seamlessly transition into the Hero section (e.g., loading counter becomes the main heading).
4. ❌ **Bad**: Scroll-jacking that breaks trackpad behavior.
   ✅ **Good**: Use Lenis scroll. It preserves native scroll mechanics while applying friction and easing.
5. ❌ **Bad**: Stuffing 15 animations into the viewport at once.
   ✅ **Good**: Orchestrate. If a 3D model is moving, keep text still. Direct the user's eye.

## Cross-References
- `gsap-mastery.md` for deep GSAP engineering: timelines, easing, ScrollTrigger, SplitText, Flip, performance, and React integration.
- `ui-ux-design-principles.md` for visual hierarchy, color theory, and typography fundamentals.
- `performance-rules.md` (Crucial: 60fps is mandatory for creative sites. Jank kills the vibe).
- `css-architecture.md` (For structuring design tokens).
