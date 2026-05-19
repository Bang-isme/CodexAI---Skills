# Project Memory Artifact Lifecycle Policy

**Policy:** hybrid — contracts and schemas are source-controlled; runtime-generated artifacts are not committed.

## Committed (source of truth)

| Path | Role |
|------|------|
| `skills/codex-project-memory/references/*.schema.json` | JSON Schema for artifacts and tool manifest |
| `skills/codex-project-memory/references/project-memory-tools.json` | Machine-readable CLI/tool harness contract |
| `skills/codex-project-memory/scripts/dashboard_template.html` | Dashboard HTML template baked into builds |
| `skills/codex-project-memory/references/*.md` | Human specs and command docs |

## Generated at runtime (do not commit)

| Path | Producer | Notes |
|------|----------|-------|
| `.codex/knowledge/index.json` | `build_knowledge_index.py` | Primary knowledge index (schema v2) |
| `.codex/knowledge/knowledge-graph.json` | `build_knowledge_index.py` | In-knowledge-dir graph copy |
| `.codex/knowledge/codebase-index.json` | `build_knowledge_index.py` | Symbol/chunk index |
| `.codex/knowledge/index.html` | `build_knowledge_index.py` | Offline dashboard |
| `.codex/knowledge/index-progress.json` | `build_knowledge_index.py` | Incremental build progress |
| `.codex/knowledge-graph.json` | `build_knowledge_graph.py` | Standalone graph (optional for `memory_status`) |
| `.codex/context/genome.md` | `generate_genome.py` | Project genome |
| `.codex/feedback/*.md` | `track_feedback.py` | Feedback logs |

Root `.gitignore` already ignores `.codex/`, so these paths are verification evidence only unless a maintainer explicitly snapshots examples for docs.

## Local / IDE paths (not product artifacts)

| Path | Policy |
|------|--------|
| `.cursor/plans/*` | IDE planning scratch — do not commit |
| `.commandcode/*` | Local command/plan scratch — do not commit |
| `skills/.codex/`, `skills/.analytics/` | Skill-pack local state — ignored via `.gitignore` |

## Snapshot exception

No generated dashboard or index files are committed by default. If a future doc needs a frozen example, add it under `skills/codex-project-memory/references/examples/` with redacted fixtures, not live `.codex/knowledge/` output from a developer machine.

## Validator alignment

`memory_status.py` treats:

- `.codex/knowledge/index.json` and `.codex/knowledge/knowledge-graph.json` as **required** (fail if missing/invalid).
- `.codex/knowledge/codebase-index.json` and `index.html` as **optional** (warn).
- `.codex/knowledge-graph.json` (standalone) as **optional** by default; use `--require-standalone-graph` when CI must enforce it.
