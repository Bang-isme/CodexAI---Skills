# Caching Patterns

## Scope and Triggers

Use when optimizing read-heavy endpoints, reducing database load, or implementing session/token storage.

## Core Principles

- Cache is acceleration, not storage: always have a fallback to source.
- Set TTL on everything: no immortal cache entries.
- Invalidate on write: stale data is a bug.
- Monitor hit ratio: below 70% usually means strategy issues.

## Cache-Aside Pattern (most common)

Request -> Check Cache -> HIT -> Return cached data -> MISS -> Query DB -> Store in cache (with TTL) -> Return.

```javascript
const getUser = async (userId) => {
  const cacheKey = `user:${userId}`;

  // 1. Try cache
  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached);

  // 2. Cache miss -> query DB
  const user = await User.findById(userId).lean();
  if (!user) return null;

  // 3. Store with TTL
  await redis.setEx(cacheKey, 300, JSON.stringify(user)); // 5 min TTL
  return user;
};

// 4. Invalidate on write
const updateUser = async (userId, data) => {
  const user = await User.findByIdAndUpdate(userId, data, { new: true });
  await redis.del(`user:${userId}`); // invalidate cache
  return user;
};
```

## TTL Strategy

| Data Type | TTL | Reason |
| --- | --- | --- |
| User session | 30 min | Security |
| API token validation | 5 min | Balance freshness/performance |
| Dashboard summary | 15-60 min | Expensive to compute |
| Config/settings | 10 min | Changes are rare |
| Static lookup (countries) | 24 hours | Almost never changes |
| Search results | 2-5 min | Stale is acceptable briefly |

## Invalidation Patterns

### Write-Through

Write -> Update DB -> Update Cache -> Return.

Pros: cache is fresh after writes.  
Cons: write latency increases.

### Write-Behind (async)

Write -> Update Cache -> Return -> (async) Update DB.

Pros: faster writes.  
Cons: data loss risk on crash before DB write.

### Event-Based Invalidation

Write -> Update DB -> Publish event -> Cache subscriber invalidates.

Best for microservices and distributed caches.

## Anti-Patterns

- Bad: cache without TTL -> memory leak and stale data forever.
- Bad: cache user-specific data in shared keys -> data leak risk.
- Bad: cache huge payloads (>1MB per key) -> Redis memory pressure.
- Bad: cache stampede on misses.
- Good: singleflight/mutex so only first miss hits DB.

## In-Memory vs Redis

| Feature | In-Memory (Map/LRU) | Redis |
| --- | --- | --- |
| Speed | Fastest (~1us) | Fast (~1ms) |
| Shared across instances | No | Yes |
| Persistence | Lost on restart | Optional |
| Best for | Single-process, small data | Multi-instance, sessions, queues |

## Observability

Track and alert on:
- hit ratio
- miss ratio
- evictions
- key size outliers
- latency p95/p99 for cache operations

## Review Checklist

- Is TTL defined for each key family?
- Is invalidation implemented for every write path?
- Is stale fallback behavior explicit?
- Are keys namespaced and tenant-safe?
- Is cache hit ratio measured and reviewed?
