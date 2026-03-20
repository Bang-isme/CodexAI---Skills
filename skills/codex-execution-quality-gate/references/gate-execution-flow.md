# Gate Execution Flow

## Phase X Verification Order

| Priority | Check | Script | Blocking |
| --- | --- | --- | --- |
| P-1 | impact predictor (pre-edit advisory) | `scripts/predict_impact.py` | warning only |
| P0 | security scan | `scripts/security_scan.py` | yes for critical findings |
| P1 | lint | `scripts/run_gate.py` | yes when detected lint exits 1 |
| P2 | tests | `scripts/run_gate.py` | yes when detected tests exit 1 |
| P3 | bundle/dependency check | `scripts/bundle_check.py` | warning only |
| P4 | tech debt scan | `scripts/tech_debt_scan.py` | warning only |
| P5 | improvement suggester (post-task) | `scripts/suggest_improvements.py` | warning only |
| P6 | output rigor guard | `scripts/output_guard.py` | warning only |
| P7 | editorial review | `scripts/editorial_review.py` | warning only unless strict deliverable gate is active |
| P8 | quality trend tracker (periodic) | `scripts/quality_trend.py` | warning only |
| P9 | UX static audit (pre-UI delivery) | `scripts/ux_audit.py` | warning only |
| P10 | accessibility static checker | `scripts/accessibility_check.py` | warning only |
| P11 | Lighthouse runtime audit | `scripts/lighthouse_audit.py` | warning only |
| P12 | Playwright setup/run helper | `scripts/playwright_runner.py` | warning only |
| P13 | server lifecycle helper (optional) | `scripts/with_server.py` | warning only |

## Execution

1. Run `run_gate.py` with project root.
2. Run `security_scan.py` with project root.
3. Optionally run `bundle_check.py` with project root.
4. Optionally run `tech_debt_scan.py` with project root.
5. Optionally run `suggest_improvements.py` after complex tasks.
6. Optionally run `output_guard.py` on plans, summaries, or recommendations that must avoid generic filler.
7. Optionally run `editorial_review.py` when the output must sound accountable, decision-ready, and less AI-generic.
8. Optionally run `predict_impact.py` before high-risk edits.
9. Optionally run `quality_trend.py --record` on periodic cadence.
10. Optionally run `ux_audit.py` before UI handoff.
11. Optionally run `accessibility_check.py` for public-facing surfaces.
12. Optionally run `lighthouse_audit.py` before deploy (requires running server URL).
13. Optionally run `playwright_runner.py` for E2E setup/check/run flows.
14. Optionally run `with_server.py` to bootstrap local server(s) before Lighthouse/Playwright checks.
15. Merge results and decide pass/fail.

## Decision Rules

- Completion allowed only if no blocking failures remain.
- Blocking failures must be fixed, then checks rerun.
- Warning-only outcomes may proceed with explicit warning to user.
- Tech debt scan is advisory in MVP and does not block completion.
- Improvement suggestions are advisory and do not block completion.
- Impact prediction is advisory and does not block completion.
- Output rigor guard is advisory for generic writing, but plans, reviews, and handoffs should default to strict-output enforcement unless the caller intentionally downgrades them with `--advisory-output`.
- Editorial review is advisory by itself, but strict plans, reviews, and handoffs should also satisfy the editorial rubric so the deliverable reads like a human-made artifact.
- Quality trend reporting is periodic and advisory and does not block completion.
- UX static audit is advisory and does not block completion.
- Accessibility static checker is advisory and does not block completion.
- Lighthouse wrapper is advisory and must fail gracefully when tool/server is unavailable.
- Playwright wrapper is advisory and must fail gracefully when tool/setup is unavailable.
- Server lifecycle helper is advisory and should be used only when runtime checks need controlled startup/shutdown.

## Override

If user says `skip gate` or `force complete`, comply and warn:
"Quality gate skipped. Lint/test/security status is unknown."

## Output Handling

For each script:

1. capture output
2. summarize errors/warnings/passes
3. ask whether to fix blocking errors when present
4. rerun after fixes to verify
