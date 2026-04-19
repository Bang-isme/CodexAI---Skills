# Performance Profiling

**Load when:** diagnosing slow pages, optimizing bundle size, fixing memory leaks, investigating slow queries, or meeting performance budgets.

## Core Web Vitals Targets

| Metric | Good | Needs Work | Poor | What It Measures |
| --- | --- | --- | --- | --- |
| LCP | < 2.5s | 2.5-4s | > 4s | Largest content paint (perceived load speed) |
| INP | < 200ms | 200-500ms | > 500ms | Interaction to Next Paint (responsiveness) |
| CLS | < 0.1 | 0.1-0.25 | > 0.25 | Cumulative Layout Shift (visual stability) |
| TTFB | < 800ms | 800ms-1.8s | > 1.8s | Time to First Byte (server response) |

## Frontend Bundle Analysis

### Tooling

```bash
# Vite
npx vite-bundle-visualizer

# Webpack
npx webpack-bundle-analyzer dist/stats.json

# Next.js
ANALYZE=true npm run build  # with @next/bundle-analyzer
```

### Budget Targets

| Asset | Budget (gzipped) | Action If Exceeded |
| --- | --- | --- |
| Main JS bundle | < 200KB | Code-split, tree-shake |
| Initial total (JS+CSS) | < 500KB | Lazy-load below-fold |
| Single route chunk | < 50KB | Extract shared deps |
| CSS total | < 100KB | Purge unused CSS |
| Images (per image) | < 200KB | WebP/AVIF, responsive srcset |

### Code Splitting Strategy

```javascript
// Route-level splitting (React)
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));

// Component-level splitting (heavy libs)
const ChartWidget = lazy(() => import('./components/ChartWidget'));
// Only loads Recharts when ChartWidget renders

// Vendor splitting (vite.config.js)
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom'],
        charts: ['recharts'],
        editor: ['@monaco-editor/react'],
      }
    }
  }
}
```

## React Performance Optimization

### When to Optimize (Decision Table)

| Symptom | Tool | Fix |
| --- | --- | --- |
| Entire page rerenders on keystroke | React DevTools Profiler | `React.memo` on stable subtrees |
| Slow list rendering (1000+ items) | Profiler + why-did-you-render | Virtualization (`react-window`) |
| Expensive calculation on every render | Console timing | `useMemo` for derived data |
| Child rerenders from parent callback | Profiler highlight updates | `useCallback` for event handlers |
| Initial load > 3s | Lighthouse + bundle analyzer | Code splitting + lazy loading |

### Anti-Patterns

```javascript
// ❌ BAD: New object/array on every render
<Child style={{ color: 'red' }} items={data.filter(x => x.active)} />

// ✅ GOOD: Stable references
const style = useMemo(() => ({ color: 'red' }), []);
const activeItems = useMemo(() => data.filter(x => x.active), [data]);
<Child style={style} items={activeItems} />

// ❌ BAD: Premature memo (simple component, no expensive render)
const Label = memo(({ text }) => <span>{text}</span>); // Overhead > benefit

// ✅ GOOD: Memo for expensive subtrees
const DataTable = memo(({ rows, columns }) => {
  // Complex table rendering with 1000+ rows
  return <Table>{/* ... */}</Table>;
});
```

## Backend Performance Profiling

### Node.js Profiling

```bash
# CPU profiling
node --prof app.js
node --prof-process isolate-*.log > profile.txt

# Heap snapshot (memory leak detection)
node --inspect app.js
# Then: Chrome DevTools → Memory → Take heap snapshot

# Clinic.js (comprehensive)
npx clinic doctor -- node app.js
npx clinic flame -- node app.js
npx clinic bubbleprof -- node app.js
```

### Response Time Monitoring

```javascript
// Middleware: track p50/p95/p99
const responseMetrics = [];

app.use((req, res, next) => {
  const start = process.hrtime.bigint();
  res.on('finish', () => {
    const ms = Number(process.hrtime.bigint() - start) / 1e6;
    responseMetrics.push({ path: req.path, method: req.method, ms, status: res.statusCode });
    if (responseMetrics.length > 10000) responseMetrics.shift();
  });
  next();
});

// Endpoint to check percentiles
app.get('/api/metrics/response-times', (req, res) => {
  const sorted = [...responseMetrics].sort((a, b) => a.ms - b.ms);
  const p = (pct) => sorted[Math.floor(sorted.length * pct / 100)]?.ms || 0;
  res.json({ p50: p(50), p95: p(95), p99: p(99), count: sorted.length });
});
```

## Database Query Profiling

### Slow Query Detection

```sql
-- PostgreSQL: find slow queries
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Explain analyze
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE user_id = 123 AND status = 'pending';
```

```javascript
// MongoDB: slow query profiling
db.setProfilingLevel(1, { slowms: 100 }); // Log queries > 100ms
db.system.profile.find().sort({ ts: -1 }).limit(10);

// Mongoose: query timing middleware
mongoose.plugin((schema) => {
  schema.pre(/^find/, function () { this._startTime = Date.now(); });
  schema.post(/^find/, function () {
    const ms = Date.now() - this._startTime;
    if (ms > 200) logger.warn(`Slow query: ${this.getFilter()} took ${ms}ms`);
  });
});
```

### Index Optimization Checklist

| Check | Action |
| --- | --- |
| Query uses full table scan | Add index on filter columns |
| Compound query (A + B) | Create compound index `{A: 1, B: 1}` |
| Sort without index | Add index matching sort order |
| Unused indexes | Drop to save write overhead |
| Covering query possible | Include projected fields in index |

## Memory Leak Detection

### Symptoms

- RSS grows continuously under constant load
- GC pauses increasing over time
- `process.memoryUsage().heapUsed` trends upward without plateau

### Detection Pattern

```javascript
// Periodic memory check
setInterval(() => {
  const { heapUsed, heapTotal, rss } = process.memoryUsage();
  logger.info('Memory', {
    heapUsedMB: Math.round(heapUsed / 1e6),
    heapTotalMB: Math.round(heapTotal / 1e6),
    rssMB: Math.round(rss / 1e6),
  });
}, 30000);
```

### Common Leak Sources

| Source | Pattern | Fix |
| --- | --- | --- |
| Event listeners | `emitter.on()` without cleanup | Use `once()` or cleanup in `beforeEach` |
| Closures holding refs | Callback retains large scope | Nullify after use |
| Global caches | Map/Set grows unbounded | Use LRU cache with max size |
| Timers | `setInterval` without `clearInterval` | Clean up on shutdown |
| DB connection pool | Connections not released | Ensure `pool.release()` in finally |

## Quick Profiling Workflow

1. **Measure first**: Lighthouse / `perf_hooks` / `EXPLAIN ANALYZE`.
2. **Identify bottleneck**: CPU? Memory? Network? Query?
3. **Fix the biggest one**: Don't scatter-optimize.
4. **Verify improvement**: Re-measure same metric.
5. **Set budget**: Prevent regression with CI checks.
