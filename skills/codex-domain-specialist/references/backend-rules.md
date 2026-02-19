# Backend Rules

## Scope and Triggers

Use this reference when tasks affect APIs, services, data persistence, reliability, and server-side business logic.

Primary triggers:
- changes under `routes/`, `controllers/`, `services/`, `api/`, `server/`
- request lifecycle changes: validation, auth, response contracts
- defects involving latency spikes, retries, data consistency, or failures

Secondary triggers:
- frontend contract changes that require backend compatibility handling
- migration, indexing, and transaction safety work
- operational concerns around observability and fault handling

Out of scope:
- pure UI composition decisions without API impact
- infra-only tuning with no service contract or runtime impact

## Core Principles

- Validate and sanitize every external input at trust boundaries.
- Keep architecture layered and dependencies directional.
- Preserve explicit API contracts and version compatibility.
- Centralize error handling and keep user-facing errors safe.
- Design for observability: logs, metrics, traces, and correlation IDs.
- Prefer idempotent operations for retriable endpoints.
- Keep business logic in services, not controllers.
- Ensure persistence operations are atomic where required.
- Use consistent response envelope and status semantics.
- Avoid hidden side effects in request handlers.

## Decision Tree

### Decision Tree A: API Lifecycle and Contract Evolution

- If change is backward compatible, update current version with contract tests.
- If change modifies required fields or semantics, introduce version strategy.
- If endpoint is public and high traffic, add deprecation window and telemetry.
- If request/response shape changes, update schema docs and client contract checks.
- If route behavior differs by role, enforce policy at authorization layer.
- If endpoint may be retried by clients, ensure idempotency key or safe semantics.

### Decision Tree B: Reliability and Failure Matrix

| Failure Signal | Immediate Action | Long-Term Pattern |
| --- | --- | --- |
| transient downstream timeout | bounded retry with jitter and timeout budget | circuit breaker + dependency SLO |
| repeated validation failures | tighten schema and input normalization | add API contract examples and guardrails |
| deadlock or write conflict | retry safe transaction path | redesign lock granularity |
| partial write in workflow | compensate or rollback transaction | saga or orchestration pattern |
| queue processing lag | prioritize and backpressure | partitioning and worker scaling |
| noisy 5xx spikes | isolate failing dependency and degrade gracefully | resilience playbook and chaos drills |

## Implementation Patterns

- Keep controller thin: auth, validation, delegation, response mapping.
- Use service layer for orchestration and business rules.
- Use repository or data access layer for DB query isolation.
- Validate payloads with strict schemas and normalize before service entry.
- Map domain errors to stable API error codes.
- Adopt structured logging with request IDs and actor context.
- Add timeout budgets and retry policies per dependency.
- Use circuit breaker or fallback around unstable external integrations.
- Implement pagination with deterministic ordering and cursor support.
- Use explicit transactions for multi-step consistency operations.
- Keep migration scripts additive and reversible when possible.
- Use feature flags for risky behavioral changes.
- Add idempotency guarantees for create-like operations.
- Maintain compatibility tests for shared API consumers.
- Instrument performance-critical paths with traces.

## Anti-Patterns

1. ❌ Bad: Embedding complex business logic directly in controllers.
   ✅ Good: Keep controllers focused on input/output orchestration and move business rules into service/domain modules.

2. ❌ Bad: Returning inconsistent response formats across endpoints.
   ✅ Good: Use a shared response serializer and error mapper so endpoint outputs remain contract-consistent.

3. ❌ Bad: Exposing internal exception details to clients.
   ✅ Good: Return sanitized error messages with request identifiers and keep stack traces in server logs.

4. ❌ Bad: Mixing authorization logic across multiple layers without ownership.
   ✅ Good: Centralize authorization checks in a single owned policy layer and call it consistently.

5. ❌ Bad: Running unbounded retries without timeout budgets.
   ✅ Good: Set bounded retries with jitter, max attempts, and total timeout budgets per dependency.

