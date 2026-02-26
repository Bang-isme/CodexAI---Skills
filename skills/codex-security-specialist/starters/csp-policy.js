// ============================================
// CONTENT SECURITY POLICY BUILDER - Express
// ============================================

/**
 * CSP helps block XSS, clickjacking, and script injection.
 * Recommended rollout:
 * 1) Start in report-only mode
 * 2) Observe violations
 * 3) Tighten policy
 * 4) Enforce
 */

const buildCSP = (env = "production", enabledSources = ["fonts"]) => {
  const isProd = env === "production";

  const policy = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "https:"],
    "font-src": ["'self'", "https://fonts.gstatic.com"],
    "connect-src": ["'self'"],
    "frame-src": ["'none'"],
    "frame-ancestors": ["'none'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "upgrade-insecure-requests": [],
  };

  if (!isProd) {
    policy["script-src"].push("'unsafe-eval'");
    policy["connect-src"].push("ws://localhost:*");
    delete policy["upgrade-insecure-requests"];
  }

  const trustedSources = {
    fonts: {
      "style-src": ["https://fonts.googleapis.com"],
      "font-src": ["https://fonts.gstatic.com"],
    },
    analytics: {
      "script-src": [
        "https://www.googletagmanager.com",
        "https://www.google-analytics.com",
      ],
      "connect-src": ["https://www.google-analytics.com"],
      "img-src": ["https://www.google-analytics.com"],
    },
    stripe: {
      "script-src": ["https://js.stripe.com"],
      "frame-src": ["https://js.stripe.com", "https://hooks.stripe.com"],
      "connect-src": ["https://api.stripe.com"],
    },
    cdn: {
      "script-src": ["https://cdn.jsdelivr.net", "https://unpkg.com"],
      "style-src": ["https://cdn.jsdelivr.net"],
    },
  };

  enabledSources.forEach((name) => {
    const source = trustedSources[name];
    if (!source) return;
    Object.entries(source).forEach(([directive, values]) => {
      policy[directive] = [...(policy[directive] || []), ...values];
    });
  });

  return policy;
};

const policyToString = (policy) =>
  Object.entries(policy)
    .map(([directive, values]) =>
      values.length ? `${directive} ${values.join(" ")}` : directive
    )
    .join("; ");

const cspMiddleware = (options = {}) => {
  const {
    reportOnly = false,
    env = process.env.NODE_ENV || "production",
    enabledSources = ["fonts"],
  } = options;

  const policy = buildCSP(env, enabledSources);
  const headerName = reportOnly
    ? "Content-Security-Policy-Report-Only"
    : "Content-Security-Policy";
  const headerValue = policyToString(policy);

  return (req, res, next) => {
    res.setHeader(headerName, headerValue);
    next();
  };
};

export { buildCSP, policyToString, cspMiddleware };
export default cspMiddleware;

// Usage:
// import cspMiddleware from "./csp-policy.js";
// app.use(cspMiddleware({ reportOnly: true, enabledSources: ["fonts", "analytics"] }));
// app.use(cspMiddleware({ reportOnly: false, enabledSources: ["fonts"] }));

/**
 * Validate CSP:
 * - Browser console: CSP violation reports
 * - https://csp-evaluator.withgoogle.com/
 * - Optional report endpoint:
 *   'report-uri': ['/api/csp-report']
 */
