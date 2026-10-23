# Backend Engineering & Modular Architecture Rules

## Scope and Triggers

Use this reference when tasks affect APIs, application services, persistence boundaries, distributed reliability, and server-side business logic.

Primary triggers:
- changes under `routes/`, `controllers/`, `services/`, `modules/`, `api/`, `server/`
- request lifecycle changes: validation, authentication/authorization, rate limiting, response DTO contracts (`SILC-###`)
- defects involving latency spikes, retries, idempotency, race conditions, or transaction consistency

---

## 1. Core Architectural Principles (Pragmatic Modular Monolith & Clean Boundaries)

1. **Strict Directional Dependencies:** `HTTP / Transport Layer -> Application / Use-Case Service -> Domain Logic -> Repository / Persistence Adapter`. Inner domain logic must never import HTTP request/response objects (`req`, `res`, `NextRequest`).
2. **Contract-First at Every Boundary (`SILC-###`):** Lock request schemas, response DTOs, and deterministic error envelopes before writing handler code. Never return raw ORM/database entities directly to clients.
3. **Validate at the Edge, Trust Internally:** Parse and coerce untrusted input into strict typed domain structures at the transport boundary (Zod / Valibot / Pydantic / JSON Schema).
4. **Idempotency by Default for Mutations:** Every state-changing endpoint subject to network retries (`POST /orders`, `POST /payments`, webhook receivers) must enforce idempotency keys (`Idempotency-Key` header + atomic storage lock).
5. **Transactional Integrity & Outbox Pattern:** Never publish external events or trigger third-party side effects inside an uncommitted database transaction. Use the **Transactional Outbox Pattern** so database state and domain events commit atomically.
6. **Bounded Resource Budgets:** Every outbound network call, database query, and worker job must specify an explicit timeout (`AbortSignal.timeout`), bounded connection pool, and backpressure limit.

---

## 2. Decision Trees

### Decision Tree A: Architecture & Module Boundary Selection

| System Context | Recommended Structure | Why |
| --- | --- | --- |
| Single repo or product team (default) | **Feature-Scoped Modular Monolith** (`modules/<domain>/{controller,service,repository,schema,types}.ts`) | High cohesion, explicit module interfaces, zero network-hop overhead |
| Shared cross-module side effects | **In-process Domain Events / Transactional Outbox** | Decouples modules without premature microservice complexity |
| Independent scaling or regulatory isolation | **Bounded Service with OpenAPI 3.1 / gRPC Contract** | Only split services when repo evidence proves independent deployment/scaling need |

### Decision Tree B: Failure & Resilience Matrix

| Failure Signal | Immediate Guardrail | Production Architecture Pattern |
| --- | --- | --- |
| Transient downstream timeout (`502/503/504`) | Bounded timeout (`3s–5s`) + exponential backoff with full jitter | Circuit breaker + fallback response or async queue deferral |
| Duplicate client/webhook submission | Reject or replay cached response via `Idempotency-Key` | Unique DB constraint on `(tenant_id, idempotency_key)` with status state machine |
| Partial write across DB + external API | Move external call outside DB transaction | Transactional Outbox table + background relay worker |
| Concurrent balance/inventory update | Optimistic concurrency (`version` column) or `SELECT ... FOR UPDATE` | Atomic conditional update (`UPDATE ... WHERE id = $1 AND version = $2`) |

---

## 3. Production Implementation Patterns (TypeScript Strict)

### A. Thin Controller + Pure Use-Case Service + Explicit DTO Mapper

```typescript
// modules/enrollments/enrollment.controller.ts
export async function createEnrollmentHandler(req: AuthenticatedRequest, res: Response, next: NextFunction) {
  try {
    const input = CreateEnrollmentSchema.parse(req.body);
    const idempotencyKey = req.header("Idempotency-Key");

    const result = await enrollmentService.enrollCandidate({
      tenantId: req.actor.tenantId,
      actorId: req.actor.userId,
      idempotencyKey,
      payload: input,
    });

    return res.status(result.replayed ? 200 : 201).json({
      data: toEnrollmentDto(result.enrollment),
      meta: { requestId: req.id, idempotentReplay: result.replayed },
    });
  } catch (err) {
    next(err);
  }
}
```

### B. Transactional Outbox Pattern (Atomic State + Event Emission)

```typescript
// Never call external webhooks/brokers inside a DB transaction.
// Write both the domain record and the outbox event in the same transaction:
export async function confirmOrderPayment(db: DatabaseClient, cmd: ConfirmPaymentCmd) {
  return db.transaction(async (tx) => {
    const updated = await tx.orders.updateWhere(
      { id: cmd.orderId, status: "pending_payment" },
      { status: "paid", paidAt: new Date() },
    );
    if (!updated) {
      throw new AppError("ORDER_STATE_CONFLICT", "Order is already processed or cannot transition to paid", 409);
    }

    await tx.outboxEvents.insert({
      aggregateType: "order",
      aggregateId: cmd.orderId,
      eventType: "order.paid.v1",
      payload: { orderId: cmd.orderId, amountCents: updated.amountCents, tenantId: cmd.tenantId },
      status: "pending",
    });

    return updated;
  });
}
```

---

## 4. Backend Anti-Patterns to Reject

1. **Fat Controllers / Anemic Services:** Mixing SQL/ORM queries, permission checks, and HTTP status formatting inside route handlers.
2. **Raw Entity Leakage:** Returning `await db.user.findUnique(...)` directly without stripping internal fields (`passwordHash`, internal flags, audit metadata).
3. **Unbounded `Promise.all` over User Input:** Firing `Promise.all(ids.map(fetchItem))` without concurrency control (`p-limit` or batch query), exhausting DB connection pools.
4. **Fire-and-Forget Async (`void sendEmail()`):** Dropping promises in request handlers where failures vanish silently without retry or dead-letter visibility.
5. **Missing Tenant Scope in Queries:** Querying by `id` alone (`WHERE id = $1`) instead of composite tenant isolation (`WHERE id = $1 AND tenant_id = $2`).

---

## 5. Pre-Handoff Verification Checklist

- [ ] Every endpoint validates body, query, and path params at the boundary before invoking domain services.
- [ ] Response payloads use explicit DTO mappers matching the `SILC-###` contract—never raw database models.
- [ ] State-mutating endpoints enforce authorization, tenant isolation, and idempotency/conflict protection (`409 Conflict` / `Idempotency-Key`).
- [ ] All outbound I/O calls define explicit timeouts and structured correlation logging (`requestId` / `traceId`).
