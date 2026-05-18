# Output Schemas

## Output Contract

Project-memory scripts have two output surfaces:

1. **CLI payloads** are printed to stdout and describe the command result. They include `status` and, when a primary file is written, a `path` or path-specific fields such as `index_path` and `graph_path`.
2. **Artifact files** are the durable JSON files written under `.codex/`. Artifact files do **not** use `status` or `path` for command execution state. They identify themselves with `schema_version`, `artifact_type`, `generated_at`, and `project_root`; the CLI payload is the source of truth for write status and output locations.

Success JSON:

```json
{
  "status": "logged",
  "path": "<project-root>/.codex/decisions/YYYY-MM-DD-<slug>.md",
  "title": "<title>"
}
```

Error JSON:

```json
{
  "status": "error",
  "path": "",
  "title": "<title>",
  "message": "<error details>"
}
```

All scripts emit `{"status": "error", "message": "..."}` on failure unless the per-script section documents a more specific error shape.

## Artifact Metadata Contract

Every durable JSON artifact produced by `build_knowledge_index.py` and `build_knowledge_graph.py` includes these top-level fields:

```json
{
  "schema_version": "2.0",
  "artifact_type": "knowledge-index|knowledge-graph",
  "generated_at": "<iso8601>",
  "project_root": "<path>",
  "stats": {"<metric>": "<value>"},
  "warnings": ["<non-fatal warning>"],
  "redaction": {"enabled": true, "strategy": "<strategy>", "description": "<text>"}
}
```

`status` and `path` are intentionally excluded from artifact files. Tests should assert this separation for knowledge artifacts: artifact files require the metadata above, while CLI payloads require `status` plus output location fields.

### Compatibility Policy

- Schema versions use `MAJOR.MINOR`.
- Bump the **minor** version when adding optional fields or new enum values that preserve existing field meanings.
- Bump the **major** version when removing required fields, changing a field meaning, changing a field type, or moving command-state fields between CLI payloads and artifacts.
- Consumers should ignore unknown fields within the same major version.

### Knowledge Artifact Schemas

| Artifact | Schema file | Required identity | Notes |
| --- | --- | --- | --- |
| `.codex/knowledge/index.json` | `references/knowledge-index.schema.json` | `schema_version`, `artifact_type`, `generated_at`, `project_root`, `stats`, `warnings`, `redaction` | Tacit-knowledge and source-coverage artifact. |
| `.codex/knowledge/knowledge-graph.json` and `.codex/knowledge-graph.json` | `references/knowledge-graph.schema.json` | `schema_version`, `artifact_type`, `generated_at`, `project_root`, `stats`, `warnings`, `redaction` | Structural dependency graph, code index, contexts, routes, models, and risk signals. |

A standalone codebase-index artifact is not currently emitted. If one is added, create `references/codebase-index.schema.json` before release and include files, chunks, symbols, references, and query metadata in both the schema and this contract.

### Per-Script Output Schemas

| Script | `status` on success | Key fields |
| --- | --- | --- |
| `decision_logger.py` | `"logged"` | `path`, `title` |
| `generate_session_summary.py` | `"generated"` | `path`, `commits`, `files_changed` |
| `generate_handoff.py` | `"generated"` | `path`, `sections` |
| `generate_changelog.py` | `"generated"` | `path`, `entries` |
| `generate_growth_report.py` | `"generated"` | `path`, `metrics` |
| `analyze_patterns.py` | `"generated"` | `path`, `patterns` |
| `build_knowledge_graph.py` | `"generated"` | `path`, artifact metadata, `stats`, `code_index`, `ai_context`, `human_context` |
| `build_knowledge_index.py` | `"built"` | artifact metadata, `index_path`, `markdown_path`, `graph_path`, `html_path`, `sources`, `graph_stats` |
| `track_feedback.py` (log) | `"logged"` | `path`, `category` |
| `track_feedback.py` (aggregate) | `"aggregated"` | `total`, `by_category` |
| `track_skill_usage.py` (record) | `"recorded"` | `skill`, `outcome` |
| `track_skill_usage.py` (report) | `"report"` | `total_entries`, `by_skill` |
| `compact_context.py` | `"compacted"` | `sessions_archived`, `feedback_archived`, `bytes_freed` |

#### Detailed Examples

#### generate_session_summary.py

```json
{"status": "generated", "path": "<file>", "commits": <int>, "files_changed": <int>}
```

#### generate_handoff.py

```json
{"status": "generated", "path": "<file>", "sections": <int>, "size_bytes": <int>, "warnings": [<string>]}
```

#### generate_changelog.py

```json
{"status": "generated", "version": "<string>", "since": "<string>", "total_commits": <int>, "categories": {<object>}, "path": "<file-or-empty>", "changelog_markdown": "<markdown>"}
```

