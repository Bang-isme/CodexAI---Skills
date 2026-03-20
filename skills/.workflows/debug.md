---
name: debug
trigger: $debug
loads: [codex-workflow-autopilot, codex-reasoning-rigor, codex-execution-quality-gate]
---

# Workflow Alias: $debug

## Trigger

Use for bug reports, broken behavior, regressions, or root-cause investigation.

## Step Outline

1. Follow the 4-phase debug loop: reproduce, analyze, test one hypothesis, then implement.
2. Document expected versus actual behavior and stabilize reproduction first.
3. Trace the failing path, compare working versus broken patterns, and isolate root cause.
4. Apply the smallest fix that addresses the verified cause.
5. Run targeted regression checks and only widen scope if evidence demands it.
6. If repeated attempts fail, escalate instead of stacking speculative fixes.

## Exit Criteria

- Root cause is stated clearly.
- Reproduction no longer fails after the fix.
- Regression evidence exists and blocking gate findings are cleared.
