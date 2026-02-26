# SOC 2 Checklist - Security, Availability, Confidentiality

## What Is SOC 2?
SOC 2 is an attestation framework (AICPA) focused on Trust Services Criteria (TSC). It is not a certification. Auditors evaluate control design and operating effectiveness over a period.

## Trust Services Criteria

| Criterion | Goal | Typical Engineering Controls |
| --- | --- | --- |
| Security (CC) | Protect systems from unauthorized access | SSO, MFA, least privilege, vulnerability management |
| Availability (A) | Keep systems available as committed | SLOs, monitoring, backups, DR runbooks |
| Processing Integrity (PI) | Accurate, complete, timely processing | Input validation, idempotency, reconciliation |
| Confidentiality (C) | Protect confidential data | Encryption, access segmentation, DLP controls |
| Privacy (P) | Handle personal data correctly | Consent, retention, DSR workflows |

## Control Areas And Checks

### Access Control
- [ ] Centralized identity provider (SSO)
- [ ] MFA required for privileged accounts
- [ ] Joiner/mover/leaver process documented
- [ ] Access review evidence retained quarterly

### Change Management
- [ ] Pull request review required
- [ ] CI checks required before merge
- [ ] Production deploy approvals enforced
- [ ] Emergency change process documented

### Logging And Monitoring
- [ ] Security-relevant logs centralized
- [ ] Alerting on critical events configured
- [ ] Log retention aligns with policy
- [ ] Time synchronization enabled across systems

### Vulnerability Management
- [ ] Regular scanning schedule documented
- [ ] Severity-based remediation SLA enforced
- [ ] Exceptions approved with expiration date
- [ ] Dependency and container scanning active

### Backup And Disaster Recovery
- [ ] Backup schedule and scope defined
- [ ] Offsite/immutable backup configured
- [ ] Restore tests performed and recorded
- [ ] RTO/RPO objectives mapped to services

## Evidence You Should Keep
- Access review reports and approval records
- PR reviews and CI pipeline logs
- Deployment logs and rollback records
- Vulnerability scan reports and tickets
- Incident records and postmortems
- Backup and restore test results
- Security training completion reports

## Quick Wins For Teams Starting SOC 2
1. Enforce MFA everywhere privileged access exists.
2. Enable audit logging for auth, secrets, and admin actions.
3. Require PR review + branch protection on default branch.
4. Set and track patching SLA by severity.
5. Add quarterly access review with owner sign-off.

## Example SLA Matrix

| Severity | Target Fix Window |
| --- | --- |
| Critical | 24-72 hours |
| High | 7 days |
| Medium | 30 days |
| Low | 90 days |

## Common Audit Failures
- Missing evidence even when control exists.
- Manual controls not consistently executed.
- Overly broad admin permissions.
- Untracked production changes.
- No restore testing for backups.

## Engineering Checklist
- [ ] Controls mapped to TSC criteria
- [ ] Owners assigned to each control
- [ ] Evidence source identified and automated where possible
- [ ] Quarterly control review scheduled
