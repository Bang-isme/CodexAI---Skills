# CSS Architecture

## Scope and Triggers

Use when structuring styling systems, naming conventions, component styling isolation, responsive layout strategy, or theme support.

## Core Principles

- Favor consistency over novelty.
- Use design tokens for all reusable values.
- Keep specificity low and predictable.
- Co-locate styles with features while preserving shared foundations.
- Build responsive and accessible by default.

## Naming Strategies

### BEM

Pattern: `block__element--modifier`

Use when:
- large teams need explicit, readable class semantics
- global stylesheets are unavoidable

Example:
- `.card`
- `.card__title`
- `.card--compact`

### CSS Modules

Use when:
- component-level style isolation is required
- avoiding global name collisions is critical

Rules:
- keep one module file per component or feature fragment
- avoid `:global` unless necessary for third-party overrides

## CSS Variables Architecture

### Token Layers

- Primitive tokens: raw colors, spacing, radius, shadow
- Semantic tokens: `--text-primary`, `--surface-muted`
- Component tokens: `--button-bg`, `--input-border`

### Rule

Do not use primitive values directly in component styles unless within token definitions.

## File Organization

- `styles/tokens.css`
- `styles/base.css`
- `styles/utilities.css`
- `components/<name>/<name>.module.css`

For Tailwind or utility systems, keep an equivalent token source of truth.

## Responsive-First Design

### Breakpoint Strategy

- Mobile-first baseline.
- Add min-width breakpoints incrementally.
- Keep breakpoints centralized.

Recommended set:
- `sm: 640px`
- `md: 768px`
- `lg: 1024px`
- `xl: 1280px`
- `2xl: 1536px`

### Layout Rules

- Use grid/flex primitives, avoid pixel-perfect absolute positioning.
- Prefer content-driven width (`minmax`, `clamp`).
- Limit line length for readability (60-80ch body text).

## Dark Mode Pattern

### Approach

- Theme via root attributes: `[data-theme="dark"]`
- Keep semantic tokens, not duplicated component rules.

Example:
```css
:root {
  --surface-0: #ffffff;
  --text-primary: #111827;
}

[data-theme='dark'] {
  --surface-0: #111827;
  --text-primary: #f9fafb;
}
```

### Rule

Never hardcode light-only colors inside components.

## Container Queries

Use when components must adapt to container width, not viewport width.

Pattern:
```css
.card-grid {
  container-type: inline-size;
}

@container (min-width: 560px) {
  .card-grid-item {
    grid-template-columns: 1fr 1fr;
  }
}
```

## CSS Grid Templates

Common patterns:
- Sidebar + main
- Dashboard cards auto-fit
- Master/detail split

Prefer:
- `grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));`
- `gap` tokens over margins between siblings

## Utility Classes vs Component Classes

- Use utilities for layout primitives and spacing shortcuts.
- Use component classes for semantic, reusable blocks.
- Do not build business semantics solely from utility soup.

## Anti-Patterns

1. Deep descendant selectors (`.a .b .c .d`).
2. `!important` as default conflict resolver.
3. Mixing multiple naming conventions in one codebase.
4. Re-defining same token values per component.
5. Viewport-only responsiveness for reusable components.

## Performance Considerations

- Avoid heavy box-shadow and blur on large surfaces.
- Minimize layout thrashing from JS-driven inline styles.
- Prefer transform/opacity animations over top/left changes.
- Keep critical CSS lean for first render.

## Accessibility Considerations

- Maintain color contrast >= WCAG AA.
- Preserve visible focus indicators.
- Respect reduced motion preference.

Pattern:
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

## Review Checklist

- Are design tokens used consistently?
- Is naming convention documented and followed?
- Are styles component-scoped where possible?
- Is dark mode handled by semantic tokens?
- Are responsive changes mobile-first and minimal?
- Are container queries used where component-driven layout is needed?
