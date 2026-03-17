# Fun Interactive Elements — Playful UI Engineering

## Scope and Triggers

Use this reference when:
- Building interactive, playful, or gamified UI elements.
- Adding micro-interactions, Easter eggs, or delight-driven features.
- Keywords: `interactive`, `fun`, `playful`, `hover effect`, `tilt`, `confetti`, `particle`, `drag`, `ripple`, `Easter egg`, `gamification`, `cursor effect`, `magnetic`, `reveal`.

**Mindset**: These elements exist to surprise and delight. They should feel effortless, fast, and never block the user. If an interaction feels "cute but slow", remove it.

---

## 1. Cursor Effects

### Custom Cursor with Context Awareness

The cursor changes personality based on what it hovers:

```javascript
const cursor = document.querySelector(".cursor");
const cursorDot = document.querySelector(".cursor-dot");

// Smooth follow with gsap.quickTo
const xTo = gsap.quickTo(cursor, "x", { duration: 0.6, ease: "power3.out" });
const yTo = gsap.quickTo(cursor, "y", { duration: 0.6, ease: "power3.out" });
const dotX = gsap.quickTo(cursorDot, "x", { duration: 0.1, ease: "none" });
const dotY = gsap.quickTo(cursorDot, "y", { duration: 0.1, ease: "none" });

window.addEventListener("mousemove", (e) => {
  xTo(e.clientX); yTo(e.clientY);
  dotX(e.clientX); dotY(e.clientY);
});

// Context: link hover → grow + "View" text
document.querySelectorAll("a, button").forEach((el) => {
  el.addEventListener("mouseenter", () => {
    gsap.to(cursor, { scale: 2.5, mixBlendMode: "difference" });
    cursor.dataset.text = el.dataset.cursorText || "View";
  });
  el.addEventListener("mouseleave", () => {
    gsap.to(cursor, { scale: 1, mixBlendMode: "normal" });
    cursor.dataset.text = "";
  });
});

// Context: image hover → expand to frame
document.querySelectorAll("img, .media").forEach((el) => {
  el.addEventListener("mouseenter", () => {
    gsap.to(cursor, { width: 80, height: 80, borderRadius: "8px", opacity: 0.3 });
  });
  el.addEventListener("mouseleave", () => {
    gsap.to(cursor, { width: 20, height: 20, borderRadius: "50%", opacity: 1 });
  });
});
```

```css
.cursor {
  position: fixed;
  top: 0; left: 0;
  width: 20px; height: 20px;
  border: 2px solid var(--brand-primary);
  border-radius: 50%;
  pointer-events: none;
  z-index: 9999;
  transform: translate(-50%, -50%);
  transition: width 0.3s, height 0.3s, border-radius 0.3s;
  mix-blend-mode: difference;
}

.cursor-dot {
  position: fixed;
  top: 0; left: 0;
  width: 6px; height: 6px;
  background: var(--brand-primary);
  border-radius: 50%;
  pointer-events: none;
  z-index: 10000;
  transform: translate(-50%, -50%);
}

/* Hide on touch devices */
@media (hover: none) {
  .cursor, .cursor-dot { display: none; }
}
```

### Cursor Trail (Particle Follow)

```javascript
const trail = [];
const trailCount = 15;

for (let i = 0; i < trailCount; i++) {
  const dot = document.createElement("div");
  dot.className = "trail-dot";
  dot.style.opacity = 1 - i / trailCount;
  dot.style.transform = `scale(${1 - i / trailCount})`;
  document.body.appendChild(dot);
  trail.push(dot);
}

let positions = Array(trailCount).fill({ x: 0, y: 0 });

window.addEventListener("mousemove", (e) => {
  positions[0] = { x: e.clientX, y: e.clientY };
});

gsap.ticker.add(() => {
  for (let i = trail.length - 1; i > 0; i--) {
    positions[i] = {
      x: positions[i].x + (positions[i - 1].x - positions[i].x) * 0.3,
      y: positions[i].y + (positions[i - 1].y - positions[i].y) * 0.3,
    };
    gsap.set(trail[i], { x: positions[i].x, y: positions[i].y });
  }
  gsap.set(trail[0], { x: positions[0].x, y: positions[0].y });
});
```

---

## 2. Card & Element Interactions

### 3D Tilt Card (Vanilla JS)

Cards tilt toward the mouse position, creating a 3D parallax feel:

