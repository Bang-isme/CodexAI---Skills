# CodexAI Scrum Agent Kit

This bundle is installed into a project-local `.agent/` folder by `install_scrum_subagents.py`.
The same installer also renders companion native Codex custom agents into `.codex/agents/`.

## Contents

- `agents/`: role briefs for Scrum core roles and delivery specialists
- `workflows/`: ceremony and release playbooks
- `services/`: lightweight manifests for tooling or docs surfaces
- `ARCHITECTURE.md`: flow diagram and operating model
- `.codex/agents/*.toml`: native Codex custom agents generated from the role briefs

## Operating Model

1. Start with `product-owner` when value, scope, or acceptance criteria are unclear.
2. Use `scrum-master` to shape sprint flow, blockers, and ceremony outputs.
3. Pull in `solution-architect` before large cross-cutting implementation.
4. Use delivery specialists for implementation, QA, security, and release.
5. Close the loop with review, retro, and release-readiness workflows.

## Integration Rule

These subagents are thin coordination layers. They are meant to invoke the deeper CodexAI skills already installed in the user environment instead of duplicating the reference knowledge inside this bundle.
