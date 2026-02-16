# Backend Rules

## Core Principles

- Validate all inputs and trust no client data.
- Use layered flow: controller -> service -> repository.
- Keep API response shapes consistent.
- Centralize error handling and hide internals.
- Log safely and never log secrets.

## API Rules

- Use explicit HTTP status codes.
- Enforce validation at the boundary layer.
- Use parameterized queries only.
- Add rate limiting on public endpoints.
- Use pagination for list endpoints.

## Security Checklist

- authentication and authorization checks
- no hardcoded secrets
- secure middleware defaults (cors, headers)
- OWASP-aware design for affected endpoints

## Data Rules

- Use migrations for schema changes.
- Use transactions for multi-step writes.
- Add indexes for frequent queries.
- Monitor slow queries.