```javascript
function initTiltCards() {
  document.querySelectorAll(".tilt-card").forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;  // -0.5 to 0.5
      const y = (e.clientY - rect.top) / rect.height - 0.5;

      gsap.to(card, {
        rotateY: x * 20,     // Max 10° tilt
        rotateX: -y * 20,
        transformPerspective: 800,
        ease: "power2.out",
        duration: 0.4,
      });

      // Inner elements parallax
      gsap.to(card.querySelector(".tilt-card__shine"), {
        x: x * 40, y: y * 40, opacity: 0.15,
      });
    });

    card.addEventListener("mouseleave", () => {
      gsap.to(card, { rotateY: 0, rotateX: 0, duration: 0.7, ease: "elastic.out(1, 0.5)" });
      gsap.to(card.querySelector(".tilt-card__shine"), { x: 0, y: 0, opacity: 0 });
    });
  });
}
```

```css
.tilt-card {
  position: relative;
  transform-style: preserve-3d;
  will-change: transform;
}

.tilt-card__shine {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, rgba(255,255,255,0.2), transparent 60%);
  pointer-events: none;
  opacity: 0;
}
```

### Magnetic Button

Button that follows the cursor within a threshold before snapping back:

```javascript
function initMagneticButtons() {
  document.querySelectorAll(".magnetic-btn").forEach((btn) => {
    const threshold = 100; // Activation radius in px

    btn.addEventListener("mousemove", (e) => {
      const rect = btn.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = e.clientX - cx;
      const dy = e.clientY - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < threshold) {
        const pull = 1 - dist / threshold; // 1 at center, 0 at edge
        gsap.to(btn, {
          x: dx * pull * 0.4,
          y: dy * pull * 0.4,
          duration: 0.3,
          ease: "power2.out",
        });
        gsap.to(btn.querySelector("span"), {
          x: dx * pull * 0.2,
          y: dy * pull * 0.2,
        });
      }
    });

    btn.addEventListener("mouseleave", () => {
      gsap.to(btn, { x: 0, y: 0, duration: 0.7, ease: "elastic.out(1, 0.3)" });
      gsap.to(btn.querySelector("span"), { x: 0, y: 0, duration: 0.5 });
    });
  });
}
```

### Ripple Click Effect

```javascript
function createRipple(e) {
  const btn = e.currentTarget;
  const ripple = document.createElement("span");
  const rect = btn.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);

  ripple.style.cssText = `
    position: absolute;
    width: ${size}px; height: ${size}px;
    left: ${e.clientX - rect.left - size / 2}px;
    top: ${e.clientY - rect.top - size / 2}px;
    background: rgba(255,255,255,0.3);
    border-radius: 50%;
    transform: scale(0);
    pointer-events: none;
  `;

  btn.appendChild(ripple);
  gsap.to(ripple, {
    scale: 2.5,
    opacity: 0,
    duration: 0.6,
    ease: "power2.out",
    onComplete: () => ripple.remove(),
  });
}

document.querySelectorAll(".ripple-btn").forEach((btn) => {
  btn.style.position = "relative";
  btn.style.overflow = "hidden";
  btn.addEventListener("click", createRipple);
});
```

---

## 3. Scroll-Driven Interactive Elements

### Parallax Tilt on Scroll

Elements tilt based on their position in the viewport:

```javascript
gsap.utils.toArray(".scroll-tilt").forEach((el) => {
  gsap.to(el, {
    rotateX: -5,
    rotateY: 5,
    scale: 1.02,
    transformPerspective: 1000,
    ease: "none",
    scrollTrigger: {
      trigger: el,
      start: "top bottom",
      end: "bottom top",
      scrub: 1,
    },
  });
});
```

### Reveal-on-Hover Image Gallery

Image is hidden by a colored overlay that splits open on hover:

```css
.reveal-image {
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.reveal-image img {
  transition: transform 0.6s cubic-bezier(0.76, 0, 0.24, 1);
}

.reveal-image:hover img {
  transform: scale(1.08);
}

.reveal-image::before,
.reveal-image::after {
  content: "";
  position: absolute;
  inset: 0;
  background: var(--surface-0);
  z-index: 1;
  transition: transform 0.6s cubic-bezier(0.76, 0, 0.24, 1);
}

.reveal-image::before { transform-origin: left; }
.reveal-image::after  { transform-origin: right; }

.reveal-image:hover::before { transform: scaleX(0); }
.reveal-image:hover::after  { transform: scaleX(0); transition-delay: 0.05s; }
```

### Text Scramble / Decode Effect

