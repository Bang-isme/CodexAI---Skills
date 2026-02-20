# Codex AI Skill Pack
## Overview
This pack extends Codex with instruction-first workflows, quality checks, and project memory utilities.
It is designed for end-to-end engineering execution: analyze intent, plan, implement, verify, and preserve knowledge.
All skills are organized for progressive loading so AI uses only relevant context.
## Skill Pipeline
Intent Analyzer -> Plan Writer -> Workflow Autopilot -> Domain Specialist -> Quality Gate -> Project Memory -> Docs Sync
## Skills
| Skill | Purpose | Scripts | References |
|---|---|---|---|
| codex-master-instructions | P0 baseline behavior and coordination rules | -- | -- |
| codex-intent-context-analyzer | Normalize requests into actionable, confirmed intent | -- | -- |
| codex-plan-writer | Produce structured, verifiable implementation plans | -- | -- |
| codex-domain-specialist | Route technical tasks into focused domain guidance | -- | 16 refs |
| codex-workflow-autopilot | Map intent to execution workflow and behavioral modes | 1 | 9 refs |
| codex-execution-quality-gate | Run verification checks and aggregate ship-readiness signals | 15 | 14 refs |
| codex-project-memory | Persist decisions, handoffs, session context, and analytics | 9 | 9 refs |
| codex-docs-change-sync | Map code changes to impacted documentation candidates | 1 | 2 refs |
| codex-doc-renderer | Render documentation to DOCX format with visual checks | 1 | -- |
## Quick Commands
| What | Command |
|---|---|
| Run quality gate | `$codex-execution-quality-gate` |
| Log decision | `$log-decision` |
| Generate changelog | `$changelog` |
| Growth report | `$growth-report` |
| Session summary | `$session-summary` |
| Teach me | `$teach` |
| Plan task | `$codex-plan-writer` |
## Customization
- Domain rules: edit files in `codex-domain-specialist/references/`
- Gate policy: edit `codex-execution-quality-gate/references/gate-policy.md`
- Workflow templates: edit files in `codex-workflow-autopilot/references/workflow-*.md`
## Priority System
P0: codex-master-instructions > P1: domain references > P2: other skills
