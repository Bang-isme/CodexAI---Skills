# Deployment Strategy

## Strategy Comparison

| Strategy | Downtime | Risk | Rollback | Best For |
| --- | --- | --- | --- | --- |
| Rolling | Zero | Low | Moderate | Standard deployment |
| Blue-Green | Zero | Low | Instant | High-availability apps |
| Canary | Zero | Lowest | Instant | Large user base |
| Recreate | Brief | Medium | Redeploy | Dev/staging |

## Blue-Green Model

Load balancer routes traffic to blue (current) and green (new). Switch to green after validation. Rollback by switching back to blue.

## Rollback Checklist

- Migration rollback path exists.
- Previous image/tag retained.
- Feature flags available for kill switch.
- Alerts configured for error spikes.
- Manual rollback runbook documented.
