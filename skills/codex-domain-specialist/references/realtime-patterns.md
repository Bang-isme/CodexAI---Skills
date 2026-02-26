# Realtime Patterns

## Scope and Triggers

Use when implementing live updates, push notifications, collaborative editing, or event-streamed dashboards.

## Core Principles

- Choose simplest mechanism that satisfies latency and consistency needs.
- Assume disconnections are normal.
- Make client updates idempotent and order-aware.
- Keep fallback path for degraded networks.

## Transport Decision Guide

| Need | Best Fit |
| --- | --- |
| One-way server updates | SSE |
| Bi-directional events | WebSocket / Socket.IO |
| Low-frequency updates | Polling |
| Enterprise proxies with strict constraints | Long polling / SSE fallback |

## WebSocket Setup

### Server Baseline

- Authenticate during handshake.
- Authorize channels/rooms per user role/ownership.
- Track connection metadata (user, tenant, version).
- Heartbeat/ping to detect dead sockets.

### Client Baseline

- Exponential reconnect with jitter.
- Queue outbound messages while reconnecting.
- Resubscribe channels after reconnect.
- Display connection status in UI.

## Socket.IO Patterns

### Rooms

- Room per entity (`project:<id>`) for scoped fanout.
- Room per user for private notifications.
- Room per tenant for multi-tenant isolation.

### Event Contracts

- Version events (`v1:item.updated`).
- Include `eventId`, `timestamp`, `correlationId`.
- Keep payload minimal and typed.

## SSE (Server-Sent Events)

Use when updates are server -> client only.

Pros:
- simpler than WebSocket
- works well with proxies/CDN in many setups

Considerations:
- one-way only
- browser connection limits per origin
- reconnect with `Last-Event-ID`

## Polling Strategies

### Fixed Interval

- Good for low criticality dashboards.
- Keep interval >= 10s when possible.

### Adaptive Polling

- Fast interval during active view.
- Slow or pause in background tab.

### Conditional Polling

- Use ETag/If-None-Match to reduce payload.
- Return 304 on no changes.

## Optimistic Updates

### Pattern

1. Apply change locally immediately.
2. Send request/event to server.
3. Confirm or rollback on response.

Rules:
- generate temporary ids for created items
- reconcile server canonical state on ack
- surface rollback errors to user

## Ordering and Idempotency

- Use monotonic sequence numbers per stream.
- Drop stale/out-of-order events when safe.
- Deduplicate by event id.

## Reconnection Handling

- Reconnect backoff: 1s, 2s, 4s, 8s, cap 30s.
- Add random jitter to avoid herd effect.
- Request missed events by last known sequence.

## Presence and Typing Indicators

- Presence should be eventually consistent.
- Expire stale presence with TTL.
- Typing indicators should auto-expire quickly (2-5s).

## Scaling Architecture

- Use message broker (Redis pub/sub, Kafka, NATS) for multi-node fanout.
- Keep sticky sessions only if necessary.
- Offload high-volume event processing to workers.

## Security Controls

- Validate all inbound realtime payloads.
- Re-check authorization per event, not only on connect.
- Rate-limit event emits per user/socket.
- Encrypt transport (TLS mandatory).

## Observability

Track:
- active connections
- reconnect rate
- event delivery latency
- dropped events
- unauthorized emit attempts

Log with correlation ids and channel identifiers.

## Anti-Patterns

1. Trusting client-only authorization for rooms.
2. No backoff on reconnect loops.
3. Broadcasting all events to all clients.
4. Missing dedupe and sequence handling.
5. Realtime-only with no fallback read path.

## Review Checklist

- Is chosen transport justified by directionality/latency?
- Are reconnect and backoff policies implemented?
- Are events versioned and idempotent?
- Is authorization enforced per channel/event?
- Is fallback strategy available when realtime fails?
