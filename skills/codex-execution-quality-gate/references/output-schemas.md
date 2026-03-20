# Output Schemas

This skill does not define a single shared JSON schema in `SKILL.md`.
The output-facing guidance moved here, while script-specific payload details remain in each CLI `--help` contract and the spec files listed in `SKILL.md`.

## Output Handling

For each script:

1. capture output
2. summarize errors/warnings/passes
3. ask whether to fix blocking errors when present
4. rerun after fixes to verify

## output_guard.py

Default mode remains heuristic and preserves the existing pass/fail contract.
When `--llm-judge` is enabled and API credentials are available, the report adds:

- `evaluation_mode`: `heuristic` or `llm`
- `llm_score`
- `heuristic_score`
- `estimated_cost_usd`
- `warnings`: fallback details when LLM judging is unavailable

Example:

```json
{
  "status": "pass",
  "score": 78,
  "evaluation_mode": "llm",
  "llm_score": 82,
  "heuristic_score": 69,
  "estimated_cost_usd": 0.001,
  "warnings": []
}
```

## editorial_review.py

Default mode remains heuristic and preserves the existing pass/fail contract.
When `--llm-judge` is enabled and API credentials are available, the report adds:

- `evaluation_mode`: `heuristic` or `llm`
- `llm_score`
- `heuristic_score`
- `estimated_cost_usd`
- `warnings`: fallback details when LLM judging is unavailable

Example:

```json
{
  "status": "pass",
  "score": 84,
  "evaluation_mode": "llm",
  "llm_score": 88,
  "heuristic_score": 74,
  "estimated_cost_usd": 0.001,
  "warnings": []
}
```

## auto_gate.py

Returns JSON with:

- `status`: `pass`, `fail`, or `error`
- `mode`: `quick`, `full`, or `deploy`
- `checks`: summarized results for the checks included in that mode
- `overall`: `pass` or `fail`
- `duration_seconds`
- `blocking_issues`
- `warnings`

Example:

```json
{
  "status": "pass",
  "mode": "quick",
  "checks": {
    "security": {"status": "pass", "critical": 0, "warnings": 2},
    "pre_commit": {"status": "pass", "lint": "pass", "test": "pass"}
  },
  "overall": "pass",
  "duration_seconds": 4.2,
  "blocking_issues": [],
  "warnings": ["2 security warning(s)."]
}
```

## install_hooks.py

Returns JSON with:

- `status`: `installed`, `dry_run`, `uninstalled`, `not_installed`, or `error`
- `project_root`
- `hook_path`
- `checks`: `security_scan`, `pre_commit_check`, and optionally `run_gate`

Example:

```json
{
  "status": "installed",
  "project_root": "D:/repo",
  "hook_path": "D:/repo/.git/hooks/pre-commit",
  "checks": ["security_scan", "pre_commit_check"]
}
```

## install_ci_gate.py

Returns JSON with:

- `status`: `generated` or `error`
- `path`
- `ci_platform`: `github` or `gitlab`

Example:

```json
{
  "status": "generated",
  "path": "D:/repo/.github/workflows/quality-gate.yml",
  "ci_platform": "github"
}
```
