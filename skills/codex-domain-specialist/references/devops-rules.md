# Devops Rules

## Scope and Triggers

Use this reference for containerization, CI/CD policy, deployment strategy, runtime observability, and rollback safety.

Primary triggers:
- Dockerfile or pipeline changes
- deployment, release, rollback, canary, blue-green decisions
- runtime instability requiring operational mitigation
- environment configuration and secret handling updates
- server management tasks: process health, scaling, node maintenance, and incident recovery

Secondary triggers:
- scaling and capacity planning adjustments
- incident response involving deployment process

Out of scope:
- local feature-only code edits without build or runtime impact

## Core Principles

- Build immutable, reproducible artifacts.
- Keep deployment steps deterministic and auditable.
- Separate build, test, and release gates clearly.
- Prefer safe rollout patterns over speed-only deployment.
- Treat observability as a release requirement.
- Keep rollback simple, fast, and well-tested.
- Externalize configuration and secrets management.
- Minimize blast radius through staged rollout.
- Automate repetitive release tasks with guardrails.
- Keep incident response paths documented and practiced.

## Decision Tree

### Decision Tree A: Deployment Strategy Selection

- If change risk is high and traffic is large, use canary rollout.
- If infrastructure supports dual environments, use blue-green for fast rollback.
- If change is low-risk and internal, rolling deploy may be sufficient.
- If schema and app deploy are coupled, split into compatible phases.
- If rollback is complex, gate release behind stronger pre-prod checks.
- If dependency changes are major, add extended soak period before full rollout.

### Decision Tree B: Pipeline and Artifact Matrix

| Stage | Required Controls | Avoid |
| --- | --- | --- |
| build | locked dependency resolution + deterministic artifact | mutable build environments |
| test | unit/integration/gate checks | skipping tests for convenience |
| security | dependency scan and secret checks | deploying with unresolved critical findings |
| deploy | staged rollout and health checks | blind full rollout |
| observe | metrics, logs, and alert validation | release without telemetry baselines |
| rollback | one-command or scripted rollback path | manual ad hoc recovery |

## Implementation Patterns

- Use multi-stage Docker builds for small secure images.
- Pin base images and dependencies for repeatability.
- Run app as non-root user in container.
- Keep CI pipeline modular with parallel quality stages.
- Use environment-specific config through secret management.
- Enforce required checks before merge and before deploy.
- Implement canary and automatic rollback thresholds.
- Store deployment metadata and changelog per release.
- Add readiness and liveness probes for service health.
- Maintain infrastructure as code for environment parity.
- Use smoke tests immediately after deployment.
- Monitor SLO-focused metrics during rollout window.
- Keep runbooks for incident triage and rollback.
- Validate migration order for app and data changes.
- Automate post-release verification reports.

## Anti-Patterns

1. ❌ Bad: Building images with floating tags only.
   ✅ Good: Pin container images with immutable version tags and digests for reproducible deployments.

2. ❌ Bad: Running production containers as root.
   ✅ Good: Run containers as non-root, drop unnecessary capabilities, and enforce least privilege.

3. ❌ Bad: Skipping gate checks to expedite deploy.
   ✅ Good: Keep mandatory CI gates and require explicit approval workflow for emergency bypasses.

4. ❌ Bad: Deploying and migrating schema in unsafe order.
   ✅ Good: Deploy backward-compatible code first, then run migrations, then enable new code paths.

5. ❌ Bad: Releasing without health checks and alert baselines.
   ✅ Good: Define readiness/liveness/smoke checks and alert thresholds before promotion.

6. ❌ Bad: Storing secrets in CI logs or plaintext config.
   ✅ Good: Store secrets in managed secret stores and mask values in logs and pipeline output.

7. ❌ Bad: Making manual production changes outside tracked pipeline.
   ✅ Good: Route all production changes through versioned automation with audit trail.

8. ❌ Bad: Using one giant pipeline job with hidden failure points.
   ✅ Good: Split pipeline into explicit stages with clear pass/fail visibility per stage.

9. ❌ Bad: Ignoring rollback rehearsal for critical services.
   ✅ Good: Rehearse rollback in staging and keep one-command rollback instructions current.

10. ❌ Bad: Overloading deployment scripts with business logic.
   ✅ Good: Keep deployment scripts infrastructure-focused and place business logic in application code.

11. ❌ Bad: Allowing silent config drift between environments.
   ✅ Good: Manage config as code and run automated drift checks between environments.

12. ❌ Bad: Treating canary alarms as non-blocking noise.
   ✅ Good: Use canary SLO breaches as automatic hold or rollback signals.

13. ❌ Bad: Missing ownership for release failure response.
   ✅ Good: Assign release on-call owner and escalation chain before each deployment.

14. ❌ Bad: Relying on tribal knowledge instead of runbooks.
   ✅ Good: Maintain versioned runbooks with exact commands, owners, and recovery criteria.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Are container images pinned by version and digest?
- [ ] Yes/No: Are runtime security settings (non-root and least privilege) enforced?
- [ ] Yes/No: Are CI/CD stages separated with mandatory quality gates?
- [ ] Yes/No: Is deployment order safe relative to schema and config changes?
- [ ] Yes/No: Is release ownership and escalation path explicitly assigned?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Do pipeline checks include build, tests, and security scans for this change?
- [ ] Yes/No: Do readiness, liveness, and smoke checks pass in the target environment?
- [ ] Yes/No: Has rollback been rehearsed successfully in staging recently?
- [ ] Yes/No: Are secret scanning and policy checks passing without unresolved critical findings?
- [ ] Yes/No: Is configuration drift detection active and green across environments?

## Cross-References

- `backend-rules.md` for service resilience and contract ownership.
- `security-rules.md` for secret management and hardening expectations.
- `testing-rules.md` for CI test layering and gate design.
- `performance-rules.md` for release-time budget monitoring.
- `database-rules.md` for migration sequencing and recovery.
- `debugging-rules.md` for incident triage and root-cause workflow.

### Scenario Walkthroughs

- Scenario: Canary deployment shows 5xx error spike after 10% traffic shift.
  - Action: Freeze rollout automatically at canary stage and compare logs/metrics against baseline.
  - Action: Trigger rollback command and open incident timeline with assigned release owner.
- Scenario: Schema migration runs before app version that supports it.
  - Action: Reorder pipeline to deploy backward-compatible app before migration step.
  - Action: Add pipeline guard that blocks migration if compatibility check fails.
- Scenario: Secret appears in CI artifact logs during deployment.
  - Action: Rotate exposed credential immediately and revoke old token/session.
  - Action: Add masking policy and log scrub checks to prevent recurrence.

### Delivery Notes

- Keep this reference aligned with project conventions and postmortems.
- Update checklists when recurring defects reveal missing guardrails.
- Prefer incremental adoption over large risky rewrites.
