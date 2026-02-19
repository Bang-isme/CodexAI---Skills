# Database Rules

## Scope and Triggers

Use this reference for schema modeling, indexing, migrations, transaction design, and query performance safeguards.

Primary triggers:
- schema creation or alteration
- migration planning and rollback concerns
- query performance degradation or lock contention
- consistency and transaction boundary decisions

Secondary triggers:
- ORM model refactor affecting persistence contracts
- data backfill and historical correction tasks

Out of scope:
- purely in-memory application logic with no persistence impact

## Core Principles

- Model data around access patterns and invariants.
- Keep schema evolution additive and reversible where possible.
- Treat indexing as workload-driven, not guesswork.
- Use transactions only where consistency requires atomicity.
- Keep read and write paths observable with query metrics.
- Preserve data integrity with constraints, not application hopes.
- Minimize lock duration and contention hotspots.
- Plan migrations with failure recovery and backfill strategy.
- Separate operational maintenance from request-critical paths.
- Validate performance under realistic production data volumes.

## Decision Tree

### Decision Tree A: Schema and Migration Strategy

- If adding optional field, deploy additive migration first.
- If adding required field, use phased migration with backfill then enforce constraint.
- If changing field semantics, create parallel field and migrate gradually.
- If table is large, split migration into chunked batches with checkpoints.
- If migration is irreversible, require explicit backup and rollback plan.
- If foreign key constraints may fail, repair data before constraint enforcement.

### Decision Tree B: Query and Index Matrix

| Query Pattern | Preferred Index Strategy | Avoid |
| --- | --- | --- |
| point lookup by unique key | unique index on lookup key | full table scan |
| range scan by time | composite index with time-leading or partitioning | non-selective multi-column index |
| filtered list with sort | index aligned to filter + sort order | sort on unindexed large dataset |
| join across large tables | indexes on join keys + selective prefilters | cross joins without constraints |
| soft-delete aware query | partial index on active rows | scanning deleted and active rows together |
| frequent aggregates | summary table/materialized view as needed | heavy aggregate per request |

## Implementation Patterns

- Define primary keys and uniqueness constraints explicitly.
- Use foreign keys where integrity boundaries are clear.
- Normalize up to clarity, denormalize only for measured read benefits.
- Keep migration files immutable after release.
- Use dual-write or backfill patterns for risky schema transitions.
- Add migration idempotency and retry-safe behavior.
- Use query plans (`EXPLAIN`) for critical read/write paths.
- Add covering indexes for high-volume endpoints when justified.
- Track slow query logs and set investigation thresholds.
- Use connection pooling with bounded concurrency.
- Use transaction isolation level appropriate to business invariants.
- Keep long-running maintenance jobs off peak request windows.
- Add archival strategy for unbounded growth tables.
- Validate data quality with consistency checks after migration.
- Document schema ownership and change history.

## Anti-Patterns

1. ❌ Bad: Running destructive migrations without staged plan.
   ✅ Good: Use expand-migrate-contract: add new structures first, migrate data safely, then remove old structures later.

2. ❌ Bad: Adding indexes blindly without workload evidence.
   ✅ Good: Create indexes from measured query plans and re-measure latency after deployment.

3. ❌ Bad: Using wide transactions for unrelated writes.
   ✅ Good: Keep transaction scope narrow to one business unit and commit quickly.

4. ❌ Bad: Ignoring lock waits and deadlock signals.
   ✅ Good: Track lock wait metrics, set lock timeouts, and retry deadlocks with bounded backoff.

5. ❌ Bad: Storing inconsistent enum-like values without constraints.
   ✅ Good: Enforce allowed values with enum or check constraints at schema level.

6. ❌ Bad: Backfilling large tables in one blocking transaction.
   ✅ Good: Backfill in small batches with checkpoints and throttle to protect production load.

7. ❌ Bad: Coupling ORM models directly to unstable external contracts.
   ✅ Good: Map persistence models to external DTOs through adapters to isolate schema changes.

8. ❌ Bad: Treating query latency as app-layer concern only.
   ✅ Good: Use `EXPLAIN ANALYZE` and index/query rewrites before adding app-layer caching.

9. ❌ Bad: Dropping columns before consumers are migrated.
   ✅ Good: Deprecate old columns in code first, verify no reads remain, then drop in a later migration.

10. ❌ Bad: Using offset pagination on very large mutable datasets.
   ✅ Good: Switch to cursor pagination on indexed keys such as `id` or `created_at,id`.

11. ❌ Bad: Ignoring nullability semantics during schema evolution.
   ✅ Good: Roll nullability changes in phases with defaults, data cleanup, and final constraints.

12. ❌ Bad: Allowing duplicate logical keys without unique constraints.
   ✅ Good: Add unique indexes for business keys and handle conflict errors explicitly.

13. ❌ Bad: Skipping post-migration verification checks.
   ✅ Good: Run post-migration checks for row counts, constraints, and critical query behavior.

14. ❌ Bad: Assuming local dataset performance equals production behavior.
   ✅ Good: Benchmark migration and query performance on production-like dataset sizes and distributions.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Does each migration include forward and rollback steps with explicit order?
- [ ] Yes/No: Are new indexes justified by observed slow queries or query-plan evidence?
- [ ] Yes/No: Are lock and transaction scopes minimized with timeout and retry strategy?
- [ ] Yes/No: Are integrity constraints (unique, foreign key, check, nullability) correctly defined?
- [ ] Yes/No: Is large data backfill planned in chunks with throttle and monitoring?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Has migration been rehearsed on a production-like snapshot before deployment?
- [ ] Yes/No: Does rollback migration execute successfully in staging?
- [ ] Yes/No: Are post-migration integrity checks automated and passing?
- [ ] Yes/No: Are before/after query plans captured for modified queries?
- [ ] Yes/No: Is pagination correctness verified under concurrent write load?

## Cross-References

- `backend-rules.md` for service-layer consistency and retries.
- `api-design-rules.md` for pagination and contract implications.
- `performance-rules.md` for hotspot diagnosis and budgets.
- `testing-rules.md` for migration and concurrency test strategy.
- `devops-rules.md` for rollout sequencing and recovery operations.
- `security-rules.md` for sensitive data handling and access controls.

### Scenario Walkthroughs

- Scenario: Add a non-null column to a 200M-row table.
  - Action: Add the column nullable, backfill in batches, then enforce `NOT NULL` after verification.
  - Action: Monitor lock time and replication lag during each backfill wave.
- Scenario: Query latency spikes after introducing new report filters.
  - Action: Capture `EXPLAIN ANALYZE` for top slow queries and add targeted composite indexes.
  - Action: Re-run load test and compare p95 latency before approving rollout.
- Scenario: Migration drops legacy column still used by one service.
  - Action: Restore column compatibility via view/alias and re-open migration with deprecation window.
  - Action: Add consumer-read checks to block future destructive migration until usage is zero.

### Delivery Notes

- Keep this reference aligned with project conventions and postmortems.
- Update checklists when recurring defects reveal missing guardrails.
- Prefer incremental adoption over large risky rewrites.
