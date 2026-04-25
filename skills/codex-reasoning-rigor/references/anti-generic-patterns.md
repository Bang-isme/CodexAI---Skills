# Anti-Generic Patterns

Use this reference when an answer sounds correct but could apply to almost any project. Generic output is the #1 failure mode for AI assistants â€” it satisfies no one and wastes the reader's time.

## The Generic Output Problem

Generic output has these symptoms:
- Advice that works for any project without modification
- No file paths, commands, or artifact names mentioned
- Improvement language without measurable change
- "Best practice" citations disconnected from repo reality
- Padded summaries that hide missing evidence

**The test:** If you can copy-paste the answer into a completely different project and it still makes sense, it's generic.

## Common Failure Modes

### 1. Advice Without Artifacts

| Generic (Fails) | Specific (Works) |
|---|---|
| "Add error handling to your API" | "Add try/catch to `src/controllers/user.ts:34-52` â€” the `createUser` handler awaits Prisma without catching `P2002` (unique constraint)" |
| "Improve your test coverage" | "Add integration tests for `POST /api/orders` â€” 0 tests exist for the order flow in `tests/`" |
| "Optimize database queries" | "Add index on `orders.user_id` â€” `EXPLAIN ANALYZE` shows sequential scan on 50K rows for `/api/users/:id/orders`" |

### 2. Improvement Language Without Measurement

| Generic | Specific |
|---|---|
| "This will improve performance" | "This reduces P95 from 800ms to 200ms (measured with `k6 run load-test.js`)" |
| "Enhances maintainability" | "Extracts 3 duplicated validation blocks into `src/utils/validate.ts` â€” removes 45 lines of duplication" |
| "Better user experience" | "Login form now shows field-level errors instead of a generic toast â€” reduces support tickets for 'can't login'" |

### 3. Single Path Without Tradeoffs

| Generic | Specific |
|---|---|
| "Use Redis for caching" | "Redis for caching vs. in-memory LRU: Redis survives restarts and shares across instances, but adds infrastructure. For single-instance MVP, LRU is simpler. For multi-instance production, Redis is required." |
| "Deploy with Docker" | "Docker vs. direct PM2: Docker gives reproducible builds but adds 200MB image size and requires Docker knowledge. PM2 is simpler for single-server VPS deployment." |

### 4. Abstract Best Practices

| Generic | Specific |
|---|---|
| "Follow SOLID principles" | "The `OrderService` class handles validation, pricing, inventory, and email â€” extract `InventoryService` and `NotificationService` to respect single responsibility" |
| "Use proper error handling" | "Replace `console.log(err)` on line 45 with `throw new AppError('Payment failed', 502, { cause: err })` so the error middleware returns structured JSON" |
| "Implement security best practices" | "Add `helmet()` middleware, set `httpOnly: true` on session cookie in `src/config/session.ts`, and validate `Content-Type` header in upload endpoint" |

## Repair Moves

When you catch yourself being generic, apply these transformations:

### Move 1: Name The Artifact
```
Before: "Add validation"
After:  "Add Zod schema validation to `src/routes/user.ts` POST handler"
```

### Move 2: Show The Command
```
Before: "Run tests to verify"
After:  "Run `npm test -- --grep 'user creation'` to verify the new validation"
```

### Move 3: State The Measurement
```
Before: "This improves performance"
After:  "Measure before/after with `curl -w '%{time_total}' /api/users`"
```

### Move 4: Add A Failure Mode
```
Before: "Use connection pooling"
After:  "Use connection pooling (max 20). Without it, 50+ concurrent requests
         exhaust PostgreSQL's default 100-connection limit, causing ECONNREFUSED"
```

### Move 5: Ground In This Repo
```
Before: "Consider adding rate limiting"
After:  "`request_log` shows 12K requests/min from same IP on April 15 â€”
         add express-rate-limit to `src/middleware/` with 100 req/min per IP"
```

## Phrases To Distrust

These phrases are **almost always** a sign of generic output. They're allowed only when followed immediately by repo-specific details:

| Phrase | Why It's Suspect | How To Fix |
|---|---|---|
| "follow best practices" | Which practices? For what? | Name the specific practice and where to apply it |
| "ensure scalability" | Scalable to what? From what baseline? | State current load + target load + specific bottleneck |
| "improve performance" | What metric? By how much? | State metric name + current value + target value |
| "enhance maintainability" | Maintainability for whom? How? | State what's hard to maintain and what change helps |
| "robust solution" | Robust against what? | Name the failure mode it handles |
| "seamless workflow" | Seamless compared to what? | State current friction point and how it's removed |
| "optimize the process" | Which step? What's slow? | Name the step and the time savings |
| "industry standard" | Which industry? Says who? | Cite the standard and why it applies here |
| "proper implementation" | Proper by what criteria? | State the specific quality criteria |
| "best-in-class" | Compared to what alternatives? | Name the alternatives and the comparison metric |

## The Specificity Checklist

Before finalizing any output, verify:

- [ ] **Artifact:** Which file, function, or config makes this real?
- [ ] **Command:** Which command verifies the change?
- [ ] **Metric:** Which observable signal changes, and by how much?
- [ ] **Failure:** What's one realistic way this could go wrong?
- [ ] **Next step:** What's the smallest concrete action to take right now?

If you can't answer all 5, the output is still too generic.

## Worked Example: Full Transformation

### âŒ Generic Version
> "The application would benefit from adding caching to improve performance. Consider using Redis as a caching layer. This is a common pattern that follows industry best practices for web application optimization. Make sure to implement proper cache invalidation to ensure data consistency."

### âœ… Specific Version
> **Finding:** `GET /api/products` averages 780ms (measured: `curl -w '%{time_total}' localhost:3000/api/products` over 20 requests). The query in `src/services/product.ts:23` runs `SELECT * FROM products JOIN categories` on every request â€” 2,400 products, no cache.
>
> **Recommendation:** Add Redis caching with 60s TTL to `GET /api/products`.
>
> **Implementation:**
> 1. Add `ioredis` to `package.json`
> 2. Create `src/lib/cache.ts` with `get/set/invalidate` wrapper
> 3. Wrap the query in `src/services/product.ts:23` with cache-first logic
> 4. Add cache invalidation to `PUT/POST/DELETE` product handlers
>
> **Risk:** Stale data for up to 60s after product update. Mitigation: explicit `cache.invalidate('products')` in write handlers.
>
> **Verification:** `curl -w '%{time_total}' /api/products` â†’ expect < 50ms on cache hit.
>
> **Not Changed:** Category list endpoint (`/api/categories`) â€” only 12 categories, not worth caching.
