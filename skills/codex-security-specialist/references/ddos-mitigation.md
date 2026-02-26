# DDoS Mitigation

## Attack Surface

| Layer | Attack Type | Goal |
| --- | --- | --- |
| L3/L4 | SYN flood, UDP flood, amplification | Exhaust bandwidth/connections |
| L7 | HTTP flood, slowloris, API abuse | Exhaust app/DB compute |

## Defense-In-Depth Model
1. Edge layer: CDN + WAF + anti-bot.
2. Network layer: load balancer rules, geo controls, connection limits.
3. Application layer: identity-aware rate limiting, challenge flows.
4. Data layer: query limits, caching, circuit breakers.

## Cloudflare Baseline
- Proxy DNS through Cloudflare.
- TLS mode: Full (Strict).
- Firewall rule for hostile ASN/IP reputation.
- Bot management enabled.
- Emergency mode for active incidents.

## AWS WAF Rate-Based Rule (Example)
```json
{
  "Name": "RateLimitPerIP",
  "Priority": 1,
  "Statement": {
    "RateBasedStatement": {
      "Limit": 2000,
      "AggregateKeyType": "IP"
    }
  },
  "Action": { "Block": {} },
  "VisibilityConfig": {
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "RateLimitPerIP"
  }
}
```

## Nginx Controls
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
limit_conn_zone $binary_remote_addr zone=addr:10m;

server {
  location /api/ {
    limit_req zone=api burst=20 nodelay;
    limit_conn addr 20;
    proxy_read_timeout 30s;
    proxy_connect_timeout 5s;
    proxy_pass http://app_backend;
  }
}
```

## Application-Level Controls
- Rate limit by user ID/API key, not only IP.
- Cost-based quotas for expensive endpoints.
- CAPTCHA/challenge for suspicious traffic.
- Protect auth, search, and export endpoints with stricter limits.

## Operational Playbook
1. Detect: threshold alerts on req/s, error rate, and latency.
2. Contain: tighten WAF/rate limits and disable nonessential features.
3. Stabilize: scale horizontally and enable cache for hot paths.
4. Recover: restore normal policy in stages.
5. Review: incident timeline, root cause, and control improvements.

## Monitoring Metrics
- Requests per second by endpoint.
- 4xx/5xx rate and tail latency (p95/p99).
- WAF blocked/challenged requests.
- Origin CPU/memory/connection pool utilization.
- Cache hit ratio.

## Checklist
- [ ] CDN/WAF active for public traffic
- [ ] L7 rate limiting enabled at edge and app
- [ ] Auth/search/export endpoints have strict limits
- [ ] DDoS runbook documented and tested
- [ ] Alert thresholds defined and reviewed
