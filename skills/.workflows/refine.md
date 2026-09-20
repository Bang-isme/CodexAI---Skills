---
name: refine
trigger: $refine
loads: [codex-frontend-design, codex-visual-quality-gate]
---

# Workflow Alias: $refine

## Trigger

`$refine`, `$polish`, `$critique`, `$audit-ui`, or `$animate` after a UI feature already works. Also `$refine <dial>` from `codex-frontend-design/references/refinement-dials.md`.

## Step Outline

1. Load `codex-frontend-design` and `references/refinement-dials.md`.
2. Apply one dial (`polish`, `critique`, `audit`, `animate`, or the named dial).
3. Do not invent a new art direction unless the user asked to redesign.
4. End with `$visual-gate` / `codex-visual-quality-gate`.

## Exit Criteria

Mechanical source checks ran. Independent review or a documented fresh-eyes self-review exists. Missing browser is `DEGRADED`, not a silent pass.
