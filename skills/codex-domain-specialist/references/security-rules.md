# Security Rules

## Scope and Triggers

Use this reference when tasks involve authentication, authorization, secrets, sensitive data, external inputs, or attack surface changes.

Primary triggers:
- auth/session/token changes
- input processing, file upload, parser, deserialization, query building
- cryptography, secret management, transport security work
- requests mentioning hardening, vulnerability, compliance, or audit

Secondary triggers:
- dependency upgrades with known CVE exposure
- API or frontend changes that expose new public endpoints
- operational changes affecting headers, proxy, CORS, cookies

Out of scope:
- cosmetic UI changes without input or data implications
- isolated internal refactor with zero boundary or data exposure impact

## Core Principles

- Assume all external input is hostile until validated and normalized.
- Keep least privilege as default for identity and access paths.
- Separate authentication from authorization decisions.
- Protect secrets in transit, at rest, and in logs.
- Minimize attack surface and expose only necessary interfaces.
- Prefer deny-by-default policy for protected operations.
- Treat dependency risk as part of application security.
- Use auditable, deterministic security controls.
- Plan for detection, containment, and recovery, not just prevention.
- Keep security controls testable and observable.

## Decision Tree

### Decision Tree A: Threat Modeling Flow

- If new public endpoint is introduced, classify assets and attacker goals first.
- If endpoint handles PII or credentials, enforce stronger auth and logging controls.
- If data mutation has financial or privileged impact, require explicit authorization checks.
- If file parsing or deserialization is involved, sandbox and strict format constraints are required.
- If third-party integration handles sensitive data, evaluate trust boundary and key lifecycle.
- If control cannot be verified by tests, redesign until measurable verification exists.

### Decision Tree B: Auth and Data Protection Matrix

| Scenario | Required Controls | Additional Controls |
| --- | --- | --- |
| login or token refresh | rate limiting + brute-force guard + secure cookie flags | device/session anomaly detection |
| admin action endpoint | role + ownership check + audit log | step-up auth for sensitive action |
| file upload | mime validation + size limit + storage isolation | malware scanning and quarantine |
| query endpoint with filters | schema validation + parameterized access | allowlist for sortable fields |
| webhook receiver | signature verification + replay protection | source IP policy and dead-letter queue |
| password reset | short TTL token + one-time use | user notification and suspicious activity lock |

## Implementation Patterns

- Validate input schemas at API boundary with explicit rejection semantics.
- Sanitize output rendered to HTML or rich content contexts.
- Use parameterized queries and ORM-safe query composition.
- Hash passwords with modern adaptive algorithms.
- Keep token lifetimes bounded and rotate refresh tokens.
- Use secure cookie flags: `httpOnly`, `secure`, `sameSite`.
- Store secrets in environment or secret manager, never in source.
- Implement per-endpoint authorization middleware with explicit policy mapping.
- Apply rate limiting and request throttling on auth and write-heavy routes.
- Add anti-replay protection for signed requests and webhooks.
- Encrypt sensitive data at rest with managed key rotation policy.
- Keep security logs structured and redact sensitive fields.
- Enforce CSP, HSTS, and secure transport headers where relevant.
- Review dependency vulnerabilities and patch with compatibility checks.
- Maintain incident response starter runbook for triage and containment.

## Anti-Patterns

1. ❌ Bad: Trusting client-side validation as security control.
   ✅ Good: Enforce all validation and authorization checks on the server boundary.

2. ❌ Bad: Building SQL or query fragments through string concatenation.
   ✅ Good: Use parameterized queries or ORM bind parameters for all user-controlled input.

3. ❌ Bad: Storing plaintext secrets or tokens in repository.
   ✅ Good: Keep secrets in managed secret stores and rotate credentials on every exposure event.

4. ❌ Bad: Returning stack traces or internal error details to clients.
   ✅ Good: Return generic error responses with request IDs and keep internal details in secure logs.

