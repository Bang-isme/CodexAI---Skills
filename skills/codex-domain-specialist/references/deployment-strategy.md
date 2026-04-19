# Deployment Strategy

**Load when:** deploying to production, setting up CI/CD pipelines, planning rollback procedures, or choosing a release strategy.

## Strategy Decision Table

| Strategy | Downtime | Risk | Rollback Speed | Infrastructure Cost | Best For |
| --- | --- | --- | --- | --- | --- |
| Rolling | Zero | Low | Moderate (drain) | 1x | Standard apps, small teams |
| Blue-Green | Zero | Low | Instant (switch) | 2x | High-availability, quick rollback |
| Canary | Zero | Lowest | Instant (route) | 1.1x | Large user base, risk-averse |
| Recreate | Brief | Medium | Redeploy required | 1x | Dev/staging, stateful apps |
| Feature Flag | Zero | Lowest | Instant (toggle) | 1x | Gradual rollout, A/B testing |

## Blue-Green Deployment

Load balancer routes 100% traffic to blue (current). Deploy to green (new). Validate. Switch traffic.

```yaml
# docker-compose.blue-green.yml
services:
  app-blue:
    image: myapp:current
    ports: ["3001:3000"]
  app-green:
    image: myapp:next
    ports: ["3002:3000"]
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx-switch.conf:/etc/nginx/conf.d/default.conf
    ports: ["80:80"]
```

### Switch Script

```bash
#!/bin/bash
# switch-traffic.sh — Blue-Green traffic switch
set -euo pipefail

TARGET=${1:?Usage: switch-traffic.sh blue|green}
NGINX_CONF="/etc/nginx/conf.d/default.conf"

if [[ "$TARGET" == "green" ]]; then
  sed -i 's/app-blue:3000/app-green:3000/' "$NGINX_CONF"
elif [[ "$TARGET" == "blue" ]]; then
  sed -i 's/app-green:3000/app-blue:3000/' "$NGINX_CONF"
fi

nginx -s reload
echo "Traffic switched to $TARGET"
```

```powershell
# switch-traffic.ps1 — Blue-Green traffic switch (Windows/PowerShell)
param([Parameter(Mandatory)][ValidateSet("blue","green")]$Target)
$conf = "C:\nginx\conf\default.conf"
if ($Target -eq "green") {
  (Get-Content $conf) -replace 'app-blue:3000','app-green:3000' | Set-Content $conf
} else {
  (Get-Content $conf) -replace 'app-green:3000','app-blue:3000' | Set-Content $conf
}
& nginx -s reload
Write-Host "Traffic switched to $Target"
```

## Canary Deployment

Route small % of traffic to new version. Monitor error rates. Gradually increase.

```nginx
# nginx canary routing
upstream backend {
  server app-stable:3000 weight=95;
  server app-canary:3000 weight=5;
}
```

### Canary Promotion Checklist

1. Deploy canary (5% traffic).
2. Monitor for 15-30 minutes: error rate, p95 latency, memory.
3. If metrics stable → increase to 25%.
4. Monitor 1 hour → increase to 50%.
5. Monitor 2 hours → promote to 100%.
6. If ANY metric degrades → instant rollback to 0%.

## Pre-Deployment Verification Gate

```bash
#!/bin/bash
# pre-deploy-check.sh — Run BEFORE every deployment
set -euo pipefail

echo "=== Pre-deployment verification ==="

# 1. Tests pass
npm test || { echo "❌ Tests failed. Aborting deploy."; exit 1; }

# 2. Build succeeds  
npm run build || { echo "❌ Build failed. Aborting deploy."; exit 1; }

# 3. No security vulnerabilities (critical/high)
npm audit --audit-level=high || { echo "⚠️ Security issues found. Review before deploy."; exit 1; }

# 4. Environment variables present
node -e "
  const required = ['DATABASE_URL', 'JWT_SECRET', 'NODE_ENV'];
  const missing = required.filter(k => !process.env[k]);
  if (missing.length) { console.error('Missing env vars:', missing); process.exit(1); }
" || exit 1

echo "✅ All pre-deployment checks passed"
```

## Post-Deployment Smoke Tests

```javascript
// smoke-test.js — Run AFTER deployment
const endpoints = [
  { url: '/api/health', expect: 200 },
  { url: '/api/v1/status', expect: 200 },
  { url: '/login', expect: 200 },
];

const runSmoke = async (baseUrl) => {
  const results = [];
  for (const { url, expect } of endpoints) {
    const res = await fetch(`${baseUrl}${url}`);
    const pass = res.status === expect;
    results.push({ url, status: res.status, pass });
    if (!pass) console.error(`❌ ${url}: expected ${expect}, got ${res.status}`);
  }
  const failed = results.filter(r => !r.pass);
  if (failed.length) {
    console.error(`${failed.length} smoke tests failed. ROLLBACK RECOMMENDED.`);
    process.exit(1);
  }
  console.log(`✅ All ${results.length} smoke tests passed`);
};
```

## Rollback Checklist

| Step | Action | Verify |
| --- | --- | --- |
| 1 | Switch traffic back (blue-green) or scale down canary | Traffic metrics normal |
| 2 | Verify rollback migration exists | `migrate:down` runs clean |
| 3 | Confirm previous image/tag is retained | `docker images` shows old tag |
| 4 | Toggle feature flags to OFF | Features disabled in UI |
| 5 | Alert configured for error spike | PagerDuty/Slack fires on 5xx spike |
| 6 | Manual rollback runbook documented | Team can execute in <5 min |

## Zero-Downtime Database Migration Rules

1. **Additive only**: Add columns/tables in deploy N, use them in deploy N+1.
2. **Never rename/drop** in the same deploy that changes code.
3. **Backfill separately**: Data migration runs as background job, not in deploy script.
4. **Column removal sequence**: Stop reading → deploy → add migration to drop → deploy again.
5. **Test migration rollback**: Every `up` must have a working `down`.

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
| --- | --- | --- |
| Deploy on Friday 5pm | No team available for rollback | Deploy Mon-Thu morning |
| Skip smoke tests | Silent failures in production | Automated post-deploy smoke |
| Manual deployment steps | Human error, inconsistency | Automate with CI/CD |
| No rollback plan | Panic when things break | Document rollback before deploy |
| Destructive migrations in deploy | Data loss, broken rollback | Additive-only migrations |
