# Workflow: Deploy
Use this workflow for pre-deployment verification and ship preparation.
## Steps
1. Run `security_scan.py` for critical vulnerability check.
2. Run `bundle_check.py` for dependency health verification.
3. Run `pre_commit_check.py` for final lint/type check.
4. Run `lighthouse_audit.py` for runtime performance baseline (web projects).
5. Run `playwright_runner.py --mode run` for E2E smoke tests (if configured).
6. Generate changelog via `generate_changelog.py` for release documentation.
7. Review all findings and confirm ship decision.
## Exit Criteria
- Zero critical security findings.
- All E2E smoke tests pass (if applicable).
- Lighthouse scores above project thresholds (if applicable).
- Changelog generated for the release.
## Common Pitfalls
- Shipping with "medium" security findings without explicit acknowledgment.
- Skipping E2E tests because "unit tests passed" - different failure surface.
- Not generating changelog, making release history untraceable.
- Running Lighthouse without `with_server.py` - audit fails silently on dead URL.
## Example Sequence
1. `security_scan.py --project-root .` -> 0 critical, 2 medium (acknowledged)
2. `bundle_check.py --project-root .` -> no anomalies
3. `pre_commit_check.py --project-root .` -> pass
4. `with_server.py --server "npm run dev" --port 3000 -- python lighthouse_audit.py --url http://localhost:3000`
5. `playwright_runner.py --project-root . --mode run`
6. `generate_changelog.py --project-root . --version "v2.1.0" --output CHANGELOG.md`
7. Confirm ship
## When to Escalate
- Critical security finding -> block deploy, fix immediately via workflow-debug.
- Lighthouse performance score < 50 -> investigate via workflow-debug before shipping.
- E2E failures -> do not ship, investigate root cause first.
