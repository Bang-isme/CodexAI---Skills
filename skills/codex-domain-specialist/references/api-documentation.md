# API Documentation Patterns

**Load when:** setting up OpenAPI/Swagger, designing API versioning, building API changelogs, or choosing between code-first vs spec-first approaches.

## Approach Decision

| Approach | How | Best For | Tools |
| --- | --- | --- | --- |
| Code-first | Write code, generate spec | Rapid development, small teams | swagger-jsdoc, tsoa, NestJS |
| Spec-first | Write OpenAPI spec, generate code | API contracts, multi-team | Stoplight, Redocly |
| Hybrid | Write spec for design, sync with code | Medium projects | Redoc + swagger-jsdoc |

## OpenAPI 3.x Best Practices

### Schema Organization

```yaml
# Use $ref for reusable schemas
components:
  schemas:
    User:
      type: object
      required: [id, email, name]
      properties:
        id:
          type: string
          format: uuid
          example: "550e8400-e29b-41d4-a716-446655440000"
        email:
          type: string
          format: email
          example: "alice@example.com"
        name:
          type: string
          minLength: 1
          maxLength: 100
          example: "Alice Johnson"
        role:
          $ref: '#/components/schemas/UserRole'
        createdAt:
          type: string
          format: date-time

    UserRole:
      type: string
      enum: [admin, user, viewer]
      description: User permission level

    # Discriminated unions for polymorphic types
    Notification:
      discriminator:
        propertyName: type
        mapping:
          email: '#/components/schemas/EmailNotification'
          push: '#/components/schemas/PushNotification'
      oneOf:
        - $ref: '#/components/schemas/EmailNotification'
        - $ref: '#/components/schemas/PushNotification'
```

### Standard Response Envelope

```yaml
components:
  schemas:
    SuccessResponse:
      type: object
      properties:
        success:
          type: boolean
          example: true
        data: {}
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    ErrorResponse:
      type: object
      required: [success, message, code]
      properties:
        success:
          type: boolean
          example: false
        message:
          type: string
          example: "User not found"
        code:
          type: string
          enum: [NOT_FOUND, VALIDATION_ERROR, UNAUTHORIZED, FORBIDDEN, INTERNAL_ERROR]
        errors:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              message:
                type: string

    PaginationMeta:
      type: object
      properties:
        page: { type: integer, example: 1 }
        limit: { type: integer, example: 20 }
        total: { type: integer, example: 150 }
        totalPages: { type: integer, example: 8 }
```

### Endpoint Documentation Pattern

```yaml
paths:
  /api/v1/users/{id}:
    get:
      summary: Get user by ID
      description: Retrieves a single user. Requires authentication.
      operationId: getUserById
      tags: [Users]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
          description: User's unique identifier
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/SuccessResponse'
                  - properties:
                      data:
                        $ref: '#/components/schemas/User'
              example:
                success: true
                data: { id: "550e8400-...", name: "Alice", email: "alice@example.com" }
        '404':
          description: User not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
```

## Code-First Setup (Node.js + swagger-jsdoc)

```javascript
import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';

const options = {
  definition: {
    openapi: '3.0.3',
    info: {
      title: 'My API',
      version: '1.0.0',
      description: 'API documentation generated from JSDoc annotations',
    },
    servers: [
      { url: 'http://localhost:3000', description: 'Development' },
      { url: 'https://api.example.com', description: 'Production' },
    ],
    components: {
      securitySchemes: {
        bearerAuth: { type: 'http', scheme: 'bearer', bearerFormat: 'JWT' },
      },
    },
  },
  apis: ['./src/routes/*.js'], // Scan route files for JSDoc
};

const spec = swaggerJsdoc(options);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(spec));
app.get('/api-docs/spec.json', (req, res) => res.json(spec)); // Raw spec endpoint
```

## Versioning Strategy

| Strategy | URL Change | Pros | Cons |
| --- | --- | --- | --- |
| URL path (`/api/v1/`) | ✅ Yes | Clear, cacheable, easy routing | URL clutter |
| Header (`Accept: application/vnd.api.v1+json`) | ❌ No | Clean URLs | Hard to test in browser |
| Query param (`?version=1`) | ❌ No | Easy to implement | Caching issues |

### Recommended: URL Path Versioning

```javascript
// Mount versioned routers
import v1Router from './routes/v1/index.js';
import v2Router from './routes/v2/index.js';

app.use('/api/v1', v1Router);
app.use('/api/v2', v2Router);

// Deprecation header for old versions
app.use('/api/v1', (req, res, next) => {
  res.set('Deprecation', 'true');
  res.set('Sunset', 'Sat, 01 Jan 2027 00:00:00 GMT');
  res.set('Link', '</api/v2>; rel="successor-version"');
  next();
});
```

### Migration Window

| Phase | Duration | Action |
| --- | --- | --- |
| v2 released | Day 0 | Both v1 and v2 active |
| Deprecation notice | Month 1 | Add `Deprecation` header to v1 |
| Migration period | Months 2-4 | Monitor v1 usage, notify consumers |
| Sunset | Month 5+ | Remove v1 only when usage → 0 |

## API Changelog Automation

```markdown
# API Changelog

## [2.1.0] - 2026-04-19

### Added
- `GET /api/v2/analytics/export` - Export analytics data as CSV

### Changed
- `POST /api/v2/users` - Added required `role` field to request body [BREAKING]

### Deprecated
- `GET /api/v1/reports` - Use `/api/v2/analytics` instead. Sunset: 2027-01-01.

### Migration
- Update client SDKs to v2.1.0
- Add `role: "user"` to all user creation payloads
```

## Anti-Patterns

| Anti-Pattern | Fix |
| --- | --- |
| No examples in spec | Always include request/response examples |
| Missing error responses | Document all error codes per endpoint |
| Generic descriptions ("Gets data") | Describe WHAT data, WHO can access, WHEN to use |
| No auth documentation | Specify security scheme on every protected endpoint |
| Spec out of sync with code | CI check: validate spec against implementation |
| No deprecation notice | HTTP `Deprecation` + `Sunset` headers |
