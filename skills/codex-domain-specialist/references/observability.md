# Observability, OpenTelemetry & SLO Engineering

## Scope and Triggers

Use when instrumenting services with structured logs, OpenTelemetry traces, RED/USE metrics, correlation IDs, SLO/error-budget alerts, and incident diagnostics.

---

## 1. The Unified Telemetry Contract (Logs + Traces + Metrics)

Every request, background job, and outbox event must carry a unified correlation context (`traceId`, `spanId`, `requestId`, `tenantId`, `actorId`) so operators can pivot from an alert -> latency histogram -> distributed trace -> exact error log in seconds.

### Structured JSON Logging Standard

Never use unstructured `console.log("User error", err)` in production services. Emit single-line JSON logs with automatic PII/secret redaction:

```typescript
import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  redact: {
    paths: [
      "req.headers.authorization",
      "req.headers.cookie",
      "*.password",
      "*.passwordHash",
      "*.token",
      "*.secret",
      "*.apiKey",
      "*.creditCard",
    ],
    censor: "[REDACTED]",
  },
  formatters: {
    level: (label) => ({ level: label }),
  },
  timestamp: pino.stdTimeFunctions.isoTime,
});
```

---

## 2. RED & USE Metrics Matrix

Instrument every HTTP/RPC boundary with **RED** metrics and every infrastructure resource (DB pool, queue, worker) with **USE** metrics:

| Signal Family | Metric Name | Type | Labels (Low Cardinality Only!) | Alert / Action Threshold |
| --- | --- | --- | --- | --- |
| **Rate (RED)** | `http_requests_total` | Counter | `method`, `route_template`, `status_code` | Sudden drop > 50% or spike > 3x baseline |
| **Errors (RED)** | `http_server_errors_total` | Counter | `method`, `route_template`, `error_code` | `5xx` rate > 1% over 5 minutes |
| **Duration (RED)** | `http_request_duration_seconds` | Histogram | `method`, `route_template` | `p95 > 500ms` or `p99 > 1.5s` for 10 minutes |
| **Utilization (USE)** | `db_pool_active_connections` | Gauge | `pool_name` | Active connections > 85% of `max` pool size |
| **Saturation (USE)** | `outbox_queue_lag_seconds` | Gauge | `queue_name` | Oldest pending event > 60 seconds |

**Cardinality Rule:** Never put unbounded values (`userId`, `email`, `orderId`, raw URL path with IDs) into metric labels—always use the normalized route template (`/api/v1/orders/:id`). Put high-cardinality IDs in structured logs and trace span attributes.

---

## 3. SLIs, SLOs, and Multi-Window Burn-Rate Alerting

- **Availability SLI:** Proportion of non-`5xx` responses (excluding client `4xx` errors).
- **Latency SLI:** Proportion of requests completing faster than the target threshold (e.g., `p95 < 400ms`).
- **Actionable Alerting Rule:** Page on-call **only** when user-visible SLO error budget is burning rapidly (e.g., > 2% error rate sustained for 5+ minutes or readiness probe down). Route slow degradations and disk/pool warnings to ticket queues.
