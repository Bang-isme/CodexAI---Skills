# Pagination Patterns

## Scope and Triggers

Use when returning lists of data that may be large. Every list endpoint must support pagination.

## Core Principle

Never return unbounded lists. Always paginate. Default `limit = 20`, max `limit = 100` (or up to 1000 for export-only endpoints).

## Offset-Based Pagination

`GET /api/items?page=2&limit=20`

Response:

```json
{
  "data": [],
  "meta": { "page": 2, "limit": 20, "total": 150, "pages": 8 }
}
```

```javascript
const page = Math.max(parseInt(req.query.page, 10) || 1, 1);
const limit = Math.min(parseInt(req.query.limit, 10) || 20, 100);
const skip = (page - 1) * limit;

const [items, total] = await Promise.all([
  Item.find(query).skip(skip).limit(limit).sort({ createdAt: -1 }).lean(),
  Item.countDocuments(query),
]);

res.json({
  success: true,
  data: items,
  meta: { page, limit, total, pages: Math.ceil(total / limit) },
});
```

Pros: simple, supports "jump to page X".  
Cons: slow on very large offsets, less consistent under concurrent inserts/deletes.

## Cursor-Based Pagination (recommended for large datasets)

`GET /api/items?cursor=<id>&limit=20`

Response:

```json
{
  "data": [],
  "meta": { "nextCursor": "abc", "hasMore": true }
}
```

```javascript
const limit = Math.min(parseInt(req.query.limit, 10) || 20, 100);
const cursor = req.query.cursor;

const query = cursor
  ? { _id: { $lt: cursor }, ...filters }
  : { ...filters };

const items = await Item.find(query)
  .sort({ _id: -1 })
  .limit(limit + 1) // fetch one extra
  .lean();

const hasMore = items.length > limit;
if (hasMore) items.pop();

res.json({
  success: true,
  data: items,
  meta: {
    nextCursor: hasMore ? items[items.length - 1]._id : null,
    hasMore,
  },
});
```

Pros: O(1)-like behavior for deep pages, stable under concurrent writes.  
Cons: cannot jump directly to arbitrary page number.

## When to Use Which

| Scenario | Pattern |
| --- | --- |
| Admin table with page selector | Offset (<100k rows) |
| Infinite scroll feed | Cursor |
| Large dataset (>100k rows) | Cursor |
| External API with simple client needs | Offset |
| Real-time feed (messages/logs) | Cursor |
| CSV export | Streaming cursor (no page API) |

## Frontend Pagination Pattern

```jsx
// URL-driven pagination (back button works)
const [searchParams, setSearchParams] = useSearchParams();
const page = parseInt(searchParams.get('page') || '1', 10);
const setPage = (p) => setSearchParams({ ...Object.fromEntries(searchParams), page: String(p) });
```

## SQL Pagination Performance

```sql
-- BAD: OFFSET scans and discards rows
SELECT * FROM items ORDER BY id DESC LIMIT 20 OFFSET 100000;

-- GOOD: Keyset pagination
SELECT * FROM items WHERE id < :last_seen_id ORDER BY id DESC LIMIT 20;
```

## Review Checklist

- Is default and max limit enforced?
- Is sorting deterministic and indexed?
- Is metadata consistent across endpoints?
- Is large dataset path using cursor/keyset?
- Are docs explicit about pagination contract?
