---
name: deploy
trigger: $deploy
loads: [codex-workflow-autopilot, codex-execution-quality-gate, codex-git-autopilot]
---

# Workflow Alias: $deploy

## Trigger

Use for shipping, pre-release checks, rollback readiness, or deployment hardening.

## Step Outline

1. Load `workflow-deploy.md` and run the full release gate sequence.
2. Check security, bundle health, lint or type gates, and runtime smoke coverage.
3. Use `with_server.py` when Lighthouse or browser automation needs a controlled URL.
4. Generate release notes or changelog output before the final ship decision.
5. Confirm rollback path, outstanding warnings, and explicit ship or no-ship call.

## Exit Criteria

- No unresolved critical security findings remain.
- Deploy evidence is current and repeatable.
- Changelog and rollback path are ready before release.
