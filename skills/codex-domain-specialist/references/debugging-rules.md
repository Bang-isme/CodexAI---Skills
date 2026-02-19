# Debugging Rules

## Scope and Triggers

Use this reference when behavior is incorrect, unstable, intermittent, or performance-degraded and root cause is unknown.

Primary triggers:
- bug reports, regression reports, production incidents
- stack traces, runtime exceptions, flaky behavior
- "not working", "broken", "random failure", "cannot reproduce" signals

Secondary triggers:
- post-release error spikes
- test flakiness with no obvious deterministic cause
- cross-system failure where ownership is unclear

Out of scope:
- speculative refactors without observed defect signal
- new feature design where no defect currently exists

## Core Principles

- Reproduce before fixing.
- Isolate before optimizing.
- Prioritize evidence over intuition.
- Fix root cause, not symptom.
- Change one variable at a time in investigation.
- Keep an explicit hypothesis backlog during debugging.
- Record expected vs actual behavior at each checkpoint.
- Preserve rollback path for risky production fixes.
- Validate fix with targeted regression tests.
- Communicate confidence level and residual risk clearly.

## Decision Tree

### Decision Tree A: Severity and Response Triage

- If incident is data-loss or security-related, escalate immediately and freeze non-essential changes.
- If incident blocks core user flow, apply hotfix workflow with rollback readiness.
- If defect is high frequency but low severity, schedule short-term patch plus long-term correction.
- If defect is intermittent and low frequency, add instrumentation first before broad code changes.
- If bug appears after release, compare recent changes and config drift before deep rewrites.
- If defect cannot be reproduced, collect telemetry and deterministic reproduction inputs.

### Decision Tree B: Investigation Matrix

| Signal Type | First Move | Second Move | Third Move |
| --- | --- | --- | --- |
| runtime exception | inspect stack trace and failing input | isolate failing branch with guard logs | confirm with minimal repro |
| logic mismatch | trace data flow source to sink | compare expected model vs actual state | add focused regression test |
| flaky test | classify nondeterminism source | control time, randomness, and IO | stabilize via deterministic harness |
| performance drop | profile before touching code | locate top hotspots by cost | optimize highest impact path |
| integration failure | verify contracts and env parity | mock dependencies for isolation | test end-to-end with controlled fixtures |
| production-only issue | compare runtime config and infra | add temporary diagnostics | ship minimal safe patch |

## Implementation Patterns

- Create a minimal reproducible case as soon as possible.
- Keep a timestamped hypothesis list with confidence score.
- Use binary search over code path or commits to narrow failure.
- Add temporary instrumentation with clear removal plan.
- Capture failing inputs and persist reproducible fixtures.
- Separate data issue, state issue, and transport issue early.
- Use feature flags to isolate risky fixes in production.
- Add canary validation before full rollout for hotfixes.
- For race conditions, control scheduler timing and concurrency.
- For memory leaks, trace object lifecycle and listener cleanup.
- For integration bugs, validate contract assumptions at boundaries.
- Convert debug findings into permanent tests and docs updates.
- Document root cause narrative with causal chain.
- Remove debug-only code after fix verification.
- Re-run full gate for high-risk modules after patch.

## Anti-Patterns

1. ❌ Bad: Guessing the fix before reproducing.
   ✅ Good: Build a deterministic reproduction with exact inputs, versions, and environment before changing code.

2. ❌ Bad: Applying multiple unrelated code changes at once.
   ✅ Good: Change one variable per experiment so each result confirms or rejects a single hypothesis.

3. ❌ Bad: Ignoring logs, traces, and stack evidence.
   ✅ Good: Use logs, traces, and stack frames as primary evidence to rank hypotheses.

4. ❌ Bad: Treating flaky tests as noise and skipping them.
   ✅ Good: Quarantine flaky tests with owner and deadline, then fix root cause instead of ignoring failures.

5. ❌ Bad: Patching symptom while root cause remains.
   ✅ Good: Trace to the failing invariant and patch the root condition, not only visible symptoms.

6. ❌ Bad: Declaring resolved without regression coverage.
   ✅ Good: Require a failing reproduction test before fix and a passing regression test after fix.

7. ❌ Bad: Leaving temporary debug instrumentation in production path.
   ✅ Good: Guard temporary instrumentation behind flags and remove it before final merge.

8. ❌ Bad: Over-optimizing before identifying actual hotspot.
   ✅ Good: Profile CPU/memory first and optimize only measured hotspots.

9. ❌ Bad: Dismissing environment drift between local and prod.
   ✅ Good: Compare runtime config, dependencies, and data shape between environments before conclusions.

10. ❌ Bad: Skipping rollback planning for high-risk fixes.
   ✅ Good: Prepare rollback or kill-switch procedures before deploying risky incident fixes.

11. ❌ Bad: Rewriting modules during incident without containment strategy.
   ✅ Good: Apply minimal containment patch during incident and defer refactor until stability returns.

12. ❌ Bad: Changing contracts without notifying dependent systems.
   ✅ Good: Notify dependent teams and provide compatibility windows before contract-impacting changes.

13. ❌ Bad: Running broad refactor while on active incident response.
   ✅ Good: Freeze non-essential refactors and prioritize service restoration tasks only.

14. ❌ Bad: Forgetting to remove stale feature flags after stabilization.
   ✅ Good: Track feature-flag cleanup tasks and remove stale flags after verification window ends.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Is the reproduction case deterministic and documented with exact environment details?
- [ ] Yes/No: Is there a prioritized hypothesis backlog tied to evidence?
- [ ] Yes/No: Is the proposed fix scoped to root cause instead of symptom masking?
- [ ] Yes/No: Is runtime instrumentation defined to verify fix effectiveness?
- [ ] Yes/No: Is a rollback or kill-switch path prepared for the deployment?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Is there a failing reproduction test or replay script before the fix?
- [ ] Yes/No: Does a regression test pass only after the fix is applied?
- [ ] Yes/No: Do logs/metrics/traces confirm the root-cause path is eliminated?
- [ ] Yes/No: Is canary monitoring configured to detect recurrence quickly?
- [ ] Yes/No: Are temporary debug flags and probes removed after validation?

## Cross-References

- `testing-rules.md` for deterministic flake reduction strategy.
- `performance-rules.md` for profiling-first optimization workflow.
- `security-rules.md` for vulnerability-aware incident response.
- `backend-rules.md` for service-level resilience handling.
- `frontend-rules.md` for UI-state and interaction debugging patterns.
- `devops-rules.md` for rollout, canary, and rollback operations.

### Scenario Walkthroughs

- Scenario: Production-only memory leak appears after 3 hours of traffic.
  - Action: Capture heap snapshots and compare object-retention growth between baseline and incident builds.
  - Action: Patch leaked listener lifecycle, then run long-duration soak test before full rollout.
- Scenario: Integration test fails randomly on CI but not locally.
  - Action: Record seed, timing, and environment details for each failure to isolate nondeterministic inputs.
  - Action: Replace race-prone timing assumptions with deterministic synchronization primitives.
- Scenario: Hotfix appears to work but error returns under load.
  - Action: Re-open hypothesis backlog and verify each assumption with production traces.
  - Action: Ship root-cause fix behind a feature flag and watch recurrence metrics for 24 hours.

### Delivery Notes

- Keep incident timeline with decision rationale and confidence levels.
- Pair each production bug with at least one permanent regression test.
- Track mean time to detect and mean time to recover trends.
- Convert recurring defect classes into preventive engineering tasks.

- Revalidate this domain checklist after each major release cycle.
- Capture one representative example per recurring issue class.
- Ensure cross-reference links stay consistent with routing table updates.
