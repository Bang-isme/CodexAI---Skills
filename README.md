# CodexAI Skill Pack

Production-oriented skill pack for OpenAI Codex.
It gives Codex a structured engineering workflow: classify requests, plan safely, execute with quality gates, persist project memory, and automate Git operations.

## Current Status

- Version: `8.2.0` (see `skills/VERSION`)
- Active skills: `11` domain skills + `2` system skills
- Core helper scripts: `30`
- Smoke validation: `32/32` script checks

## What This Pack Adds

- Deterministic skill contracts (`SKILL.md`) with clear activation rules
- Intent normalization before implementation
- Plan-first workflow for complex requests
- Context compression (`Project Genome`) for large repositories
- Quality verification gates before completion claims
- Persistent project memory (`.codex/decisions`, `.codex/sessions`, `.codex/context`)
- Auto-commit pipeline with CI gate + GPG signing support

## Skill Architecture

```text
Master Instructions (P0)
  -> Intent Context Analyzer
  -> Plan Writer
  -> Workflow Autopilot
  -> Domain Specialist
  -> Context Engine (Genome)
  -> Execution Quality Gate
  -> Project Memory
  -> Docs Change Sync
  -> Git Autopilot
  -> Doc Renderer (optional)
```

## Skill Catalog

| Skill | Purpose | Scripts |
| --- | --- | --- |
| `codex-master-instructions` | P0 behavior, governance, completion discipline | 0 |
| `codex-intent-context-analyzer` | Normalize prompts into actionable intent JSON | 0 |
| `codex-plan-writer` | Produce structured, verifiable implementation plans | 0 |
| `codex-workflow-autopilot` | Route tasks into executable workflow phases | 1 |
| `codex-domain-specialist` | Domain-specific guidance with strict context boundaries | 0 |
| `codex-context-engine` | Generate/load multi-layer project context maps | 0 |
| `codex-execution-quality-gate` | Lint/test/security/audit verification suite | 15 |
| `codex-project-memory` | Decisions, summaries, changelog, genome, analytics | 11 |
| `codex-docs-change-sync` | Map code diffs to impacted documentation candidates | 1 |
| `codex-git-autopilot` | Task-scoped commit pipeline with gate + GPG + push | 1 |
| `codex-doc-renderer` | DOCX render pipeline for visual fidelity checks | 1 |

## Repository Layout

```text
CodexAI---Skills/
|- skills/
|  |- codex-*/               # Skill folders
|  |- .system/               # Installer/creator system skills
|  |- templates/
|  |- tests/
|  |- VERSION
|  `- CHANGELOG.md
|- docs/
|- README.md
`- LICENSE
```

## Installation

Copy the full `skills/` content into your Codex home.

### Windows (PowerShell)

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

### macOS/Linux

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

## High-Value Commands

| Use Case | Command |
| --- | --- |
| Environment check | `$codex-doctor` |
| Generate project genome | `$codex-genome` |
| Compact old memory files | `$compact-context` |
| Run quality gate | `$codex-execution-quality-gate` |
| Log decision | `$log-decision` |
| Session summary | `$session-summary` |
| Generate changelog | `$changelog` |
| Auto commit/push | `python auto_commit.py --project-root <path> --files <files...>` |

## Validation

Run smoke tests from repo root:

```bash
python skills/tests/smoke_test.py --verbose
```

Expected result: all checks pass (`32/32` at version `8.2.0`).

## Dependencies

### Core Pack

- Python `3.10+` recommended
- Git

### Optional Runtime Tools

- Node.js/npm/npx (Playwright, Lighthouse, JS quality gates)
- GPG (for `codex-git-autopilot` verified commit workflow)
- Poppler + `pdf2image` (for `codex-doc-renderer`)

Install `pdf2image`:

```bash
pip install pdf2image
```

## Versioning and Release Notes

- Current version: `skills/VERSION`
- Detailed history: `skills/CHANGELOG.md`
- Semantic versioning is used for pack-level releases

## Contribution Guidelines

1. Update behavior contracts in `SKILL.md` first.
2. Keep script outputs machine-readable (JSON-first).
3. Add/adjust tests for new scripts or contract changes.
4. Run smoke test before commit.
5. Keep docs synchronized (`README`, `CHANGELOG`, relevant skill docs).

## Security and Data Scope

- Project memory is stored locally in `<project-root>/.codex/`.
- Review generated summaries/handoffs before external sharing.
- Do not commit sensitive data from `.codex/` artifacts into product repositories.

## License

MIT. See `LICENSE`.
