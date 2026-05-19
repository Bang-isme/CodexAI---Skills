# Project Memory CI Release Gate

Commands assume repo root `skills/` as `SKILLS_ROOT` and Python 3.10+.

## Release gate (recommended order)

```bash
# 1. Focused memory/tooling tests
python -m pytest skills/tests/test_full_cycle_hardening.py -q -k "memory_status or project_memory_tool or memory_tools_fixture"

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
- `memory_status --strict`: exit `1` when `status` is `warn`

### Expected advisory warnings (not release blockers)

After a normal build, `memory_status` may report `warn` with only:

- `code_index and codebase_index file sets differ (...)`

This is expected: the structural graph and the codebase symbol index use different traversal scopes and caps. Treat it as disclosure, not a failed build, unless your team makes graph/codebase parity mandatory in a future phase.

Regenerate artifacts before gating:

```bash
python skills/codex-project-memory/scripts/build_knowledge_index.py --project-root .
python skills/codex-project-memory/scripts/build_knowledge_graph.py --project-root .
```

Do not commit `.codex/` output; see `references/artifact-lifecycle-policy.md`.

## Full skills test suite

```bash
python -m pytest skills/tests -q
```

### Windows symlink limitation

On Windows without symlink privilege, one traversal test fails with `WinError 1314`:

```bash
python -m pytest skills/tests -q -k "not test_project_traversal_does_not_follow_symlinks_outside_root"
```

This is an OS/environment constraint, not a product-memory logic failure.

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
