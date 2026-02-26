# Auth Patterns

## Scope and Triggers

Use when implementing authentication, authorization, session handling, token lifecycle, or account security controls.

Primary triggers:
- login/signup/reset-password flows
- JWT or session middleware changes
- role/permission model updates
- SSO/OAuth integration requests

## Core Principles

- Authentication proves identity; authorization grants permissions.
- Keep token lifecycle explicit: issue, refresh, revoke, expire.
- Store secrets in environment variables, never in source.
- Keep auth logic centralized and auditable.
- Treat every auth endpoint as attack surface.

## JWT Lifecycle

### Access + Refresh Model

- Access token TTL: short (5-30 minutes).
- Refresh token TTL: medium (7-30 days).
- Refresh token should be revocable (hash in DB/Redis).
- Rotate refresh tokens on every refresh call.

### Recommended Claims

- `sub`: user identifier
- `iat`, `exp`: issuance and expiration
- `iss`, `aud`: issuer and audience
- `role` or `scopes`: authorization context
- `jti`: unique token id for revocation tracking

### Rotation Flow

1. Client sends refresh token.
2. Server validates signature and token family.
3. Server revokes old refresh token.
4. Server issues new access + refresh pair.
5. Server logs audit event.

## Refresh Token Revocation Strategies

| Strategy | Pros | Cons |
| --- | --- | --- |
| Token version on user record | Simple global revoke | Revokes all sessions |
| Token family + blacklist | Granular per-device revoke | More storage + cleanup |
| Short-lived refresh only | Minimal state | More frequent login prompts |

## OAuth2 Flows

### Authorization Code (Server-side)

Use for trusted backend apps that can keep client secret secure.

Flow:
1. Redirect user to provider authorization URL.
2. Receive one-time authorization code.
3. Exchange code for access/refresh token server-side.
4. Fetch profile and map/link account.

### Authorization Code + PKCE (SPA/Mobile)

Use for public clients without secret storage.

- Generate `code_verifier` and `code_challenge`.
- Send challenge in authorize request.
- Send verifier in token exchange.
- Provider validates challenge-verifier pairing.

PKCE is mandatory for mobile and browser-based public clients.

## Session-Based Auth

Use when you need server-side session invalidation and strong control.

### Pattern

- Store session id in secure, httpOnly cookie.
- Session data in Redis/database.
- Rotate session id after login and privilege escalation.
- CSRF protection required for cookie-based auth.

### Cookie Flags

- `HttpOnly: true`
- `Secure: true` (production)
- `SameSite: Lax` or `Strict`
- Explicit expiration + inactivity timeout

## Authorization Patterns

### RBAC (Role-Based Access Control)

- Define roles (user, manager, admin).
- Map roles to permissions centrally.
- Enforce at route and service boundaries.

### ABAC (Attribute-Based Access Control)

- Evaluate resource ownership, team, region, policy.
- Use policy engine for complex conditions.

### Practical Rule

- Use RBAC by default.
- Add ABAC rules only where role granularity is insufficient.

## Password Security

### Hashing

- Prefer Argon2id where available.
- Use bcrypt cost 10-14 when Argon2 unavailable.
- Never store raw or reversible passwords.

### Policies

- Min length 8-12, allow passphrases.
- Block known-breached passwords.
- Rate-limit login and reset endpoints.

## Account Lockout and Abuse Controls

- Track failed login attempts by account + IP.
- Temporary lockout after threshold (for example 5 fails, 15 min).
- Progressive delays for repeated failures.
- Always return generic error for invalid credentials.

## 2FA Overview

### Options

- TOTP app (recommended baseline)
- Hardware keys (WebAuthn/FIDO2, highest assurance)
- SMS OTP (fallback only)

### Enrollment Pattern

1. Re-auth user before enabling 2FA.
2. Generate secret and recovery codes.
3. Verify first OTP before activation.
4. Store hashed recovery codes.

## Secure Auth API Checklist

- `POST /auth/signup`
- `POST /auth/signin`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`

Each endpoint should have:
- input validation
- rate limits
- audit logs
- consistent error envelope

## Anti-Patterns

1. Storing JWT in localStorage without XSS hardening.
2. Long-lived access tokens (>1 day).
3. No refresh token revocation path.
4. Role checks only in frontend UI.
5. Returning detailed credential failure reasons.
6. Password hashing with unsalted SHA variants.

## Observability and Auditing

Log security events with correlation ids:
- login success/failure
- refresh rotation success/failure
- lockout triggered/released
- password change/reset
- role/permission changes

Do not log sensitive token values or password fields.

## Review Checklist

- Are access and refresh TTLs explicitly defined?
- Is refresh token rotation implemented?
- Is revoke/kill-session capability present?
- Are auth endpoints rate-limited?
- Are role checks enforced server-side?
- Is password hashing algorithm and cost appropriate?
- Is 2FA flow resistant to replay and brute force?
