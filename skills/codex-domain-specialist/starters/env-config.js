// ============================================
// ENV CONFIG STARTER — Fail-Fast Zod Schema Validation
// Zero Secret-Prefix Logging + Unified Env Key Names
// ============================================
import { z } from 'zod';

const EnvSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  DATABASE_URL: z.string().url('DATABASE_URL must be a valid connection URL'),
  REDIS_URL: z.string().url().optional(),
  JWT_SECRET: z.string().min(32, 'JWT_SECRET must be at least 32 characters'),
  JWT_REFRESH_SECRET: z.string().min(32, 'JWT_REFRESH_SECRET must be at least 32 characters'),
  JWT_ACCESS_TTL: z.string().default('15m'),
  JWT_REFRESH_TTL: z.string().default('7d'),
  CORS_ORIGIN: z.string().min(1, 'CORS_ORIGIN must be explicitly configured'),
  LOG_LEVEL: z.enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace']).default('info'),
});

export function loadEnvConfig(rawEnv = process.env) {
  const parsed = EnvSchema.safeParse(rawEnv);
  if (!parsed.success) {
    const missing = parsed.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join('; ');
    throw new Error(`Invalid environment configuration: ${missing}`);
  }
  return parsed.data;
}
