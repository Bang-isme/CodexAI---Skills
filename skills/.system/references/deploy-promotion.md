# Plugin pack CI and local packaging

This repository is a **skill/plugin pack**. GitHub Actions here validate and test the pack — they do **not** deploy to staging or production servers.

## What runs in CI

| Workflow | Purpose |
|----------|---------|
| `ci.yml` | Validators, contracts, tests, memory scale (medium), trust harness smoke |
| `scale-nightly.yml` | Large-tier memory scale stress (weekly) |
| `release.yml` | Optional manual ZIP build (`workflow_dispatch` only) |

No `deploy.yml`, no GitHub Environments, and no S3/SSH promotion in CI.

## Local operator (optional)

Before sharing a ZIP or opening a release PR, run:

```bash
python skills/.system/scripts/local_release_gate.py --format json
python skills/.system/scripts/local_release_gate.py --apply --format json
```

`promote_deploy.py` remains available for teams that want to **manually** copy a ZIP to S3/SSH from their machine (set env vars locally). It is not wired into GitHub Actions.

## External consumers

Downstream teams install from source, global skills sync, or a ZIP they build locally. Promotion timing and hosting are outside this plugin repo.
