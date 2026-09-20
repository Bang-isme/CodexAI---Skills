# Anti-Patterns

These are the recurring mistakes that make engineer-built UIs feel generic. Each section shows the wrong move, the fix, and the design principle being violated.

## 1. Default Blue Syndrome
- Problem: Reaching for `#007bff`, `#2196F3`, or `#3B82F6` by reflex makes the product feel like a starter template.
- Wrong:
```css
.button-primary {
  background: #007bff;
  color: #fff;
}
```
- Better:
```css
.button-primary {
  background: #22d3ee;
  color: #0b1020;
  box-shadow: 0 14px 32px rgba(34, 211, 238, 0.28);
}
```
- Violated principle: intentional palette selection.

## 2. Card Soup
- Problem: Ten identical cards in a grid erase hierarchy and make all content feel equally important.
- Wrong:
```css
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.card { min-height: 220px; }
```
- Better:
```css
.grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 24px;
}
.card--hero { grid-column: span 7; min-height: 360px; }
.card--side { grid-column: span 5; }
```
- Violated principle: visual hierarchy.

## 3. Shadow Abuse
- Problem: Stacking multiple fuzzy shadows on every component makes the interface muddy instead of premium.
- Wrong:
```css
.card {
  box-shadow: 0 2px 4px rgba(0,0,0,0.1), 0 8px 24px rgba(0,0,0,0.18);
}
```
- Better:
```css
.card {
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.12);
  border: 1px solid rgba(148, 163, 184, 0.18);
}
```
- Violated principle: depth discipline.

## 4. Border-Radius Monoculture
- Problem: Giving everything `8px` radius is the fastest route to "generic SaaS template."
- Wrong:
```css
.button, .card, .input, .modal {
  border-radius: 8px;
}
```
- Better:
```css
:root {
  --radius-sm: 12px;
  --radius-md: 18px;
  --radius-lg: 28px;
}
.button { border-radius: var(--radius-sm); }
.input { border-radius: var(--radius-sm); }
.card { border-radius: var(--radius-md); }
.modal { border-radius: var(--radius-lg); }
```
- Violated principle: component rhythm and scale.

## 5. Text Wall
- Problem: Large copy blocks without hierarchy or line-length control create fatigue.
- Wrong:
```css
.content p {
  max-width: none;
  line-height: 1.4;
}
```
- Better:
```css
.content {
  max-width: 68ch;
}
.content p {
  line-height: 1.7;
  margin-block: 0 1rem;
}
.content h2 { margin-top: 3rem; }
```
- Violated principle: readability and rhythm.

## 6. Icon Confetti
- Problem: Throwing icons next to every label creates noise and weakens real signals.
- Wrong:
```html
<li><span>⚡</span> Fast onboarding</li>
<li><span>⭐</span> Premium support</li>
<li><span>✅</span> Secure by default</li>
```
- Better:
```html
<li class="feature-row">
  <strong>Fast onboarding</strong>
  <span>Start in under 10 minutes with presets and templates.</span>
</li>
```
- Violated principle: meaningful emphasis.

## 7. Rainbow Palette
- Problem: Too many saturated colors destroy focus and make the product look like a template mashup.
- Wrong:
```css
.badge-a { background: #ef4444; }
.badge-b { background: #eab308; }
.badge-c { background: #10b981; }
.badge-d { background: #3b82f6; }
```
- Better:
```css
:root {
  --accent: #22d3ee;
  --accent-soft: rgba(34, 211, 238, 0.14);
}
.badge {
  background: var(--accent-soft);
  color: #0b1020;
}
```
- Violated principle: palette restraint.

## 8. Tiny Text
- Problem: `12px` body copy on desktop feels dense, cheap, and often fails accessibility.
- Wrong:
```css
body {
  font-size: 12px;
}
```
- Better:
```css
body {
  font-size: 16px;
  line-height: 1.6;
}
.meta {
  font-size: 0.875rem;
}
```
- Violated principle: accessible typography.

## 9. No Whitespace
- Problem: When every component touches the next, the interface feels rushed and low-trust.
- Wrong:
```css
.section {
  padding: 16px;
}
```
- Better:
```css
.section {
  padding: clamp(64px, 8vw, 112px) clamp(24px, 6vw, 80px);
}
```
- Violated principle: whitespace and pacing.

## 10. Spacing Roulette
- Problem: Random `13px`, `19px`, `27px`, and `31px` gaps make the UI feel inconsistent even when users cannot explain why.
- Wrong:
```css
.card { padding: 19px; }
.card + .card { margin-top: 27px; }
.form-row { gap: 13px; }
```
- Better:
```css
:root {
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
}
.card { padding: var(--space-6); }
.card + .card { margin-top: var(--space-8); }
.form-row { gap: var(--space-4); }
```
- Violated principle: rhythm through repetition.

## 11. Generic Stock Hero
- Problem: A random smiling-team stock image disconnects from the product and collapses credibility.
- Wrong:
```html
<section class="hero">
  <img src="/stock/team-happy.jpg" alt="">
</section>
```
- Better:
```html
<section class="hero">
  <figure class="product-shot">
    <img src="/img/dashboard-overview.png" alt="Dashboard showing workflow automation metrics">
  </figure>
</section>
```
- Violated principle: relevance and proof.

## 12. Button Style Explosion
- Problem: Every button variant trying to be unique removes hierarchy instead of creating it.
- Wrong:
```css
.btn-a { background: #2563eb; border-radius: 8px; }
.btn-b { background: #10b981; border-radius: 999px; }
.btn-c { background: #f59e0b; border-radius: 4px; }
```
- Better:
```css
.btn-primary {
  background: #22d3ee;
  color: #0b1020;
}
.btn-secondary {
  background: transparent;
  border: 1px solid rgba(148, 163, 184, 0.28);
  color: inherit;
}
```
- Violated principle: hierarchy and consistency.

## 13. Modal Abuse
- Problem: Pushing every task into a modal traps the user, kills context, and often breaks accessibility.
- Wrong:
```js
openModal("edit-profile");
openModal("change-password");
openModal("billing");
```
- Better:
```html
<div class="settings-shell">
  <aside class="settings-shell__nav"></aside>
  <section class="settings-shell__panel"></section>
</div>
```
- Violated principle: progressive disclosure and task continuity.

## 14. Infinite Scroll Without Purpose
- Problem: Infinite scroll is often added because it feels modern, not because it helps the task.
- Wrong:
```js
window.addEventListener("scroll", loadMoreItems);
```
- Better:
```html
<nav class="results-nav">
  <button class="btn-secondary">Load 20 more</button>
</nav>
```
- Violated principle: user control and orientation.

## 15. Spinner-Only Loading
- Problem: A lone spinner says "wait" but provides no structure or confidence about what is coming.
- Wrong:
```html
<div class="spinner"></div>
```
- Better:
```html
<article class="skeleton-card">
  <div class="skeleton skeleton-title"></div>
  <div class="skeleton skeleton-line"></div>
  <div class="skeleton skeleton-line"></div>
</article>
```
```css
.skeleton-card {
  display: grid;
  gap: 12px;
  padding: 24px;
}
```
- Violated principle: perceived performance and structure.
