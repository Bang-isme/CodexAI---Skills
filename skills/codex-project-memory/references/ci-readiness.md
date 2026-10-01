# Project Memory CI Release Gate

Commands assume the plugin source is checked out at the repository root and its skills live in `skills/`. The source includes local checks; hosted CI must be configured in the consuming repository.

## Release gate (recommended order)

```bash
# 1. Checked-in Python and Node helper tests
python -m unittest discover -s skills/tests -p "test_*.py"
node --test skills/tests/responsive_capture_stitch.test.mjs skills/tests/responsive_capture_core.test.mjs skills/tests/responsive_capture_browser.test.mjs

# 2. Pack health (contracts + registry)
python skills/.system/scripts/check_pack_health.py --skills-root skills --format json

# 3. Memory status on a project with built artifacts
python skills/codex-project-memory/scripts/build_knowledge_index.py --project-root .
python skills/codex-project-memory/scripts/memory_status.py --project-root . --format json
python skills/codex-project-memory/scripts/memory_status.py --project-root . --strict
```

Expected:

- Pack health: `status: pass`
- `memory_status` default: exit `0` when `status` is `pass` or `warn`
- `memory_status --strict`: exit `0` when `status` is `pass`; exit `1` when `status` is `warn` or `fail`

### Coherence comparison

`memory_status` compares graph `code_index` keys to the **LANGUAGE_REGISTRY subset** of `codebase-index.json` files (same predicate as `build_knowledge_graph.py`). Markdown, TOML, shell, and config names such as `Dockerfile` are reported as `coherence.expected_extras` and do **not** warn.

A warn of `code_index and comparable codebase_index file sets differ` means a true mismatch: the graph is missing a code file the indexer has, or the graph contains a path the indexer does not. `--strict` is appropriate in CI after regenerating artifacts.

A missing `.codex/knowledge-graph.json` is **not** warned when standalone graph policy is optional (default). Only use `--require-standalone-graph` when CI must enforce that file exists and is schema v2.

Regenerate artifacts before gating:

```bash
python skills/codex-project-memory/scripts/build_knowledge_index.py --project-root .
python skills/codex-project-memory/scripts/build_knowledge_graph.py --project-root .
```

Do not commit `.codex/` output; see `references/artifact-lifecycle-policy.md`.

## Checked-in test suites

```bash
python -m unittest discover -s skills/tests -p "test_*.py"
node --test skills/tests/responsive_capture_stitch.test.mjs skills/tests/responsive_capture_core.test.mjs skills/tests/responsive_capture_browser.test.mjs
```

The browser fixture skips when Playwright and Chromium are unavailable. A skipped browser fixture is not responsive-render verification; the visual gate must remain `DEGRADED` until real captures are reviewed.

## Strict and artifact policy flags

| Flag | Effect |
|------|--------|
| `--strict` | Exit code `1` when overall `status` is `warn` |
| `--require-standalone-graph` | Missing or schema-invalid `.codex/knowledge-graph.json` is a **fail**, not a warn |
| `--max-age-hours N` | Stale `generated_at` beyond N hours adds warnings |

Stdout includes `policy` metadata:

```json
{
  "policy": {
    "standalone_graph": "optional",
    "strict_warnings_exit_nonzero": false,
    "max_age_hours": 168
  }
}
```

## Tool harness entry point

Read `references/project-memory-tools.json` (schema `2.0`) for:

- `exit_codes` — success vs failure (and `strict_warn_as_failure` for `memory_status`)
- `warning_policy` — `none`, `advisory`, or `strict_exit`
- `required_artifact_modes` — `required`, `optional`, or `generated_on_success`

Do not scrape prose from `script-commands.md` for automation; use the JSON manifest and `references/output-schemas.md` for field shapes.

## Scale SLA (medium → very large repos)

See `references/scale-sla.md` for tier definitions and `run_scale_gate.py` report fields. It suggests schedules for a consuming repository; the source pack does not ship those scheduled jobs.

Quick rules:

- Prefer `--incremental` on repeat builds; use `--rebuild` only when invalidating caches.
- Raise `--max-files` above the default 1000 when indexing large trees; choose fixture sizes that fit the available runner.
- Run representative medium and large fixtures locally or in CI configured by the consuming repository; do not treat example sizes as measured SLA.
- Do not treat missing `.codex/knowledge-graph.json` as failure unless `--require-standalone-graph` is set.

## Consumer CI integration

Use `skills/templates/github-actions-quality-gate.yml` as a starting point, then adapt Python/Node versions, dependency installation, and the skills root path to the consuming repository. Add a scheduled scale job only after measuring an acceptable runner budget. This template is not an active workflow for the plugin repository.
