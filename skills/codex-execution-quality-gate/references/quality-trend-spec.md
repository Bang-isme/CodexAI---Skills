# Quality Trend Spec

## Purpose

Track quality metrics over time to understand whether code health is improving or declining.

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
2. Run `quality_trend.py --report` to compare snapshots over time.
3. Present health score, grade, declining metrics, and focused recommendations.

## Automation Guidance

- Can be integrated in CI to record snapshots on merge to `main`.
- Keep snapshots in `.codex/quality/snapshots/` for longitudinal analysis.
