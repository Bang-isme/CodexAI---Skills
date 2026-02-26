# Error Handling Patterns

## Scope and Triggers

Use when designing error boundaries, server/client exception handling, retry behavior, and incident visibility.

## Core Principles

- Classify errors before handling.
- Keep user-facing messages safe and actionable.
- Preserve diagnostic context for operators.
- Never silently swallow errors.

## Error Taxonomy

| Type | Example | Handling |
| --- | --- | --- |
| Operational | timeout, validation failure | expected branch + recover |
| Programming | null dereference, wrong type | fail fast + fix code |
| External dependency | API outage, DB unavailable | retry/fallback/circuit breaker |
| Security | auth tampering, invalid signature | block + audit |

## React Error Boundary Pattern

Use for render-time failures in component trees.

Rules:
- place boundaries around risky feature zones
- show fallback UI with retry/navigation action
- log error + component stack to monitoring

Limitations:
- does not catch async event handler errors by default
- does not catch SSR errors on server runtime

## Frontend Try/Catch Strategy

- wrap async actions at use-case boundaries
- map network/validation/auth errors to typed UI states
- avoid generic `catch` that discards context

Pattern:
- `loading`
- `error`
- `data`

Maintain all three states explicitly.

## Backend Error Envelope

Standard response fields:
- `success: false`
- `code`: stable machine-readable code
- `message`: safe user-facing text
- `correlationId`: trace id for support

Never expose stack traces in production responses.

## AppError Pattern

Use explicit domain errors for operational failures.

Fields:
- `statusCode`
- `code`
- `isOperational`
- optional `details`

Global error middleware maps known errors and logs unknowns.

## Logging Layers

### Application Logs

- request start/end
- domain decision points
- handled error branches

### Infrastructure Logs

- load balancer, gateway, db, queue logs

### Correlation

- propagate `correlationId` across services
- include id in every error log line

## Error Reporting (Sentry-style)

Capture:
- exception class and stack
- user/tenant context (redacted)
- release version
- environment
- breadcrumbs/traces

Sampling:
- 100% for critical auth/payment paths
- reduced sampling for noisy low-priority errors

## Retry Strategies

Retry only transient errors:
- 408, 429, 5xx, connection resets

Use:
- exponential backoff + jitter
- max attempts (3-5)
- timeout budget

Do not retry:
- 4xx validation/auth errors (except 429 with policy)

## Circuit Breaker Integration

- open breaker after threshold failures
- short-circuit quickly while open
- half-open trial requests to detect recovery

## Graceful Degradation

- show cached/stale data when fresh fetch fails
- disable non-critical features during outage
- provide retry actions and status indicators

## Anti-Patterns

1. Catch-all blocks returning success anyway.
2. Retrying every error indiscriminately.
3. Logging full secrets/PII in errors.
4. Throwing raw dependency errors directly to clients.
5. No correlation id in distributed systems.

## Testing Error Paths

- unit test domain error mapping
- integration test dependency failure branches
- e2e test user-facing fallback flows
- chaos tests for transient outages

## Review Checklist

- Are errors classified and mapped explicitly?
- Are user-safe messages separated from internal details?
- Is global error middleware present and consistent?
- Are retries bounded and selective?
- Is monitoring/reporting wired with context?
- Are critical failure paths covered by tests?
