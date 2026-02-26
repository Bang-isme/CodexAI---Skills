# Performance Profiling

## Core Web Vitals Targets

| Metric | Good | Needs Work | Poor |
| --- | --- | --- | --- |
| LCP | < 2.5s | 2.5-4s | > 4s |
| INP | < 200ms | 200-500ms | > 500ms |
| CLS | < 0.1 | 0.1-0.25 | > 0.25 |

## Bundle Analysis

```bash
npx vite-bundle-visualizer
npx webpack-bundle-analyzer dist/stats.json
```

Suggested budget:
- main bundle < 200KB gzip
- initial total < 500KB gzip

## React Optimization Patterns

- `React.memo` for expensive subtrees.
- `useMemo` for costly calculations.
- `useCallback` for stable callback identities.
- `lazy()` and route-level code splitting.

## Backend Profiling

- Node profiler: `node --prof` and `--prof-process`.
- Monitor p50/p95/p99 response times.
- Run `EXPLAIN ANALYZE` for slow queries.
- Track `process.memoryUsage()` for leak detection.
