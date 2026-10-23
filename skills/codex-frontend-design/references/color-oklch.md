# Color Architecture with Perceptual OKLCH

Use `oklch(Lightness Chroma Hue)` for all new color tokens. Unlike hex or RGB, OKLCH is perceptually uniform: changing hue at the same lightness (`L`) preserves perceived contrast and visual weight.

---

## 1. Core Principles

1. **Tint Neutrals Toward the Brand Hue:** Never use dead achromatic grays (`#808080`, `#e5e5e5`) or pure `#000000` / `#ffffff`. Add a subtle chroma (`0.005–0.025`) at the brand's hue angle so surfaces, borders, and text feel cohesive.
2. **Layered Surface Architecture (Elevation by Lightness, Not Heavy Shadows):**
   - `--surface-canvas`: Base page background
   - `--surface-1`: Primary content container / table / panel
   - `--surface-2`: Subtle recessed well, code block, or secondary group
   - `--surface-elevated`: Popover, modal, or sticky bar
3. **One Primary Action Hue:** Reserve high chroma (`0.14–0.22`) for the single primary interactive accent and semantic status signals (`success`, `warning`, `danger`). Everything else stays quiet.
4. **Reject the Default "AI Slop" Palette:** Never default to `#007bff` / `#3b82f6` blue or dark-mode purple-to-cyan neon gradients unless the brand contract explicitly mandates them.

---

## 2. Canonical OKLCH Token Architecture (Light & Dark Polarity)

```css
:root {
  color-scheme: light;
  --brand-hue: 255;       /* Customize per product identity (e.g., 25=terracotta, 155=forest, 255=cobalt) */

  /* Surfaces */
  --surface-canvas: oklch(0.985 0.004 var(--brand-hue));
  --surface-1: oklch(0.998 0.002 var(--brand-hue));
  --surface-2: oklch(0.955 0.008 var(--brand-hue));
  --surface-elevated: oklch(1 0 0);

  /* Ink / Typography Hierarchy */
  --ink-primary: oklch(0.18 0.02 var(--brand-hue));
  --ink-secondary: oklch(0.42 0.02 var(--brand-hue));
  --ink-muted: oklch(0.56 0.015 var(--brand-hue));

  /* Structural Hairlines */
  --border-subtle: oklch(0.89 0.01 var(--brand-hue));
  --border-strong: oklch(0.76 0.018 var(--brand-hue));

  /* Primary Action & Focus */
  --action-primary: oklch(0.48 0.16 var(--brand-hue));
  --action-primary-hover: oklch(0.42 0.17 var(--brand-hue));
  --action-primary-fg: oklch(0.99 0.005 var(--brand-hue));
  --focus-ring: oklch(0.55 0.18 var(--brand-hue) / 0.35);

  /* Semantic Status (Perceptually Balanced) */
  --status-success: oklch(0.52 0.14 155);
  --status-success-bg: oklch(0.95 0.03 155);
  --status-warn: oklch(0.62 0.15 75);
  --status-warn-bg: oklch(0.96 0.04 75);
  --status-danger: oklch(0.54 0.19 25);
  --status-danger-bg: oklch(0.95 0.03 25);
}

[data-theme="dark"] {
  color-scheme: dark;
  /* Dark mode elevates surfaces by stepping Lightness UP (0.14 -> 0.18 -> 0.22) */
  --surface-canvas: oklch(0.14 0.012 var(--brand-hue));
  --surface-1: oklch(0.18 0.015 var(--brand-hue));
  --surface-2: oklch(0.22 0.018 var(--brand-hue));
  --surface-elevated: oklch(0.25 0.02 var(--brand-hue));

  --ink-primary: oklch(0.95 0.008 var(--brand-hue));
  --ink-secondary: oklch(0.74 0.014 var(--brand-hue));
  --ink-muted: oklch(0.58 0.012 var(--brand-hue));

  --border-subtle: oklch(0.27 0.016 var(--brand-hue));
  --border-strong: oklch(0.38 0.02 var(--brand-hue));

  --action-primary: oklch(0.66 0.15 var(--brand-hue));
  --action-primary-hover: oklch(0.72 0.14 var(--brand-hue));
  --action-primary-fg: oklch(0.14 0.02 var(--brand-hue));
}
```

---

## 3. Contrast & Polarity Rules

- **Lightness Delta (`ΔL`) for Legibility:**
  - Body text (`--ink-primary`) vs background (`--surface-canvas` / `--surface-1`): keep `|ΔL| >= 0.65` (exceeds WCAG AA 4.5:1).
  - Secondary text (`--ink-secondary`) vs background: keep `|ΔL| >= 0.48`.
- **Dark Mode Depth:** In dark mode, drop shadows are barely visible. Communicate elevation by stepping surface lightness **upward** (`L: 0.14 -> 0.18 -> 0.22`) and pairing with a `1px` top/outer border (`--border-subtle`).
- `DESIGN.md` contracts support both `oklch(...)` and `#RRGGBB` hex tokens.
