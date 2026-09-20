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

## Breakpoint honesty

If the source has no media query, container query, or framework responsive class on a new page, the mechanical gate records missing responsive coverage. Utility-first code counts if it encodes breakpoints.

## Touch and pointer

Hit targets on primary actions meet ~44px on the mobile plan. Hover-only instructions are duplicated for touch.
