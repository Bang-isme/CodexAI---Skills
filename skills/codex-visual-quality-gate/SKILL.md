---
name: codex-visual-quality-gate
description: Use after UI implementation for mechanical source checks and a rendered or fresh-eyes review.
load_priority: on-demand
version: "18.1.0"
---

## TL;DR
Mechanical checks are source evidence, not aesthetic scores. A valid approval requires complete route × viewport × state capture evidence and a recorded review of every stitched page and source slice. Missing browser, screenshots, coverage, provenance, or review is `DEGRADED`; high-confidence defects or gaps fail.

## Activation
Substantial UI delivery or `$visual-gate`. Skip backend-only work.

## Gate workflow

1. Exercise every UX-contract flow and declared route/state, including important interaction/error/empty/success paths. Where they apply and can be reproduced, include slow loading, failed network requests, long content, and repeated actions; record a scenario as not applicable or unavailable rather than inventing state requirements. Check keyboard/focus, labels, contrast, semantic structure, and reduced motion as applicable.
   - For a narrative/scroll-driven surface, also test normal, fast, and backward scrolling; direct anchor entry, refresh, and browser back/forward; keyboard navigation; and the reduced-motion static state. Check that sticky navigation does not cover the target heading, the active-section indicator never moves keyboard focus, essential content is visible without waiting for motion, and section context survives a direct jump.
2. Run `scripts/capture_responsive_matrix.mjs` with the project route/state manifest. It warms lazy content and makes overlapping viewport-sized screenshots, full-page composites, exact viewport dimensions, and a 320–2560 px width scan. Horizontal overflow, browser errors, and off-viewport interactive controls cause width-specific capture; off-viewport controls are review signals, not automatic defects.
3. Open and inspect every stitched image **and every original slice**. Evaluate the screenshot at its stated route, state, and viewport; record reviewer, summary, checked capture keys, and evidence-linked findings in `visualReview`. Compare before and after at the same route, state, and viewport when baseline evidence exists. On each major route, verify the first visual anchor, primary information/action, current location, and next step are clear; consider first-time-user understanding and returning-user efficiency where those audiences exist. Record exercised flows, route/state checks, and functional/accessibility results in `functionalReview`. Review through relevant product, visual/interaction, maintainability, accessibility, and regression lenses; use a lens only when it can reveal a distinct risk.
   - For a structural change, inspect the layout contract's **must hold** items and the chosen creative move in the rendered captures. Check long labels, variable-height rows, media, primary action reachability, content order, and local overflow behavior. Keep a product-fit signature move when it helps the task; fix or roll back the change if it breaks an invariant at a required width.
   - For a narrative sequence, inspect the beats in order and by direct entry. Confirm each beat adds context or meaning, transitions preserve orientation, and the reduced-motion static state communicates the same story.
   - When custom or meaningful imagery is used, inspect it in the rendered component at its actual size. At relevant desktop, tablet, and mobile captures, verify its crop and focal point, safe space, copy contrast, relationship to the visual direction, and any specified art-direction change. Check meaningful versus decorative alt text, confirm essential content and controls still work without the asset, and exercise its image-load failure fallback. Record findings against capture keys; do not require an image when the product has no image job.
   - When the UI change also moves files, adds a shared abstraction, or changes state/data ownership, review the new dependency direction and affected consumers. Confirm the structural move solves a concrete maintenance issue; line count alone is not evidence. Run the relevant type, test, and build checks, and record gaps rather than requiring unrelated project-wide cleanup.
4. Run `scripts/visual_quality_gate.py --project-root <app> --capture-manifest <manifest> --format json`. It checks all routes/flows/states, seven anchor profiles, breakpoint edges, PNG dimensions, continuous overlapping slice coverage, responsive sweep samples, overflow, provenance, and visual/functional/accessibility review completeness.
5. Fix or justify high-confidence findings; perform at most two inspect/fix rounds. For each material manual finding, record its capture key or source location, observed symptom, user impact, severity, confirmed root cause or hypothesis, expected outcome, and actual resolution/verification. After a structural change, review the full width sweep and breakpoint edges; after shared-style, token, navigation, or state changes, recheck affected routes and shared-component consumers and record the regression matrix in the existing audit note for broad work. Unresolved blocking/P0/P1 findings fail. Missing coverage or image inspection is `DEGRADED`.

Viewport anchors (CSS px at device scale 1): 1280×800, 1440×900, 1920×1080; 768×1024, 1024×768; 390×844, 844×390. These are browser emulations, not physical-device certification.

## References
- `../codex-frontend-design/references/anti-slop.md`
- `../codex-frontend-design/references/composition.md`
- `../codex-frontend-design/references/responsive-evidence.md`
