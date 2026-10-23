# Caching, Singleflight & Stampede Protection Patterns

## Scope and Triggers

Use when optimizing read-heavy endpoints, reducing database load, caching computed aggregations, or managing distributed session/rate-limit state.

---

## 1. Core Caching Principles

1. **Cache Is an Ephemeral Accelerator, Never the Source of Truth:** The system must remain functionally correct (though slower) if the cache is completely cold or unavailable.
2. **Every Key Requires an Explicit TTL + Jitter:** Immortal keys leak memory and serve stale data forever. Add ±10% random TTL jitter (`ttl + random(-30, 30)`) to prevent mass synchronized expiration (thundering herd).
3. **Namespace & Tenant-Scope Every Key:** Format keys as `<env>:<tenantId>:<domain>:<entityId>:v<schemaVersion>` (e.g., `prod:t_89:campaign:c_42:v2`). Never store tenant-specific data under a global un-scoped key.
4. **Protect Hot Keys with Singleflight (Request Coalescing):** When a hot cache key expires under high concurrency, coalesce concurrent in-process misses into a single database query.

---

## 2. Cache-Aside + Singleflight (Anti-Stampede Pattern)

```typescript
const inflightRequests = new Map<string, Promise<unknown>>();

export async function getOrSetCache<T>(
  cacheKey: string,
  ttlSeconds: number,
  fetcher: () => Promise<T>,
): Promise<T> {
  // 1. Fast path: check Redis cache
  const cached = await redis.get(cacheKey);
  if (cached !== null) {
    return JSON.parse(cached) as T;
  }

  // 2. Singleflight: coalesce concurrent misses for the same key within this process
  const existing = inflightRequests.get(cacheKey) as Promise<T> | undefined;
  if (existing) {
    return existing;
  }

  const promise = (async () => {
    try {
      const fresh = await fetcher();
      if (fresh !== null && fresh !== undefined) {
        const jitter = Math.floor(ttlSeconds * 0.1 * (Math.random() * 2 - 1));
        await redis.setEx(cacheKey, Math.max(1, ttlSeconds + jitter), JSON.stringify(fresh));
      }
      return fresh;
    } finally {
      inflightRequests.delete(cacheKey);
    }
  })();

  inflightRequests.set(cacheKey, promise);
  return promise;
}
```

---

## 3. Cache Invalidation & Negative Caching Matrix

| Scenario | Recommended Pattern | Why |
| --- | --- | --- |
| **Standard CRUD Entity Read/Write** | **Cache-Aside + Delete-on-Write** (`await redis.del(key)` after DB commit) | Deleting on write avoids race conditions where two concurrent writes overwrite cache out of order |
| **Repeated Queries for Non-Existent IDs** (Cache Penetration attack) | **Negative Caching** (store sentinel `"__NULL__"` with short `30s–60s` TTL) | Prevents attackers or broken clients from bypassing cache and hammering the database with misses |
| **Expensive Dashboard Aggregations** | **Stale-While-Revalidate (Soft TTL + Hard TTL)** | Serve slightly stale data immediately while refreshing asynchronously in the background |
| **Immutable Reference Data** | **In-Memory LRU + Versioned Key** | Ultra-fast sub-millisecond access without network hop |
