---
name: release-readiness
description: Decide whether the increment is ready to ship based on quality, security, operations, and rollback evidence.
---

# Release Readiness

## Lead

`scrum-master`

## Support

`qa-engineer`, `security-engineer`, `devops-engineer`, `product-owner`

## Time-Box

30-45 minutes.

## Steps

1. **Quality gate review:** Run full quality gate and review results.
2. **Test status check:** Confirm all test suites pass (unit, integration, E2E).
3. **Security scan:** Review security findings — zero critical/high allowed.
4. **Performance check:** Verify Lighthouse/load test scores meet thresholds.
5. **Rollback plan:** Confirm rollback procedure exists and has been tested.
6. **Release notes:** Confirm changelog/release notes are complete and accurate.
7. **Stakeholder expectations:** Confirm PO has approved the increment for release.
8. **Go/No-Go decision:** Make explicit ship or no-ship decision with evidence.

## Go/No-Go Decision Matrix

| Criterion | Go ✅ | No-Go ❌ |
|---|---|---|
| **Tests** | All suites pass | Any critical test failing |
| **Security** | 0 critical, 0 high findings | Any critical or high finding |
| **Performance** | Scores meet thresholds | P95 exceeds SLA or Lighthouse < 50 |
| **Rollback** | Procedure documented and tested | No rollback plan |
| **Release notes** | Complete and reviewed | Missing or inaccurate |
| **PO approval** | Explicitly approved | Not reviewed by PO |
| **Known bugs** | Only low/cosmetic, documented | Any high-impact bug not documented |
| **Data migration** | Tested and reversible | Untested or irreversible |

**Decision rule:** ALL criteria must be "Go" for ship decision. Any "No-Go" blocks the release.

## Release Checklist

### Pre-Release

- [ ] Full test suite passes (`npm test`, E2E, integration)
- [ ] Security scan clean (`security_scan.py` → 0 critical/high)
- [ ] Performance baseline captured (Lighthouse, load test)
- [ ] Bundle size checked (`bundle_check.py`)
- [ ] Database migrations tested in staging
- [ ] Environment variables confirmed for production
- [ ] Feature flags configured correctly
- [ ] API versioning confirmed (if breaking changes)

### Release

- [ ] Changelog/release notes published
- [ ] Git tag created (`git tag -a vX.Y.Z`)
- [ ] Deployment triggered (CI/CD or manual)
- [ ] Smoke test in production after deploy
- [ ] Monitoring dashboards checked (error rate, response time)
- [ ] Stakeholders notified of release

### Post-Release (First 24h)

- [ ] Error rate stable (no spike vs pre-release)
- [ ] P95 response time stable
- [ ] No new critical bugs reported
- [ ] Rollback not triggered → release confirmed successful

## Rollback Plan Template

```markdown
### Rollback Plan — vX.Y.Z

**Trigger:** Rollback if any of:
- Error rate exceeds 5% in first 2 hours
- P95 response time exceeds 2x pre-release baseline
- Critical user-facing bug reported by 3+ users

**Procedure:**
1. Revert deployment: `[exact rollback command]`
2. Verify rollback: `curl -s /health` → 200 OK, version = previous
3. Revert database migration (if applicable): `[migration rollback command]`
4. Notify stakeholders: [channel/email]
5. Create incident report from `codex-document-writer` incident template

**Rollback owner:** [person/role]
**Communication channel:** [Slack/Teams channel]
```

## Deliverables

- Explicit ship / no-ship decision with evidence
- Go/No-Go matrix filled in
- Blocker list (if no-ship)
- Rollback plan documented
- Release notes / changelog
- Post-release monitoring plan

## Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| "Tests pass, let's ship" | Tests are necessary but not sufficient — check security, performance, rollback |
| No rollback plan | Never ship without a tested rollback procedure |
| Shipping on Friday afternoon | Ship early in the week with monitoring time available |
| Skipping staging validation | Always test in staging-like environment first |
| Release notes written after shipping | Write during sprint, finalize before release |
