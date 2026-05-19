# Deploy promotion (staging → production)

Plugin pack releases are **ZIP artifacts**, not container deploys. GitHub Actions implements promotion; optional S3/SSH targets attach when secrets exist.

## Flow

| Stage | Trigger | Environment | Output |
|-------|---------|-------------|--------|
| Staging | `CI` workflow completes successfully on `main` | `staging` | Artifact `codexai-skill-pack-staging` (14d) |
| Production | Tag push `v*` | `production` (approval required) | GitHub Release + `dist/*.zip` |
| Manual | `workflow_dispatch` on `deploy.yml` | `staging` or `production` | Gate + optional S3/SSH |

## GitHub configuration (repo settings)

1. **Environments** → create `staging` and `production`.
2. **production** → enable **Required reviewers** (and optional wait timer).
3. **Secrets** (optional real deploy):
   - `S3_BUCKET_STAGING`, `S3_BUCKET_PRODUCTION`
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
   - `SSH_HOST_STAGING`, `SSH_HOST_PRODUCTION`, `SSH_KEY` (for SSH; wire in workflow if using key-based auth)
4. **Variables** (optional): `S3_PREFIX`, `SSH_USER`, `SSH_DEPLOY_PATH`

## Local operator path

```bash
# Dry-run validators + release plan
python skills/.system/scripts/local_release_gate.py --format json

# Build ZIP locally
python skills/.system/scripts/local_release_gate.py --apply --format json

# Preview S3 commands without uploading
python skills/.system/scripts/local_release_gate.py --apply --target s3 --dry-run --format text
```

After local gate passes: `git tag vX.Y.Z && git push origin vX.Y.Z` → approve **production** deployment in GitHub Actions.

## Scripts

| Script | Role |
|--------|------|
| `local_release_gate.py` | Pack health + contracts + ZIP dry-run/apply |
| `promote_deploy.py` | Extract ZIP smoke + optional S3/SSH |
| `build_release_zip.py` | Canonical ZIP builder |

## Schema

See `deploy-targets.schema.json` for automation contracts.
