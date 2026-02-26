# ISO 27001 - Information Security Management

## What Is ISO 27001?
ISO/IEC 27001 is a certifiable standard for Information Security Management Systems (ISMS). It requires continuous risk assessment, control implementation, evidence collection, and regular review.

## Annex A Controls For Engineering Teams

### A.5 - Information Security Policies
- [ ] Security policy documented and accessible to all staff
- [ ] Policy reviewed annually or after major incidents
- [ ] Acceptable use policy defined for assets and data
- [ ] Remote work security policy enforced

### A.6 - Organization Of Information Security
- [ ] Security ownership is explicit (roles and responsibilities)
- [ ] Separation of duties enforced (dev != deploy != approve)
- [ ] Security contacts and escalation paths documented
- [ ] Security activities integrated into project management

### A.7 - Human Resource Security
- [ ] Background checks before privileged access
- [ ] Mandatory annual security awareness training
- [ ] Offboarding access revoked within 24 hours
- [ ] NDA required for sensitive data access

### A.8 - Asset Management
- [ ] Asset inventory maintained (servers, DBs, APIs, services)
- [ ] Data classification model in place:
  - Public
  - Internal
  - Confidential
  - Restricted
- [ ] Data retention schedule defined and implemented
- [ ] Secure disposal process for hardware and data

### A.9 - Access Control
- [ ] Least privilege and need-to-know are default
- [ ] Access review performed quarterly
- [ ] MFA required for admin and remote access
- [ ] Service accounts use machine identities only
- [ ] Privileged access managed via PAM or equivalent controls
- [ ] Access revoked within 24h after role change or departure

### A.10 - Cryptography
- [ ] Encryption policy documented and approved
- [ ] Data at rest encrypted (AES-256 or equivalent)
- [ ] Data in transit encrypted (TLS 1.2+)
- [ ] Key management lifecycle documented
- [ ] Key rotation schedule enforced
- [ ] Cryptographic suite reviewed at least yearly

### A.12 - Operations Security
- [ ] Change management process active
- [ ] Environments separated (dev/staging/prod)
- [ ] Malware protections enabled where applicable
- [ ] Backup policy includes schedule, encryption, offsite copy, restore test
- [ ] Logging and monitoring centralized
- [ ] Time synchronization enforced (NTP)
- [ ] Vulnerability management with patch SLA

### A.14 - System Development And Maintenance
- [ ] Security requirements defined in specifications
- [ ] Secure coding standards published and enforced
- [ ] Code review includes security checks
- [ ] Test data sanitized (no production PII in non-prod)
- [ ] SAST/DAST/SCA integrated into CI/CD
- [ ] Penetration testing schedule defined

### A.16 - Incident Management
- [ ] Incident response plan documented and exercised
- [ ] Incident classification and escalation matrix defined
- [ ] Post-incident review process implemented
- [ ] Evidence preservation process documented
- [ ] Regulatory notification timelines documented

### A.18 - Compliance
- [ ] Applicable laws and frameworks identified (GDPR, PCI-DSS, etc.)
- [ ] Privacy impact assessments run for high-risk features
- [ ] Internal and external audit schedules maintained
- [ ] Compliance evidence retained and auditable

## Developer Control Mapping

| Developer Action | ISO Control | Implementation Example |
| --- | --- | --- |
| Hash passwords | A.10 | `bcrypt` with cost factor 12+ |
| Encrypt DB at rest | A.10 | Cloud KMS + encrypted storage |
| Log security events | A.12 | Structured logs to SIEM |
| Quarterly access review | A.9 | Automated IAM report and approval |
| Sanitize test data | A.14 | Data masking/anonymization pipeline |
| Run scans in CI | A.14 | Semgrep, Trivy, dependency audit |
| Enforce admin MFA | A.9 | WebAuthn or TOTP |
| Test backup restore | A.12 | Monthly restore drill |

## Evidence Checklist
- [ ] Security policies and yearly review records
- [ ] Access review reports and approvals
- [ ] CI scan reports and remediation tickets
- [ ] Backup/restore test evidence
- [ ] Incident response drill reports
- [ ] Asset inventory and data classification records
