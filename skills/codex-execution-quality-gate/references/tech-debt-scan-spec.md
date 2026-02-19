# Tech Debt Scan
## Purpose
Detect structural tech debt signals such as TODO and FIXME density, large files, deep nesting, and duplication.
It helps teams plan cleanup work with clear technical evidence.
## When to Run
- During review workflows and maintenance audits.
- On periodic quality checks for long-lived codebases.
- Before major refactors touching shared modules.
- On explicit `$tech-debt` requests.
## How AI Uses It
1. Run `tech_debt_scan.py` for the project root.
2. Parse debt signals and categorize by priority or severity.
3. Propose an actionable remediation order with smallest-highest-impact fixes first.
## Integration Behavior
- Trigger on `$tech-debt` or "run tech debt scan".
- Auto-run in review-oriented quality workflows.
- Advisory only and does not block completion in MVP.
## Output Intent
- Produce an actionable debt inventory for planning and prioritization.
- Caveat: heuristics can over-report in generated or intentionally verbose code areas.
