# API Security Advanced

## Beyond basic auth — deep API protection patterns.

## API Authentication Layers

```
Layer 1: TLS (encryption in transit)          — mandatory
Layer 2: API Key (identify client)            — for service-to-service
Layer 3: JWT/OAuth (authenticate user)        — for user-facing APIs
Layer 4: RBAC/ABAC (authorize action)         — per-endpoint
Layer 5: Rate Limiting (abuse prevention)     — per-user, per-endpoint
Layer 6: Input Validation (injection defense) — every input
Layer 7: Output Filtering (data leak prevention) — every response
```

## API Key Management

```javascript
// API keys for service-to-service (NOT user auth)
const apiKeyMiddleware = (req, res, next) => {
  const key = req.headers['x-api-key'];
  if (!key) return res.status(401).json({ error: 'API key required' });

  const client = apiKeys.get(key); // from encrypted store
  if (!client) return res.status(403).json({ error: 'Invalid API key' });

  req.apiClient = client; // attach client metadata
  next();
};

// API key properties
// - Prefix for identification: pk_live_xxx, sk_test_xxx
// - Scoped permissions: read-only, read-write, admin
// - Expiration date
// - Rate limit tier
```

## Request Signing (Webhook Verification)

```javascript
import crypto from 'crypto';

// Sender: sign payload
const signPayload = (payload, secret) => {
  const timestamp = Math.floor(Date.now() / 1000);
  const signatureBase = `${timestamp}.${JSON.stringify(payload)}`;
  const signature = crypto.createHmac('sha256', secret)
    .update(signatureBase).digest('hex');
  return { signature: `v1=${signature}`, timestamp };
};

// Receiver: verify signature
const verifyWebhook = (req, secret) => {
  const signature = req.headers['x-webhook-signature'];
  const timestamp = parseInt(req.headers['x-webhook-timestamp']);

  // Prevent replay attacks: reject if timestamp > 5 min old
  if (Math.abs(Date.now() / 1000 - timestamp) > 300) return false;

  const expected = crypto.createHmac('sha256', secret)
    .update(`${timestamp}.${req.rawBody}`).digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature.replace('v1=', '')),
    Buffer.from(expected)
  );
};
```

## Rate Limiting Tiers

```javascript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';

const createLimiter = (windowMs, max, keyPrefix) => rateLimit({
  windowMs, max,
  keyGenerator: (req) => req.user?.id || req.ip,
  store: new RedisStore({ sendCommand: (...args) => redis.sendCommand(args) }),
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => res.status(429).json({
    error: 'Too many requests',
    retryAfter: Math.ceil(windowMs / 1000),
  }),
});

// Tier-based limiters
const tiers = {
  public:     createLimiter(15 * 60 * 1000, 100, 'pub'),    // 100 req/15min
  authenticated: createLimiter(15 * 60 * 1000, 500, 'auth'), // 500 req/15min
  premium:    createLimiter(15 * 60 * 1000, 2000, 'prem'),   // 2000 req/15min
  auth:       createLimiter(60 * 1000, 5, 'login'),           // 5 req/min (login)
  sensitive:  createLimiter(60 * 60 * 1000, 10, 'sens'),      // 10 req/hour (password reset)
};
```

## Output Filtering (Prevent Data Leaks)

```javascript
// NEVER return raw database objects
// Always use a serializer/presenter

const userPresenter = (user, isAdmin = false) => ({
  id: user._id,
  firstName: user.firstName,
  lastName: user.lastName,
  email: user.email,
  role: user.role,
  createdAt: user.createdAt,
  // Admin-only fields
  ...(isAdmin && {
    lastLogin: user.lastLogin,
    loginAttempts: user.loginAttempts,
    isLocked: user.isLocked,
  }),
  // NEVER include: password, tokens, internal IDs, api keys
});

// Middleware: strip sensitive fields from error responses
const sanitizeError = (err, req, res, next) => {
  const response = {
    success: false,
    message: err.isOperational ? err.message : 'Internal server error',
    code: err.code || 'INTERNAL_ERROR',
  };
  // NEVER expose: stack trace, DB query, internal paths in production
  if (process.env.NODE_ENV === 'development') {
    response.stack = err.stack;
  }
  res.status(err.statusCode || 500).json(response);
};
```

## API Security Checklist
- [ ] All endpoints require authentication (except health + public routes)
- [ ] RBAC/ABAC enforced per endpoint
- [ ] Rate limiting on all endpoints (stricter for auth routes)
- [ ] Input validated and sanitized at boundary
- [ ] Output filtered through presenters (no raw DB objects)
- [ ] Error responses don't leak internal details in production
- [ ] Webhook signatures verified with timing-safe comparison
- [ ] API keys scoped and rotatable
- [ ] CORS configured for specific origins (not *)
- [ ] Request body size limited
