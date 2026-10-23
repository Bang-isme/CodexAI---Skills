# CodexAI Refinement Dials

Targeted UI refinement passes inside `codex-frontend-design`. Execute one focused pass at a time, then verify with `$visual-gate`.

| Dial | Alias | Focus |
| --- | --- | --- |
| `polish` | `$polish` | Optical alignment, spacing rhythm, border/surface consistency, micro-detail |
| `critique` | `$critique` | Visual hierarchy, information architecture, focal anchor, primary action clarity |
| `audit` | `$audit-ui` | Accessibility, responsive reflow, state completeness, token compliance |
| `animate` | `$animate` | Purposeful choreography, compositor-safe transitions, reduced-motion parity |
| `adapt` | | Cross-viewport layout adaptation (320px–2560px) and container queries |
| `bolder` | | Stronger typographic contrast, focal weight, and spatial asymmetry |
| `quieter` | | Strip competing chrome, decorative noise, and redundant borders |
| `simplify` | | Reduce cognitive load, collapse secondary controls, flatten nested cards |
| `clarify` | | Action-oriented microcopy, honest labels, error recovery guidance |
| `colorize` | | Perceptual OKLCH contrast, tinted neutrals, semantic status hues |
| `delight` | | One product-specific signature micro-interaction with zero task friction |
| `extract` | | Promote repeated UI primitives and magic values into design system tokens |
| `harden` | | Long-label resilience, overflow protection, slow-network/error/empty states |
| `normalize` | | Align drifted components back to the incumbent `DESIGN.md` contract |
| `onboard` | | First-time user orientation, empty-state activation, progressive disclosure |
| `optimize` | | Render performance, layout-shift elimination, asset sizing, animation cleanup |
| `persist-contract` | `$design-md` | Persist approved visual tokens and rationale into `DESIGN.md` |

Invoke with `$refine <dial>` or `.workflows/refine.md`.
