# Testing Strategy, Factories & Contract Harness

**Load when:** designing test suites across Unit, Integration, `SILC-###` Contract, UI Component, and E2E layers, or deciding what to mock vs run for real.

---

## 1. Mocking Decision Matrix (When to Mock vs Use Real Dependencies)

| Dependency | Unit Test | Integration Test | E2E Test | Rule |
| --- | --- | --- | --- | --- |
| **Pure Domain / Utility Modules** | Real | Real | Real | Never mock internal domain functions |
| **Database / ORM (Postgres/SQLite/Mongo)** | N/A (keep unit tests DB-free) | **Real Test DB** (transaction rollback or container) | Real | Never mock SQL/ORM query builders |
| **Third-Party HTTP APIs (Stripe, Resend, OAuth)** | Stub interface | **Deterministic HTTP Intercept (MSW / nock)** | Sandbox or local fake server | Verify request payload + handle 4xx/5xx/timeout responses |
| **System Clock / Timers** | Fake clock (`vi.setSystemTime`) | Controlled clock | Real clock | Never use real `sleep()` to test TTL/expiry |
| **Frontend Network Layer** | N/A | **MSW (Mock Service Worker)** matching `SILC-###` DTOs | Real backend | Test real `fetch`/React Query hooks against MSW handlers |

---

## 2. Composable Test Data Factory Pattern (TypeScript)

Never copy-paste 30-line inline object literals across test files. Use typed factory functions with monotonic counters so tests remain concise and collision-free:

```typescript
let sequence = 1;

export function buildEnrollmentCandidate(overrides: Partial<EnrollmentCandidate> = {}): EnrollmentCandidate {
  const id = sequence++;
  return {
    id: `cand_${id}`,
    tenantId: "tenant_default",
    email: `candidate.${id}@example.test`,
    fullName: `Candidate ${id}`,
    status: "pending_verification",
    budgetCents: 25_000,
    createdAt: new Date("2026-10-23T08:00:00.000Z"),
    ...overrides,
  };
}
```

---

## 3. SILC Contract & API Integration Test Pattern

Verify that the backend route produces the exact `SILC-###` success and error envelopes expected by the frontend consumer:

```typescript
describe("POST /api/v1/campaigns (SILC-001 Contract)", () => {
  it("returns 201 with canonical DTO shape and validates schema", async () => {
    const res = await request(app)
      .post("/api/v1/campaigns")
      .set("Authorization", `Bearer ${validToken}`)
      .set("Idempotency-Key", "idem_1001")
      .send({
        name: "Autumn Launch",
        slug: "autumn-launch",
        budgetCents: 50_000,
        currency: "USD",
        startAt: "2026-11-01T00:00:00Z",
        endAt: "2026-11-30T00:00:00Z",
      });

    expect(res.status).toBe(201);
    expect(CampaignResponseEnvelopeSchema.safeParse(res.body).success).toBe(true);
    expect(res.body.meta.requestId).toEqual(expect.any(String));
  });

  it("returns 422 with structured fieldErrors when budgetCents is below minimum", async () => {
    const res = await request(app)
      .post("/api/v1/campaigns")
      .set("Authorization", `Bearer ${validToken}`)
      .send({ name: "Too Small", slug: "too-small", budgetCents: 100 });

    expect(res.status).toBe(422);
    expect(res.body.error.code).toBe("VALIDATION_FAILED");
    expect(res.body.error.fieldErrors).toEqual(
      expect.arrayContaining([expect.objectContaining({ field: "budgetCents" })]),
    );
  });
});
```

---

## 4. Frontend Component & Accessibility Integration Testing

Test components the way a real user and assistive technology interact with them:
1. Query elements by accessible role and label (`getByRole("button", { name: /save changes/i })`, `getByLabelText(...)`), never by fragile CSS class names.
2. Exercise all 6 interactive states: `default`, `loading` (`aria-busy`), `empty`, `validation error` (`fieldErrors`), `network error + retry`, and `success`.
3. Verify keyboard navigation (`userEvent.tab()`, `Enter`, `Escape`) on dialogs, menus, and forms.
