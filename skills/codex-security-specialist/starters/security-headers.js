// ============================================
// SECURITY HEADERS STARTER — Comprehensive Express Setup
// ============================================
import helmet from 'helmet';

const configureSecurityHeaders = (app) => {
  // Helmet: sets 11+ security headers
  app.use(helmet({
    // Content Security Policy
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
        imgSrc: ["'self'", 'data:', 'https:'],
        fontSrc: ["'self'", 'https://fonts.gstatic.com'],
        connectSrc: ["'self'", process.env.API_URL || ''],
        frameSrc: ["'none'"],
        objectSrc: ["'none'"],
        baseUri: ["'self'"],
        formAction: ["'self'"],
        upgradeInsecureRequests: [],
      },
    },
    // Strict Transport Security
    hsts: {
      maxAge: 63072000,         // 2 years
      includeSubDomains: true,
      preload: true,
    },
    // Prevent clickjacking
    frameguard: { action: 'deny' },
    // Prevent MIME sniffing
    noSniff: true,
    // Referrer Policy
    referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
    // Permissions Policy
    permittedCrossDomainPolicies: { permittedPolicies: 'none' },
  }));

  // Additional headers not covered by Helmet
  app.use((req, res, next) => {
    // Permissions Policy (replaces Feature-Policy)
    res.setHeader('Permissions-Policy',
      'camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=()');

    // Prevent caching of sensitive responses
    if (req.path.startsWith('/api/auth') || req.path.startsWith('/api/user')) {
      res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, private');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
    }

    // Remove server identification
    res.removeHeader('X-Powered-By');

    next();
  });
};

export default configureSecurityHeaders;

// Usage:
// import configureSecurityHeaders from './security-headers.js';
// configureSecurityHeaders(app);

/**
 * HEADERS SET:
 * ✅ Content-Security-Policy    — prevent XSS, injection
 * ✅ Strict-Transport-Security  — force HTTPS
 * ✅ X-Frame-Options            — prevent clickjacking
 * ✅ X-Content-Type-Options     — prevent MIME sniffing
 * ✅ Referrer-Policy            — control referer header
 * ✅ Permissions-Policy         — restrict browser features
 * ✅ X-DNS-Prefetch-Control     — control DNS prefetching
 * ✅ Cache-Control              — prevent caching sensitive data
 * ❌ X-Powered-By               — removed (information leak)
 *
 * TEST: https://securityheaders.com/?q=your-site.com
 * TARGET: Grade A+ on securityheaders.com
 */
