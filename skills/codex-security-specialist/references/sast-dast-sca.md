# SAST, DAST & SCA — Deep Dive

## Comparison

| Aspect | SAST | DAST | SCA |
| --- | --- | --- | --- |
| What | Analyze source code | Analyze running app | Analyze dependencies |
| When | CI (on every commit) | CD (on staging) | CI (on every commit) |
| Speed | Fast (seconds-minutes) | Slow (minutes-hours) | Fast (seconds) |
| False positives | Medium-High | Low-Medium | Low |
| Finds | Code bugs, injection, hardcoded secrets | Runtime vulns, misconfig, auth bypass | Known CVEs in packages |
| Misses | Runtime config issues | Code-level bugs | Zero-day exploits |
| Tools | Semgrep, SonarQube, CodeQL | OWASP ZAP, Burp Suite | Snyk, npm audit, Dependabot |

## SAST — Semgrep (Recommended)

```bash
# Install
pip install semgrep

# Run with auto rules (OWASP, security)
semgrep scan --config auto .

# Specific rulesets
semgrep scan --config p/owasp-top-ten .
semgrep scan --config p/javascript .
semgrep scan --config p/nodejs .
semgrep scan --config p/react .

# Custom rules
semgrep scan --config ./security-rules/ .
```

### Custom Semgrep Rule Example
```yaml
# .semgrep/no-eval.yml
rules:
  - id: no-eval
    patterns:
      - pattern: eval(...)
    message: "eval() is dangerous — use JSON.parse() or a safe alternative"
    severity: ERROR
    languages: [javascript, typescript]

  - id: no-raw-sql
    patterns:
      - pattern: |
          $DB.query(`... ${$VAR} ...`)
    message: "SQL injection risk — use parameterized queries"
    severity: ERROR
    languages: [javascript, typescript]

  - id: no-hardcoded-secret
    patterns:
      - pattern: |
          $KEY = "sk_live_..."
    message: "Hardcoded secret detected — use environment variables"
    severity: ERROR
    languages: [javascript, typescript]
```

## SAST — SonarQube

```yaml
# docker-compose for SonarQube
services:
  sonarqube:
    image: sonarqube:community
    ports: ["9000:9000"]
    environment:
      SONAR_JDBC_URL: jdbc:postgresql://db:5432/sonar
    volumes: [sonar-data:/opt/sonarqube/data]

# CI scanner
sonar-scan:
  script:
    - npx sonarqube-scanner
        -Dsonar.projectKey=myapp
        -Dsonar.sources=src
        -Dsonar.host.url=https://sonar.example.com
        -Dsonar.token=$SONAR_TOKEN
```

## SAST — CodeQL (GitHub native)

```yaml
# .github/workflows/codeql.yml
name: CodeQL Analysis
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
  schedule: [{ cron: '0 6 * * 1' }]  # Weekly

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript
          queries: security-and-quality  # Extended rules
      - uses: github/codeql-action/analyze@v3
```

## DAST — OWASP ZAP in CI

```yaml
dast:
  stage: staging
  services:
    - name: app:$CI_COMMIT_SHA
      alias: target
  script:
    # Baseline scan (passive — fast)
    - docker run ghcr.io/zaproxy/zaproxy:stable zap-baseline.py
        -t http://target:3000
        -J zap-baseline.json

    # API scan (active — comprehensive)
    - docker run ghcr.io/zaproxy/zaproxy:stable zap-api-scan.py
        -t http://target:3000/api-docs.json
        -f openapi
        -J zap-api.json

    # Full scan (active — most thorough, slowest)
    # Only run weekly, not on every PR
    - docker run ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py
        -t http://target:3000
        -J zap-full.json
```

## SCA — Dependency Scanning

```bash
# npm audit (built-in)
npm audit --production              # Production deps only
npm audit fix --force               # Auto-fix (may break things)

# Snyk (most comprehensive)
npx snyk test                       # Test for known vulns
npx snyk monitor                    # Continuous monitoring
npx snyk code test                  # SAST via Snyk

# OSV Scanner (Google's open-source)
osv-scanner --lockfile=package-lock.json

# License compliance
npx license-checker --production --failOn 'GPL'
```

### Dependabot Configuration
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: npm
    directory: "/"
    schedule: { interval: weekly }
    open-pull-requests-limit: 10
    reviewers: ["security-team"]
    labels: ["dependencies", "security"]
    allow:
      - dependency-type: production    # Only production deps
    groups:
      minor-patch:
        update-types: ["minor", "patch"]
```

## Handling Findings

```
Finding → Triage (true positive?) → YES → Fix → Verify → Close
                                  → NO  → Suppress with reason
```

### Suppression Policy
- Every suppression MUST have a comment explaining WHY
- Suppressions reviewed quarterly
- Critical/High suppressions expire after 90 days (must re-evaluate)
