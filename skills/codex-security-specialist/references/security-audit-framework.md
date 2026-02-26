# Security Audit Framework

## Objective
Provide a repeatable audit framework covering application, infrastructure, cloud, DevSecOps, and compliance controls with clear evidence requirements.

## Audit Types
- Application security audit.
- Infrastructure hardening audit.
- Cloud security configuration audit.
- DevSecOps pipeline audit.
- Compliance readiness audit (ISO/SOC/GDPR).
- Incident readiness and response audit.

## Application Security Checklist
- [ ] Authentication and session controls reviewed.
- [ ] Authorization checks enforced on every sensitive route.
- [ ] Input validation and output encoding verified.
- [ ] Security headers configured and tested.
- [ ] Dependency vulnerabilities triaged within SLA.
- [ ] Secret handling validated (no hardcoded secrets).

## Infrastructure Checklist
- [ ] SSH hardening and key-only auth for admin access.
- [ ] Host firewall default-deny with explicit allowlist.
- [ ] Patch baseline and auto-update policy documented.
- [ ] Time sync, audit logging, and retention configured.
- [ ] Backup and restore drill evidence available.

## Cloud Checklist
- [ ] IAM least-privilege with periodic access review.
- [ ] Public exposure checks for storage and databases.
- [ ] Encryption at rest and in transit verified.
- [ ] CloudTrail/GuardDuty/monitoring enabled.
- [ ] Network segmentation by environment/workload.

## DevSecOps Checklist
- [ ] SAST, DAST, and SCA integrated in CI pipeline.
- [ ] IaC scanning and policy checks required before deploy.
- [ ] Artifact signing/provenance in release process.
- [ ] Security gate blocks high/critical findings by policy.
- [ ] Exception process has owner, expiry, and justification.

## Access Review Process
1. Extract user/service account permissions from IAM/IdP.
2. Map each permission to owner and business justification.
3. Revoke stale or over-privileged access.
4. Record approvals and remediation actions.
5. Repeat at least quarterly.

## Automated Daily Security Health Check (Example)
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "[1] Check expiring certificates (<30 days)"
echo "[2] Check vulnerability scanner feed status"
echo "[3] Check backup job status"
echo "[4] Check failed-login spikes"
echo "[5] Check disabled or stale security controls"
```

## Audit Evidence Matrix

| Control | Evidence |
| --- | --- |
| MFA enforcement | IdP policy export and sampled user proof |
| Code review gate | PR settings and merge logs |
| Vulnerability SLA | Ticket timestamps and remediation records |
| Backup restore | Restore test logs and sign-off |
| Incident drill | Tabletop report and action items |

## Report Template
- Scope and systems reviewed.
- Method and tools used.
- Findings by severity.
- Business impact and affected assets.
- Remediation plan with owner and deadline.
- Residual risk statement.

## Severity Model
- Critical: active exploit path or systemic control failure.
- High: major weakness with realistic exploitation path.
- Medium: control gap needing planned remediation.
- Low: hygiene or documentation issue.

## Checklist
- [ ] Audit scope approved by stakeholders
- [ ] Evidence sources identified before execution
- [ ] Findings tracked in ticket system
- [ ] Re-audit planned after remediation
