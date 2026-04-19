---
name: debug
trigger: $debug
loads: [codex-workflow-autopilot, codex-systematic-debugging, codex-test-driven-development, codex-execution-quality-gate]
---

# Workflow Alias: $debug

## Trigger

Use for bug reports, broken behavior, regressions, or root-cause investigation.

## Step Outline

1. **Activate `codex-systematic-debugging` (`$root-cause`)** — follow the 4-phase process.
2. **Phase 1: Root Cause Investigation** — read errors carefully, reproduce consistently, check recent changes, gather evidence at each component boundary, trace data flow backward.
3. **Phase 2: Pattern Analysis** — find working examples, compare against references, identify differences.
4. **Phase 3: Hypothesis & Testing** — form single hypothesis, test with smallest change, verify.
5. **Phase 4: Implementation** — create failing test (`$tdd`), implement single fix, verify.
6. If 3+ fixes fail, **stop and question architecture** (Phase 4.5) — discuss with user before continuing.
7. Run `$gate` before claiming fix is complete.

## Red Flags — Stop Immediately

- Proposing fixes before completing Phase 1
- Stacking multiple untested fixes
- "Quick fix for now, investigate later"
- "One more fix attempt" after 2+ failures

## Exit Criteria

- Root cause is stated clearly with evidence.
- Failing reproduction test exists (RED phase verified).
- Fix passes reproduction test (GREEN phase verified).
- No other tests broken.
- Regression evidence exists and `$gate` passes.
