# Feature Flags

## Scope

Use for progressive rollout, canary releases, A/B testing, and kill-switch behavior.

## Simple Implementation

```javascript
const features = {
  NEW_DASHBOARD: { enabled: true, rolloutPercent: 100 },
  DARK_MODE: { enabled: true, rolloutPercent: 50 },
  EXPORT_CSV: { enabled: false, rolloutPercent: 0 },
  BETA_AI_SEARCH: { enabled: true, rolloutPercent: 10, allowList: ['admin'] },
};

const isFeatureEnabled = (featureName, user = null) => {
  const flag = features[featureName];
  if (!flag || !flag.enabled) return false;
  if (flag.allowList?.includes(user?.role)) return true;
  if (flag.rolloutPercent >= 100) return true;
  if (!user?.id) return false;

  const hash = simpleHash(user.id + featureName) % 100;
  return hash < flag.rolloutPercent;
};
```

## Rollout Strategy

| Phase | Rollout | Duration | Action |
| --- | --- | --- | --- |
| Internal | allow-list only | 1 week | Team testing |
| Canary | 5% | 2-3 days | Monitor failures/latency |
| Beta | 25% | 1 week | Collect feedback |
| GA | 100% | ongoing | Remove flag after stabilization |

## Rules

- Every flag has owner and expiry date.
- Clean up flags shortly after full rollout.
- Code must work with flag ON and OFF.
- Avoid nested feature flags.
