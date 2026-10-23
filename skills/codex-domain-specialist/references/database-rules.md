# Database Architecture, Indexing & Transaction Rules

## Scope and Triggers

Use this reference for relational (PostgreSQL/MySQL/SQLite) and document (MongoDB) schema modeling, composite/partial indexing, zero-downtime migrations, transaction isolation, and query performance safeguards.

Primary triggers:
- schema creation, alteration, or `SILC-002` persistence contract definition
- migration planning, lock-contention prevention, and rollback safety
- slow query optimization (`EXPLAIN ANALYZE`), N+1 elimination, and deadlock resolution

---

## 1. Core Persistence Principles

1. **Enforce Invariants in the Schema, Not Just Application Code:** Use `NOT NULL`, `UNIQUE`, `CHECK` constraints, foreign keys, and strict domain types (`BIGINT` cents for money, `TIMESTAMPTZ` for UTC timestamps) so bad data cannot be persisted even if a service bug occurs.
2. **Workload-Driven Indexing (`ESR` Rule: Equality -> Sort -> Range):** Every query in a request path must be backed by an index aligned to its `WHERE` equality predicates, `ORDER BY` sort columns, and range filters.
3. **Zero-Downtime Expand-and-Contract Migrations:** Never rename, drop, or add an un-defaulted `NOT NULL` column in a single deployment step while old application instances are still running.
4. **Short, Deterministic Transactions:** Never perform network calls, file uploads, or LLM invocations inside an open database transaction. Acquire row locks in a consistent primary-key order to prevent deadlocks.
5. **Eliminate N+1 Queries at the Repository Layer:** Use explicit joins, `WHERE id = ANY($1)`, or DataLoader batching—never execute a query inside a `for`/`map` loop.

---

## 2. Indexing & Query Optimization Matrix

| Access Pattern | Optimal Index Strategy | PostgreSQL Example |
| --- | --- | --- |
| Tenant-scoped list sorted by newest | Composite B-Tree (`Equality, Sort`) | `CREATE INDEX CONCURRENTLY idx_orders_tenant_created ON orders (tenant_id, created_at DESC, id DESC);` |
| Active-only records (soft delete / queue) | **Partial Index** (smaller, faster in-memory footprint) | `CREATE INDEX CONCURRENTLY idx_jobs_pending ON jobs (scheduled_at) WHERE status = 'pending' AND deleted_at IS NULL;` |
| High-throughput read avoiding heap lookup | **Covering Index** (`INCLUDE`) | `CREATE INDEX CONCURRENTLY idx_users_email_cover ON users (email) INCLUDE (id, tenant_id, password_hash);` |
| JSONB / Array containment | **GIN Index** on specific path | `CREATE INDEX CONCURRENTLY idx_events_tags_gin ON events USING GIN (tags);` |
| Idempotency key deduplication | **Composite Unique Constraint** | `CREATE UNIQUE INDEX CONCURRENTLY uq_idempotency_tenant_key ON idempotency_keys (tenant_id, key);` |

Always verify critical queries with `EXPLAIN (ANALYZE, BUFFERS)` and confirm `Index Scan` or `Index Only Scan` rather than `Seq Scan` on large tables.

---

## 3. Transaction Isolation & Concurrency Patterns

| Concurrency Hazard | Recommended Control | Implementation Pattern |
| --- | --- | --- |
| **Lost Update** (two requests overwrite same row) | Optimistic Locking (`version` integer) | `UPDATE accounts SET balance_cents = $1, version = version + 1 WHERE id = $2 AND version = $3` (0 rows affected -> `409 Conflict`) |
| **Double Spend / Inventory Oversell** | Pessimistic Row Lock (`FOR UPDATE`) or Conditional Atomic Update | `UPDATE inventory SET reserved = reserved + $1 WHERE sku = $2 AND (available - reserved) >= $1 RETURNING *` |
| **Queue Worker Contention** | Skip Locked (`FOR UPDATE SKIP LOCKED`) | `SELECT id FROM outbox_events WHERE status = 'pending' ORDER BY created_at LIMIT 50 FOR UPDATE SKIP LOCKED` |
| **Deadlock under Concurrent Batch Writes** | Deterministic Lock Ordering | Sort all target row IDs ascending (`ids.sort()`) before executing multi-row updates in a transaction |

---

## 4. Database Anti-Patterns to Reject

1. **Floating-Point Currency (`FLOAT` / `REAL`):** Always store monetary amounts as integer minor units (`BIGINT` cents) or `NUMERIC(19, 4)`.
2. **Naive `OFFSET` Pagination on Large Tables:** `OFFSET 50000 LIMIT 25` forces the database to scan and discard 50,000 rows. Use keyset/cursor pagination (`WHERE (created_at, id) < ($1, $2)`).
3. **Unbounded `SELECT *` on Wide Tables:** Project only the columns required by the DTO or domain operation.
4. **Blocking Table Locks in Production Migrations:** In PostgreSQL, use `CREATE INDEX CONCURRENTLY` and add foreign keys with `NOT VALID` followed by `VALIDATE CONSTRAINT` so live reads/writes are not blocked.
