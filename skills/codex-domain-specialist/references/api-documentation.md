# API Documentation Patterns

## OpenAPI Best Practices

- Document summary, params, request body, responses for every endpoint.
- Use shared `$ref` schemas for Error/Pagination/Common entities.
- Include example payloads.
- Document auth requirements explicitly.

## Standard Response Envelope

```json
{ "success": true, "data": {}, "meta": { "page": 1, "total": 50 } }
```

```json
{ "success": false, "message": "User not found", "code": "NOT_FOUND", "errors": [] }
```

## Versioning Strategy

- Prefer URL versioning (`/api/v1`, `/api/v2`) for breaking changes.
- Keep previous major API active during migration window.
- Track consumer usage and publish migration notes.

## Changelog Rules

- Log all breaking changes.
- Include migration guidance.
- Use ISO dates in entries.
