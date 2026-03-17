# Quality Trend Spec

## Purpose

Track quality metrics over time to understand whether code health, gate discipline, and deliverable quality are improving or declining.

## When To Record

- Weekly (recommended).
- At sprint boundaries.
- Before and after major refactors.

## When To Report

- During sprint planning.
- During tech-debt review.
- Before setting quality goals for the next cycle.

## How AI Uses It

1. Run `quality_trend.py --record` to save periodic snapshots.
2. Let `run_gate.py` append gate events to `.codex/quality/gate-events.jsonl`.
3. Run `quality_trend.py --report` to compare snapshots over time.
4. Present health score, grade, declining metrics, gate pass rate, strict-output failures, editorial-quality trends, and focused recommendations.

## Automation Guidance

- Can be integrated in CI to record snapshots on merge to `main`.
- Keep snapshots in `.codex/quality/snapshots/` for longitudinal analysis.
- Gate event logs should be kept in `.codex/quality/gate-events.jsonl` so reports can correlate code-shape trends with deliverable quality trends, including editorial score drift over time.
