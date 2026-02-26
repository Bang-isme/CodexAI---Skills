# OWASP Top 10 — Deep Dive

## A01: Broken Access Control (most critical)

### Attack
```
User A authenticated → changes URL from /api/users/123 to /api/users/456
→ Sees User B's data (IDOR — Insecure Direct Object Reference)
```

### Vulnerable Code
```javascript
// ❌ BAD — no ownership check
router.get('/api/orders/:id', authenticate, async (req, res) => {
  const order = await Order.findById(req.params.id);  // Any user can access any order
  res.json(order);
});
```

### Fixed Code
```javascript
// ✅ GOOD — ownership verified
router.get('/api/orders/:id', authenticate, async (req, res) => {
  const order = await Order.findOne({ _id: req.params.id, userId: req.user.id });
  if (!order) return res.status(404).json({ error: 'Not found' });
  res.json(order);
});

// ✅ BETTER — middleware for all resource routes
const ownershipCheck = (model, idField = '_id', userField = 'userId') => async (req, res, next) => {
  const item = await model.findOne({ [idField]: req.params.id, [userField]: req.user.id });
  if (!item) return res.status(404).json({ error: 'Not found' });
  req.resource = item;
  next();
};
```

### Prevention Checklist
- [ ] Every data endpoint verifies ownership or role
- [ ] Admin routes use role middleware (`authorize('admin')`)
- [ ] URL path IDs cannot be guessed (use UUID, not sequential)
- [ ] CORS restricts origins
- [ ] JWT token validated on every request

## A02: Cryptographic Failures

### Common Mistakes
```
❌ MD5 or SHA1 for passwords → use bcrypt/argon2
❌ HTTP for sensitive data → enforce HTTPS everywhere
❌ Storing credit cards → use tokenization (Stripe)
❌ Hardcoded encryption keys → use Vault/KMS
❌ Base64 "encryption" → Base64 is encoding, NOT encryption
```

### Correct Password Hashing
```javascript
import bcrypt from 'bcryptjs';

// Hash (signup)
const hash = await bcrypt.hash(password, 12);  // cost factor 12

// Verify (login)
const match = await bcrypt.compare(inputPassword, storedHash);

// NEVER: MD5, SHA1, SHA256 for passwords (too fast → brute-forceable)
// NEVER: encrypt passwords (use one-way hash, not reversible encryption)
```

## A03: Injection

### SQL Injection
```javascript
// ❌ VULNERABLE
db.query(`SELECT * FROM users WHERE email = '${req.body.email}'`);
// Attack: email = "' OR 1=1; DROP TABLE users; --"

// ✅ PARAMETERIZED
db.query('SELECT * FROM users WHERE email = $1', [req.body.email]);
```

### NoSQL Injection
```javascript
// ❌ VULNERABLE — req.body could contain { password: { $gt: "" } }
User.findOne({ email: req.body.email, password: req.body.password });

// ✅ SAFE — explicit type casting
User.findOne({ email: String(req.body.email) });

// ✅ SAFE — use express-mongo-sanitize
app.use(mongoSanitize()); // strips $ operators from input
```

### Command Injection
```javascript
// ❌ VULNERABLE
exec(`ping ${req.query.host}`);
// Attack: host = "google.com; rm -rf /"

// ✅ SAFE — use execFile with explicit args
execFile('ping', ['-c', '4', req.query.host]);

// ✅ BETTER — validate input format
if (!/^[a-zA-Z0-9.-]+$/.test(req.query.host)) throw BadRequest('Invalid host');
```

## A04: Insecure Design

### Patterns to Implement
- Threat modeling BEFORE coding (not after)
- Rate limiting on all sensitive operations
- Account lockout after N failed attempts
- CAPTCHA on public forms
- Separation of duties (user can't approve own request)

## A05: Security Misconfiguration

### Common Misconfigs
```
❌ Default credentials on databases/services
❌ Stack traces in production error responses
❌ Directory listing enabled on web server
❌ Unnecessary services/ports exposed
❌ Debug mode in production (NODE_ENV=development)
❌ CORS: origin = "*" with credentials
❌ Missing security headers
```

## A06: Vulnerable and Outdated Components

```bash
# Check npm dependencies for vulnerabilities
npm audit
npm audit fix

# Use Snyk for deeper analysis
npx snyk test

# Automated: Dependabot / Renovate Bot
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 10
```

## A07: Identification and Authentication Failures

### Secure Auth Checklist
- [ ] Passwords hashed with bcrypt/argon2 (cost ≥ 12)
- [ ] Account lockout after 5 failed attempts (15 min cooldown)
- [ ] Session timeout ≤ 30 min idle
- [ ] MFA available for sensitive accounts
- [ ] Password reset tokens single-use + expire in 1 hour
- [ ] No default/hardcoded credentials
- [ ] Rate limit login endpoint (5/min)

## A08: Software and Data Integrity Failures

### Subresource Integrity (SRI)
```html
<!-- Verify CDN scripts haven't been tampered with -->
<script src="https://cdn.example.com/lib.js"
  integrity="sha384-abc123..."
  crossorigin="anonymous"></script>
```

## A09: Security Logging and Monitoring Failures
→ See `siem-log-analysis.md`

## A10: Server-Side Request Forgery (SSRF)

```javascript
// ❌ VULNERABLE — user controls URL
const response = await fetch(req.body.url);
// Attack: url = "http://169.254.169.254/latest/meta-data/" (AWS metadata)

// ✅ SAFE — whitelist allowed domains
const ALLOWED_HOSTS = ['api.example.com', 'cdn.example.com'];
const url = new URL(req.body.url);
if (!ALLOWED_HOSTS.includes(url.hostname)) throw Forbidden('Domain not allowed');

// ✅ SAFE — block internal IPs
const isInternalIP = (ip) => /^(10\.|172\.(1[6-9]|2|3[01])\.|192\.168\.|127\.|169\.254\.)/.test(ip);
```
