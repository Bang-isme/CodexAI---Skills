---
name: codex-project-memory
description: Use for project memory, decisions, handoffs, genome, knowledge index, changelog, and patterns that must persist across sessions.
load_priority: on-demand
---

## TL;DR
10 scripts for project knowledge persistence. Decision tree: Log -> decision/feedback. Generate -> changelog/session-summary/handoff. Analyze -> patterns/knowledge-graph/knowledge-index/project-genome. Maintain -> compact old context. Triggers: `$changelog`, `$session-summary`, `$log-decision`, `$compact-context`, `$knowledge`, `$codex-genome`.

# Codex Project Memory

## Activation

1. Activate after complex tasks involving architecture, design decisions, or refactors.
2. Activate on explicit `$codex-project-memory` or `$memory`.
3. Activate on explicit command `$log-decision`.
4. Activate on `$handoff` or when user asks to generate handoff context.
5. Activate on `$session-summary` or when user asks to summarize a coding session.
6. Activate on `$analyze-patterns` or "learn project style".
7. Activate on `$log-feedback` or "track my fix".
8. Activate on `$feedback-summary` for aggregated feedback recall.
9. Activate on `$build-graph` or "map project" to generate project knowledge graph.
10. Activate on `$changelog` to generate release-oriented commit summaries.
11. Activate on `$compact-context` or "clean up old sessions".
12. Activate on `$codex-genome`, `$generate-genome`, or `$genome` to create layered project context docs.
13. Activate on `$knowledge`, "make tacit knowledge visible", or "build knowledge index" to generate `.codex/knowledge/INDEX.md`, `.codex/knowledge/index.json`, and `.codex/knowledge/knowledge-graph.json`.
14. Activate on "memory status", "validate project memory", or before CLI/tool-harness handoff to run `scripts/memory_status.py` against generated artifacts.
15. Before pausing multi-step work for context compaction or handoff, create a session-summary checkpoint and complete its task-state fields from the current session.

## Decision Tree Routing

```
User intent -> Memory action?
    |- Log/record -> What?
    |   |- Decision -> decision_logger.py
    |   `- Feedback -> track_feedback.py
    |
    |- Generate/export -> What?
    |   |- Handoff -> generate_handoff.py
    |   |- Session recap -> generate_session_summary.py
    |   `- Changelog -> generate_changelog.py
    |
    |- Analyze -> What?
    |   |- Patterns -> analyze_patterns.py
    |   |- Dependencies -> build_knowledge_graph.py
    |   |- Tacit knowledge index -> build_knowledge_index.py
    |   `- Context genome -> generate_genome.py
    |
    |- Maintain -> What?
    |   `- Compact old memory -> compact_context.py
    |
    `- Not memory -> skip
```

## Rules

- Follow `references/unified-memory-architecture.md` for the 4-Tier Memory Hierarchy (L0 Execution State -> L1 Genome/Knowledge Index -> L2 Normative Specs/ADRs -> L3 Role Docs), SSOT conflict precedence, and deterministic Write-Back Protocol.
- Use the decision tree to choose one memory action before invoking scripts.
- Run `--help` before invoking helper scripts and treat them as black-box tools unless customization or bug fixing is required.
- Review existing files in `.codex/decisions/` before logging a similar technical choice.
- Use the default output paths and chaining guidance from `references/behavior-guide.md` unless the user requests overrides.
- A generated session summary is a Git snapshot, not a complete task handoff. Fill its task-state, active spec/ACs, SILC integration seam status, verification, and next-step prompts before treating it as resumable memory.
- `--since last-session` is scoped to the current repository, branch, and reachable commit history; complete the newest matching checkpoint before using it as the next boundary. It is a Git-history selector, not a task selector.
- Return the created path plus the headline metrics from each script JSON payload.
- See `skills/.system/REGISTRY.md` for full script paths.

## Reference Files

- `references/unified-memory-architecture.md`: 4-tier SSOT read hierarchy, authority precedence, and deterministic write-back protocol across sessions.
- `references/decision-journal-spec.md`: decision logging criteria and naming conventions.
- `references/handoff-spec.md`: handoff usage guidance.
- `references/session-summary-spec.md`: session summary workflow and retention guidance.
- `references/changelog-spec.md`: release-focused changelog generation rules.
- `references/pattern-learner-spec.md`: project style learning behavior.
- `references/feedback-tracker-spec.md`: feedback logging and aggregate usage.
- `references/knowledge-graph-spec.md`: deep architecture mapping and refresh guidance.
- `build_knowledge_index.py`: schema-versioned project knowledge index from genome, role docs, decisions, commits, config, and the structural knowledge graph; redacts secret-like values, stores provenance/confidence and a source fingerprint for staleness checks.
- `references/knowledge-index.schema.json`: output contract for `.codex/knowledge/index.json`.
- `references/knowledge-graph.schema.json`: output contract for `.codex/knowledge/knowledge-graph.json` and `.codex/knowledge-graph.json`.
- `references/context-compactor-spec.md`: retention policy, archive layout, and dry-run expectations.
- `references/behavior-guide.md`: detailed per-script behaviors, defaults, and chaining guidance.
- `references/script-commands.md`
- `references/output-schemas.md`
- `references/project-memory-tools.json`: machine-readable tool manifest for CLI/MCP-style harness generation.
- `references/project-memory-tools.schema.json`: schema for the tool manifest.
- `references/ci-readiness.md`: release gate commands, strict mode, and Windows symlink deselection.
- `references/artifact-lifecycle-policy.md`: hybrid commit policy for schemas vs generated `.codex/` artifacts.
