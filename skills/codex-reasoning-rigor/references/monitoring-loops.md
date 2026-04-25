# Monitoring Loops

Attach a monitoring loop to any workflow that will repeat or can drift. A monitoring loop turns a one-time improvement into a sustained practice.

## Monitoring Contract

Every monitoring loop must define these 4 fields:

| Field | Question It Answers | Example |
|---|---|---|
| `signal` | What do I observe? | Test pass rate per commit |
| `healthy` | What does good look like? | ≥95% pass rate, 0 flaky tests |
| `drift` | What does degradation look like? | Pass rate drops below 90%, flaky test count > 2 |
| `action` | What do I do when it goes red? | Quarantine flaky tests, investigate root cause, block merge |

## Real-World Monitoring Examples

### CI/CD Health

```yaml
signal: CI pipeline duration and pass rate
healthy:
  - Pipeline completes in < 10 minutes
  - Pass rate > 98% over last 20 runs
  - Zero infrastructure failures
drift:
  - Pipeline > 15 minutes (creeping test time)
  - Pass rate drops below 95%
  - Same test fails intermittently
action:
  - Profile slow tests → split or parallelize
  - Quarantine flaky tests → fix or delete within 1 sprint
  - Check runner resource limits
```

### Code Quality Trend

```yaml
signal: Lint errors, type errors, and TODO count per commit
healthy:
  - 0 lint errors in CI
  - 0 TypeScript strict errors
  - TODO count stable or decreasing
drift:
  - Lint warnings suppressed instead of fixed
  - `@ts-ignore` count increasing
  - TODO count growing > 5 per sprint
action:
  - Add lint-staged pre-commit hook
  - Review @ts-ignore additions in PR review
  - Schedule TODO cleanup sprint task
```

### Test Coverage

```yaml
signal: Line and branch coverage per module
healthy:
  - Core modules > 80% coverage
  - New code has > 90% coverage
  - No module drops more than 5% between releases
drift:
  - Coverage declining for 3+ consecutive PRs
  - New features shipped without tests
  - Coverage report shows untested critical paths
action:
  - Add coverage gate to CI (fail if below threshold)
  - Flag untested PRs in review
  - Prioritize test debt in next sprint
```

### API Performance

```yaml
signal: Response time percentiles (P50, P95, P99) and error rate
healthy:
  - P50 < 100ms, P95 < 500ms, P99 < 1s
  - Error rate < 0.1%
  - No endpoint > 2s at P99
drift:
  - P95 exceeds 500ms for 3+ consecutive measurements
  - Error rate spikes above 1%
  - Single endpoint degrades while others stay stable (N+1 query?)
action:
  - Profile slow endpoints with tracing
  - Check database query plans (EXPLAIN ANALYZE)
  - Add caching or pagination if data volume is the cause
```

### Dependency Health

```yaml
signal: Outdated dependencies, known vulnerabilities, peer conflicts
healthy:
  - `npm audit` shows 0 high/critical vulnerabilities
  - No dependency > 2 major versions behind
  - Zero peer dependency warnings
drift:
  - `npm audit` shows new high/critical
  - Framework (React, Next.js) is 2+ major versions behind
  - Peer dependency warnings appear after install
action:
  - Run `npm audit fix` for auto-fixable issues
  - Schedule major version upgrades as sprint tasks
  - Pin problematic transitive dependencies
```

### Documentation Freshness

```yaml
signal: Docs last-modified date vs code last-modified date
healthy:
  - API docs updated within same PR as API change
  - README matches current setup steps
  - Architecture diagrams reflect current service map
drift:
  - Code changed 10+ commits ago, docs unchanged
  - README setup steps fail on fresh clone
  - Architecture diagram shows removed services
action:
  - Add docs-change-sync check to PR template
  - Test README steps quarterly (or use CI)
  - Update architecture diagrams during sprint review
```

## Anti-Drift Rules

If a workflow improvement depends on human memory alone, it will decay. Prefer automated enforcement:

| Human Memory | Automated Alternative |
|---|---|
| "Remember to run tests" | Pre-commit hook or CI gate |
| "Keep coverage above 80%" | Coverage threshold in CI config |
| "Update docs when API changes" | `codex-docs-change-sync` script in PR workflow |
| "Review TODOs regularly" | Scheduled TODO scan report |
| "Check for vulnerabilities" | `npm audit` in CI pipeline |

## When to Attach a Monitoring Loop

| Situation | Monitoring Needed? |
|---|---|
| One-time bug fix | ❌ No (but regression test = yes) |
| New CI workflow | ✅ Yes — monitor pipeline health |
| Performance optimization | ✅ Yes — monitor P95 trend |
| Dependency upgrade | ✅ Yes — monitor for regressions |
| New team process | ✅ Yes — monitor adoption rate |
| Architecture change | ✅ Yes — monitor error rate and latency |
| Documentation improvement | ⚠️ Maybe — if docs frequently drift |

## Template

Use this template when adding a monitoring loop to any recommendation:

```markdown
### Monitoring

| Signal | Healthy | Drift | Action |
|---|---|---|---|
| <what to observe> | <what good looks like> | <what bad looks like> | <concrete next step> |

**Check frequency:** <daily / per-PR / per-sprint / per-release>
**Owner:** <role or person>
```
