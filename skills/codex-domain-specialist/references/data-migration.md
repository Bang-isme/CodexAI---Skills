# Zero-Downtime Data Migration & Backfill Patterns

## Scope and Triggers

Use when altering database schemas, backfilling production tables, splitting/merging columns, or seeding deterministic development fixtures.

---

## 1. The Expand-and-Contract Protocol (Zero-Downtime Schema Evolution)

Never perform a breaking schema change (renaming a column, changing a column type, or dropping a column) in a single step. Execute the **4-Phase Expand-and-Contract lifecycle**:

```
Phase 1: EXPAND (DB)      -> Add new nullable column / table alongside old column (non-blocking)
Phase 2: DUAL-WRITE (App) -> Deploy app code that writes to BOTH old and new columns, reads from old
Phase 3: BACKFILL (Job)   -> Run chunked, throttled background backfill for historical rows; verify parity
Phase 4: CONTRACT (App/DB)-> Switch app reads to new column, remove old-column writes, then drop old column in a later release
```

### Safe vs Unsafe DDL Operations (PostgreSQL)

| Change Goal | Unsafe (Blocks Production Traffic) | Safe Zero-Downtime Pattern |
| --- | --- | --- |
| Add index on large table | `CREATE INDEX idx_name ON tbl(col);` | `CREATE INDEX CONCURRENTLY idx_name ON tbl(col);` |
| Add `NOT NULL` column | `ALTER TABLE tbl ADD col TEXT NOT NULL;` (without default on old DBs or full rewrite) | Add nullable -> backfill in batches -> add `CHECK (col IS NOT NULL) NOT VALID` -> `VALIDATE CONSTRAINT` |
| Add Foreign Key | `ALTER TABLE child ADD FOREIGN KEY ...` (locks both tables) | `ALTER TABLE child ADD CONSTRAINT fk_name FOREIGN KEY (...) NOT VALID;` then `ALTER TABLE child VALIDATE CONSTRAINT fk_name;` |
| Drop column | `ALTER TABLE tbl DROP COLUMN col;` while app still queries `SELECT *` | Stop referencing column in code + deploy first -> drop column in next release |

---

## 2. Production-Safe Chunked Backfill Pattern

Never run an unbounded `UPDATE table SET ...` across millions of rows in a single transaction—it bloats WAL/undo logs, holds row locks, and spikes replication lag.

```typescript
// Keyset-chunked, idempotent, throttled backfill runner
export async function runChunkedBackfill(db: DatabaseClient, batchSize = 1000, pauseMs = 50) {
  let lastId = "00000000-0000-0000-0000-000000000000";
  let totalUpdated = 0;

  while (true) {
    const batch = await db.query<{ id: string; legacyAmount: number }>(
      `SELECT id, legacy_amount AS "legacyAmount"
       FROM invoices
       WHERE id > $1 AND amount_cents IS NULL
       ORDER BY id ASC
       LIMIT $2`,
      [lastId, batchSize],
    );

    if (batch.rows.length === 0) break;

    await db.transaction(async (tx) => {
      for (const row of batch.rows) {
        await tx.query(
          `UPDATE invoices
           SET amount_cents = $1
           WHERE id = $2 AND amount_cents IS NULL`,
          [Math.round(row.legacyAmount * 100), row.id],
        );
      }
    });

    lastId = batch.rows[batch.rows.length - 1].id;
    totalUpdated += batch.rows.length;
    await new Promise((resolve) => setTimeout(resolve, pauseMs));
  }

  return { totalUpdated, lastCursor: lastId };
}
```

---

## 3. Migration & Seed Safety Checklist

- [ ] Every migration is deterministic, versioned, and has a documented `down` / rollback path.
- [ ] Seed scripts explicitly guard against running in production (`if (env.NODE_ENV === "production") process.exit(1)`).
- [ ] Large backfills use keyset cursor batching (`WHERE id > last_id LIMIT 1000`), idempotency predicates (`WHERE new_col IS NULL`), and inter-batch throttling.