Characters scramble randomly before resolving to the final text:

```javascript
class TextScramble {
  constructor(el) {
    this.el = el;
    this.chars = "!<>-_\\/[]{}—=+*^?#________";
    this.frame = 0;
    this.queue = [];
    this.resolve = null;
  }

  setText(newText) {
    const oldText = this.el.textContent;
    const length = Math.max(oldText.length, newText.length);
    this.queue = [];

    for (let i = 0; i < length; i++) {
      const from = oldText[i] || "";
      const to = newText[i] || "";
      const start = Math.floor(Math.random() * 20);
      const end = start + Math.floor(Math.random() * 20);
      this.queue.push({ from, to, start, end });
    }

    cancelAnimationFrame(this.frameRequest);
    this.frame = 0;
    this.update();
    return new Promise((resolve) => (this.resolve = resolve));
  }

  update() {
    let output = "";
    let complete = 0;

    for (let i = 0; i < this.queue.length; i++) {
      const { from, to, start, end } = this.queue[i];
      if (this.frame >= end) {
        complete++;
        output += to;
      } else if (this.frame >= start) {
        output += this.chars[Math.floor(Math.random() * this.chars.length)];
      } else {
        output += from;
      }
    }

    this.el.textContent = output;
    if (complete === this.queue.length) {
      this.resolve?.();
    } else {
      this.frameRequest = requestAnimationFrame(() => this.update());
      this.frame++;
    }
  }
}

// Usage: cycle through phrases
const el = document.querySelector(".scramble-text");
const fx = new TextScramble(el);
const phrases = ["Creative Developer", "Problem Solver", "UI Engineer"];
let counter = 0;

function next() {
  fx.setText(phrases[counter]).then(() => setTimeout(next, 2000));
  counter = (counter + 1) % phrases.length;
}
next();
```

---

## 4. Particle & Confetti Effects

### Confetti Burst on Action

```javascript
function confettiBurst(x, y) {
  const colors = ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff", "#ff6bcb"];
  const count = 30;

  for (let i = 0; i < count; i++) {
    const particle = document.createElement("div");
    particle.style.cssText = `
      position: fixed; width: 8px; height: 8px;
      background: ${colors[Math.floor(Math.random() * colors.length)]};
      border-radius: ${Math.random() > 0.5 ? "50%" : "2px"};
      pointer-events: none; z-index: 9999;
      left: ${x}px; top: ${y}px;
    `;
    document.body.appendChild(particle);

    gsap.to(particle, {
      x: gsap.utils.random(-200, 200),
      y: gsap.utils.random(-300, 100),
      rotation: gsap.utils.random(-360, 360),
      scale: 0,
      opacity: 0,
      duration: gsap.utils.random(0.8, 1.5),
      ease: "power3.out",
      onComplete: () => particle.remove(),
    });
  }
}

// Trigger on button click
document.querySelector(".celebrate-btn").addEventListener("click", (e) => {
  confettiBurst(e.clientX, e.clientY);
});
```

### Floating Particles Background (CSS Only)

```css
.particles {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.particle {
  position: absolute;
  width: 4px; height: 4px;
  background: hsla(200, 80%, 60%, 0.3);
  border-radius: 50%;
  animation: float linear infinite;
}

@keyframes float {
  0%   { transform: translateY(100vh) scale(0); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 1; }
  100% { transform: translateY(-10vh) scale(1); opacity: 0; }
}

/* Generate 20 particles with staggered delays */
.particle:nth-child(1)  { left: 5%;  animation-duration: 12s; animation-delay: 0s; }
.particle:nth-child(2)  { left: 15%; animation-duration: 10s; animation-delay: 1s; }
.particle:nth-child(3)  { left: 25%; animation-duration: 14s; animation-delay: 3s; }
.particle:nth-child(4)  { left: 35%; animation-duration: 11s; animation-delay: 2s; }
.particle:nth-child(5)  { left: 45%; animation-duration: 13s; animation-delay: 4s; }
.particle:nth-child(6)  { left: 55%; animation-duration: 9s;  animation-delay: 1.5s; }
.particle:nth-child(7)  { left: 65%; animation-duration: 15s; animation-delay: 0.5s; }
.particle:nth-child(8)  { left: 75%; animation-duration: 11s; animation-delay: 3.5s; }
.particle:nth-child(9)  { left: 85%; animation-duration: 12s; animation-delay: 2.5s; }
.particle:nth-child(10) { left: 95%; animation-duration: 10s; animation-delay: 5s; }
```

