# Git Workflow

## Branching Strategy (Trunk-Based for Small Teams)

- `main` for production-ready code.
- short-lived `feature/*`, `fix/*`, `hotfix/*` branches.

## Branch Naming

- `feature/add-user-dashboard`
- `fix/login-validation-error`
- `hotfix/security-patch-auth`
- `chore/update-dependencies`

## Conventional Commits

```text
<type>(<scope>): <subject>
```

Examples:

- `feat(auth): add refresh token rotation`
- `fix(dashboard): correct birthday filter logic`
- `refactor(api): extract validation middleware`
- `docs(readme): update setup instructions`
- `test(users): add integration tests`
- `chore(deps): update mongoose`

## PR Template Essentials

- what changed and why
- change type
- test evidence
- screenshots for UI changes

## Release Tagging

```bash
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

Use semantic versioning: MAJOR.MINOR.PATCH.
