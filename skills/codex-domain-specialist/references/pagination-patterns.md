# Pagination Patterns (Cursor & Keyset Default)

## Scope and Triggers

Use when designing or implementing list endpoints, infinite feeds, data tables, or batch exports. Every list endpoint must bound its page size and use deterministic ordering.

---

## 1. Core Principles

1. **Keyset / Cursor Pagination Is the Default:** Never use unbounded queries, and avoid `OFFSET` on growing tables. Cursor pagination (`WHERE (created_at, id) < ($1, $2)`) guarantees `O(1)` index-seek performance at any depth and prevents skipped/duplicate rows during concurrent inserts.
2. **Bounded Page Sizes:** Enforce `limit` at the schema boundary (`default: 25`, `min: 1`, `max: 100`).
3. **Deterministic Tie-Breaker Sort:** Always sort by a timestamp or sequence column **plus a unique tie-breaker column** (`ORDER BY created_at DESC, id DESC`).
4. **Canonical Envelope (`SILC-001`):** Return `{ data, meta: { requestId, pagination: { limit, nextCursor, hasMore } } }` without a redundant `success: true` boolean.

---

## 2. Keyset / Cursor Pagination Implementation (TypeScript + SQL / ORM)

### Cursor Encoding & Decoding

```typescript
export interface PaginationCursor {
  createdAt: string;
  id: string;
}

export function encodeCursor(row: { createdAt: Date; id: string }): string {
  return Buffer.from(
    JSON.stringify({ createdAt: row.createdAt.toISOString(), id: row.id }),
    "utf-8",
  ).toString("base64url");
}

export function decodeCursor(raw?: string): PaginationCursor | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(Buffer.from(raw, "base64url").toString("utf-8"));
    if (typeof parsed?.createdAt === "string" && typeof parsed?.id === "string") {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}
```

### Query & Response Pattern (`limit + 1` Lookahead)

```typescript
// Fetch limit + 1 rows to determine hasMore without an expensive COUNT(*) query
const decoded = decodeCursor(query.cursor);
const rows = await db.query(
  `SELECT id, name, status, created_at AS "createdAt"
   FROM campaigns
   WHERE tenant_id = $1
     AND ($2::timestamptz IS NULL OR (created_at, id) < ($2::timestamptz, $3::text))
   ORDER BY created_at DESC, id DESC
   LIMIT $4`,
  [tenantId, decoded?.createdAt ?? null, decoded?.id ?? null, limit + 1],
);

const hasMore = rows.length > limit;
const pageItems = hasMore ? rows.slice(0, limit) : rows;
const nextCursor = hasMore ? encodeCursor(pageItems[pageItems.length - 1]) : null;

return res.status(200).json({
  data: pageItems.map(toCampaignDto),
  meta: {
    requestId: req.id,
    pagination: {
      limit,
      nextCursor,
      hasMore,
    },
  },
});
```

---

## 3. When Offset Pagination Is Permitted (`shortcut:` Ceiling Required)

Use `OFFSET` pagination **only** for bounded, small back-office tables where the product explicitly requires arbitrary page-number jumps (`Page 1, 2, ... 12`) AND the dataset is guaranteed to stay small. When used, annotate the query with an explicit shortcut ceiling:

```typescript
// shortcut: 10000 rows, migrate to keyset cursor pagination when table exceeds 10000 rows
```

---

## 4. Review Checklist

- [ ] Does the schema clamp `limit` to `1..100` (with a sensible default such as `25`)?
- [ ] Does the `ORDER BY` clause include a unique tie-breaker (`created_at DESC, id DESC`) backed by a matching composite index?
- [ ] Does the response use `meta.pagination = { limit, nextCursor, hasMore }`?