---

## 5. Hover Effects Collection

### Underline Slide (Left to Right)

```css
.link-slide {
  position: relative;
  text-decoration: none;
}
.link-slide::after {
  content: "";
  position: absolute;
  bottom: -2px; left: 0;
  width: 100%; height: 2px;
  background: currentColor;
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.4s cubic-bezier(0.76, 0, 0.24, 1);
}
.link-slide:hover::after {
  transform: scaleX(1);
  transform-origin: left;
}
```

### Background Slide-Fill Button

```css
.btn-fill {
  position: relative;
  padding: 12px 32px;
  border: 2px solid var(--brand-primary);
  background: transparent;
  color: var(--brand-primary);
  overflow: hidden;
  transition: color 0.4s;
  z-index: 1;
}
.btn-fill::before {
  content: "";
  position: absolute;
  inset: 0;
  background: var(--brand-primary);
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.4s cubic-bezier(0.76, 0, 0.24, 1);
  z-index: -1;
}
.btn-fill:hover { color: white; }
.btn-fill:hover::before {
  transform: scaleX(1);
  transform-origin: left;
}
```

### Glitch Text Effect

```css
.glitch {
  position: relative;
  font-weight: 700;
}
.glitch::before, .glitch::after {
  content: attr(data-text);
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
}
.glitch::before {
  color: #ff006e;
  clip-path: inset(0 0 60% 0);
  animation: glitch-top 2s infinite;
}
.glitch::after {
  color: #00f0ff;
  clip-path: inset(60% 0 0 0);
  animation: glitch-bottom 2s infinite;
}
@keyframes glitch-top {
  0%, 90%, 100% { transform: none; }
  92% { transform: translate(-3px, -2px); }
  94% { transform: translate(3px, 1px); }
  96% { transform: translate(-1px, 2px); }
}
@keyframes glitch-bottom {
  0%, 90%, 100% { transform: none; }
  91% { transform: translate(2px, 1px); }
  93% { transform: translate(-3px, -1px); }
  95% { transform: translate(1px, 2px); }
}
```

### Image Reveal on Hover (Clip-Path)

```css
.clip-reveal {
  clip-path: circle(0% at 50% 50%);
  transition: clip-path 0.6s cubic-bezier(0.76, 0, 0.24, 1);
}
.trigger:hover .clip-reveal {
  clip-path: circle(75% at 50% 50%);
}
```

### Marquee / Infinite Scroll Text

```css
.marquee {
  display: flex;
  overflow: hidden;
  white-space: nowrap;
  gap: var(--space-8);
}
.marquee__inner {
  display: flex;
  gap: var(--space-8);
  animation: marquee 20s linear infinite;
}
.marquee:hover .marquee__inner {
  animation-play-state: paused;
}
@keyframes marquee {
  to { transform: translateX(-50%); }
}
```
*HTML: duplicate content twice inside `.marquee__inner` for seamless loop.*

---

## 6. Drag & Drop / Gesture Interactions

### Draggable Elements (GSAP Draggable)

```javascript
import { Draggable } from "gsap/Draggable";
gsap.registerPlugin(Draggable);

Draggable.create(".draggable-card", {
  type: "x,y",
  bounds: ".container",
  inertia: true,               // Throw with momentum
  edgeResistance: 0.7,         // Rubber-band at edges
  onDragStart: function () {
    gsap.to(this.target, { scale: 1.05, boxShadow: "0 20px 40px rgba(0,0,0,0.2)" });
  },
  onDragEnd: function () {
    gsap.to(this.target, { scale: 1, boxShadow: "0 4px 12px rgba(0,0,0,0.1)" });
  },
  snap: {
    x: (val) => Math.round(val / 20) * 20,  // Snap to 20px grid
    y: (val) => Math.round(val / 20) * 20,
  },
});
```

### Swipeable Cards (Tinder-style)

```javascript
Draggable.create(".swipe-card", {
  type: "x,y",
  inertia: true,
  onDrag: function () {
    const rotation = this.x / 10;
    gsap.set(this.target, { rotation });
    // Opacity based on distance
    const distance = Math.abs(this.x);
    if (this.x > 0) {
      gsap.set(".like-indicator", { opacity: distance / 200 });
    } else {
      gsap.set(".nope-indicator", { opacity: distance / 200 });
    }
  },
  onDragEnd: function () {
    if (Math.abs(this.x) > 150) {
      // Swipe away
      gsap.to(this.target, {
        x: this.x > 0 ? 600 : -600,
        rotation: this.x > 0 ? 30 : -30,
        opacity: 0,
        duration: 0.5,
        onComplete: () => this.target.remove(),
      });
    } else {
      // Snap back
      gsap.to(this.target, { x: 0, y: 0, rotation: 0, duration: 0.5, ease: "elastic.out(1, 0.5)" });
    }
  },
});
```

