# DESIGN.md Spec Essentials

Source studied from the upstream DESIGN.md repository documents `docs/spec.md` and `README.md`.

## Purpose

`DESIGN.md` is a plain-text design contract for coding agents. It combines:

- YAML frontmatter for machine-readable tokens
- ordered markdown sections for rationale and usage guidance

Use it when a project needs persistent design intent that can survive across sessions, contributors, and code generation passes.

## Core Token Schema

```yaml
version: alpha
name: <string>
description: <string>
colors:
  <token-name>: "#RRGGBB"
typography:
  <token-name>:
    fontFamily: <string>
    fontSize: <dimension>
    fontWeight: <number>
    lineHeight: <dimension-or-number>
    letterSpacing: <dimension>
rounded:
  <scale-level>: <dimension>
spacing:
  <scale-level>: <dimension-or-number>
components:
  <component-name>:
    <token-name>: <string-or-token-ref>
```

## Allowed Primitive Types

- Color: `#` + hex in sRGB, for example `#1A1C1E`
- Dimension: value with `px`, `em`, or `rem`
- Token reference: `{colors.primary}`
- Typography object: `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, optional `letterSpacing`, `fontFeature`, `fontVariation`

## Canonical Section Order

Use `##` headings in this order when sections exist:

1. `Overview` or `Brand & Style`
2. `Colors`
3. `Typography`
4. `Layout` or `Layout & Spacing`
5. `Elevation & Depth` or `Elevation`
6. `Shapes`
7. `Components`
8. `Do's and Don'ts`

## Component Tokens

Component entries are where abstract tokens become implementation-ready decisions.

```yaml
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 12px
```

Common properties supported by the upstream CLI:

- `backgroundColor`
- `textColor`
- `typography`
- `rounded`
- `padding`
- `size`
- `height`
- `width`

## Behavior With Unknown Content

- Unknown section heading: preserved, not an error
- Unknown token names: allowed if the values are valid
- Unknown component properties: allowed with a warning
- Duplicate section headings: error

## What The Linter Cares About

The upstream `lint` command validates structure and token references, and it also checks contrast findings in some token combinations. High-value failure cases:

- broken token references
- missing `primary` color when colors exist
- invalid typography objects
- duplicate sections
- out-of-order sections

## Practical Guidance For This Pack

- Keep the contract short but normative. Put tokens in YAML and only rationale in markdown.
- Use `codex-design-system` references to choose palette and typography inputs before filling the contract.
- Treat contract diffs as design changes that deserve review, not as passive documentation churn.
