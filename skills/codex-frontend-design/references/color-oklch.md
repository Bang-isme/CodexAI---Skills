# Color with OKLCH

Prefer `oklch()` for new palettes. Tint neutrals toward the brand hue. Avoid pure `#000` / `#fff`.

```css
:root {
  --bg: oklch(0.99 0.01 85);
  --fg: oklch(0.22 0.03 85);
  --accent: oklch(0.55 0.14 35);
  --muted: oklch(0.45 0.02 85);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: oklch(0.22 0.02 85);
    --fg: oklch(0.95 0.01 85);
  }
}
```

Do not use cyan-on-dark plus purple-to-blue gradients as the default "AI" palette. `DESIGN.md` may store either hex or `oklch()`.
