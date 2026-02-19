# Bundle Check
## Purpose
Analyze dependencies for bundle size growth, duplication signals, and dependency risk patterns.
It provides a quick dependency health snapshot before release decisions.
## When to Run
- Before production deployment or release packaging.
- After adding or upgrading significant dependencies.
- During performance or bundle-size optimization work.
## How AI Uses It
1. Run `bundle_check.py` for the target project.
2. Review dependency counts, size signals, and duplication warnings.
3. Flag anomalies and recommend targeted follow-up checks.
## Integration Behavior
- Trigger on `$bundle-check` or "check bundle health".
- Auto-run for dependency-heavy change sets when context indicates risk.
- Advisory behavior only; findings are warnings, not completion blockers.
## Output Intent
- Summarize dependency and bundle health to support deployment readiness.
- Caveat: outputs are heuristic and should be combined with runtime profiling when needed.
