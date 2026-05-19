# Project Memory Scale SLA

Service-level expectations when running project-memory tooling on repositories from **small** through **very large** file trees.

## Tiers

| Tier | Typical size | CI coverage | Recommended flags |
|------|----------------|-------------|-------------------|
| Small | &lt; 1,000 tracked files | Default `memory-tooling` on plugin repo | Default traversal (`max_files` 1000) |
| Medium | 1,000–10,000 files | PR gate `memory-at-scale-medium` (2500 synthetic files) | `--max-files 5000`, `--incremental` |
| Large | 10,000–50,000+ files | Weekly `scale-nightly` (8000 synthetic files) | `--max-files 10000`, `--incremental`, monitor duration |
| Monorepo / huge | 50,000+ files | Not fully simulated in CI | Incremental only; raise caps deliberately; shard by path |

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

CI medium/large tiers use polyglot fixtures so gates exercise multi-parser indexing, not Python-only trees.

## Operator guidance

- Do **not** commit `.codex/` output; see `references/artifact-lifecycle-policy.md`.
- On Windows CI, exclude symlink traversal test when lacking privilege (see `ci-readiness.md`).
- Advisory `memory_status` warn (graph vs codebase parity) is expected on real repos; use `--strict` only when policy requires it.
- External CLI wrappers should read `skills/.system/references/plugin-tools.json` entry `memory_scale_gate` instead of shell-scripting individual memory commands.

## CI workflows

| Workflow | Job | When |
|----------|-----|------|
| `ci.yml` | `memory-at-scale-medium` | Every PR / push to `main` |
| `scale-nightly.yml` | `memory-at-scale-large` | Weekly + manual dispatch |
| `ci.yml` | `memory-tooling` | Real plugin repo integration |

Release packaging (`release.yml`) relies on PR gates; it does not run the large tier gate to keep tag builds fast.
