# Testing Rules & The Modern Testing Trophy

## Scope and Triggers

Use this reference for planning and executing unit, contract (`SILC-###`), integration, E2E, and regression testing strategies.

Primary triggers:
- new feature implementation, bug fixes, refactors, and cross-domain integration (`SILC-###`)
- flaky test elimination, coverage gaps, and quality gate failures
- deciding between real dependencies vs mocks/fakes

---

## 1. The CodexAI Testing Trophy (Confidence per Engineering Dollar)

Prioritize tests that verify real behavior and integration contracts over brittle mock-heavy unit tests:

```
          ┌───────────────────────────┐
          │   E2E Journey Tests (~10%) │  Critical user flows (Auth -> Action -> Persist)
          ├───────────────────────────┤
          │  SILC Contract & API (~25%)│  FE <-> BE DTO schema, status codes, error envelopes
          ├───────────────────────────┤
          │ Integration Tests (~40%)   │  Service + real Test DB / transaction rollback, UI + MSW
          ├───────────────────────────┤
          │  Pure Unit Tests (~25%)    │  Pure domain math, state machines, parsers, validators
          ├───────────────────────────┤
          │   Static Analysis (100%)   │  TypeScript strict, linter, schema validation
          └───────────────────────────┘
```

---

## 2. Core Testing Rules (Non-Negotiable)

1. **Test Behavior & Contracts, Never Implementation Internals:** Assert what the function, component, or endpoint produces (return value, HTTP response, DOM state, database row)—never assert private method calls or internal state hook order.
2. **Real Database for Persistence Tests:** Never mock ORM query chains (`jest.spyOn(prisma.user, 'findMany')`). A mocked query passes even when the SQL syntax, column name, or index is broken. Run integration tests against an isolated test database or transactional rollback harness.
3. **Enforce `SILC-###` Contract Parity:** Every API endpoint and its frontend consumer must share or validate against the same schema (Zod / OpenAPI / JSON Schema) in automated tests, covering both `2xx` success and `4xx` (`fieldErrors`, `409 Conflict`, `401/403`) error envelopes.
4. **Zero Arbitrary `sleep()` Calls:** Never use `setTimeout` or fixed sleeps in tests. Use deterministic fake timers (`vi.useFakeTimers()`), condition polling (`waitFor`), or explicit event/promise barriers.
5. **Every Bug Fix Starts with a Failing Regression Test (`$tdd`):** Reproduce the exact bug in an automated test, watch it fail (`RED`), apply the minimal fix (`GREEN`), and keep the test permanently.

---

## 3. Boundary & Edge-Case Verification Matrix

For every changed function, endpoint, or component, include tests across these 5 boundary dimensions:

| Dimension | Required Test Cases |
| --- | --- |
| **1. Empty / Null / Zero** | Empty array `[]`, empty string `""`, whitespace-only `"   "`, `0`, `null`/`undefined` |
| **2. Exact Boundaries (Off-by-One)** | `min - 1`, `min`, `max`, `max + 1` (e.g., pagination `limit=1`, `limit=100`, `limit=101`) |
| **3. State & Concurrency Conflicts** | Duplicate submission (`Idempotency-Key` replay), invalid state transition (`paid -> pending`), stale version (`409`) |
| **4. Authorization & Tenant Isolation** | Unauthenticated (`401`), insufficient role (`403`), User A attempting to read/mutate Tenant B's resource (`404`/`403`) |
| **5. Upstream / Network Failure** | Timeout, `429 Too Many Requests`, malformed payload, database constraint violation |

---

## 4. Flaky Test Quarantine & Elimination Protocol

- **Shared Mutable State:** Reset database tables, in-memory caches, and environment overrides before each test (`beforeEach`), and generate unique IDs/emails per test via factories.
- **Order-Dependent Queries:** Any test asserting a list must either verify deterministic `ORDER BY` in the production query or sort by a stable key.
- **TimeZone / Clock Drift:** Freeze time to a deterministic UTC timestamp (`2026-10-23T12:00:00Z`) whenever testing expiration, billing cycles, or date formatting.
