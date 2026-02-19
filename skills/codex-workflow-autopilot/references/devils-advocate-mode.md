# Devil's Advocate Mode

## Purpose

Use this reference to aggressively stress-test a plan, design, or implementation path before commit or release.

## Trigger Signals

- "be critical"
- "poke holes"
- "red team this"
- "find blind spots"
- requests for worst-case analysis or failure pre-mortem

## Attack Framework

Evaluate the proposal through these lenses:

1. Correctness failure
2. Reliability failure
3. Security failure
4. Performance failure
5. Operability failure
6. Rollback failure

## Contrarian Checklist

- What assumption is most likely false?
- Which dependency can fail first under load?
- Which data path can cause irreversible damage?
- Which step has weakest observability?
- Which rollback step is missing or untested?
- What breaks for legacy consumers?
- What breaks if this is retried concurrently?

## Risk Ranking

Use simple scoring for each risk:

- Impact: low | medium | high
- Likelihood: low | medium | high
- Priority: high if impact=high or likelihood=high; critical if both high

## Mitigation Protocol

For every high/critical risk:

1. Define an immediate mitigation control.
2. Define a verification test that proves mitigation works.
3. Define a rollback condition with explicit threshold.

## Output Contract

When this mode is active, return:

1. Top risks ranked by severity
2. Evidence or assumptions behind each risk
3. Mitigation steps per risk
4. Ship/No-ship recommendation with conditions

## Avoid

- Vague warnings without evidence.
- Listing risks without mitigation actions.
- Blocking delivery without practical alternatives.
