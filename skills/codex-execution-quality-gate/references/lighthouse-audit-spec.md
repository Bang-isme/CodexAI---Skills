# Lighthouse Audit Spec

## Purpose

`lighthouse_audit.py` wraps Lighthouse CLI to collect performance, accessibility, best-practices, and SEO signals from a running URL.

## When to Run

- Before production deployment.
- During frontend performance tuning.
- After major UI routing/layout changes.

## Requirements

- Running target URL (example: `http://localhost:3000`)
- Lighthouse CLI available through `npx lighthouse`

If Lighthouse is missing, the script returns actionable JSON install guidance instead of crashing.

## Input

- `--url` (required)
- `--output-dir` (optional, default `./.codex/lighthouse`)
- `--categories` (optional CSV aliases supported)
- `--device` (`mobile|desktop`)
- `--runs` (median aggregation for multi-run stability)

## Output

- `status`: `audited` or `error`
- `url`, `device`
- `scores` (0-100)
- `metrics` (FCP, LCP, TBT, CLS, Speed Index)
- `opportunities` (top savings candidates)
- `report_path`
- `summary`
- optional `warnings`

## Integration Notes

- Advisory check, non-blocking in MVP.
- Recommended before release candidate cut.
