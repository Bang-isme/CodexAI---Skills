# Api Design Rules

## Scope and Triggers

Use this reference for REST or GraphQL contract design, pagination, versioning, idempotency, and error envelope consistency.

Primary triggers:
- new endpoint design or endpoint behavior changes
- pagination, filtering, sorting, and search contract changes
- response format and error model redesign requests
- backward compatibility questions from client teams

Secondary triggers:
- API gateway routing and request normalization
- webhook and callback contract definitions

Out of scope:
- internal-only function signatures with no external contract exposure

## Core Principles

- Contracts are products: prioritize consistency and evolvability.
- Keep response envelope deterministic and discoverable.
- Use explicit status codes and error semantics.
- Design idempotency for retried write operations.
- Version deliberately and document migration windows.
- Keep pagination predictable and stable under growth.
- Separate transport concerns from business semantics.
- Provide machine-parseable error codes and human-readable context.
- Validate inputs and reject ambiguous parameter combinations.
- Preserve backward compatibility by default.

## Decision Tree

### Decision Tree A: Contract Evolution and Versioning

- If change is additive and non-breaking, evolve current version.
- If change removes fields or semantics, introduce new version path.
- If existing clients cannot migrate quickly, support dual contracts temporarily.
- If endpoint is internal but shared, still version with changelog discipline.
- If error model changes, provide mapping period and compatibility shim.
- If pagination strategy changes, expose migration guide and test fixtures.

### Decision Tree B: Endpoint Contract Matrix

| Scenario | Preferred Pattern | Avoid |
| --- | --- | --- |
| list endpoints | cursor pagination + stable sort key | offset-only for huge datasets |
| mutation endpoints | idempotency key for retriable calls | duplicate side effects on retry |
| validation errors | 4xx with field-level error details | generic 500 for client mistakes |
| partial failures | explicit per-item result structure | silent dropped items |
| filtering and sorting | allowlisted params with schema validation | arbitrary query pass-through |
| cross-client compatibility | explicit deprecation timeline | undocumented breaking changes |

## Implementation Patterns

- Use common response envelope like `{ success, data, error, meta }`.
- Include correlation ID or request ID in metadata.
- Define typed schemas for request and response payloads.
- Standardize error code taxonomy across services.
- Enforce parameter validation and defaults at boundary.
- Use cursor pagination for large and evolving datasets.
- Provide deterministic ordering for pagination stability.
- Add idempotency keys to critical write operations.
- Keep endpoint naming resource-oriented and predictable.
- Document behavior for empty results and partial results.
- Add compatibility tests for previous API versions.
- Use API changelog entries for contract-level changes.
- Avoid overfetching by supporting selective field patterns where safe.
- Use rate limits and quota headers for public APIs.
- Provide clear deprecation headers and sunset policies.

## Anti-Patterns

1. ❌ Bad: Returning inconsistent shapes across similar endpoints.
   ✅ Good: Enforce one response envelope schema across endpoints and validate it with contract tests in CI.

2. ❌ Bad: Using 200 status for known error scenarios.
   ✅ Good: Return semantic 4xx/5xx statuses and include stable error codes in the response body.

3. ❌ Bad: Changing field semantics without versioning.
   ✅ Good: Introduce a new field or version path, keep old semantics during migration, and publish a sunset date.

4. ❌ Bad: Overloading one endpoint with unrelated behaviors.
   ✅ Good: Split unrelated actions into dedicated resources or sub-actions such as `/orders/{id}/cancel`.

5. ❌ Bad: Ignoring idempotency for retry-prone mutations.
   ✅ Good: Require `Idempotency-Key` for retriable writes and deduplicate by request fingerprint on the server.

6. ❌ Bad: Using opaque or unstable pagination cursors.
   ✅ Good: Use cursor pagination on indexed stable keys (for example `created_at,id`) and return `next_cursor`.

7. ❌ Bad: Exposing internal exception names in API errors.
   ✅ Good: Map internal exceptions to public error contracts and keep stack details in internal logs only.

8. ❌ Bad: Allowing unbounded filters and sorts.
   ✅ Good: Allowlist filter/sort fields and enforce page size caps and query complexity limits.

9. ❌ Bad: Shipping endpoint changes without contract tests.
   ✅ Good: Add request/response schema tests and consumer compatibility tests before merging contract changes.

10. ❌ Bad: Removing fields without migration window.
   ✅ Good: Mark fields deprecated first, monitor usage, and remove only after the documented migration window ends.

11. ❌ Bad: Designing around one client while breaking others.
   ✅ Good: Design additive changes by default and validate the contract against all supported client versions.

12. ❌ Bad: Missing metadata for pagination and request tracing.
   ✅ Good: Include pagination metadata and `request_id` in responses for traceability and debugging.

13. ❌ Bad: Returning partial failures without per-item error detail.
   ✅ Good: Return per-item status objects with `error_code` and message for each failed item in batch operations.

14. ❌ Bad: Treating docs as optional for public contract changes.
   ✅ Good: Update API docs and changelog in the same PR as the contract change, including migration notes.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Are status codes and error envelope shapes consistent with the platform API standard?
- [ ] Yes/No: Is pagination cursor-based with stable indexed ordering for mutable datasets?
- [ ] Yes/No: Are retriable write endpoints protected by an explicit idempotency strategy?
- [ ] Yes/No: Is a backward-compatibility and deprecation window defined for breaking changes?
- [ ] Yes/No: Are filter and sort parameters allowlisted with explicit limits?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Do contract tests validate request and response schemas for all changed endpoints?
- [ ] Yes/No: Is there a retry test proving idempotent writes do not create duplicate side effects?
- [ ] Yes/No: Do pagination tests verify cursor stability across concurrent inserts?
- [ ] Yes/No: Are previous supported client versions still passing compatibility tests?
- [ ] Yes/No: Do batch endpoints verify per-item error payloads on partial failure?

## Cross-References

- `backend-rules.md` for layered implementation and reliability controls.
- `typescript-rules.md` for DTO and schema typing discipline.
- `database-rules.md` for pagination/index implications.
- `security-rules.md` for auth and boundary hardening.
- `testing-rules.md` for contract and compatibility testing depth.
- `devops-rules.md` for rollout and version migration operations.

### Scenario Walkthroughs

- Scenario: Orders API moves from offset pagination to cursor pagination.
  - Action: Introduce `next_cursor` while keeping offset params temporarily for legacy clients.
  - Action: Add migration docs and compatibility tests to prove both modes during transition.
- Scenario: A new write endpoint is retried by mobile clients on poor networks.
  - Action: Require `Idempotency-Key` and store a deterministic response for duplicate keys.
  - Action: Add tests that send identical requests twice and assert exactly one write occurs.
- Scenario: Bulk update endpoint returns partial success.
  - Action: Return per-item `status`, `error_code`, and `message` instead of one generic failure.
  - Action: Add integration tests asserting clients can recover failed items deterministically.

### Delivery Notes

- Keep this reference aligned with project conventions and postmortems.
- Update checklists when recurring defects reveal missing guardrails.
- Prefer incremental adoption over large risky rewrites.