5. ❌ Bad: Sharing admin and user permissions in one broad role.
   ✅ Good: Define least-privilege roles and enforce granular permission checks per sensitive action.

6. ❌ Bad: Using long-lived bearer tokens without rotation.
   ✅ Good: Use short-lived access tokens with refresh rotation and revocation support.

7. ❌ Bad: Ignoring CORS and cookie policy interactions.
   ✅ Good: Define strict CORS allowlists and secure cookie attributes (`HttpOnly`, `Secure`, `SameSite`).

8. ❌ Bad: Logging full request payloads containing sensitive fields.
   ✅ Good: Redact sensitive fields before logging and block insecure log patterns in review.

9. ❌ Bad: Allowing unrestricted file uploads and parser behavior.
   ✅ Good: Allowlist file types and size limits, then scan uploaded files before processing.

10. ❌ Bad: Skipping dependency audit for internet-facing services.
   ✅ Good: Run automated dependency and vulnerability scans in CI with patch SLAs.

11. ❌ Bad: Hardcoding crypto keys or initialization vectors.
   ✅ Good: Generate cryptographic keys and IVs via secure RNG and load keys from secure storage.

12. ❌ Bad: Treating security scanning findings as optional documentation.
   ✅ Good: Treat critical scan findings as release blockers unless a documented exception is approved.

13. ❌ Bad: Disabling auth checks in non-test runtime paths.
   ✅ Good: Keep auth bypasses confined to test doubles and assert they are disabled in production builds.

14. ❌ Bad: Deploying without security-focused rollback strategy.
   ✅ Good: Prepare security rollback playbooks to revoke tokens, disable features, and restore safe versions quickly.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Are server-side authentication and authorization checks enforced for all sensitive operations?
- [ ] Yes/No: Are secrets and cryptographic keys managed outside source control with rotation policy?
- [ ] Yes/No: Are trust-boundary inputs validated and outputs safely encoded?
- [ ] Yes/No: Are sensitive fields redacted from logs and telemetry?
- [ ] Yes/No: Is least-privilege role design applied to admin and privileged paths?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Are SAST, SCA, and secret scans passing for changed code and dependencies?
- [ ] Yes/No: Are authorization bypass attempts tested for protected routes?
- [ ] Yes/No: Are file upload abuse cases (type spoofing, oversize, malware) tested?
- [ ] Yes/No: Are token expiry, refresh rotation, and revocation flows tested?
- [ ] Yes/No: Is security rollback procedure tested for high-risk releases?

## Cross-References

- `backend-rules.md` for resilient server-side contract handling.
- `api-design-rules.md` for secure API error and versioning behavior.
- `database-rules.md` for data integrity and persistence safety.
- `testing-rules.md` for security-focused test layering.
- `devops-rules.md` for deployment-time hardening and secrets handling.
- `debugging-rules.md` for incident triage and root-cause process.

### Scenario Walkthroughs

- Scenario: Credential stuffing attacks target login endpoint.
  - Action: Add rate limiting, account lockout thresholds, and anomaly alerts on auth failures.
  - Action: Verify lockout and recovery behavior with automated security tests.
- Scenario: Critical CVE appears in an auth dependency.
  - Action: Patch or pin to fixed version immediately and redeploy through emergency pipeline.
  - Action: Run regression security tests and document remediation timeline in incident notes.
- Scenario: Admin route is accessible by non-admin token due policy bug.
  - Action: Add explicit role checks in policy layer and deny by default on missing claims.
  - Action: Add negative authorization tests for every admin endpoint before release.

### Delivery Notes

- Keep security exceptions time-bound with explicit owner and expiry.
- Require post-incident review for material security events.
- Integrate dependency and secret scanning into release gates.
- Document threat model updates for new public attack surfaces.

- Revalidate this domain checklist after each major release cycle.
- Capture one representative example per recurring issue class.
- Ensure cross-reference links stay consistent with routing table updates.
