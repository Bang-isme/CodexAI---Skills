# UX Audit Spec

## Purpose

`ux_audit.py` performs static UX analysis on frontend code without running a browser.

## When to Run

- Before UI delivery to QA/product.
- After implementing new user flows, forms, or async data screens.
- During final non-blocking quality review for frontend-heavy tasks.

## Checks

1. Missing loading state
2. Missing error state
3. Missing empty state
4. Form without validation
5. Button without disabled state
6. Image without meaningful alt
7. Anchor without valid href
8. Touch target too small
9. Hover without focus-visible
10. Custom clickable elements without accessibility metadata

## Output Contract

- `status`: `audited`
- `framework`: detected or user-provided (`react|vue|html`)
- `files_scanned`
- `total_issues`
- `by_severity`
- `issues[]` with `file/line/severity/check/message/suggestion`
- `summary`
- `score` from weighted penalties

## Severity Model

- `critical`: broken resilience or inaccessible interactions
- `warning`: missing UX state coverage
- `info`: lower-impact quality concerns

## Integration Notes

- This check is advisory and non-blocking in MVP.
- Run with full project root scan; hidden directories are skipped.
