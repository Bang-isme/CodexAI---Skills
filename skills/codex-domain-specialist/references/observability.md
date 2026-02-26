# Observability

## Three Pillars

Logs (what happened) + Metrics (how much) + Traces (where/how long).

## Metrics (Prometheus style)

```javascript
import promClient from 'prom-client';

promClient.collectDefaultMetrics({ prefix: 'app_' });

const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5],
});

const activeConnections = new promClient.Gauge({
  name: 'http_active_connections',
  help: 'Number of active HTTP connections',
});

const requestCounter = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
});

const metricsMiddleware = (req, res, next) => {
  activeConnections.inc();
  const end = httpRequestDuration.startTimer();

  res.on('finish', () => {
    const route = req.route?.path || req.path;
    const labels = { method: req.method, route, status_code: res.statusCode };
    end(labels);
    requestCounter.inc(labels);
    activeConnections.dec();
  });

  next();
};

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', promClient.register.contentType);
  res.end(await promClient.register.metrics());
});
```

## Key Metrics

| Category | Metric | Alert Threshold |
| --- | --- | --- |
| Latency | p50, p95, p99 response time | p95 > 500ms |
| Traffic | requests/second | > 2x baseline |
| Errors | error rate (5xx / total) | > 1% |
| Saturation | CPU, memory, connections | > 80% |
| Business | signups/hour, orders/hour | < 50% baseline |

## SLO/SLI

- SLI: 99.5% of requests return in under 500ms.
- SLO: maintain SLI across rolling 30 days.
- Error budget: 0.5% slow/failed requests per month.

## Alerting Rules

- Page: error rate > 5% for 5 minutes, or hard down.
- Ticket: error rate > 1% for 15 minutes, or p95 > 2s.
- Log/anomaly: new error type or unusual drift.

## Distributed Tracing

- Propagate `X-Correlation-ID` across gateway/services/workers.
- Include the same ID in logs and traces for end-to-end debugging.
