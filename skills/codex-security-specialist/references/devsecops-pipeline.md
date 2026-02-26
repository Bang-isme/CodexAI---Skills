# DevSecOps Pipeline

## Core Principle
Security is NOT a phase — it runs in EVERY phase of CI/CD. Shift left: find vulns early = cheaper to fix.

## Pipeline Architecture

```
Developer workstation        CI Pipeline                    CD Pipeline
┌──────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ pre-commit hooks  │    │ 1. Lint + Format     │    │ 7. Image Sign       │
│ • secret scan     │───→│ 2. Unit Tests        │───→│ 8. Deploy (staging) │
│ • lint            │    │ 3. SAST (code scan)  │    │ 9. DAST Scan        │
│ • format          │    │ 4. SCA (deps scan)   │    │ 10. Smoke Tests     │
└──────────────────┘    │ 5. Build Image        │    │ 11. Deploy (prod)   │
                        │ 6. Image Scan (CVE)   │    │ 12. Runtime Monitor │
                        └─────────────────────┘    └─────────────────────┘
```

## Pre-Commit Hooks (Developer Side)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: check-merge-conflict
      - id: detect-private-key          # Block private keys
      - id: check-added-large-files
        args: ['--maxkb=500']

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets               # Block hardcoded secrets
        args: ['--baseline', '.secrets.baseline']

  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint                      # Dockerfile lint

  - repo: https://github.com/eslint/eslint
    rev: v8.56.0
    hooks:
      - id: eslint                        # JS/TS security lint
        args: ['--config', '.eslintrc.security.js']
```

## CI Pipeline Stages

### Stage 1-2: Build & Test (fail fast)
```yaml
build-and-test:
  script:
    - npm ci
    - npm run lint
    - npm run test -- --coverage
    - npm run build
  artifacts:
    reports:
      coverage: coverage/lcov.info
```

### Stage 3: SAST (Static Application Security Testing)
```yaml
sast-scan:
  script:
    # Semgrep — fast, supports JS/TS/Python/Go
    - semgrep scan --config auto --error --json -o semgrep-results.json .
    # Rules: OWASP Top 10, injection, auth bypass, hardcoded secrets
  allow_failure: false   # Block merge on critical findings
```

### Stage 4: SCA (Software Composition Analysis)
```yaml
dependency-scan:
  script:
    - npm audit --audit-level=high
    - npx snyk test --severity-threshold=high
  allow_failure: false   # Block on HIGH/CRITICAL CVEs
```

### Stage 5-6: Build & Scan Image
```yaml
image-scan:
  script:
    - docker build -t app:$CI_COMMIT_SHA .
    - trivy image --exit-code 1 --severity HIGH,CRITICAL app:$CI_COMMIT_SHA
    - dockle app:$CI_COMMIT_SHA
```

### Stage 9: DAST (Dynamic Application Security Testing)
```yaml
dast-scan:
  stage: staging
  script:
    # Deploy to staging first, then scan running application
    - docker run -t ghcr.io/zaproxy/zaproxy:stable zap-api-scan.py
        -t https://staging.example.com/api-docs.json
        -f openapi
        -r dast-report.html
  artifacts:
    paths: [dast-report.html]
  allow_failure: true   # DAST may have false positives — review manually
```

## Security Gate Policy

| Severity | Pre-commit | CI | CD (staging) | Production |
| --- | --- | --- | --- | --- |
| Critical | Block commit | Block merge | Block deploy | Rollback |
| High | Warn | Block merge | Warn | Monitor |
| Medium | Ignore | Warn | Ignore | Log |
| Low | Ignore | Ignore | Ignore | Log |

## Metrics to Track

| Metric | Target | Measure |
| --- | --- | --- |
| Mean time to remediate (MTTR) Critical | < 24 hours | Ticket created → fix deployed |
| MTTR High | < 1 week | Ticket created → fix deployed |
| Known vuln count (Critical+High) | 0 | Dashboard count |
| Dependency freshness | < 30 days behind latest | Renovate/Dependabot report |
| SAST false positive rate | < 20% | Suppressions / total findings |
| Security scan coverage | 100% of repos | Repos with CI security scanning |
