# Web Security Deep Dive

**Load when:** configuring CORS, CSP, CSRF protection, preventing injection attacks, implementing rate limiting, or hardening security headers.

## OWASP Top 10 Quick Reference

| Risk | What It Is | Key Defense |
| --- | --- | --- |
| A01: Broken Access Control | Users act beyond permissions | RBAC middleware, least privilege |
| A02: Cryptographic Failures | Weak encryption, exposed secrets | AES-256, bcrypt, env vars |
| A03: Injection | SQL/NoSQL/Command injection | Parameterized queries, sanitize |
| A04: Insecure Design | Missing threat modeling | Threat model before coding |
| A05: Security Misconfiguration | Default configs, verbose errors | Helmet, disable debug in prod |
| A06: Vulnerable Components | Outdated dependencies | `npm audit`, Dependabot |
| A07: Auth/Identity Failures | Weak passwords, broken sessions | MFA, secure session config |
| A08: Data Integrity Failures | Untrusted deserialization | Validate all inputs, SRI |
| A09: Logging Failures | No security event logging | Log auth events, rate limits |
| A10: SSRF | Server-side request forgery | Allowlist URLs, block internal |

## CORS Configuration

```javascript
import cors from 'cors';

// ❌ BAD: Allow everything
app.use(cors()); // origin: '*', credentials ignored

// ✅ GOOD: Explicit allowlist with credentials
const allowedOrigins = [
  'https://app.example.com',
  'https://admin.example.com',
];

app.use(cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (mobile apps, curl, server-to-server)
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
  exposedHeaders: ['X-Total-Count', 'X-Request-ID'],
  maxAge: 86400, // Preflight cache: 24 hours
}));
```

## Content Security Policy (CSP)

```javascript
import helmet from 'helmet';

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],                          // No inline scripts
      styleSrc: ["'self'", 'https://fonts.googleapis.com'],
      fontSrc: ["'self'", 'https://fonts.gstatic.com'],
      imgSrc: ["'self'", 'data:', 'https:'],          // Allow data URIs for inline images
      connectSrc: ["'self'", 'https://api.example.com'],
      frameSrc: ["'none'"],                            // No iframes
      objectSrc: ["'none'"],                           // No Flash/plugins
      baseUri: ["'self'"],                             // Prevent base tag hijacking
      formAction: ["'self'"],                          // Forms only submit to self
      upgradeInsecureRequests: [],                     // Force HTTPS
    },
  },
  crossOriginEmbedderPolicy: true,
  crossOriginOpenerPolicy: { policy: 'same-origin' },
  crossOriginResourcePolicy: { policy: 'same-origin' },
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
}));
```

## CSRF Protection

```javascript
import csrf from 'csurf';

// Cookie-based CSRF (stateless)
app.use(csrf({
  cookie: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
  }
}));

// Expose token to frontend
app.get('/api/csrf-token', (req, res) => {
  res.json({ csrfToken: req.csrfToken() });
});

// For SPAs: double-submit cookie pattern
// Frontend reads token from cookie, sends in X-CSRF-Token header
```

## Rate Limiting

```javascript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import { createClient } from 'redis';

// General API rate limit
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 100,                    // 100 requests per window
  standardHeaders: true,       // Return RateLimit-* headers
  legacyHeaders: false,
  message: { error: 'Too many requests, try again later' },
  store: new RedisStore({ sendCommand: (...args) => redisClient.sendCommand(args) }),
});

// Strict auth rate limit (brute force protection)
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,                     // Only 5 login attempts per 15 min
  skipSuccessfulRequests: true,
  message: { error: 'Too many login attempts. Try again in 15 minutes.' },
});

app.use('/api/', apiLimiter);
app.use('/api/auth/login', authLimiter);
app.use('/api/auth/register', authLimiter);
```

## Injection Prevention

```javascript
// SQL Injection: ALWAYS use parameterized queries
// ❌ BAD
await db.query(`SELECT * FROM users WHERE email = '${email}'`);
// ✅ GOOD
await db.query('SELECT * FROM users WHERE email = $1', [email]);

// NoSQL Injection: Sanitize MongoDB operators
import mongoSanitize from 'express-mongo-sanitize';
app.use(mongoSanitize()); // Strips $ and . from req.body/query/params

// ❌ BAD: Direct user input in query
const user = await User.findOne({ email: req.body.email });
// If req.body.email = { "$gt": "" } → returns first user!

// ✅ GOOD: Explicit string cast
const user = await User.findOne({ email: String(req.body.email) });

// Command Injection: Never use shell commands with user input
// ❌ BAD
exec(`git log --author="${username}"`);
// ✅ GOOD
execFile('git', ['log', `--author=${username}`]); // No shell interpolation
```

## Security Headers Audit Checklist

| Header | Value | Purpose |
| --- | --- | --- |
| Strict-Transport-Security | `max-age=31536000; includeSubDomains; preload` | Force HTTPS |
| X-Content-Type-Options | `nosniff` | Prevent MIME sniffing |
| X-Frame-Options | `DENY` or `SAMEORIGIN` | Prevent clickjacking |
| X-XSS-Protection | `0` | Disable buggy browser XSS filter |
| Referrer-Policy | `strict-origin-when-cross-origin` | Control referer leaking |
| Permissions-Policy | `camera=(), microphone=(), geolocation=()` | Disable unused browser APIs |
| Content-Security-Policy | See CSP section above | Prevent XSS, injection |

## Password Security

```javascript
import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12; // Minimum 10, prefer 12+

// Hash
const hash = await bcrypt.hash(password, SALT_ROUNDS);

// Compare
const isValid = await bcrypt.compare(inputPassword, storedHash);

// Password policy
const passwordPolicy = {
  minLength: 12,
  requireUppercase: true,
  requireLowercase: true,
  requireNumber: true,
  requireSpecial: true,
  maxLength: 128,        // Prevent bcrypt DoS (72 byte limit anyway)
  rejectCommon: true,    // Check against breached password lists
};
```

## Anti-Patterns

| Anti-Pattern | Risk | Fix |
| --- | --- | --- |
| `cors({ origin: '*' })` with credentials | Credential theft | Explicit origin allowlist |
| Secrets in code/git | Leaked API keys | `.env` + `.gitignore` |
| Error stack in production response | Info disclosure | Generic error messages |
| No rate limiting on auth | Brute force attacks | 5 attempts / 15 min |
| `eval()` with user input | Remote code execution | Never use eval |
| JWT with no expiry | Permanent session hijack | Short expiry + refresh token |
| HTTP in production | Man-in-the-middle | Force HTTPS + HSTS |
