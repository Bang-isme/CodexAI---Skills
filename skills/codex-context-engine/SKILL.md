---
name: codex-context-engine
description: Use when a project has 50+ files, missing context, or explicit $codex-genome request; generates multi-layer project context to reduce hallucination.
load_priority: always
---

## TL;DR

Generate `.codex/context/genome.md` for macro project understanding. Load `genome.md` automatically if it exists. For large projects, also generate per-module maps. This reduces hallucination by giving AI compressed project knowledge instead of raw file scanning.

# Context Engine (Project Genome)

## Activation

1. **Auto-load:** If `.codex/context/genome.md` exists in the project, load it at session start.
2. **Auto-suggest:** If project has 50+ files and no `genome.md` exists, suggest generating one.
3. **Explicit:** On `$codex-genome`, `$generate-genome`, or `$genome` command.

## Quick Commands

- `$codex-genome` / `$genome` - Generate or refresh project genome
- `$codex-genome --force` / `$genome --force` - Force regeneration

## When to Generate

| Project Size | Action |
| --- | --- |
| < 50 files | Optional. Suggest only if user asks |
| 50-500 files | Suggest on first encounter. Shallow depth (`genome.md` only) |
| 500+ files | Strongly recommend. Full depth (`genome.md` + module maps) |

## When to Load

- **genome.md:** Load at session start if it exists. This is your project briefing - read it before any code edit.
- **Module maps:** Load only the module(s) relevant to the current task. Never load all module maps at once.

## How to Use Context

Follow the 4-Tier Unified Memory Architecture (`../codex-project-memory/references/unified-memory-architecture.md`):
- **Tier 1 (L0):** Check `.codex/profile.json` and active session/pulse state first.
- **Tier 2 (L1):** Load `.codex/context/genome.md` and `.codex/knowledge/INDEX.md` for macro orientation.
- **Tier 3 (L2):** Honor active `.codex/specs/<slug>/SPEC.md`, `DESIGN.md`, and `.codex/decisions/*.md` as normative authority over generated summaries.
- **Tier 4 (L3):** Load only the active role's `.codex/project-docs/<role>/*.md` and `.codex/context/modules/{module-name}.md`.

After loading `genome.md`:

1. You now know the tech stack, directory structure, entry points, data models, API surface, and coding conventions.
2. When working on a specific module, check if `.codex/context/modules/{module-name}.md` exists and load it.
3. Use this knowledge to avoid:
   - Guessing import paths (genome tells you the structure)
   - Wrong naming conventions (genome tells you the patterns)
   - Missing dependencies (genome tells you module boundaries)
   - Hallucinating APIs (genome tells you the real routes)

## Script Invocation

- Use `generate_genome.py` from `codex-project-memory`.
- See `skills/.system/REGISTRY.md` for full script paths.

## Sanitized Reuse Map

For rung 2 of the precision ladder, build a compact helper index with `../codex-runtime-hook/scripts/reuse_map.py`. The script lives with the runtime hook because this skill does not ship a `scripts/` directory.

The index stays under 2000 characters, lists shared folders first (`utils`, `lib`, `shared`, `common`, `helpers`, `services`), and skips `tests`, `node_modules`, `dist`, `vendor`, `.git`, and `.codex`. It does not follow symlinks. Folder names and exported symbols that are not plain identifiers are dropped, including names that contain newlines or instruction-injection text. On any unexpected error the map is empty.

## Script Invocation Discipline

1. Always run `--help` before invoking.
2. Treat script as a black-box tool and execute by contract first.
3. Read script source only when customization or bug fixing is required.

## Freshness Check

- `genome.md` includes a "Generated:" timestamp and file counts.
- If current file count differs significantly (>20%) from `genome.md` counts, suggest re-generation.
- When user restructures the project (adds/removes modules), remind to regenerate.

## Output Files

| File | Purpose | Size Target |
| --- | --- | --- |
| `.codex/context/genome.md` | Macro project context | 500-800 words |
| `.codex/context/modules/{name}.md` | Per-module detail | 200-400 words each |

## Context Loading Budget

- `genome.md`: always (~2000-2400 tokens)
- Module maps: max 3 at a time (~600-1200 tokens each)
- Total context overhead: <5000 tokens (<4% of context window)
