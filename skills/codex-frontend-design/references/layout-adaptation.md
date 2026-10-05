# Layout Adaptation

Adaptation is part of the design contract, not a CSS afterthought.

## Viewports in one pass

Design and verify at least one desktop width and one mobile width in the same review batch. Independent visual review needs both screenshots together.

## Reflow rules

| Surface mode | Narrow viewport |
| --- | --- |
| `persuade` | Claim and primary CTA stay in the first screen; social proof can stack |
| `operate` | Filters and primary table/list remain reachable; secondary nav collapses |
| `read` | Measure stays readable; side nav becomes in-page or drawer |
| `experience` | Atmosphere can crop; navigation cannot disappear |

## Content-safe layout rules

Write the layout contract as behavior across content and widths, not as a screenshot's pixel coordinates. For substantial changes, specify the minimum width/ordering of the main regions, which regions may stack or collapse, and how dense content behaves.

- Use intrinsic sizing for flexible tracks, such as `minmax(0, 1fr)`, and allow grid/flex children to shrink with `min-width: 0` where needed.
- Let text and data rows grow vertically. Avoid fixed heights for variable content; use truncation only when the full value remains available through an intentional disclosure.
- Keep media in a declared aspect ratio and choose crop/fit behavior for each layout. Do not let media dimensions decide the width of neighboring content.
- Give tables a local horizontal-scroll region only when preserving column comparison is the best narrow-screen task flow; otherwise recompose rows while retaining labels and reading order.
- Use absolute positioning for decoration, not essential content or controls. Keep primary actions in normal flow and reachable at every target width.
- Derive breakpoints from the repository's existing system and observed content fit. Change a breakpoint only when a specific composition fails there and verify just below, at, and just above it.

For a risky layout change, implement the new composition on one representative route or component first. Check realistic long labels, data, empty/loading/error states, and the narrow layout before extending a shared change to other consumers. If a **must hold** item in the layout contract fails, correct or roll back that structural change before polishing it.

## Breakpoint honesty

If the source has no media query, container query, or framework responsive class on a new page, the mechanical gate records missing responsive coverage. Utility-first code counts if it encodes breakpoints.

## Touch and pointer

Hit targets on primary actions meet ~44px on the mobile plan. Hover-only instructions are duplicated for touch.
