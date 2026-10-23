# Deployment Strategy & Quantitative Rollback Runbook

**Load when:** deploying to production, designing release pipelines, coordinating database migrations with app rollouts, or authoring rollback runbooks.

---

## 1. Release Strategy Decision Matrix

| Strategy | Downtime | Rollback Speed | Best For | Key Prerequisite |
| --- | --- | --- | --- | --- |
| **Rolling Update** | Zero | Fast (`1–3 min` image re-pin) | Stateless APIs & web apps | Readiness probe + graceful `SIGTERM` drain |
| **Blue-Green** | Zero | Instant (`< 10s` router switch) | High-criticality services | Backward-compatible DB schema (Expand-and-Contract) |
| **Canary (5% -> 25% -> 100%)** | Zero | Instant (`< 10s` weight reset) | High-traffic user-facing changes | Automated SLO comparison between canary and stable cohorts |
| **Feature Flag Ring Rollout** | Zero | Instant (`< 1s` flag kill-switch) | Decoupling code deploy from feature release | Tested default-off fallback branch in code |

---

## 2. Quantitative Canary & Rollout Abort Criteria

Never promote a canary or complete a rollout "by gut feel". Define explicit quantitative abort thresholds before deploying:

| Telemetry Signal | Bake / Soak Window | Automatic Rollback / Abort Trigger |
| --- | --- | --- |
| **HTTP `5xx` Error Rate** | `15 min` at 5% traffic, `30 min` at 25% | Canary `5xx` rate > `1.0%` or > `2x` stable baseline |
| **Latency (`p95` / `p99`)** | `15 min` per step | Canary `p95` latency increases > `30%` over stable baseline |
| **Container CrashLoop / OOM** | Immediate (`0 min`) | Any `OOMKilled` or `> 1` container restart during rollout |
| **Database Lock / Pool Saturation** | `5 min` | Active DB pool > `90%` or lock-wait timeouts > `5/min` |

---

## 3. Production Rollback Runbook Template

Every production deployment must have a verified 3-step rollback plan:

1. **Application Rollback (First Response — `< 2 minutes`):**
   - Revert traffic weight to `100%` stable (Canary/Blue-Green), toggle off the feature flag kill-switch, or redeploy the previous immutable image digest (`myapp@sha256:...`).
2. **Database Compatibility Guarantee:**
   - Because all schema changes follow **Expand-and-Contract** (`data-migration.md`), the previous application version continues running cleanly against the expanded schema without requiring an immediate, risky destructive `DOWN` migration during an incident.
3. **Post-Rollback Verification:**
   - Confirm `GET /health/ready` returns `200 OK`, `5xx` rate returns to baseline (`< 0.1%`), and outbox/queue consumers drain normally. Log incident timeline and root-cause follow-up in `.codex/project-docs/devops/DO-05-incident-response.md`.