---

## 7. Easter Eggs & Delight Patterns

### Konami Code Detector

```javascript
const konamiCode = [
  "ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown",
  "ArrowLeft", "ArrowRight", "ArrowLeft", "ArrowRight",
  "KeyB", "KeyA",
];
let konamiIndex = 0;

document.addEventListener("keydown", (e) => {
  if (e.code === konamiCode[konamiIndex]) {
    konamiIndex++;
    if (konamiIndex === konamiCode.length) {
      activateEasterEgg();
      konamiIndex = 0;
    }
  } else {
    konamiIndex = 0;
  }
});

function activateEasterEgg() {
  // Confetti explosion!
  confettiBurst(window.innerWidth / 2, window.innerHeight / 2);
  // Or: toggle dark/neon theme, play sound, show hidden message
}
```

### Click Counter Achievement

```javascript
let clickCount = 0;
const achievements = [
  { count: 10, message: "🎯 Sharp Clicker!", color: "#ffd93d" },
  { count: 50, message: "🔥 Click Master!", color: "#ff6b6b" },
  { count: 100, message: "💎 Diamond Hands!", color: "#4d96ff" },
];

document.querySelector(".click-target").addEventListener("click", (e) => {
  clickCount++;
  const achievement = achievements.find((a) => a.count === clickCount);
  if (achievement) {
    showToast(achievement.message, achievement.color);
    confettiBurst(e.clientX, e.clientY);
  }
});
```

### Logo Spin on Click

```javascript
document.querySelector(".logo").addEventListener("click", () => {
  gsap.to(".logo", {
    rotation: "+=360",
    duration: 0.8,
    ease: "power3.inOut",
  });
});
```

---

## 8. Performance & Accessibility Rules

### Performance

1. **No layout thrash**: All effects use `transform` and `opacity` only.
2. **Event throttling**: Use `gsap.ticker` or `requestAnimationFrame` for mousemove — never raw event listeners doing DOM updates.
3. **Clean up**: Remove particles/confetti after animation. Use `onComplete: () => el.remove()`.
4. **Mobile**: Disable custom cursors and heavy hover effects on touch devices (`@media (hover: none)`).
5. **Particle budget**: Max 50 simultaneous particles. More = FPS drop.

### Accessibility

1. **`prefers-reduced-motion`**: Disable all decorative animations:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
  .cursor, .cursor-dot, .trail-dot, .particle { display: none; }
}
```
2. **Keyboard navigation**: Interactive elements must remain keyboard-accessible even with custom cursor/hover effects.
3. **Screen reader**: Easter eggs and decorative elements should have `aria-hidden="true"`.
4. **Focus indicators**: Custom hover effects must NOT remove `:focus-visible` outlines.

---

## Anti-Patterns

1. ❌ **Bad**: Custom cursor on the entire page including form inputs and text selection.
   ✅ **Good**: Disable custom cursor over `input`, `textarea`, `select` (let native cursor work).

2. ❌ **Bad**: Confetti on every button click (overwhelming).
   ✅ **Good**: Reserve confetti for milestone moments (form submit, achievement, purchase).

3. ❌ **Bad**: Heavy particle system running even when off-screen.
   ✅ **Good**: Use `IntersectionObserver` to pause particles when section is not visible.

4. ❌ **Bad**: Tilt effect that makes text unreadable.
   ✅ **Good**: Limit tilt to max 10° and keep text sharp with `backface-visibility: hidden`.

5. ❌ **Bad**: Easter egg that requires interaction to proceed (blocks UX flow).
   ✅ **Good**: Easter eggs are bonuses, never gates. The page must work without them.

---

## Cross-References

- `gsap-mastery.md` for GSAP timeline, ScrollTrigger, and performance optimization.
- `creative-ui-ux.md` for storytelling flow and agency-level design.
- `ui-ux-design-principles.md` for visual hierarchy (interactive elements must not break it).
- `performance-rules.md` for FPS budgets and rendering costs.
- `accessibility-rules.md` for `prefers-reduced-motion` and keyboard navigation.
