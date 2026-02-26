# Validation Patterns

## Scope and Triggers

Use when handling user input, API requests, form submissions, or data transformation boundaries.

## Core Principle

Validate at boundaries, trust internally. Every external input is untrusted.

## Backend Validation (Joi)

```javascript
import Joi from 'joi';

const schemas = {
  createUser: Joi.object({
    email: Joi.string().email().required().max(255).lowercase().trim(),
    password: Joi.string().min(8).max(128).required()
      .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
      .message('Password must contain lowercase, uppercase, and number'),
    firstName: Joi.string().trim().min(1).max(100).required(),
    lastName: Joi.string().trim().min(1).max(100).required(),
    role: Joi.string().valid('user', 'manager', 'admin').default('user'),
  }),

  updateUser: Joi.object({
    email: Joi.string().email().max(255).lowercase().trim(),
    firstName: Joi.string().trim().min(1).max(100),
    lastName: Joi.string().trim().min(1).max(100),
  }).min(1),

  pagination: Joi.object({
    page: Joi.number().integer().min(1).default(1),
    limit: Joi.number().integer().min(1).max(100).default(20),
    sort: Joi.string().valid('createdAt', 'name', 'email').default('createdAt'),
    order: Joi.string().valid('asc', 'desc').default('desc'),
    search: Joi.string().trim().max(200).allow(''),
  }),

  mongoId: Joi.string().pattern(/^[0-9a-fA-F]{24}$/).message('Invalid ID format'),
};

const validate = (schema, source = 'body') => (req, res, next) => {
  const { error, value } = schema.validate(req[source], {
    abortEarly: false,
    stripUnknown: true,
    convert: true,
  });

  if (error) {
    return res.status(422).json({
      success: false,
      message: 'Validation failed',
      errors: error.details.map((d) => ({
        field: d.path.join('.'),
        message: d.message.replace(/"/g, ''),
      })),
    });
  }

  req.validated = value;
  next();
};
```

## Frontend Validation (React)

```jsx
const useFormValidation = (schema) => {
  const [errors, setErrors] = useState({});

  const validate = (data) => {
    const { error } = schema.validate(data, { abortEarly: false });
    if (!error) {
      setErrors({});
      return true;
    }

    const fieldErrors = {};
    error.details.forEach((d) => {
      fieldErrors[d.path[0]] = d.message.replace(/"/g, '');
    });
    setErrors(fieldErrors);
    return false;
  };

  const clearError = (field) => {
    setErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  };

  return { errors, validate, clearError };
};
```

## Sanitization Rules

| Input Type | Sanitize | Example |
| --- | --- | --- |
| Email | lowercase + trim | `  User@MAIL.com  ` -> `user@mail.com` |
| String fields | trim | `  John  ` -> `John` |
| HTML content | escape/strip tags | prevent XSS |
| File upload | MIME + extension + size validation | do not trust only `Content-Type` |
| URL params | format checks (ObjectId, UUID, int) | `/users/abc` -> 400 |
| Search query | trim + max length + regex escaping | avoid ReDoS |

## Anti-Patterns

- Validate only on frontend.
- Trust uploaded content type headers.
- Allow unbounded string length.
- Hand-write fragile regex where library validators exist.
- Return raw database errors directly.

## Review Checklist

- Are all external boundaries validated?
- Are unknown fields stripped or rejected?
- Are error responses consistent and safe?
- Are ids and pagination params validated?
- Is sanitization done before persistence and rendering?
