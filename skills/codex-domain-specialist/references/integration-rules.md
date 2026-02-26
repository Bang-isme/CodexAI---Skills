# Integration Rules

## Scope and Triggers

Use when connecting systems, designing APIs between services, or implementing third-party integrations.

## Core Principles

- Every external call can fail; design for it.
- Use timeouts on all outbound requests (connect: 5s, read: 30s).
- Retry with exponential backoff plus jitter for transient failures.
- Log all integration points with correlation IDs.
- Never trust external data; validate at boundary.

## API Integration Patterns

### REST Client Best Practices

```javascript
const client = axios.create({
  baseURL: 'https://api.service.com/v1',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// Retry interceptor
client.interceptors.response.use(null, async (error) => {
  if (error.response?.status >= 500 && retries < 3) {
    await sleep(1000 * 2 ** retries);
    return client.request(error.config);
  }
  throw error;
});
```

### Circuit Breaker Pattern

```text
CLOSED -> (failures > threshold) -> OPEN -> (timeout) -> HALF-OPEN -> (success) -> CLOSED
                                                    -> (failure) -> OPEN
```

- Threshold: 5 failures in 60 seconds.
- Open duration: 30 seconds.
- Half-open: allow 1 request to test recovery.

### Webhook Design

- HMAC signature verification on every webhook.
- Return 200 immediately, process async.
- Idempotency: store webhook ID and skip duplicates.
- Retry policy: exponential backoff, max 5 attempts.

## Database Integration (Multi-DB)

- MongoDB for flexible documents plus PostgreSQL/MySQL for relational data.
- Sync via application layer, not DB triggers.
- Use logical IDs, not ObjectId, for cross-DB references.
- Transaction boundaries: one DB per transaction, saga for cross-DB workflows.

## Caching Layer

```text
Client -> API -> Cache (Redis) -> Database
                 miss -> Database -> Cache(set TTL) -> Response
```

- Cache-aside: application manages cache.
- TTL: 5min for frequently changing data, 1hr for stable data.
- Cache invalidation: on write, invalidate related keys.
- Never cache user-specific sensitive data without encryption.
