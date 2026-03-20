# Micro-Interactions

Patterns below synthesize production-safe motion ideas from [Motion](https://motion.dev/), [GSAP](https://gsap.com/), Framer sites, and loading/accessibility guidance from web.dev. Respect reduced-motion preferences before shipping any of them.

## Base Accessibility Guard

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

## 1. Hover Lift
- Use when: clickable cards, result rows, feature tiles.
- Duration/easing: `180ms`, `cubic-bezier(0.2, 0.8, 0.2, 1)`.
- CSS:
```css
.hover-lift {
  transition: transform 180ms cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 180ms ease;
}
.hover-lift:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.18);
}
```
- Avoid when: tables or dense lists would feel jittery.

## 2. Entrance Fade-Up
- Use when: hero blocks, cards, KPI tiles.
- Duration/easing: `420-520ms`, `cubic-bezier(0.22, 1, 0.36, 1)`.
- CSS:
```css
.fade-up {
  opacity: 0;
  transform: translateY(20px);
  animation: fade-up 480ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
@keyframes fade-up {
  to { opacity: 1; transform: translateY(0); }
}
```
- Avoid when: every node in a long page animates on first paint.

## 3. Button Press
- Use when: primary buttons, segmented controls, icon actions.
- Duration/easing: `80-120ms`, `ease-out`.
- CSS:
```css
.pressable {
  transition: transform 100ms ease-out, box-shadow 100ms ease-out;
}
.pressable:active {
  transform: scale(0.975);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.16);
}
```
- Avoid when: the target is destructive or very small.

## 4. Skeleton Shimmer
- Use when: cards, feed items, tables, dashboard widgets that take more than `300ms`.
- Duration/easing: `1.2-1.6s`, linear infinite.
- CSS:
```css
.skeleton {
  background: linear-gradient(90deg, rgba(255,255,255,0.04), rgba(255,255,255,0.16), rgba(255,255,255,0.04));
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}
@keyframes shimmer {
  to { background-position: -200% 0; }
}
```
- Avoid when: the content resolves almost instantly or the skeleton shape does not match the final layout.

## 5. Scroll Reveal
- Use when: storytelling sections, feature rows, landing pages.
- Duration/easing: `360-480ms`, ease-out.
- JS:
```js
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) entry.target.classList.add("is-visible");
  });
}, { threshold: 0.16 });

document.querySelectorAll(".reveal").forEach((node) => observer.observe(node));
```
- CSS:
```css
.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 420ms ease, transform 420ms ease;
}
.reveal.is-visible {
  opacity: 1;
  transform: translateY(0);
}
```
- Avoid when: scrolling containers are nested or content should remain instantly readable.

## 6. Toast Notification
- Use when: save success, undo affordances, lightweight async updates.
- Duration/easing: `220-280ms` enter, `180ms` exit.
- CSS:
```css
.toast {
  transform: translateX(24px);
  opacity: 0;
  animation: toast-in 240ms ease forwards;
}
@keyframes toast-in {
  to { transform: translateX(0); opacity: 1; }
}
```
- Avoid when: the message is blocking or requires detailed explanation.

## 7. Accordion Expand
- Use when: FAQ, filters, settings groups.
- Duration/easing: `220-280ms`, `ease`.
- JS:
```js
document.querySelectorAll("[data-accordion]").forEach((button) => {
  button.addEventListener("click", () => {
    const panel = document.getElementById(button.getAttribute("aria-controls"));
    panel.style.maxHeight = panel.hidden ? `${panel.scrollHeight}px` : "0px";
    panel.hidden = !panel.hidden;
  });
});
```
- CSS:
```css
.accordion__panel {
  overflow: hidden;
  max-height: 0;
  transition: max-height 260ms ease;
}
```
- Avoid when: content height changes significantly after open.

## 8. Focus Glow
- Use when: forms, command palettes, keyboard navigation.
- Duration/easing: `120-180ms`, ease.
- CSS:
```css
.focus-glow:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.18), 0 0 0 6px rgba(56, 189, 248, 0.32);
  transition: box-shadow 140ms ease;
}
```
- Avoid when: you are replacing the browser focus ring with lower-contrast styling.

## 9. Page Transition Crossfade
- Use when: route changes, stepper flows, modal swaps.
- Duration/easing: `180-240ms`, ease.
- CSS:
```css
.page {
  animation: page-in 220ms ease both;
}
@keyframes page-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
```
- Avoid when: every navigation becomes perceptibly slower in a high-frequency workflow.

## 10. Subtle Parallax
- Use when: hero illustrations, decorative layers, background glow fields.
- Duration/easing: frame-synced via `requestAnimationFrame`.
- JS:
```js
const layers = document.querySelectorAll("[data-parallax]");
window.addEventListener("pointermove", (event) => {
  const x = (event.clientX / window.innerWidth - 0.5) * 12;
  const y = (event.clientY / window.innerHeight - 0.5) * 12;
  layers.forEach((node) => {
    const depth = Number(node.dataset.parallax || 1);
    node.style.transform = `translate(${x * depth}px, ${y * depth}px)`;
  });
});
```
- Avoid when: there is heavy GPU usage already or motion sensitivity is a concern.

## 11. Cursor Follow Highlight
- Use when: premium galleries, interactive lists, studio sites.
- Duration/easing: `120-180ms`, ease-out.
- CSS:
```css
.cursor-follow {
  --x: 50%;
  --y: 50%;
  background: radial-gradient(circle at var(--x) var(--y), rgba(255,255,255,0.14), transparent 36%);
  transition: background-position 140ms ease-out;
}
```
- JS:
```js
document.querySelectorAll(".cursor-follow").forEach((node) => {
  node.addEventListener("pointermove", (event) => {
    const rect = node.getBoundingClientRect();
    node.style.setProperty("--x", `${event.clientX - rect.left}px`);
    node.style.setProperty("--y", `${event.clientY - rect.top}px`);
  });
});
```
- Avoid when: the component is primarily form-focused or keyboard-only.

## 12. Magnetic Button
- Use when: showcase CTAs, campaign buttons, playful product marketing.
- Duration/easing: `120ms`, ease-out.
- JS:
```js
document.querySelectorAll("[data-magnetic]").forEach((button) => {
  button.addEventListener("pointermove", (event) => {
    const rect = button.getBoundingClientRect();
    const x = event.clientX - rect.left - rect.width / 2;
    const y = event.clientY - rect.top - rect.height / 2;
    button.style.transform = `translate(${x * 0.18}px, ${y * 0.18}px)`;
  });
  button.addEventListener("pointerleave", () => { button.style.transform = "translate(0, 0)"; });
});
```
- Avoid when: buttons are small, destructive, or need precise cursor stability.

## 13. Text Reveal Wipe
- Use when: hero headlines, section titles, milestone numbers.
- Duration/easing: `500-700ms`, `cubic-bezier(0.22, 1, 0.36, 1)`.
- CSS:
```css
.text-reveal {
  display: inline-block;
  overflow: hidden;
}
.text-reveal > span {
  display: inline-block;
  transform: translateY(110%);
  animation: text-reveal 640ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
@keyframes text-reveal {
  to { transform: translateY(0); }
}
```
- Avoid when: body paragraphs or assistive-tech critical text would be delayed.

## 14. Counter Animate
- Use when: KPI strips, impact numbers, launch stats.
- Duration/easing: `800-1400ms`, ease-out.
- JS:
```js
document.querySelectorAll("[data-count]").forEach((node) => {
  const target = Number(node.dataset.count);
  const start = performance.now();
  const duration = 1200;
  const tick = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    node.textContent = Math.round(target * (1 - Math.pow(1 - progress, 3))).toLocaleString();
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
});
```
- Avoid when: numbers change in real time or exact values matter instantly.

## 15. Progress Bar Sweep
- Use when: uploads, onboarding progress, async tasks with measurable status.
- Duration/easing: proportional to actual progress; use `120ms` transition smoothing.
- CSS:
```css
.progress {
  overflow: clip;
  border-radius: 999px;
}
.progress__fill {
  width: calc(var(--progress, 0) * 1%);
  transition: width 120ms ease-out;
}
```
- Avoid when: you do not have a real progress estimate and can only fake one.
