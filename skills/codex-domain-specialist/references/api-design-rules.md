# API Design & Contract-First Rules (`SILC-###` Standard)

## Scope and Triggers

Use this reference for REST, OpenAPI 3.1, tRPC, or GraphQL contract design, pagination, versioning, idempotency, rate limiting, and error envelope consistency.

Primary triggers:
- new endpoint design or `SILC-###` contract locking between Frontend and Backend
- pagination, filtering, sorting, and bulk-operation contract changes
- response envelope, error taxonomy, and backward-compatibility reviews

---

## 1. Core Principles

1. **Contracts Are Normative (`SILC-###`):** Lock the endpoint route, HTTP verb, request schema, response DTO, and error envelope in `SPEC.md` or OpenAPI/Zod schema before parallel FE/BE coding begins.
2. **Deterministic Envelopes:** Success and error payloads must follow a single predictable structure across all endpoints so client state machines (`loading`, `empty`, `error`, `success`) never guess field names.
3. **Semantic HTTP Status Codes:** Never return `200 OK` with `{"success": false}`. Use exact HTTP semantics (`200`, `201`, `202`, `204`, `400`, `401`, `403`, `404`, `409`, `422`, `429`, `503`).
4. **Keyset / Cursor Pagination by Default:** For any dataset that can grow beyond a few hundred rows, use cursor pagination (`cursor`, `limit`, `nextCursor`, `hasMore`) backed by a deterministic composite index `(created_at, id)`.
5. **Tiered Rate Limiting & Quota Headers:** Protect public and authenticated endpoints with explicit rate limits and return standard `RateLimit-*` / `Retry-After` headers.

---

## 2. Canonical Response & Error Envelopes

### A. Success Envelope (Single Resource & Cursor-Paginated Collection)

```json
{
  "data": [
    {
      "id": "inv_01J8Z9X2",
      "Number": "INV-2026-0042",
      "amountCents": 14900,
      "currency": "USD",
      "status": "paid",
      "issuedAt": "2026-10-23T08:15:00Z"
    }
  ],
  "meta": {
    "requestId": "req_9f8e7d6c",
    "pagination": {
      "limit": 25,
      "nextCursor": "eyJjcmVhdGVkQXQiOiIyMDI2LTEwLTIzVDA4OjE1OjAwWiIsImlkIjoiaW52XzAxSjhaOVgyIn0=",
      "hasMore": true
    }
  }
}
```

### B. Deterministic Error Envelope (RFC 9457 Problem Details Compatible)

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "title": "Request validation failed",
    "status": 422,
    "detail": "One or more fields failed business validation.",
    "requestId": "req_9f8e7d6c",
    "fieldErrors": [
      {
        "field": "budgetCents",
        "code": "MIN_VALUE",
        "message": "Campaign budget must be at least 500 cents ($5.00)."
      }
    ]
  }
}
```

---

## 3. Idempotency, Rate Limiting & Versioning Matrix

| Concern | Engineering Standard | Implementation Detail |
| --- | --- | --- |
| **Idempotent Mutations** | Require `Idempotency-Key: <uuid>` on `POST`/`PATCH` payment, order, or provisioning routes | Hash request payload + key; store `(tenant_id, key, payload_hash, status, response_body)` with 24h TTL. Return `409` if same key is reused with different payload. |
| **Cursor Pagination** | Encode `(sortColumnValue, uniqueId)` in cursor | Query: `WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT $3 + 1` |
| **Allowlisted Filtering & Sorting** | Strictly validate `sort` and `filter` keys against an enum allowlist | Reject unknown sort/filter fields with `400 Bad Request`; never interpolate raw query strings into SQL/NoSQL |
| **Tiered Rate Limiting** | Separate buckets for Auth/Login (`5/min`), Mutations (`60/min`), Reads (`300/min`) | Key by `tenantId + userId` (or IP for anonymous routes); emit `Retry-After` on `429 Too Many Requests` |
| **Non-Breaking Evolution** | Additive changes only within `/api/v1` | Add optional fields; never rename or change the type of an existing field without a new version or dual-write deprecation window |

---

## 4. API Review Checklist

- [ ] Does every endpoint match the `SILC-###` contract in route, method, status codes, DTO shape, and `fieldErrors` structure?
- [ ] Are money values represented as integer minor units (`amountCents: 14900` + `currency: "USD"`) or exact decimal strings rather than IEEE-754 floats?
- [ ] Are timestamps formatted as UTC ISO-8601 strings (`YYYY-MM-DDTHH:mm:ssZ`)?
- [ ] Are list endpoints bounded by a maximum `limit` (e.g., `max: 100`, `default: 25`) with deterministic tie-breaker ordering?
