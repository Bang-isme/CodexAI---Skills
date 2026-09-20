---
version: alpha
name: {{name}}
description: {{description}}
colors:
  primary: "oklch(0.55 0.14 40)"
  secondary: "oklch(0.45 0.02 85)"
  tertiary: "oklch(0.62 0.08 160)"
  neutral: "oklch(0.97 0.01 85)"
  surface: "oklch(0.99 0.008 85)"
  text: "oklch(0.22 0.03 85)"
typography:
  display-xl:
    fontFamily: "Fraunces"
    fontSize: 3.5rem
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: -0.03em
  heading-lg:
    fontFamily: "Fraunces"
    fontSize: 2rem
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: -0.02em
  body-md:
    fontFamily: "Source Serif 4"
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.6
  label-sm:
    fontFamily: "IBM Plex Mono"
    fontSize: 0.875rem
    fontWeight: 500
    lineHeight: 1.4
rounded:
  sm: 8px
  md: 14px
  lg: 24px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 12px
  card-default:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: 24px
---

## Overview

{{overview}}

## Colors

- **Primary (`#111827`)** anchors headlines, text-heavy surfaces, and deep contrast states.
- **Secondary (`#6B7280`)** supports borders, captions, and lower-emphasis utility content.
- **Tertiary (`#0F766E`)** is the main interaction accent for buttons, focus moments, and active UI states.
- **Neutral (`#F8FAFC`)** sets the main canvas with a clean but not sterile background tone.
- **Surface (`#FFFFFF`)** is reserved for raised surfaces and content containers.
- **Text (`#111827`)** is the default reading color across the interface.

## Typography

- **Display and heading** levels use Fraunces for a specific editorial voice.
- **Body and labels** use Source Serif 4; never default to Inter, Space Grotesk, or system-ui-only.
- Keep label sizes tight and consistent; do not introduce ad-hoc font sizes outside the token map unless the contract is updated.

## Layout

- Use an 8px base spacing rhythm with a narrow content width for reading surfaces and wider rails for dashboard or data-heavy screens.
- Favor asymmetric hierarchy over perfectly even grids so the most important element is obvious on first scan.

## Elevation & Depth

- Depth should come primarily from contrast, surface layering, and one disciplined shadow recipe rather than stacked random shadows.
- Use heavier elevation only for menus, dialogs, and transient overlays that need separation from the page plane.

## Shapes

- Rounded corners should stay within the defined `rounded` scale.
- Use larger radii for containers and smaller radii for controls to create hierarchy without visual noise.

## Components

- Primary actions inherit `button-primary` tokens and should remain visually dominant.
- Default cards inherit `card-default` tokens and should feel structural, not ornamental.
- Add additional component token entries here once a surface becomes a repeating pattern.

## Do's and Don'ts

- Do keep tokens authoritative and prose explanatory.
- Do update component tokens when repeated UI patterns emerge.
- Do lint the contract before exporting or coding from it.
- Do not add duplicate sections or move them out of canonical order.
- Do not let implementation drift outrun the contract for long-lived products.
