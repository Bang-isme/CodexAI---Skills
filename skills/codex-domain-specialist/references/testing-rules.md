# Testing Rules

## Scope and Triggers

Use this reference for planning and executing unit, integration, e2e, and regression testing strategies.

Primary triggers:
- requests involving new features, bug fixes, refactors, and reliability hardening
- flaky tests, insufficient coverage, and quality gate instability
- uncertainty about mock depth and test boundary choices

Secondary triggers:
- release readiness checks and canary confidence gaps
- migration and contract change verification

Out of scope:
- one-off throwaway scripts with no maintainability expectation

## Core Principles

- Tests should protect behavior contracts, not implementation details.
- Use the smallest test level that gives meaningful confidence.
- Keep tests deterministic and isolated from non-essential side effects.
- Prefer clear failure diagnostics over opaque assertions.
- Encode regression history as permanent tests.
- Balance fast feedback loops with realistic integration confidence.
- Use a practical TDD loop for risky logic: red -> green -> refactor.
- Mock strategically, not universally.
- Keep test data readable and representative.
- Prevent flaky signals from polluting delivery confidence.
- Tie test scope to risk and change impact.

## Decision Tree

### Decision Tree A: Test Level Selection

- If logic is pure and bounded, start with unit tests.
- If behavior spans modules or infrastructure boundary, add integration tests.
- If user journey or system workflow is critical, add e2e tests.
- If bug was production-facing, add targeted regression tests at failing layer.
- If change affects contract, add consumer-facing contract tests.
- If performance-sensitive path changed, include perf verification checks.

### Decision Tree B: Mocking Strategy Matrix

| Scenario | Preferred Mock Strategy | Avoid |
| --- | --- | --- |
| pure utility logic | no mocks, direct assertions | mocking internal language features |
| service with external API | mock external boundary only | mocking every internal helper |
| DB interaction | integration with test DB or transaction sandbox | brittle deep ORM method mocks |
| UI component behavior | mock network boundary, keep interaction real | snapshot-only without behavior checks |
| retry/time-based logic | controlled clock and deterministic scheduler | sleeping in tests |
| flaky integration path | isolate unreliable dependency with contract fixtures | disabling test permanently |

## Implementation Patterns

- Use test pyramid with explicit ratio targets by layer.
- Apply TDD on high-risk branches to lock behavior before implementation drift.
- Keep unit tests fast and independent.
- Build integration harness with realistic boundary adapters.
- Use fixtures/factories to keep setup readable.
- Use contract tests for APIs and shared DTOs.
- Tag tests by scope to enable selective execution.
- Add retry policy only for known nondeterministic external dependencies.
- Use fake timers for time-sensitive logic.
- Keep e2e suite focused on business-critical journeys.
- Capture flaky test metadata and triage within SLA.
- Add mutation or property-based tests for high-risk logic where useful.
- Keep snapshot tests scoped and reviewed for signal quality.
- Verify negative and recovery paths, not only success cases.
- Ensure test cleanup prevents state bleed across runs.
- Enforce quality gates with clear failure ownership.

## Anti-Patterns

1. ❌ Bad: Writing only happy-path tests.
   ✅ Good: Add edge, failure, and boundary cases for each changed behavior.

2. ❌ Bad: Asserting implementation internals instead of behavior.
   ✅ Good: Assert observable outputs, API contracts, and user-visible behavior.

3. ❌ Bad: Mocking everything and losing real integration confidence.
   ✅ Good: Use mocks selectively and keep integration tests for real boundaries.

4. ❌ Bad: Using sleep-based timing assertions.
   ✅ Good: Use fake timers or deterministic synchronization instead of fixed sleeps.

5. ❌ Bad: Ignoring flaky tests for long periods.
   ✅ Good: Quarantine flaky tests with owner and expiry date, then prioritize root-cause fixes.

6. ❌ Bad: Merging large changes without regression coverage.
   ✅ Good: Require regression tests for bug fixes and high-risk refactors before merge.

7. ❌ Bad: Treating coverage percentage as sole quality metric.
   ✅ Good: Use coverage with risk-based assertions and critical-path verification.

8. ❌ Bad: Keeping brittle snapshot baselines without intent.
   ✅ Good: Replace broad snapshots with focused assertions that encode expected behavior.

9. ❌ Bad: Running e2e for every tiny change with no selection strategy.
   ✅ Good: Select impacted end-to-end suites by change scope and run full suite on release cadence.

10. ❌ Bad: Sharing mutable global test state between cases.
   ✅ Good: Isolate tests with fresh fixtures and cleanup hooks between cases.

11. ❌ Bad: Duplicating fixture setup across many files.
   ✅ Good: Centralize reusable fixtures/factories and compose scenario-specific overrides.

12. ❌ Bad: Leaving failing tests quarantined indefinitely.
   ✅ Good: Enforce quarantine expiry and fail CI when deadline passes without fix.

13. ❌ Bad: Not testing error handling and rollback behavior.
   ✅ Good: Add negative-flow tests that verify rollback, retries, and user-facing recovery.

14. ❌ Bad: Ignoring contract drift between services and clients.
   ✅ Good: Run consumer/provider contract tests continuously for shared APIs.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Is the unit/integration/e2e test mix appropriate for this change scope?
- [ ] Yes/No: Are mocks limited to unstable dependencies while preserving integration confidence?
- [ ] Yes/No: Are flaky tests tracked with owner and expiration policy?
- [ ] Yes/No: Are contract-impacting changes accompanied by contract tests?
- [ ] Yes/No: Is regression-test policy applied for every bug fix in scope?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Do tests cover happy, edge, and failure paths for changed behavior?
- [ ] Yes/No: Are timing-sensitive tests deterministic (fake timers or controlled synchronization)?
- [ ] Yes/No: Are fixtures isolated and reset between test cases?
- [ ] Yes/No: Is impacted e2e subset selected appropriately with full-suite cadence defined?
- [ ] Yes/No: Are quarantined tests re-evaluated and resolved before release?

## Cross-References

- `debugging-rules.md` for root-cause and regression conversion flow.
- `api-design-rules.md` for contract and compatibility testing.
- `backend-rules.md` for service-level integration boundaries.
- `frontend-rules.md` and `react-patterns.md` for component test priorities.
- `performance-rules.md` for perf regression testing strategy.
- `security-rules.md` for abuse and negative-path test requirements.

### Scenario Walkthroughs

- Scenario: Flaky integration test blocks CI pipeline intermittently.
  - Action: Capture seed, timing, and dependency state on each failure to isolate race source.
  - Action: Replace nondeterministic waits with event-based synchronization and remove quarantine.
- Scenario: Large feature PR passes unit tests but breaks downstream API consumer.
  - Action: Add provider and consumer contract tests to validate request/response compatibility.
  - Action: Gate merge on contract suite pass for all supported consumer versions.
- Scenario: Critical bug fix merged without regression test and reappears later.
  - Action: Add failing reproduction test first, then fix and keep test permanent in regression suite.
  - Action: Update review checklist to block bug-fix PRs lacking regression coverage.

### Delivery Notes

- Keep this reference aligned with project conventions and postmortems.
- Update checklists when recurring defects reveal missing guardrails.
- Prefer incremental adoption over large risky rewrites.
