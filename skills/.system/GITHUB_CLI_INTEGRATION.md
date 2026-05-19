# GitHub CLI Integration

This pack treats GitHub CLI (`gh`) as the supported path for pull request, release, and future project-CLI automation.

## Why `gh`

- It avoids scraping GitHub pages or requiring custom REST wrappers for common workflows.
- It provides a standard auth store for local users.
- It maps cleanly to CI via `GH_TOKEN` or `GITHUB_TOKEN`.

## Install

Windows:

```powershell
winget install --id GitHub.cli -e
```

macOS:

```bash
brew install gh
```

Linux:

Follow the official GitHub CLI package instructions:

```text
https://github.com/cli/cli#installation
```

## Authenticate

Local interactive setup:

```powershell
gh auth login
gh auth status
```

Recommended choices for normal repository work:

- Host: `GitHub.com`
- Protocol: `HTTPS`
- Scopes: include `repo` for private repositories and PR automation
- Credential storage: GitHub CLI managed storage

Do not write tokens into plugin manifests, skill docs, generated artifacts, or source files.

## CI / Project CLI Wrapper

For non-interactive wrappers, provide one of these environment variables:

```bash
GH_TOKEN=<token>
GITHUB_TOKEN=<token>
```

Then verify before invoking PR/release commands:

```bash
gh auth status
gh repo view --json nameWithOwner
```

Future project CLI wrappers should:

1. Check that `gh` is available.
2. Run `gh auth status` before GitHub operations.
3. Fail with a clear setup message when auth is missing.
4. Never echo tokens or persist them into `.codex/`, plugin manifests, or logs.

