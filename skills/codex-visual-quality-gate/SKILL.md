---
name: codex-visual-quality-gate
description: Use after UI implementation for mechanical source checks and a rendered or fresh-eyes review.
load_priority: on-demand
version: "18.0.0"
---

## TL;DR
Mechanical checks are source evidence, not aesthetic scores. Prefer an independent reviewer. In a single-agent session, do a fresh-eyes self-review and mark independent review `DEGRADED` if you also authored the UI. Missing browser is `DEGRADED`, not a silent pass.

## Activation
Substantial UI delivery or `$visual-gate`. Skip backend-only work.

## Dual assessment
1. Review A: screenshots/contract, or a documented self-review against `codex-frontend-design/references/anti-slop.md`.
2. Review B: `visual_quality_gate.py` plus UX/a11y wrappers. Optional full-page stitcher: `scripts/stitch_full_page_capture.mjs` when Node exists.
3. Maximum two inspect/fix rounds.

## References
- `../codex-frontend-design/references/anti-slop.md`
- `../codex-frontend-design/references/composition.md`