#### generate_growth_report.py

```json
{"status": "generated", "path": "<file>", "improvement_areas": <int>, "sessions_analyzed": <int>, "warnings": [<string>]}
```

#### analyze_patterns.py

```json
{"status": "generated", "path": "<file>", "profile": {<object>}, "warnings": [<string>]}
```

#### track_feedback.py

```json
{"status": "logged", "path": "<file>", "file": "<string>", "category": "<string>", "severity": "<string>"}
```

Aggregate mode:

```json
{"total_feedback": <int>, "by_category": {<object>}, "by_severity": {<object>}, "top_files": [<object>], "recent": [<object>], "patterns": "<string>"}
```

#### track_skill_usage.py

```json
{"status": "recorded", "path": "<file>", "entry": {"date": "<YYYY-MM-DD>", "skill": "<name>", "task": "<task>", "outcome": "<success|partial|failed>", "notes": "<string>", "duration_estimate": "<string>"}, "skills_root": "<path>"}
```

Report mode:

```json
{"status": "report_ready", "total_usages": <int>, "period": {"from": "<YYYY-MM-DD>", "to": "<YYYY-MM-DD>"}, "by_skill": {<object>}, "unused_skills": [<string>], "most_effective": "<string>", "least_effective": "<string>", "recommendations": [<string>], "trends": {"overall_success_rate": <float>, "direction": "<improving|stable|declining>"}, "warnings": [<string>]}
```

#### build_knowledge_graph.py

CLI payload:

```json
{"status": "generated", "path": "<file>", "schema_version": "2.0", "artifact_type": "knowledge-graph", "generated_at": "<iso8601>", "project_root": "<path>", "stats": {"total_files": <int>, "total_edges": <int>, "modules": <int>, "routes": <int>, "models": <int>, "circular_dependencies": <int>, "files_scanned": <int>, "files_skipped": <int>, "bytes_scanned": <int>}, "warnings": [<string>], "redaction": {"enabled": false, "strategy": "none", "description": "<text>"}, "coverage": {"files_scanned": <int>, "files_skipped": <int>, "candidate_files": <int>, "bytes_scanned": <int>, "skipped_reasons": {<object>}, "warnings": <int>, "limits": {<object>}}, "file_dependencies": {<object>}, "code_index": {"<relative-file>": {"path": "<relative-file>", "language": "<language>", "module": "<module>", "parser": {"parser": "<parser-family>", "confidence": "<high|medium|low|none>", "resolver_strategy": "<strategy>"}, "lines": <int>, "definitions": [<string>], "imports": [<string>], "imported_by": [<string>], "external_imports": [<string>], "is_test": <bool>, "is_entrypoint": <bool>, "risk_tags": [<string>]}}, "entrypoints": [<string>], "external_dependencies": {<object>}, "module_boundaries": {<object>}, "api_routes": [<object>], "data_models": {<object>}, "risk_signals": [<object>], "ai_context": {<object>}, "human_context": {<object>}, "circular_dependencies": [<object>]}
```

The written `knowledge-graph.json` artifact contains the same fields except `status` and `path`.

`code_index[*].parser` describes the registry entry used for the file. Dedicated JavaScript/TypeScript and Python extractors report `high` confidence; language-specific pattern extractors for Go, Rust, Java, C#, PHP, Ruby, Kotlin, Swift, Vue/Svelte, Terraform, YAML, and JSON generally report `medium`; asset-oriented HTML/CSS/SCSS/SQL extractors report `low`.

#### build_knowledge_index.py

CLI payload:

```json
{"status": "built", "schema_version": "2.0", "artifact_type": "knowledge-build-payload", "generated_at": "<iso8601>", "project_root": "<path>", "index_path": "<file>", "markdown_path": "<file>", "graph_path": "<file>", "html_path": "<file>", "codebase_index_path": "<file>", "progress_path": "<file>", "progress_fetch_url": "<relative-url>", "stats": {<object>}, "warnings": [<string>], "redaction": {<object>}, "sources": {<object>}, "graph_stats": {<object>}, "codebase_stats": {<object>}, "coverage": {<object>}, "risk_signals": <int>, "redaction_applied": <bool>, "redaction_patterns_version": "<semver>", "redaction_counts": {<object>}}
```

The written `index.json` artifact contains `artifact_type: "knowledge-index"`, metadata, `sources`, `architecture_seams`, `domain_vocabulary`, `decisions`, `recent_commits`, `package`, and `tacit_knowledge`. It does not contain `status`, `path`, or the path-specific CLI fields.

#### compact_context.py

```json
{"status": "compacted", "sessions_archived": <int>, "feedback_archived": <int>, "decisions_kept": <int>, "bytes_freed": <int>}
```
