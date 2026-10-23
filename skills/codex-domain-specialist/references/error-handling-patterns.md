# Error Handling & Resilience Patterns

## Scope and Triggers

Use when designing server/client error boundaries, domain exception hierarchies, retry/circuit-breaker policies, and structured incident telemetry.

---

## 1. Error Taxonomy & Action Matrix

Classify every failure into one of four categories before deciding how to handle it:

| Category | Examples | HTTP Status | Client Behavior (`SILC-###`) | Operator / Log Action |
| --- | --- | --- | --- | --- |
| **1. Domain / Validation (`Operational`)** | Invalid input, insufficient funds, duplicate slug, expired invite | `400 / 409 / 422` | Show inline `fieldErrors` or actionable recovery banner; preserve form state | Log at `warn`/`info` with `requestId` and `code`; never page on-call |
| **2. Auth / Permission (`Security`)** | Expired JWT, missing scope, cross-tenant access attempt | `401 / 403 / 404` | Redirect to re-auth or show permission-denied state; mask resource existence on cross-tenant `404` | Log security audit event with actor, IP, and target resource |
| **3. Transient Dependency (`External`)** | Upstream payment gateway timeout, DB connection pool busy, `429` | `502 / 503 / 504` | Show non-destructive retry CTA + preserve user draft | Bounded retry with jitter; trip circuit breaker if error rate exceeds threshold; log at `error` |
| **4. Programmer / Invariant Bug (`Fatal`)** | Null dereference, schema drift, unhandled promise rejection | `500` | Render safe generic error message + `requestId` for support | Log full stack trace + correlation context at `error`/`fatal`; alert engineering |

---

## 2. Backend Domain Error Hierarchy (TypeScript)

```typescript
export class AppError extends Error {
  public readonly code: string;
  public readonly statusCode: number;
  public readonly isOperational: boolean;
  public readonly fieldErrors?: Array<{ field: string; code: string; message: string }>;

  constructor(
    code: string,
    message: string,
    statusCode = 400,
    options?: {
      isOperational?: boolean;
      fieldErrors?: Array<{ field: string; code: string; message: string }>;
      cause?: unknown;
    },
  ) {
    super(message, { cause: options?.cause });
    this.name = "AppError";
    this.code = code;
    this.statusCode = statusCode;
    this.isOperational = options?.isOperational ?? true;
    this.fieldErrors = options?.fieldErrors;
  }
}

// Centralized Express/Fastify/Next error boundary
export function globalErrorHandler(err: unknown, req: Request, res: Response, _next: NextFunction) {
  const requestId = req.header("x-request-id") ?? "unknown";

  if (err instanceof AppError && err.isOperational) {
    logger.warn({ err, requestId, code: err.code, path: req.path }, "Operational request error");
    return res.status(err.statusCode).json({
      error: {
        code: err.code,
        title: err.message,
        status: err.statusCode,
        requestId,
        fieldErrors: err.fieldErrors ?? [],
      },
    });
  }

  logger.error({ err, requestId, path: req.path }, "Unhandled internal exception");
  return res.status(500).json({
    error: {
      code: "INTERNAL_SERVER_ERROR",
      title: "An unexpected error occurred. Please retry or contact support with the request ID.",
      status: 500,
      requestId,
      fieldErrors: [],
    },
  });
}
```

---

## 3. Frontend Error Boundary & Async Recovery (`SILC-###` Consumer)

1. **Scoped UI Error Boundaries:** Wrap independent route segments, charts, and third-party widgets in dedicated Error Boundaries so a single widget failure degrades locally with a `"Retry section"` button instead of crashing the whole app shell.
2. **Typed Async Result Handling:** Map API responses directly from the `SILC-###` error envelope:
   - `422` with `fieldErrors` -> bind directly to form field error state and move focus to the first invalid input.
   - `409 Conflict` -> explain the state conflict and offer to refresh/merge latest server data.
   - `429 / 503` -> respect `Retry-After` and keep user input intact.
3. **Never Swallow Errors:** `catch (err) { console.log(err) }` is a blocking quality failure. Every catch block must either recover deterministically, transition UI state to `error`, or rethrow with enriched context.
