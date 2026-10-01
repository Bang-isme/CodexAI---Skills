# Project Artifact Layout

Use this map when a workflow needs to create durable project context. These folders are created on demand; do not initialize every area for a routine change.

## Project work artifacts

| Path | Owner / producer | Use and lifecycle |
| --- | --- | --- |
| `.codex/profile.json` | Runtime hook profile initializer | Small project routing preferences; human-owned and optional. |
| `.codex/context/` | Genome generator | Generated codebase context; refresh when useful, do not hand-edit. |
| `.codex/project-docs/` | Role-doc initializer | Human-owned project brief and selected role docs. Default init creates only the brief and ADR template; add role folders only when needed. |
| `.codex/specs/` | Spec workflow | Human-reviewed feature requirements and acceptance criteria. |
| `.codex/design/` | Frontend design and visual gate | Product/surface contracts, visual direction, route/state manifests, and review evidence. Keep captures under `reviews/`. |
| `.codex/knowledge/` | Knowledge index builder | Generated indexes and graph; regenerate with the owning script. Optional HTML is created only when requested. |
| `.codex/knowledge-graph.json` | Standalone graph builder | Optional legacy standalone graph output. Prefer the normal `.codex/knowledge/` index workflow for routine project context. |
| `.codex/quality/`, `.codex/state/` | Quality trend and execution gate | Reports and gate state; machine-generated, safe to regenerate. |
| `.codex/sessions/` | Session summary workflow | Human-readable session handoffs; retain only summaries useful to the project. |
| `.codex/decisions/`, `.codex/feedback/`, `.codex/skill-usage/` | Project memory tools | Append-only decision, feedback, and usage records. Use only when the project needs that history. |

## Host integration and package output

These folders serve the host or the pack itself; they are not application source folders:

| Path | Purpose |
| --- | --- |
| `.agents/` | Codex/agent host skills, agents, and local plugin marketplace metadata. |
| `.claude/` | Claude Code project skills and local settings. Global plugin cache lives in the host-managed Claude directory. |
| `.cursor/` | Cursor rules and skills adapter. |
| `.codex-plugin/`, `.claude-plugin/`, `.cursor-plugin/` | Host package manifests and marketplace catalogs in this plugin repository; do not copy these as application folders. |
| `.gemini/` and `.agents/plugins/` | Antigravity/Gemini host adapter locations, depending on install scope. |
| `.codexai/` | Generic host harness files and its optional evidence. Do not use this as a second root for normal project specs or design work. |
| `dist/` | Release archives. Created only when a release/archive build is explicitly applied. |

## Rules for clean output

1. Inspect the repository and follow its existing source, test, asset, and docs conventions before adding directories.
2. Create only paths needed for the requested work. Do not create empty `misc`, `output`, `final`, `generated`, duplicate app roots, or unrelated role folders.
3. Keep feature code and tests with the owning feature. Keep screenshots, reports, context indexes, and other generated evidence in the owner path above, not beside application source.
4. Use an existing artifact rather than creating a second copy under another name. If a new artifact type is necessary, record its owner and lifecycle here.
5. Do not move or rename existing user-owned project files just to match this map. Preserve the repository's conventions and use the map for new CodexAI-owned artifacts.
