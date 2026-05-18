# Output Schemas

## Output Contract

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

### Per-Script Output Schemas

| Script | `status` on success | Key fields |
| --- | --- | --- |
| `decision_logger.py` | `"logged"` | `path`, `title` |
| `generate_session_summary.py` | `"generated"` | `path`, `commits`, `files_changed` |
| `generate_handoff.py` | `"generated"` | `path`, `sections` |
| `generate_changelog.py` | `"generated"` | `path`, `entries` |
| `generate_growth_report.py` | `"generated"` | `path`, `metrics` |
| `analyze_patterns.py` | `"generated"` | `path`, `patterns` |
| `build_knowledge_graph.py` | `"generated"` | `path`, `stats`, `code_index`, `ai_context`, `human_context` |
| `build_knowledge_index.py` | `"built"` | `index_path`, `markdown_path`, `graph_path`, `html_path`, `sources`, `graph_stats` |
| `track_feedback.py` (log) | `"logged"` | `path`, `category` |
| `track_feedback.py` (aggregate) | `"aggregated"` | `total`, `by_category` |
| `track_skill_usage.py` (record) | `"recorded"` | `skill`, `outcome` |
| `track_skill_usage.py` (report) | `"report"` | `total_entries`, `by_skill` |
| `compact_context.py` | `"compacted"` | `sessions_archived`, `feedback_archived`, `bytes_freed` |

All scripts emit `{"status": "error", "message": "..."}` on failure.

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

```json
{"status": "generated", "path": "<file>", "generated_at": "<iso8601>", "project_root": "<path>", "stats": {"total_files": <int>, "total_edges": <int>, "modules": <int>, "routes": <int>, "models": <int>, "circular_dependencies": <int>, "files_scanned": <int>, "files_skipped": <int>, "bytes_scanned": <int>}, "coverage": {"files_scanned": <int>, "files_skipped": <int>, "candidate_files": <int>, "bytes_scanned": <int>, "skipped_reasons": {<object>}, "warnings": <int>, "limits": {<object>}}, "file_dependencies": {<object>}, "code_index": {"<relative-file>": {"path": "<relative-file>", "language": "<language>", "module": "<module>", "parser": {"parser": "<parser-family>", "confidence": "<high|medium|low|none>", "resolver_strategy": "<strategy>"}, "lines": <int>, "definitions": [<string>], "imports": [<string>], "imported_by": [<string>], "external_imports": [<string>], "is_test": <bool>, "is_entrypoint": <bool>, "risk_tags": [<string>]}}, "entrypoints": [<string>], "external_dependencies": {<object>}, "module_boundaries": {<object>}, "api_routes": [<object>], "data_models": {<object>}, "risk_signals": [<object>], "ai_context": {<object>}, "human_context": {<object>}, "circular_dependencies": [<object>], "warnings": [{"type": "<string>", "path": "<relative-path>", "reason": "<string>", "severity": "<info|warning|error>"}]}
```

`code_index[*].parser` describes the registry entry used for the file. Dedicated JavaScript/TypeScript and Python extractors report `high` confidence; language-specific pattern extractors for Go, Rust, Java, C#, PHP, Ruby, Kotlin, Swift, Vue/Svelte, Terraform, YAML, and JSON generally report `medium`; asset-oriented HTML/CSS/SCSS/SQL extractors report `low`.

#### build_knowledge_index.py

```json
{"status": "built", "index_path": "<file>", "markdown_path": "<file>", "graph_path": "<file>", "html_path": "<file>", "sources": {<object>}, "graph_stats": {<object>}, "coverage": {<object>}}
```

#### compact_context.py

```json
{"status": "compacted", "sessions_archived": <int>, "feedback_archived": <int>, "decisions_kept": <int>, "bytes_freed": <int>}
```