6. ❌ Bad: Writing raw string-concatenated SQL queries.
   ✅ Good: Use parameterized queries or query builders to prevent injection and improve query plan reuse.

7. ❌ Bad: Executing schema changes directly in production manually.
   ✅ Good: Apply schema changes through versioned migrations in the CI/CD pipeline with audit history.

8. ❌ Bad: Ignoring transaction boundaries in multi-write workflows.
   ✅ Good: Wrap related writes in explicit transactions and rollback on any intermediate failure.

9. ❌ Bad: Shipping endpoints without rate limiting for abusive paths.
   ✅ Good: Apply route-level rate limits on auth, search, and high-cost endpoints with clear quotas.

10. ❌ Bad: Treating 200 status as success wrapper for failed operations.
   ✅ Good: Map failures to proper HTTP statuses and keep 2xx responses for successful operations only.

11. ❌ Bad: Logging secrets, tokens, or raw sensitive payloads.
   ✅ Good: Redact or hash sensitive fields before logging and block raw secret logging in code review.

12. ❌ Bad: Skipping compatibility checks when changing DTO fields.
   ✅ Good: Run backward-compatibility tests and version adapters when DTO contracts evolve.

13. ❌ Bad: Catching errors broadly and swallowing root cause context.
   ✅ Good: Catch specific exception types, preserve causal context, and include correlation IDs.

14. ❌ Bad: Ignoring slow-query signals and index health.
   ✅ Good: Track slow-query metrics, inspect execution plans, and add or tune indexes for repeated hotspots.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Are controllers thin and business logic implemented in services or domain modules?
- [ ] Yes/No: Are authentication and authorization checks enforced in a single owned boundary?
- [ ] Yes/No: Are transaction boundaries explicit for every multi-write operation touched?
- [ ] Yes/No: Are retry, timeout, and rate-limit policies defined for risky endpoints?
- [ ] Yes/No: Are logs sanitized to prevent PII or secret leakage?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Do integration tests cover the full controller-service-repository path for changed endpoints?
- [ ] Yes/No: Is transaction rollback verified when one write in a multi-step flow fails?
- [ ] Yes/No: Are timeout and retry behaviors tested against transient dependency failures?
- [ ] Yes/No: Do contract compatibility tests catch DTO changes for existing consumers?
- [ ] Yes/No: Are performance checks or alerts defined for modified heavy queries?

## Cross-References

- `api-design-rules.md` for versioning, pagination, and error envelope policy.
- `database-rules.md` for schema, indexing, migration, and query safety.
- `security-rules.md` for threat modeling and auth hardening.
- `performance-rules.md` for latency budgets and hotspot triage.
- `testing-rules.md` for layered backend testing strategy.
- `devops-rules.md` for deployment, rollback, and operational controls.
- `typescript-rules.md` for typed DTO and contract consistency.

### Scenario Walkthroughs

- Scenario: Checkout workflow writes order, payment, and inventory in one request.
  - Action: Wrap all writes in one transaction boundary and rollback all writes when payment fails.
  - Action: Add integration tests that force mid-flow failure and assert no partial persistence remains.
- Scenario: Public search endpoint receives abusive traffic spikes.
  - Action: Add route-level rate limiting with per-IP and per-token quotas.
  - Action: Monitor reject counts and latency to tune limits without breaking legitimate users.
- Scenario: Legacy client breaks after DTO field rename.
  - Action: Reintroduce old field alias with deprecation notice and maintain both fields temporarily.
  - Action: Add compatibility tests against the legacy client contract before full removal.

### Delivery Notes

- Keep release notes for API behavior changes and known caveats.
- Capture root cause and follow-up actions for reliability incidents.
- Prefer progressive rollout for high-impact backend contract changes.
- Validate rollback viability before announcing completion.

- Revalidate this domain checklist after each major release cycle.
- Capture one representative example per recurring issue class.
- Ensure cross-reference links stay consistent with routing table updates.
