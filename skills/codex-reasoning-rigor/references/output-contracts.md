# Output Contracts

Use output contracts to make answers falsifiable and actionable. An output contract forces the answer to include enough structure that the reader can verify, challenge, or act on it â€” instead of just nodding along.

## Why Output Contracts Matter

Without a contract, AI output tends toward:
- Vague advice that "sounds right" but can't be verified
- Missing next steps that leave the reader stuck
- No evidence, making it impossible to trust
- No risks mentioned, creating false confidence

With a contract, every output earns its credibility.

## Contract Types

### Minimum Contract (Every Substantial Output)

Every non-trivial answer must include these fields:

```markdown
## Decision
<Chosen path and why it was chosen over alternatives.>

## Evidence
<Commands run, files inspected, or data that supports the decision.>

## Risks
<What could go wrong and under what conditions.>

## Next Step
<The single most important action to take next, with owner if applicable.>
```

**Example â€” Bad (No Contract):**
> "You should use Redis for caching. It's fast and widely used. Let me know if you need help setting it up."

**Example â€” Good (With Contract):**
> **Decision:** Use Redis for API response caching because the current P95 response time (800ms) exceeds the 500ms target, and 70% of requests are repeated reads.
>
> **Evidence:** `curl -w '%{time_total}' /api/products` â†’ 820ms average over 10 requests. `SELECT count(*) FROM request_log WHERE path='/api/products' AND created_at > now()-interval '1h'` â†’ 4,200 requests, 3,100 unique.
>
> **Risks:** Cache invalidation on product updates. Mitigation: TTL of 60s + explicit invalidation on write endpoints.
>
> **Next Step:** Add `ioredis` dependency and implement cache middleware in `src/middleware/cache.ts`. Verify with before/after P95 comparison.

### Workflow Contract

For process improvements, add these fields:

```markdown
## Owner
<Role or person responsible for this workflow.>

## Monitoring
| Signal | Healthy | Drift | Action |
|---|---|---|---|
| <observable> | <good state> | <bad state> | <response> |

## Rollback
<How to revert if the workflow causes problems.>
```

**Example:**
> **Owner:** Tech Lead
>
> **Monitoring:**
> | Signal | Healthy | Drift | Action |
> |---|---|---|---|
> | PR review time | < 24h average | > 48h for 3+ PRs | Add reviewer rotation |
>
> **Rollback:** If review bottleneck worsens, revert to previous direct-merge policy for hotfixes.

### Review Contract

For reviews, audits, and code assessments:

```markdown
## Finding
<What was found â€” specific, not vague.>

## Impact
<Why it matters â€” what breaks, degrades, or becomes risky.>

## Boundary
<Exact files, functions, or lines affected.>

## Fix
<Specific action or decision needed.>
```

**Example â€” Bad:**
> "The error handling could be improved."

**Example â€” Good:**
> **Finding:** Unhandled promise rejection in `src/services/payment.ts:42` â€” `processPayment()` awaits `stripe.charges.create()` without try/catch.
>
> **Impact:** Stripe API timeout (>30s) crashes the server process. Production logs show 3 instances in the past week.
>
> **Boundary:** `src/services/payment.ts:42-58`, `src/controllers/order.ts:23` (caller).
>
> **Fix:** Wrap in try/catch, return typed error to controller, add timeout configuration (30s â†’ 10s with retry).

### Implementation Contract

For code work and feature delivery:

```markdown
## Files Changed
| File | Change |
|---|---|
| <path> | <what changed and why> |

## Verification Command
`<exact command to run>`

## Behavior Change
<What is different in observable behavior after this change.>

## Deliberately Unchanged
<What was considered but intentionally left alone, and why.>
```

**Example:**
> **Files Changed:**
> | File | Change |
> |---|---|
> | `src/middleware/auth.ts` | Added rate limiting (100 req/min per IP) |
> | `src/config/limits.ts` | New config file for rate limit thresholds |
> | `tests/middleware/auth.test.ts` | Added 3 rate-limit test cases |
>
> **Verification:** `npm test -- --grep "rate limit"` â†’ 3/3 pass
>
> **Behavior Change:** Requests exceeding 100/min from same IP now receive 429 Too Many Requests instead of proceeding.
>
> **Deliberately Unchanged:** Login endpoint not rate-limited separately â€” will address in next sprint with account-based limiting.

### Planning Contract

For plans, proposals, and roadmaps:

```markdown
## Goal
<Measurable outcome, not activity.>

## Scope
| In Scope | Out of Scope |
|---|---|
| <item> | <item> |

## Success Criteria
<How we know this is done â€” specific, testable conditions.>

## Dependencies
<What must be true before this can start.>

## Risks
| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| <risk> | H/M/L | H/M/L | <action> |
```

## Contract Selection Guide

| Output Type | Required Contract |
|---|---|
| Quick answer to simple question | None needed |
| Technical recommendation | Minimum Contract |
| Code change | Implementation Contract |
| Review or audit | Review Contract |
| Process/workflow change | Workflow Contract |
| Plan or proposal | Planning Contract |
| "Is it done?" claim | Implementation Contract + evidence from `evidence-ladder.md` |

## Quality Check

Before delivering, verify the contract is real:

- [ ] Could someone disagree with the decision based on the evidence? (If not, the evidence is missing)
- [ ] Could someone verify the claim without asking you? (If not, the command is missing)
- [ ] Could someone identify when this goes wrong? (If not, the risks are missing)
- [ ] Could someone take action without asking "what next?" (If not, the next step is missing)
