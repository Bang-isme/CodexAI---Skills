---
name: codex-visual-quality-gate
description: Use after UI implementation to run mechanical source checks and independent rendered review with bounded inspect/fix loops.
load_priority: on-demand
version: "16.0.0"
---

## TL;DR
Mechanical checks are source evidence, not aesthetic scores. Independent visual review must not be the same agent that just wrote the UI. Desktop and mobile screenshots belong in one batch. Default stop is two inspect/fix rounds. Missing browser or subagent is `DEGRADED`, not a silent pass.

## Activation
1. Substantial UI delivery or `$visual-gate`.
2. After `frontend-specialist` on new or redesigned surfaces.
3. `auto_gate.py` full/deploy when changed files look like UI.

Skip for backend-only or trivial CSS one-liners unless the user asks.

## Dual assessment
1. Review A: design critique from screenshots and the UX/direction contract. Do not read detector output yet.
2. Review B: mechanical JSON from `visual_quality_gate.py` plus a11y/UX audit wrappers.
3. Parent synthesizes. Material failures go back to implementation, not to the reviewer rewriting the app.

## Mechanical evidence
Runnable via `codex-visual-quality-gate/scripts/visual_quality_gate.py` (dry-run default). Categories include card repetition, missing hierarchy/tokens, arbitrary spacing/radius, default-font/gradient clichés, competing CTAs, missing responsive/reduced-motion/state coverage. Blocking only when the criterion is determinate in source.

## Rendered review
Require desktop + mobile in one capture pass when a browser exists. If the host cannot screenshot or spawn an independent reviewer, set `review_status` to `DEGRADED` and record the reason.

## Finish loop
Maximum two inspect/fix rounds by default. Remaining material issues are a handoff list, not infinite polish.

## Optional Node detector
If a local `impeccable` binary exists, or `npx --no-install impeccable detect` can run without installing, attach its result as `optional_detector: available`. Otherwise `skipped` or `failed`. Never block the Python core on Node.

## References
- `../codex-design-system/references/composition.md`
- `../codex-design-system/references/anti-slop.md`
- `../codex-execution-quality-gate/references/ux-audit-spec.md`
