# Input Validation & Schema Boundary Patterns

## Scope and Triggers

Use when handling user input, API request payloads, query parameters, environment variables, webhook payloads, or form submissions.

## Core Principle

**Parse, don't just validate.** Every external boundary (HTTP body, query string, URL params, webhook payload, `process.env`, LLM output) is untrusted until parsed through a strict schema that strips unknown keys, normalizes strings, and outputs a static TypeScript/Python type.

---

## 1. Shared Contract Validation with Zod (TypeScript Strict)

Define schemas once per domain module and infer static types directly so validation rules and TypeScript types never drift:

```typescript
import { z } from "zod";

export const CreateCampaignSchema = z
  .object({
    name: z.string().trim().min(3, "Campaign name must be at least 3 characters").max(120),
    slug: z
      .string()
      .trim()
      .toLowerCase()
      .regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, "Slug must be lowercase kebab-case"),
    budgetCents: z.number().int().min(500, "Minimum budget is 500 cents ($5.00)").max(100_000_000),
    currency: z.enum(["USD", "EUR", "VND"]),
    startAt: z.string().datetime({ offset: true }),
    endAt: z.string().datetime({ offset: true }),
    tags: z.array(z.string().trim().min(1).max(32)).max(10).default([]),
  })
  .strict() // Reject unexpected/injected properties
  .refine((data) => new Date(data.endAt) > new Date(data.startAt), {
    path: ["endAt"],
    message: "End time must be after start time",
  });

export type CreateCampaignInput = z.infer<typeof CreateCampaignSchema>;

export const CursorPaginationSchema = z.object({
  cursor: z.string().trim().max(512).optional(),
  limit: z.coerce.number().int().min(1).max(100).default(25),
  sortOrder: z.enum(["asc", "desc"]).default("desc"),
});
```

---

## 2. Boundary Validation Middleware (`SILC-###` Error Mapping)

Map schema validation failures directly to the canonical `422 Unprocessable Entity` error envelope with `fieldErrors`:

```typescript
import { AnyZodObject, ZodError } from "zod";
import { AppError } from "../errors/app-error";

export function validateRequest(schemas: {
  body?: AnyZodObject;
  query?: AnyZodObject;
  params?: AnyZodObject;
}) {
  return (req: Request, _res: Response, next: NextFunction) => {
    try {
      if (schemas.body) req.body = schemas.body.parse(req.body);
      if (schemas.query) req.query = schemas.query.parse(req.query);
      if (schemas.params) req.params = schemas.params.parse(req.params);
      next();
    } catch (err) {
      if (err instanceof ZodError) {
        const fieldErrors = err.issues.map((issue) => ({
          field: issue.path.join(".") || "root",
          code: issue.code.toUpperCase(),
          message: issue.message,
        }));
        return next(
          new AppError("VALIDATION_FAILED", "Request validation failed", 422, { fieldErrors }),
        );
      }
      next(err);
    }
  };
}
```

---

## 3. Fail-Fast Environment Configuration Validation

Never read raw `process.env.SOME_KEY` deep inside business services. Validate all environment variables at process boot:

```typescript
const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]),
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  DATABASE_URL: z.string().url(),
  SESSION_SECRET: z.string().min(32, "SESSION_SECRET must be at least 32 characters"),
});

export const env = EnvSchema.parse(process.env);
```

---

## 4. Defense-in-Depth Sanitization & Security Rules

1. **Mass-Assignment Prevention:** Always use `.strict()` or explicit field allowlists; never pass raw `req.body` into `db.update()` or `Object.assign()`.
2. **File Upload Validation:** Validate file size, extension allowlist, and magic-byte MIME signature on the server; store uploaded files with generated UUID names outside the web root or via presigned object storage URLs.
3. **Webhook Signature Verification:** Verify HMAC cryptographic signatures (`Stripe-Signature`, `X-Hub-Signature-256`) against the raw request buffer before parsing JSON.
4. **Unicode & Whitespace Normalization:** `.trim()` and normalize user-supplied identifiers (emails, slugs, usernames) before uniqueness checks or database persistence.
