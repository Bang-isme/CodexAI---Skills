# Logging Patterns

## Scope and Triggers

Use when implementing application logging, debugging production issues, or setting up observability.

## Core Principles

- Log for operators: structured, machine-readable, actionable.
- Every request gets a correlation id.
- Never log secrets, tokens, passwords, or plain PII.
- Use appropriate log levels to avoid noise.

## Log Levels

| Level | Use When | Production? |
| --- | --- | --- |
| error | Unrecoverable failure needing action | Always |
| warn | Recoverable/degraded behavior | Always |
| info | Important business events | Always |
| http | Request lifecycle summaries | Recommended |
| debug | Detailed execution trace | Dev only |

## Structured Logging Setup (Winston)

```javascript
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
    winston.format.errors({ stack: true }),
    process.env.NODE_ENV === 'production'
      ? winston.format.json()
      : winston.format.combine(winston.format.colorize(), winston.format.simple())
  ),
  defaultMeta: { service: 'api' },
  transports: [new winston.transports.Console()],
});

export default logger;
```

## Correlation ID Middleware

```javascript
import { randomUUID } from 'crypto';

const correlationMiddleware = (req, res, next) => {
  req.correlationId = req.headers['x-correlation-id'] || randomUUID();
  res.setHeader('x-correlation-id', req.correlationId);
  next();
};
```

Usage:

```javascript
logger.info('User created', {
  correlationId: req.correlationId,
  userId: user.id,
});
```

## HTTP Request Logger Pattern

```javascript
const httpLogger = (req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - start;
    const meta = {
      method: req.method,
      path: req.originalUrl,
      status: res.statusCode,
      duration: `${duration}ms`,
      correlationId: req.correlationId,
      ip: req.ip,
      userAgent: req.headers['user-agent']?.slice(0, 100),
    };

    if (res.statusCode >= 500) logger.error('Request failed', meta);
    else if (res.statusCode >= 400) logger.warn('Client error', meta);
    else logger.http('Request completed', meta);
  });

  next();
};
```

## What to Log vs Never Log

| Always Log | Never Log |
| --- | --- |
| method/path/status/duration | passwords, tokens, API keys |
| error message + stack | full body dumps in production |
| user id (not email) | payment card numbers, SSN |
| correlation id | session tokens |
| business events | sensitive PII without masking |

## Error Logging Pattern

```javascript
app.use((err, req, res, next) => {
  const logMeta = {
    correlationId: req.correlationId,
    method: req.method,
    path: req.originalUrl,
    userId: req.user?.id,
    code: err.code,
  };

  if (err.isOperational) {
    logger.warn(err.message, logMeta);
  } else {
    logger.error(err.message, { ...logMeta, stack: err.stack });
    // send to Sentry/PagerDuty if needed
  }

  next(err);
});
```

## Production Checklist

- Request logging includes duration and correlation id.
- Correlation id is propagated across async work.
- Error handler logs structured metadata.
- Secret and PII redaction is enforced.
- Log retention/rotation policy is configured.
- Alerts exist for elevated error rate.

## Anti-Patterns

- Free-text logs with no structure.
- Debug-level flood in production.
- Logging entire request payloads by default.
- Missing correlation id in distributed traces.
- Ignoring log volume and ingestion costs.

## Review Checklist

- Are logs structured JSON in production?
- Are sensitive fields redacted?
- Is correlation id present at all boundaries?
- Are levels appropriate for each event type?
- Are error logs actionable and contextual?
