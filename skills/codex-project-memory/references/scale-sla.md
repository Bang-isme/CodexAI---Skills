# Project Memory Scale SLA

Service-level expectations when running project-memory tooling on repositories from **small** through **very large** file trees.

## Tiers

| Tier | Typical size | Suggested local check | Recommended flags |
|------|----------------|-------------|-------------------|
| Small | &lt; 1,000 tracked files | Default scale-gate run | Default traversal (`max_files` 1000) |
| Medium | 1,000–10,000 files | Synthetic fixture and representative project sample | `--max-files 5000`, `--incremental` |
| Large | 10,000–50,000+ files | Larger synthetic fixture; measure on the target machine | `--max-files 10000`, `--incremental`, monitor duration |
| Monorepo / huge | 50,000+ files | No broad performance claim; profile a representative checkout | Incremental only; raise caps deliberately; shard by path |

## Commands

```bash
# Generate synthetic fixture (local debugging; polyglot on by default)
python skills/codex-project-memory/scripts/generate_scale_fixture.py \
  --output-dir /tmp/scale-fixture --file-count 2500 --seed 42 --include-package-json

# Python-only fixture (legacy / fastest smoke)
python skills/codex-project-memory/scripts/generate_scale_fixture.py \
  --output-dir /tmp/scale-fixture-py --file-count 500 --no-polyglot

# Run scale gate (medium tier defaults)
python skills/codex-project-memory/scripts/run_scale_gate.py \
  --tier medium --report-path scale-gate-report-medium.json --format json
```

## Scale gate report (`scale-gate-report.json`)

| Field | Meaning |
|-------|---------|
| `status` | `pass` or `fail` |
| `duration_seconds` | Wall-clock time for full gate |
| `within_budget` | `duration_seconds <= budget_seconds` |
| `incremental_reused` | `codebase-index.json` → `incremental.reused_files` after second build |
| `memory_status` | Result from `memory_status.py` (`pass` / `warn` / `fail`) |
| `failures` | Human-readable failure reasons |
| `fixture_extension_counts` | Extensions emitted by `generate_scale_fixture` (`.py`, `.js`, `.ts`, `.go`, …) |
| `index_parsers` | Parser kinds in `codebase-index.json` (expects `regex-python-symbols` + `regex-js-ts-symbols` when `file_count >= 10`) |
| `index_languages` | Language labels assigned by `codebase_indexer.py` |

## Polyglot fixture coverage

The scale gate fixture rotates extensions aligned with `codebase_indexer.py` `CODE_EXTENSIONS`:

| Extension | Indexer parser | Notes |
|-----------|----------------|-------|
| `.py` | `regex-python-symbols` | Primary symbol extraction |
| `.js`, `.ts`, `.tsx` | `regex-js-ts-symbols` | Includes React TSX |
| `.go`, `.java`, `.rs` | `line-window` | Generic symbol window |
| `.sql`, `.md`, `.yaml` | `structured-text-regex` or `line-window` | Docs/config paths |
| `package.json`, `tsconfig.json`, `Dockerfile` | Config discovery | Via `--include-package-json` |

Use polyglot fixtures so a local gate exercises multi-parser indexing, not Python-only trees. Fixture size is a test input, not a performance guarantee.

## Operator guidance

- Do **not** commit `.codex/` output; see `references/artifact-lifecycle-policy.md`.
- After a fresh index+graph build, `memory_status --strict` should exit 0. Indexer-only extras (`.md`, `.toml`, `Dockerfile`) are `expected_extras`, not warnings.
- External CLI wrappers should read `skills/.system/references/plugin-tools.json` entry `memory_scale_gate` instead of shell-scripting individual memory commands.

## Suggested schedule for a consuming repository

| Check | Suggested frequency | Notes |
|----------|-----|------|
| Medium fixture | Pull request or release candidate | Keep the run bounded and save the JSON report |
| Large fixture | Scheduled or on-demand | Measure runtime and memory on the actual runner |
| Project memory checks | After index/graph generation | Treat stale inputs and strict warnings explicitly |

These are recommendations only. This pack source does not ship scheduled GitHub Actions workflows.
