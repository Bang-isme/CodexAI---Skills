// ============================================
// EXPRESS API STARTER — Contract-First (SILC-001)
// Zod Boundary Validation + RFC 9457 Error Envelope + Cursor Pagination + Idempotency
// ============================================
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import crypto from 'node:crypto';
import jwt from 'jsonwebtoken';
import { z, ZodError } from 'zod';

const app = express();

// --- 1. Security & Request Correlation Middleware ---
app.use(helmet());
app.use(
  cors({
    origin: process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : false,
    credentials: true,
  })
);
app.use(express.json({ limit: '1mb' }));
app.use((req, res, next) => {
  req.id = req.header('x-request-id') || `req_${crypto.randomUUID()}`;
  res.setHeader('X-Request-Id', req.id);
  next();
});

// --- 2. Tiered Rate Limiting ---
const readLimiter = rateLimit({ windowMs: 60_000, max: 300, standardHeaders: true, legacyHeaders: false });
const mutationLimiter = rateLimit({ windowMs: 60_000, max: 60, standardHeaders: true, legacyHeaders: false });

// --- 3. Operational AppError & Zod Validation Middleware ---
export class AppError extends Error {
  constructor(code, message, statusCode = 400, fieldErrors = []) {
    super(message);
    this.code = code;
    this.statusCode = statusCode;
    this.fieldErrors = fieldErrors;
    this.isOperational = true;
  }
}

export const validateRequest = (schemas) => (req, _res, next) => {
  try {
    if (schemas.body) req.body = schemas.body.parse(req.body);
    if (schemas.query) req.query = schemas.query.parse(req.query);
    if (schemas.params) req.params = schemas.params.parse(req.params);
    next();
  } catch (err) {
    if (err instanceof ZodError) {
      const fieldErrors = err.issues.map((issue) => ({
        field: issue.path.join('.') || 'root',
        code: issue.code.toUpperCase(),
        message: issue.message,
      }));
      return next(new AppError('VALIDATION_FAILED', 'Request validation failed', 422, fieldErrors));
    }
    next(err);
  }
};

// --- 4. Fail-Closed Authentication & RBAC ---
export const authenticate = (req, _res, next) => {
  const token = req.cookies?.accessToken || req.header('authorization')?.replace(/^Bearer\s+/i, '');
  if (!token) {
    return next(new AppError('UNAUTHORIZED', 'Authentication required', 401));
  }
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    req.actor = { userId: payload.sub, tenantId: payload.tenantId, role: payload.role };
    next();
  } catch {
    next(new AppError('INVALID_TOKEN', 'Invalid or expired authentication token', 401));
  }
};

export const authorize = (...allowedRoles) => (req, _res, next) => {
  if (!req.actor || !allowedRoles.includes(req.actor.role)) {
    return next(new AppError('FORBIDDEN', 'Insufficient permissions for this operation', 403));
  }
  next();
};

// --- 5. Schemas & Cursor-Paginated / Idempotent Routes ---
const ListItemsQuerySchema = z.object({
  cursor: z.string().trim().max(512).optional(),
  limit: z.coerce.number().int().min(1).max(100).default(25),
  search: z.string().trim().max(120).optional(),
});

const CreateItemBodySchema = z
  .object({
    name: z.string().trim().min(2, 'Name must be at least 2 characters').max(120),
    amountCents: z.number().int().min(0, 'Amount cannot be negative'),
  })
  .strict();

app.get(
  '/api/v1/items',
  readLimiter,
  authenticate,
  validateRequest({ query: ListItemsQuerySchema }),
  async (req, res, next) => {
    try {
      const { cursor, limit, search } = req.query;
      // Query repository with tenantId + keyset cursor (createdAt, id)
      const items = [];
      const hasMore = false;
      const nextCursor = null;

      res.status(200).json({
        data: items,
        meta: {
          requestId: req.id,
          pagination: { limit, nextCursor, hasMore },
          filter: { search: search || null, cursor: cursor || null },
        },
      });
    } catch (error) {
      next(error);
    }
  }
);

app.post(
  '/api/v1/items',
  mutationLimiter,
  authenticate,
  validateRequest({ body: CreateItemBodySchema }),
  async (req, res, next) => {
    try {
      const idempotencyKey = req.header('Idempotency-Key');
      if (!idempotencyKey) {
        throw new AppError('IDEMPOTENCY_KEY_REQUIRED', 'Idempotency-Key header is required for mutations', 400);
      }
      const created = {
        id: `itm_${crypto.randomUUID()}`,
        tenantId: req.actor.tenantId,
        name: req.body.name,
        amountCents: req.body.amountCents,
        createdAt: new Date().toISOString(),
      };
      res.status(201).json({
        data: created,
        meta: { requestId: req.id, idempotentReplay: false },
      });
    } catch (error) {
      next(error);
    }
  }
);

// --- 6. Centralized RFC 9457-Compatible Error Boundary ---
app.use((err, req, res, _next) => {
  const status = err.isOperational ? err.statusCode : 500;
  const code = err.isOperational ? err.code : 'INTERNAL_SERVER_ERROR';
  const title = err.isOperational ? err.message : 'An unexpected server error occurred.';

  res.status(status).json({
    error: {
      code,
      title,
      status,
      requestId: req.id,
      fieldErrors: err.fieldErrors || [],
    },
  });
});

export default app;
