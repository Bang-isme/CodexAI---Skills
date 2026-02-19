# Workflow: Review

Use this workflow for technical review, risk assessment, and codebase quality evaluation.

## Steps

1. Run `tech_debt_scan.py` for structural debt signals.
2. Run `quality_trend.py --report` for historical quality direction.
3. Run `security_scan.py` for security findings.
4. Aggregate findings across functional, security, and maintainability dimensions.
5. Prioritize recommendations by severity and actionability.

## Exit Criteria

- Findings grouped by severity (`critical`, `high`, `medium`, `low`).
- Immediate blockers clearly separated from advisory improvements.
- Follow-up actions documented in priority order.

## Common Pitfalls

- Running only one check type (for example lint only) while skipping security and structural checks.
- Not aggregating findings across dimensions before reporting final recommendations.
- Presenting raw script output without severity prioritization and owner/action mapping.
- Treating advisory trends as optional noise even when they indicate sustained decline.
- Skipping follow-up ownership assignment after identifying repeated high-severity findings.
- Reporting findings without attaching a verification command for each recommended action.

## Example Sequence

1. Run technical debt scan:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\tech_debt_scan.py" --project-root .`
2. Run trend report for recent baseline:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\quality_trend.py" --project-root . --report --days 30`
3. Run security scan for risk exposure:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\security_scan.py" --project-root .`
4. Aggregate findings and group severity as `critical > high > medium > low`.
5. Present top findings with clear remediation actions, owner suggestions, and urgency labels.
6. If findings are broad and cross-domain, trigger deeper workflow review before sign-off.
7. If release readiness is unclear, run pre-commit intelligence against staged follow-up fixes:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\pre_commit_check.py" --project-root .`
8. For dependency-risk review context, run bundle signal check:
   `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\bundle_check.py" --project-root .`
9. Summarize decisions in a concise action matrix: blocker, owner, due window, and verification command.

## When to Escalate

- Critical security findings are present and require immediate patching; do not defer.
- Quality trend has declined for 3 or more snapshots and requires architecture review.
- Tech debt signals exceed 50 findings and indicate a dedicated refactor sprint is needed.
- Escalate to human release review when multiple critical findings remain unresolved at handoff time.
- Escalate to cross-team triage when findings require coordinated backend, frontend, and infrastructure remediation.
