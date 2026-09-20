# Script Commands

Canonical command paths are centralized in `skills/.system/REGISTRY.md`.

## Execution Command

### Decision Logger

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/decision_logger.py" --project-root <path> --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/decision_logger.py" --project-root <path> --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>`

### Context Handoff Generator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_handoff.py" --project-root <path>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_handoff.py" --project-root <path>`

### Session Summary Generator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_session_summary.py" --project-root <path> --since today`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_session_summary.py" --project-root <path> --since today`

### Changelog Generator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_changelog.py" --project-root <path> --since "30 days ago"`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_changelog.py" --project-root <path> --since "30 days ago"`

### Growth Report Generator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_growth_report.py" --project-root <path> --skills-root "<SKILLS_ROOT>"`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_growth_report.py" --project-root <path> --skills-root "<SKILLS_ROOT>"`

### Pattern Learner

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/analyze_patterns.py" --project-root <path>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/analyze_patterns.py" --project-root <path>`

### Feedback Tracker

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/track_feedback.py" --project-root <path> --file <file> --ai-version <text> --user-fix <text> --category <category>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/track_feedback.py" --project-root <path> --file <file> --ai-version <text> --user-fix <text> --category <category>`
- Aggregate:
  `python ".../track_feedback.py" --project-root <path> --aggregate`

### Skill Evolution Tracker

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/track_skill_usage.py" --skills-root "<SKILLS_ROOT>" --record --skill <skill-name> --task <task> --outcome <success|partial|failed> --notes <text>`
- Report:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/track_skill_usage.py" --skills-root "<SKILLS_ROOT>" --report`

### Knowledge Graph Builder

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/build_knowledge_graph.py" --project-root <path>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/build_knowledge_graph.py" --project-root <path>`
- Output:
  `.codex/knowledge-graph.json` by default, including `code_index`, `entrypoints`, `external_dependencies`, `module_boundaries`, `api_routes`, `data_models`, `risk_signals`, `ai_context`, and `human_context`.

### Knowledge Index and Optional HTML Dashboard

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/build_knowledge_index.py" --project-root <path>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/build_knowledge_index.py" --project-root <path>`
- Output:
  `.codex/knowledge/index.json`, `.codex/knowledge/INDEX.md`, `.codex/knowledge/knowledge-graph.json`, and `.codex/knowledge/codebase-index.json`, all written atomically (temp file + rename). `index.json` carries `source.git_head` and `source.tree_fingerprint` for staleness checks. Add `--html` (or `--watch`/`--serve`) to also write `.codex/knowledge/index.html`.
- Query:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/build_knowledge_index.py" --project-root <path> --query "<terms>" --top-k 10`
- Incremental:
  On by default; unchanged files are reused by content hash. `--no-incremental` disables reuse, `--rebuild` discards the previous codebase index entirely.
- Full flag list:
  `--output-dir`, `--progress-file`, `--html`, `--watch`/`--serve` with `--host`/`--port`, `--query`/`--top-k`, `--incremental`/`--no-incremental`, `--rebuild`, `--no-redaction`, `--format json|text`.
- Scale controls:
  Use traversal flags `--max-files` (1000), `--max-file-bytes` (256 KiB), `--max-total-bytes` (20 MiB), `--include`, `--exclude`, and `--follow-symlinks true|false` when building large projects. Hard-skipped directories include `.git`, `node_modules`, `dist`, `build`, `target`, `.venv`, `.codex`, `.codexai-backups`.

### Memory Status Validator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/memory_status.py" --project-root <path>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/memory_status.py" --project-root <path>`
- CI strict (warnings fail the gate):
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/memory_status.py" --project-root <path> --strict`
- Require standalone graph:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/memory_status.py" --project-root <path> --require-standalone-graph`
- Verify file tree against the recorded fingerprint (slower; catches uncommitted changes):
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/memory_status.py" --project-root <path> --verify-tree`
- Output:
  JSON status (`pass`, `warn`, or `fail`) with `policy`, artifact checks, age staleness, `source` staleness (git HEAD vs `index.json.source.git_head`, optional tree fingerprint), and graph/codebase coherence. Coherence compares `code_index` to the LANGUAGE_REGISTRY subset of the indexer; `.md`/config extras are `expected_extras` (not warnings). `index.html` is never checked.
- See also:
  `references/ci-readiness.md`, `references/artifact-lifecycle-policy.md`, `references/project-memory-tools.json`

### Memory Scale Gate

- Run a synthetic scale gate (fixture -> index -> incremental reuse -> memory_status):
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/run_scale_gate.py" --tier medium --report-path scale-gate-report-medium.json --format json`
- Tiers: `medium` (2500 files, max 5000, 420 s budget) and `large` (8000 files, max 10000, 900 s budget, standalone graph required). Overrides: `--file-count`, `--max-files`, `--budget-seconds`, `--seed`, `--keep-fixture`, `--project-root`.
- Summarize for CI job summaries:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/write_scale_gate_summary.py" --report-path scale-gate-report-medium.json --title "Memory scale gate (medium)"`
- See also: `references/scale-sla.md`.

### Project Genome Generator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_genome.py" --project-root <path>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_genome.py" --project-root <path>`
- Options:
  `--depth auto|shallow|full` (default: auto), `--sections all|architecture,api,data,security,tests,file_map`, `--format md|json`. `genome.md` is regenerated on every run (`--force` is accepted for backward compatibility and has no extra effect); treat it as a generated artifact and keep human notes in role docs or decisions.
- Output:
  JSON summary + `.codex/context/genome.md` and optional `.codex/context/modules/*.md`

### auto_commit.py

- **Skill**: `codex-git-autopilot`
- **Purpose**: Automated commit with CI gate + GPG signing
- **Command**: `python auto_commit.py --project-root <dir> --files <file1> <file2>`
- **Options**: `--dry-run`, `--skip-tests`, `--no-push`, `--setup-gpg`, `--message`, `--type`, `--scope`
- **Output**: JSON with commit hash, push status, GPG status

### Context Compactor

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/compact_context.py" --project-root <path> --max-age-days 90 --keep-latest 5`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/compact_context.py" --project-root <path> --max-age-days 90 --keep-latest 5`
- Dry run:
  `python ".../compact_context.py" --project-root <path> --dry-run`
