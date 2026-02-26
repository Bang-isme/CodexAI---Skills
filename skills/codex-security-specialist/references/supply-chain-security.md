# Software Supply Chain Security

## Core Principle
Your software is only as secure as its weakest dependency. Attackers target the supply chain because one compromised package can infect thousands of apps.

## Attack Vectors

| Vector | How It Works | Real Examples |
| --- | --- | --- |
| Typosquatting | Malicious package with similar name | `colouors` instead of `colors` |
| Dependency confusion | Public package overrides private name | Private `@company/utils` vs public `utils` |
| Maintainer takeover | Attacker gains access to maintainer account | `event-stream` npm package (2018) |
| Build system compromise | Inject malicious code during CI/CD | SolarWinds (2020) |
| Protestware | Maintainer intentionally sabotages package | `node-ipc` wiper (2022) |

## Defense Layers

### Layer 1: Dependency Pinning
```json
// package.json — pin exact versions
{
  "dependencies": {
    "express": "4.18.2",       // ✅ Exact
    "mongoose": "^8.0.0"       // ⚠️ Range — can auto-update
  }
}

// Use package-lock.json — commit to git!
// npm ci (not npm install) — uses exact lockfile
```

### Layer 2: Lockfile Integrity
```bash
# Verify lockfile hasn't been tampered with
npm ci                    # Fails if lockfile doesn't match package.json
npm ci --ignore-scripts   # Don't run postinstall scripts (security)

# npm audit signatures (verify package provenance)
npm audit signatures
```

### Layer 3: Dependency Review
```yaml
# .github/workflows/dependency-review.yml
name: Dependency Review
on: pull_request
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
          deny-licenses: GPL-3.0, AGPL-3.0   # License compliance
          allow-ghsas: GHSA-xxxx             # Known accepted risks
```

### Layer 4: SBOM (Software Bill of Materials)
```bash
# Generate SBOM (CycloneDX format)
npx @cyclonedx/cyclonedx-npm --output-file sbom.json

# Syft (supports many ecosystems)
syft packages dir:. -o cyclonedx-json > sbom.json

# Scan SBOM for vulnerabilities
grype sbom:sbom.json
```

### Layer 5: Package Provenance
```bash
# npm provenance: verify package was built from source
npm publish --provenance  # Publisher signs with CI identity

# Sigstore: sign and verify artifacts
cosign sign myapp:v1.0.0
cosign verify myapp:v1.0.0
```

### Layer 6: Private Registry
```bash
# Use private npm registry for internal packages
# Verdaccio (self-hosted) or GitHub Packages / Artifactory

# .npmrc — prioritize private registry
@company:registry=https://npm.company.com/
//npm.company.com/:_authToken=${NPM_TOKEN}

# Block public packages with same scope
# Configure registry to reject public lookups for @company/* scope
```

## Dependency Hygiene

```bash
# Monthly dependency update routine:

# 1. Check for vulnerabilities
npm audit

# 2. Update dependencies
npm outdated                     # See what's behind
npx npm-check-updates -u         # Update package.json
npm install                      # Install updates
npm test                         # Verify nothing breaks

# 3. Review changelogs of major updates

# 4. Generate updated SBOM
npx @cyclonedx/cyclonedx-npm --output-file sbom.json
```

## Automation

| Tool | Purpose | Frequency |
| --- | --- | --- |
| Dependabot / Renovate | Auto-PR for dependency updates | Weekly |
| npm audit CI | Block merge on known CVEs | Every build |
| Snyk monitor | Continuous vulnerability monitoring | Real-time |
| Socket.dev | Detect suspicious package behavior | Every install |
| dependency-review-action | Review new deps in PRs | Every PR |

## Emergency Response: Compromised Dependency
```
1. IDENTIFY: Which package, which version, which vulnerability
2. PIN: Lock to last known good version immediately
3. AUDIT: Check if malicious code executed in your environment
4. PATCH: Update to patched version or find alternative
5. NOTIFY: Alert team, log incident
6. REVIEW: Check all projects using affected package
```

## Checklist
- [ ] package-lock.json committed to git
- [ ] CI uses `npm ci` (not `npm install`)
- [ ] npm audit runs in CI pipeline
- [ ] Dependabot or Renovate configured
- [ ] License compliance checked (no GPL in commercial)
- [ ] SBOM generated for each release
- [ ] Private packages scoped (`@company/`)
- [ ] Postinstall scripts reviewed for suspicious behavior
- [ ] No unnecessary dependencies (audit with `depcheck`)
