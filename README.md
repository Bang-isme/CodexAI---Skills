# CodexAI Skill Pack

A production-grade skill framework for OpenAI Codex.
This pack standardizes how Codex handles engineering work from request intake to verified delivery.

## Executive Summary

CodexAI Skill Pack adds a structured operating model to Codex:
- Understand intent before coding.
- Use plans for complex work.
- Apply domain-specific guidance only when relevant.
- Enforce verification before completion claims.
- Persist project memory across sessions.
- Automate safe commit workflows with optional GPG signing.

Current baseline:
- Pack version: `8.2.0`
- Core skill folders: `11`
- System skill folders: `2`
- Core script inventory: `30`
- Smoke test baseline: `32/32` checks passing

## Why This Exists

Without explicit workflow constraints, AI coding tends to drift:
- weak requirement interpretation
- inconsistent validation
- context loss across sessions
- low trust in completion claims

This pack addresses those failure modes with deterministic skill contracts (`SKILL.md`) and script-backed verification.

## Architecture

```text
Master Instructions (P0)
  -> Intent Context Analyzer
  -> Plan Writer
  -> Workflow Autopilot
  -> Domain Specialist
  -> Context Engine (Project Genome)
  -> Execution Quality Gate
  -> Project Memory
  -> Docs Change Sync
  -> Git Autopilot
  -> Doc Renderer (optional)
```

## What Is Included

### Core Skills

| Skill | Primary Role | Script Count |
| --- | --- | --- |
| `codex-master-instructions` | Global behavior, process rules, completion policy | 0 |
| `codex-intent-context-analyzer` | Prompt normalization and intent structuring | 0 |
| `codex-plan-writer` | Verifiable implementation plan authoring | 0 |
| `codex-workflow-autopilot` | Task-to-workflow routing | 1 |
| `codex-domain-specialist` | Domain routing with context boundaries | 0 |
| `codex-context-engine` | Generate/load compressed project context maps | 0 |
| `codex-execution-quality-gate` | Lint/test/security/quality verification | 15 |
| `codex-project-memory` | Decisions, summaries, changelog, genome, analytics | 11 |
| `codex-docs-change-sync` | Code-diff to documentation impact mapping | 1 |
| `codex-git-autopilot` | Safe auto-commit pipeline with gate and push | 1 |
| `codex-doc-renderer` | DOCX rendering utility for visual checks | 1 |

### System Skills

| Skill | Role |
| --- | --- |
| `.system/skill-installer` | Install skills from curated list or GitHub |
| `.system/skill-creator` | Author and evolve skills with consistent structure |

## Repository Layout

```text
CodexAI---Skills/
|- skills/
|  |- codex-*/
|  |- .system/
|  |- templates/
|  |- tests/
|  |- VERSION
|  `- CHANGELOG.md
|- docs/
|- README.md
`- LICENSE
```

## Quick Start (5 Minutes)

### 1. Install Into Codex Home

Windows (PowerShell):

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

macOS/Linux:

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

### 2. Validate Installation

From repo root:

```bash
python skills/tests/smoke_test.py --verbose
```

Expected on current release: `32/32 passed`.

### 3. Run Your First Commands

- Environment check: `$codex-doctor`
- Generate project context map: `$codex-genome`
- Run quality gate: `$codex-execution-quality-gate`
- Log architectural decision: `$log-decision`

## Common Workflows

### Feature Development

1. Intent analysis and constraints normalization.
2. Plan generation for complex scope.
3. Implementation in bounded steps.
4. Quality gate execution.
5. Optional auto-commit and push.

### Bug Fixing

1. Root-cause-oriented debugging flow.
2. Smallest viable fix.
3. Re-verification with fresh evidence.
4. Feedback logging when AI correction is needed.

### Documentation Sync

1. Detect changed source files.
2. Map impacted docs candidates.
3. Review and apply documentation updates.

## Key Commands

| Intent | Command |
| --- | --- |
| Doctor check | `$codex-doctor` |
| Generate genome | `$codex-genome` |
| Compact memory | `$compact-context` |
| Run pre-commit style checks | `$pre-commit` |
| Smart tests | `$smart-test` |
| Predict blast radius | `$impact` |
| Session summary | `$session-summary` |
| Changelog generation | `$changelog` |
| Auto commit | `python auto_commit.py --project-root <path> --files <file1> <file2>` |

## Project Memory Model

Local memory artifacts are written under `<project-root>/.codex/`.

| Path | Purpose |
| --- | --- |
| `.codex/decisions/` | durable decision records |
| `.codex/sessions/` | session summaries and handoff context |
| `.codex/feedback/` | correction and feedback tracking |
| `.codex/context/` | project genome and module maps |
| `.codex/state/` | workflow state (for example gate counters) |

## Git Autopilot and Verified Commits

`codex-git-autopilot` provides a guarded commit pipeline:
1. collect task-scoped files
2. stage selected files
3. run pre-commit gate
4. generate conventional commit message
5. sign commit if GPG is configured
6. push to current remote branch

Key options:
- `--dry-run`
- `--skip-tests`
- `--no-push`
- `--setup-gpg`

Note:
- GitHub `Verified` badge requires both local signing and public key registration in GitHub settings.

## Dependencies

### Required

- Python `3.10+` recommended
- Git

### Optional (Feature-Specific)

- Node.js/npm/npx for JS-focused quality scripts
- GPG for signed commits
- Poppler and `pdf2image` for DOCX rendering

Install doc-renderer Python dependency:

```bash
pip install pdf2image
```

## Quality and Safety Guarantees

- JSON-first script output contracts for tool interoperability.
- Timeout coverage on subprocess-heavy scripts to avoid indefinite hangs.
- Error recovery and circuit-breaker guidance in master instructions.
- No force-push behavior in Git autopilot workflow.

## Release Management

- Current version source of truth: `skills/VERSION`
- Full release history: `skills/CHANGELOG.md`
- Semantic versioning at pack level

## Contributing

1. Update `SKILL.md` contract first.
2. Add scripts only when runtime/tool execution is required.
3. Keep outputs deterministic and machine-readable.
4. Update smoke tests for new scripts.
5. Sync documentation with behavior changes.

## Security and Data Handling

- Memory files are local by default.
- Review generated reports before sharing externally.
- Avoid committing private `.codex/` artifacts from product repositories.

## License

MIT. See `LICENSE`.
