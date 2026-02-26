// ============================================
// ADVANCED RATE LIMITER - Redis + Express
// Sliding window and token bucket implementations.
// ============================================

import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379");

const getClientIp = (req) =>
  (req.headers["x-forwarded-for"] || "").split(",")[0].trim() || req.ip || "unknown";

const getIdentityKey = (req) => req.user?.id || req.apiKey?.id || getClientIp(req);

const sendLimitHeaders = (res, { limit, remaining, resetEpochSec }) => {
  res.setHeader("X-RateLimit-Limit", String(limit));
  res.setHeader("X-RateLimit-Remaining", String(Math.max(remaining, 0)));
  res.setHeader("X-RateLimit-Reset", String(resetEpochSec));
};

const tooMany = (res, message, retryAfterSec) =>
  res.status(429).json({
    success: false,
    code: "RATE_LIMITED",
    message,
    retryAfterSec,
  });

// Sliding window using sorted set timestamps
const slidingWindowLimiter = ({
  windowMs,
  max,
  keyPrefix = "rl",
  keyFn = getIdentityKey,
  message = "Too many requests",
} = {}) => {
  if (!windowMs || !max) throw new Error("windowMs and max are required");

  return async (req, res, next) => {
    try {
      const key = `${keyPrefix}:${keyFn(req)}`;
      const now = Date.now();
      const windowStart = now - windowMs;
      const member = `${now}:${Math.random().toString(36).slice(2, 10)}`;

      const pipeline = redis.pipeline();
      pipeline.zremrangebyscore(key, 0, windowStart);
      pipeline.zadd(key, now, member);
      pipeline.zcard(key);
      pipeline.pexpire(key, windowMs);
      const results = await pipeline.exec();
      const count = Number(results?.[2]?.[1] || 0);

      const remaining = max - count;
      const resetEpochSec = Math.ceil((now + windowMs) / 1000);
      sendLimitHeaders(res, { limit: max, remaining, resetEpochSec });

      if (count > max) {
        const retryAfterSec = Math.ceil(windowMs / 1000);
        res.setHeader("Retry-After", String(retryAfterSec));
        return tooMany(res, message, retryAfterSec);
      }

      return next();
    } catch (error) {
      // Fail-open for availability, but log aggressively in real implementation.
      return next();
    }
  };
};

// Token bucket using Redis hash
const tokenBucketLimiter = ({
  tokensPerInterval = 10,
  interval = 1000,
  maxBurst = 100,
  keyPrefix = "tb",
  keyFn = getIdentityKey,
  message = "Rate limit exceeded",
} = {}) => {
  return async (req, res, next) => {
    try {
      const key = `${keyPrefix}:${keyFn(req)}`;
      const now = Date.now();
      const ratePerMs = tokensPerInterval / interval;
      const ttlMs = Math.max(interval * 2, 60_000);

      const data = await redis.hgetall(key);
      let tokens = data.tokens !== undefined ? Number(data.tokens) : maxBurst;
      let last = data.last !== undefined ? Number(data.last) : now;
      if (!Number.isFinite(tokens)) tokens = maxBurst;
      if (!Number.isFinite(last)) last = now;

      const elapsed = Math.max(0, now - last);
      const replenished = elapsed * ratePerMs;
      tokens = Math.min(maxBurst, tokens + replenished);

      if (tokens < 1) {
        const retryAfterSec = Math.ceil((1 - tokens) / ratePerMs / 1000);
        res.setHeader("Retry-After", String(Math.max(1, retryAfterSec)));
        sendLimitHeaders(res, {
          limit: maxBurst,
          remaining: 0,
          resetEpochSec: Math.ceil((now + retryAfterSec * 1000) / 1000),
        });
        return tooMany(res, message, Math.max(1, retryAfterSec));
      }

      tokens -= 1;
      await redis
        .multi()
        .hset(key, "tokens", tokens.toFixed(6), "last", now)
        .pexpire(key, ttlMs)
        .exec();

      sendLimitHeaders(res, {
        limit: maxBurst,
        remaining: Math.floor(tokens),
        resetEpochSec: Math.ceil((now + interval) / 1000),
      });
      return next();
    } catch (error) {
      return next();
    }
  };
};

const limiters = {
  // General API
  api: slidingWindowLimiter({ windowMs: 60_000, max: 120, keyPrefix: "rl:api" }),

  // Authentication endpoints
  auth: slidingWindowLimiter({
    windowMs: 15 * 60_000,
    max: 20,
    keyPrefix: "rl:auth",
    message: "Too many authentication attempts",
  }),

  // Search endpoints
  search: slidingWindowLimiter({
    windowMs: 60_000,
    max: 60,
    keyPrefix: "rl:search",
  }),

  // Export endpoints
  export: slidingWindowLimiter({
    windowMs: 3_600_000,
    max: 5,
    keyPrefix: "rl:export",
    message: "Export quota exceeded",
  }),

  // Upload endpoints
  upload: slidingWindowLimiter({
    windowMs: 3_600_000,
    max: 10,
    keyPrefix: "rl:upload",
    message: "Upload quota exceeded",
  }),

  // Burst-friendly for chat/realtime use cases
  burst: tokenBucketLimiter({
    tokensPerInterval: 10,
    interval: 1000,
    maxBurst: 100,
    keyPrefix: "tb:burst",
  }),
};

export { slidingWindowLimiter, tokenBucketLimiter, limiters };
export default limiters;

// Usage:
// import limiters from "./rate-limiter-advanced.js";
// app.use("/api/", limiters.api);
// app.use("/api/auth/", limiters.auth);
// app.use("/api/search", limiters.search);
// app.use("/api/export", limiters.export);
