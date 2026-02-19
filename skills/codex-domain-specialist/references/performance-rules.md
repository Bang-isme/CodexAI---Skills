# Performance Rules

## Scope and Triggers

Use this reference when tasks involve latency, throughput, rendering smoothness, memory usage, or compute hotspots.

Primary triggers:
- p95 latency regressions, frame drops, slow pages, heavy queries
- CPU or memory spikes in frontend or backend
- requests for optimization, profiling, or budget enforcement

Secondary triggers:
- architecture refactors likely to change performance characteristics
- release readiness checks requiring perf confidence

Out of scope:
- micro-optimizations with no measured bottleneck signal

## Core Principles

- Profile first, optimize second.
- Focus on top bottlenecks by user impact and cost.
- Set explicit budgets and enforce them continuously.
- Keep optimization changes measurable and reversible.
- Avoid tradeoffs that harm reliability or readability without clear gain.
- Consider full path: client, network, server, and data layer.
- Distinguish cold-start from steady-state behavior.
- Use caching intentionally with invalidation strategy.
- Prefer algorithmic improvements before low-level tweaks.
- Track trends over time, not one-off benchmark wins.

## Decision Tree

### Decision Tree A: Hotspot Triage Flow

- If issue is unknown, run profiler or tracing first.
- If hotspot is CPU-bound computation, reduce complexity or cache results.
- If hotspot is IO-bound, improve batching, indexing, or concurrency controls.
- If issue is frontend render cost, isolate rerender sources and memoize selectively.
- If latency comes from downstream dependency, apply timeout and fallback strategy.
- If memory grows unbounded, inspect lifecycle, caches, and listener cleanup.

### Decision Tree B: Optimization Choice Matrix

| Symptom | Preferred Action | Avoid |
| --- | --- | --- |
| slow list rendering | virtualization and row memoization | full DOM render for large sets |
| API p95 regression | trace call graph and DB plan | random query rewrites |
| repeated expensive compute | memoized selector or precompute | recompute every request/render |
| high cache miss | adjust key strategy and TTL | infinite cache retention |
| startup lag | defer non-critical initialization | blocking boot with optional work |
| GC pressure | reduce allocations and object churn | tuning runtime flags first |

## Implementation Patterns

- Define budgets for critical flows (latency, render, memory, payload).
- Add profiling checkpoints before and after optimization.
- Use flamegraphs and query plans to locate top cost centers.
- Optimize data shape and payload size at boundaries.
- Batch network and DB requests where semantics allow.
- Use caching with explicit key, TTL, and invalidation policies.
- Use lazy loading and code splitting for non-critical paths.
- Keep hot loops allocation-light and deterministic.
- Avoid synchronous blocking calls on critical request paths.
- Use connection pooling and concurrency limits for stability.
- Instrument performance metrics with release annotations.
- Optimize only when measurable gain exceeds maintenance cost.
- Capture performance baselines in CI for high-risk services.
- Add fallback behavior for degraded dependency performance.
- Review optimization impact on readability and correctness.

## Anti-Patterns

1. ❌ Bad: Optimizing without baseline metrics.
   ✅ Good: Capture baseline latency, throughput, and resource metrics before making optimization changes.

2. ❌ Bad: Chasing tiny improvements while major bottleneck remains.
   ✅ Good: Prioritize the largest measured hotspot first using profiler and flamegraph data.

3. ❌ Bad: Caching everything without invalidation plan.
   ✅ Good: Cache only expensive deterministic paths and define explicit TTL and invalidation triggers.

4. ❌ Bad: Sacrificing correctness for micro-benchmark gains.
   ✅ Good: Keep correctness and SLA tests mandatory while optimizing performance-critical code.

5. ❌ Bad: Using premature memoization across entire UI tree.
   ✅ Good: Memoize only components or calculations proven expensive by profiling.

6. ❌ Bad: Ignoring network and serialization overhead.
   ✅ Good: Measure payload size, compression ratio, and serialization cost, then optimize transfer and encoding.

7. ❌ Bad: Rewriting architecture without targeted hotspot evidence.
   ✅ Good: Limit changes to measured hotspots before proposing architectural rewrites.

8. ❌ Bad: Running heavy work on main/UI thread.
   ✅ Good: Move expensive tasks to workers, background jobs, or async pipelines.

9. ❌ Bad: Ignoring p95 and tail latencies.
   ✅ Good: Track p95/p99 latency and optimize tail performance, not only average metrics.

10. ❌ Bad: Treating one local benchmark as production truth.
   ✅ Good: Validate performance on production-like workloads and infrastructure before final decisions.

11. ❌ Bad: Adding complexity for negligible user impact.
   ✅ Good: Reject optimizations with low user impact when maintenance cost is high.

12. ❌ Bad: Forgetting to track regressions over time.
   ✅ Good: Add automated performance regression checks and trend dashboards.

13. ❌ Bad: Overlooking memory leaks during optimization changes.
   ✅ Good: Profile memory growth and enforce cleanup for listeners, caches, and buffers.

14. ❌ Bad: Tuning runtime flags before fixing algorithmic issues.
   ✅ Good: Fix algorithmic complexity and query/index design before runtime-level tuning.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Are baseline metrics and target budgets documented before optimization work?
- [ ] Yes/No: Are optimization choices tied to measured hotspots rather than assumptions?
- [ ] Yes/No: Is cache strategy explicit with invalidation and TTL policy?
- [ ] Yes/No: Are algorithmic improvements prioritized over micro-tuning flags?
- [ ] Yes/No: Are latency, CPU, and memory tradeoffs documented for the proposed change?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Are before and after benchmarks run under the same workload and environment?
- [ ] Yes/No: Are p95 and p99 latency changes measured and reported?
- [ ] Yes/No: Are cache hit, miss, and stale-data behaviors tested?
- [ ] Yes/No: Are memory leak checks performed for long-running paths touched?
- [ ] Yes/No: Are automated alerts configured for performance regression thresholds?

## Cross-References

- `frontend-rules.md` and `react-patterns.md` for UI render optimization.
- `backend-rules.md` and `database-rules.md` for service/query performance.
- `devops-rules.md` for release-time monitoring and rollback.
- `testing-rules.md` for performance regression test strategy.
- `nextjs-patterns.md` for route-level caching and rendering tradeoffs.

### Scenario Walkthroughs

- Scenario: API p95 latency jumps after adding advanced filters.
  - Action: Profile query and serialization hotspots, then add targeted index and payload trimming.
  - Action: Re-run load tests and approve only if p95 returns within budget.
- Scenario: React table typing lags when users enter search text.
  - Action: Debounce expensive filtering and memoize derived row models based on stable inputs.
  - Action: Measure rerender counts and interaction latency before and after the fix.
- Scenario: Memory usage climbs continuously in worker process.
  - Action: Capture heap snapshots to locate retained objects and leaked listeners.
  - Action: Add leak regression test and memory threshold alert for the worker service.

### Delivery Notes

- Keep this reference aligned with project conventions and postmortems.
- Update checklists when recurring defects reveal missing guardrails.
- Prefer incremental adoption over large risky rewrites.
