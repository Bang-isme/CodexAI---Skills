// ============================================
// ENV CONFIG STARTER - Fail Fast, Validate Early
// ============================================

/**
 * Load and validate environment variables at startup.
 * If any required variable is missing -> crash immediately with clear error.
 * Never use process.env directly in business code - import from this module.
 */
function required(key, fallback = undefined) {
  const value = process.env[key] || fallback;
  if (value === undefined || value === '') {
    console.error(`\nFATAL: Missing required env variable: ${key}`);
    console.error('Set it in .env or environment before starting.\n');
    process.exit(1);
  }
  return value;
}

function optional(key, fallback = '') {
  return process.env[key] || fallback;
}

function int(key, fallback) {
  const raw = process.env[key];
  if (raw === undefined && fallback !== undefined) {
    return fallback;
  }
  const parsed = parseInt(raw, 10);
  if (Number.isNaN(parsed)) {
    console.error(`\nFATAL: Env variable ${key} must be integer, got: "${raw}"\n`);
    process.exit(1);
  }
  return parsed;
}

function bool(key, fallback = false) {
  const raw = process.env[key];
  if (raw === undefined) {
    return fallback;
  }
  return ['true', '1', 'yes'].includes(raw.toLowerCase());
}

// --- Export validated config object ---
export const config = {
  // Server
  port: int('PORT', 3000),
  nodeEnv: optional('NODE_ENV', 'development'),
  isDev: optional('NODE_ENV', 'development') === 'development',
  isProd: optional('NODE_ENV', 'development') === 'production',

  // Databases
  mongoUri: required('MONGO_URI'),
  pgUri: required('PG_URI'),
  redisUrl: optional('REDIS_URL', 'redis://localhost:6379'),

  // Auth
  jwtSecret: required('JWT_SECRET'),
  jwtRefreshSecret: required('JWT_REFRESH_SECRET'),
  jwtAccessTtl: optional('JWT_ACCESS_TTL', '15m'),
  jwtRefreshTtl: optional('JWT_REFRESH_TTL', '7d'),
  bcryptRounds: int('BCRYPT_ROUNDS', 12),

  // CORS
  corsOrigin: optional('CORS_ORIGIN', '*'),

  // Rate Limiting
  rateLimitWindow: int('RATE_LIMIT_WINDOW_MS', 15 * 60 * 1000),
  rateLimitMax: int('RATE_LIMIT_MAX', 100),

  // Logging
  logLevel: optional('LOG_LEVEL', 'info'),

  // External Services (optional)
  smtpHost: optional('SMTP_HOST'),
  smtpPort: int('SMTP_PORT', 587),
  smtpUser: optional('SMTP_USER'),
  smtpPass: optional('SMTP_PASS'),
  sentryDsn: optional('SENTRY_DSN'),
};

// --- Startup validation log ---
if (config.isDev) {
  const masked = (v) => (v ? `${v.slice(0, 4)}****` : '(not set)');
  console.log('Config loaded:');
  console.log(`PORT=${config.port} | ENV=${config.nodeEnv}`);
  console.log(`MONGO=${masked(config.mongoUri)} | PG=${masked(config.pgUri)}`);
  console.log(`JWT=${masked(config.jwtSecret)} | CORS=${config.corsOrigin}`);
}

/**
 * RULES:
 * 1. NEVER use process.env.X directly in any other file
 * 2. Import { config } from './config.js' everywhere
 * 3. All required vars crash at startup if missing
 * 4. Sensitive values are never logged (only first 4 chars)
 * 5. Keep .env.example in repo with all keys (no values)
 */
