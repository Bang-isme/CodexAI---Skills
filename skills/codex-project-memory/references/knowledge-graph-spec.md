# Knowledge Graph Spec

## Purpose

Build a project-wide structural graph (dependencies, module boundaries, routes, models) so AI can reason with architecture-level context.

## When To Build

- At project start.
- After major restructuring.
- Weekly refresh for active repositories.

## How AI Uses It

1. Run `build_knowledge_graph.py` to generate `.codex/knowledge-graph.json`.
2. Read graph before complex refactors, cross-module changes, or API-impact work.
3. Use module boundaries and route/model maps to reduce incorrect assumptions.

## Complements

- `predict_impact.py` can use graph context to estimate dependents more accurately.
- `project-profile.json` and session summaries provide additional style/history context.

## Limitations

- Parsing is regex-based and best-effort.
- Dynamic imports and advanced runtime wiring may be missed.
- Re-run regularly to keep graph fresh.
