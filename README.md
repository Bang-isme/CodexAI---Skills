# CodexAI Skill Pack

Instruction-first skill framework for OpenAI Codex, designed for real developer workflows: analyze intent, plan execution, apply domain-specific guidance, run quality gates, and persist project memory across sessions.

## Why This Pack

- Standardize how Codex handles build, fix, debug, review, docs, and handoff tasks.
- Keep behavior in `SKILL.md` and use scripts only for tool-backed actions.
- Reduce regressions with verification scripts before completion.
- Improve long-term consistency with local project memory (`.codex/`).

## Skill Pipeline

```text
Intent Analyzer
  -> Plan Writer
  -> Workflow Autopilot
  -> Domain Specialist
  -> Execution Quality Gate
  -> Project Memory
  -> Docs Change Sync
```

## Repository Layout

```text
CodexAI---Skills/
|- skills/
|  |- codex-master-instructions/
|  |- codex-intent-context-analyzer/
|  |- codex-plan-writer/
|  |- codex-workflow-autopilot/
|  |- codex-domain-specialist/
|  |- codex-execution-quality-gate/
|  |- codex-project-memory/
|  |- codex-docs-change-sync/
|  |- codex-doc-renderer/
|  |- tests/
|- docs/
|- README.md
`- LICENSE
```

## Core Skills

- `codex-master-instructions`: Top-priority behavioral baseline.
- `codex-intent-context-analyzer`: Request parsing into structured intent JSON.
- `codex-plan-writer`: Plan file generation for medium/large tasks.
- `codex-workflow-autopilot`: Workflow routing and behavioral mode selection.
- `codex-domain-specialist`: Layered domain routing with context boundaries.
- `codex-execution-quality-gate`: Verification checks (lint, tests, security, audits).
- `codex-project-memory`: Decisions, handoff, session summaries, and learning loops.
- `codex-docs-change-sync`: Code-diff to documentation candidate mapping.
- `codex-doc-renderer`: DOCX-focused document rendering utility.

## Installation

Copy the `skills/` directory into your Codex home.

### Windows (PowerShell)

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

### macOS/Linux

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

## Quick Commands

- Quality gate: `$codex-execution-quality-gate`
- Pre-commit checks: `$pre-commit`
- Smart test selection: `$smart-test`
- Impact prediction: `$impact`
- Decision logging: `$log-decision`
- Session summary: `$session-summary`
- Handoff export: `$handoff`
- Changelog generation: `$changelog`
- Growth report: `$growth-report`
- Teaching mode: `$teach`

## Local Validation

Run smoke tests for script availability and help contracts:

```bash
python skills/tests/smoke_test.py --verbose
```

## Requirements

- Python 3.8+
- Git
- Node.js/npm (for Lighthouse/Playwright wrappers and related checks)

## Versioning

Current skill pack version is tracked in `skills/VERSION`.

## Contributing

1. Keep behavior changes in `SKILL.md` first.
2. Add scripts only for real tool/runtime execution.
3. Prefer deterministic JSON output for script contracts.
4. Update references and README when adding new capabilities.

## Security and Privacy

Project-memory artifacts are local by default under `<project-root>/.codex/`. Review generated handoff/summary files before sharing externally.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
