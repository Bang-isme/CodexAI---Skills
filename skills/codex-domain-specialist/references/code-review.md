# Code Review Guidelines

## Correctness

- Does implementation match requested behavior?
- Are edge cases handled?
- Are failure paths explicit?

## Security

- No secrets in code.
- Input validation and sanitization present.
- Auth/authz enforced where required.
- No injection vectors introduced.

## Performance

- Avoid N+1 queries.
- Avoid unnecessary rerenders.
- Paginate large datasets.
- Avoid blocking calls in request handlers.

## Maintainability

- Functions reasonably scoped (target < 50 lines where possible).
- Files not oversized (target < 500 lines).
- Naming clear and consistent.
- No dead/commented-out production code.

## Testing

- New behavior covered by tests.
- Edge cases tested.
- Tests deterministic.

## PR Size Guidance

| Lines Changed | Category | Review Time |
| --- | --- | --- |
| < 50 | Tiny | ~10 min |
| 50-200 | Small | ~30 min |
| 200-500 | Medium | ~1 h |
| > 500 | Large (consider split) | >2 h |

## Feedback Tone

- Use specific, actionable comments with rationale.
- Mark nits clearly as non-blocking.
- Avoid ambiguous or accusatory feedback.
