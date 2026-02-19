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
