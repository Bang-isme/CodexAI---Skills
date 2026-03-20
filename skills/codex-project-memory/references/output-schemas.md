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
| `build_knowledge_graph.py` | `"generated"` | `path`, `stats` |
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
{"status": "generated", "path": "<file>", "generated_at": "<iso8601>", "project_root": "<path>", "stats": {"total_files": <int>, "total_edges": <int>, "modules": <int>, "routes": <int>, "models": <int>, "circular_dependencies": <int>}, "file_dependencies": {<object>}, "module_boundaries": {<object>}, "api_routes": {<object>}, "data_models": {<object>}, "circular_dependencies": [<object>], "warnings": [<string>]}
```

#### compact_context.py

```json
{"status": "compacted", "sessions_archived": <int>, "feedback_archived": <int>, "decisions_kept": <int>, "bytes_freed": <int>}
```
