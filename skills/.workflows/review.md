---
name: review
trigger: $review
loads: [codex-workflow-autopilot, codex-execution-quality-gate, codex-reasoning-rigor]
---

# Workflow Alias: $review

## Trigger

Use for audits, code reviews, technical risk assessment, or release-readiness inspection.

## Step Outline

1. Load `workflow-review.md` and gather debt, trend, and security signals.
2. Aggregate findings across functionality, maintainability, and security.
3. Separate blockers from advisory items and order them by severity.
4. Run `output_guard` and `editorial_review` on the final written review.
5. Publish a concise action matrix with owners, urgency, and verification steps.

## Exit Criteria

- Findings are severity-ordered and easy to act on.
- Blockers and advisory items are clearly separated.
- The written review passes output-quality and editorial checks.
