# CodexAI Proprietary Frontend Craft Recipes

Use these native CodexAI implementation recipes only when the approved UX contract or design brief calls for them. Every recipe prioritizes layout stability, zero-jank compositor transforms, perceptual OKLCH tokens, and full `prefers-reduced-motion` parity.

---

## 1. Layered Optical Elevation (No Muddy Shadows)

Replace single heavy drop-shadows with a 1px directional border + dual-layer ambient/key shadow tinted toward the surface hue:

```css
:root {
  --surface-card: oklch(0.99 0.004 250);
  --border-subtle: oklch(0.88 0.01 250 / 0.65);
  --shadow-elevation-1:
    0 1px 2px oklch(0.18 0.02 250 / 0.05),
    0 8px 24px -4px oklch(0.18 0.02 250 / 0.07);
  --shadow-elevation-2:
    0 2px 4px oklch(0.18 0.02 250 / 0.06),
    0 18px 40px -8px oklch(0.18 0.02 250 / 0.12);
}

.surface-elevated {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-elevation-1);
  transition: transform 180ms cubic-bezier(0.22, 1, 0.36, 1),
              box-shadow 180ms cubic-bezier(0.22, 1, 0.36, 1);
}
```

The 1px border owns the edge. Both shadow layers fall downward, so the border and the shadow do not compete on the same edge. If they trace the same edge, drop one of them.

---

## 2. Intrinsic Asymmetric Grid (Anti-Bento-Soup)

When content items have unequal hierarchy (one primary anchor + supporting context), use a 12-column intrinsic grid with `minmax(0, 1fr)` so long labels or code blocks never force horizontal overflow:

```css
.editorial-split-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: clamp(1rem, 2.2vw, 2rem);
  align-items: start;
}

.editorial-split-grid__primary {
  grid-column: span 7;
  min-width: 0;
}

.editorial-split-grid__secondary {
  grid-column: span 5;
  min-width: 0;
}

@media (max-width: 900px) {
  .editorial-split-grid__primary,
  .editorial-split-grid__secondary {
    grid-column: 1 / -1;
  }
}
```

---

## 3. Zero-Layout-Shift Collapsible Disclosure

Never animate `height` or `max-height` directly. Use CSS Grid `grid-template-rows: 0fr -> 1fr` for deterministic accordion/disclosure transitions:

```css
.disclosure-panel {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 240ms cubic-bezier(0.22, 1, 0.36, 1);
}

.disclosure-panel[data-state="open"] {
  grid-template-rows: 1fr;
}

.disclosure-panel__inner {
  overflow: hidden;
  min-height: 0;
}

@media (prefers-reduced-motion: reduce) {
  .disclosure-panel {
    transition: none;
  }
}
```

---

## 4. Restrained Staggered Entrance Choreography

Limit page-load choreography to the primary viewport focal cluster (3–4 elements max, total duration under 650ms):

```css
@keyframes codex-enter-rise {
  from {
    opacity: 0;
    transform: translate3d(0, 12px, 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

.choreo-item {
  animation: codex-enter-rise 420ms cubic-bezier(0.16, 1, 0.3, 1) both;
  animation-delay: calc(var(--stagger-index, 0) * 65ms);
}

@media (prefers-reduced-motion: reduce) {
  .choreo-item {
    animation: none;
    opacity: 1;
    transform: none;
  }
}
```

---

## 5. High-Contrast Translucent Surface (Controlled Chrome)

Use translucent chrome only on persistent navigation headers or floating command bars where spatial continuity behind the bar aids orientation—never on every content card:

```css
.persistent-chrome-bar {
  background: color-mix(in oklch, var(--surface-canvas) 84%, transparent);
  backdrop-filter: blur(12px) saturate(140%);
  -webkit-backdrop-filter: blur(12px) saturate(140%);
  border-bottom: 1px solid var(--border-subtle);
}

@supports not (backdrop-filter: blur(1px)) {
  .persistent-chrome-bar {
    background: var(--surface-canvas);
  }
}
```

---

## 6. Numeric Craft Constants

Use these constants when a recipe needs a number. They are implementation limits, not decoration targets.

### Border and shadow

A border and a shadow must not compete on the same edge. The border is the edge. The shadow is offset off that edge. Do not stack a 1px outline and a contact shadow that redraws the same side.

### Corner radius and control height

Radius scale: `8px` / `14px` / `24px`. Controls that receive a click or a tap use a height of at least `44px`. Do not pair a `24px` radius with a control shorter than that height; the ends become pills that miss the hit target.

### One-pixel gradient border

A gradient border is `1px`. Every color stop stays under opacity `0.4` (stop opacity `< 0.4`). A stop at `0.4` or above reads as a second solid edge.

```css
.gradient-edge {
  border: 1px solid transparent;
  background:
    linear-gradient(var(--surface-card), var(--surface-card)) padding-box,
    linear-gradient(oklch(0.72 0.02 250 / 0.35), oklch(0.72 0.02 250 / 0.12)) border-box;
}
```

### Progressive blur mask stack

Blur steps resolve downward and finish at `0px`. Do not leave the top step in place after the reveal.

```css
.progressive-blur {
  --blur-stack: 10px, 4px, 0px;
}
```

### Loader hold

Suppress a spinner when the wait is under `150ms`. Once the spinner is shown, hold it for `400–600ms` so it does not flash off on the next frame. A hold shorter than `400ms` blinks. A hold longer than `600ms` makes a finished response look stuck.

### Pointer trails

Pointer trails emit a sample by distance traveled. A stationary cursor never emits on a timer. If the pointer has not moved, the trail adds no point. Prefer the native cursor unless the brief gives the trail a product job.
