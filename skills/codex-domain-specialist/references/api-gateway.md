# API Gateway Patterns

## When to Use

- Multiple backend services need one entry point.
- Cross-cutting concerns must be centralized (auth, CORS, rate limit, logs).
- Version routing and request transformation are needed.

## Architecture

Client -> API Gateway -> User Service
                    -> Order Service
                    -> Payment Service
                    -> Notification Service

## Gateway Responsibilities

| Concern | Implementation |
| --- | --- |
| Authentication | Verify JWT and attach user context |
| Rate Limiting | Per-user, per-endpoint, per-tier |
| Routing | Path-based mapping to services |
| Load Balancing | Round-robin/weighted/least-connections |
| Circuit Breaker | Open/half-open/closed for unstable downstream |
| Caching | Cache selected GET responses |
| Logging | Structured logs + correlation id |
| Transformation | Normalize request/response versions |

## Simple Gateway (Express)

```javascript
import { createProxyMiddleware } from 'http-proxy-middleware';

app.use('/api/users', authenticate, createProxyMiddleware({
  target: 'http://user-service:3001',
  pathRewrite: { '^/api/users': '/users' },
  changeOrigin: true,
  onProxyReq: (proxyReq, req) => {
    proxyReq.setHeader('X-User-ID', req.user.id);
    proxyReq.setHeader('X-User-Role', req.user.role);
    proxyReq.setHeader('X-Correlation-ID', req.correlationId);
  },
}));

app.use('/api/orders', authenticate, createProxyMiddleware({
  target: 'http://order-service:3002',
  pathRewrite: { '^/api/orders': '/orders' },
}));
```

## Gateway vs Service Mesh

| Feature | API Gateway | Service Mesh |
| --- | --- | --- |
| Position | Edge (client to services) | East-west (service to service) |
| Use case | External API management | Internal traffic control |
| Complexity | Low to medium | High |
| Best for | Small/medium service counts | Large service meshes |
