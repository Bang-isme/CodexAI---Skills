// ============================================
// HEALTH CHECK STARTER - K8s/Docker Ready
// ============================================
import os from 'os';
import mongoose from 'mongoose';

const checkMongo = async () => {
  try {
    const state = mongoose.connection.readyState;
    if (state !== 1) return { status: 'unhealthy', message: `State: ${state}` };
    await mongoose.connection.db.admin().ping();
    return { status: 'healthy' };
  } catch (err) {
    return { status: 'unhealthy', message: err.message };
  }
};

const checkRedis = async (redisClient) => {
  try {
    const pong = await redisClient.ping();
    return { status: pong === 'PONG' ? 'healthy' : 'unhealthy' };
  } catch (err) {
    return { status: 'unhealthy', message: err.message };
  }
};

const checkSequelize = async (sequelize) => {
  try {
    await sequelize.authenticate();
    return { status: 'healthy' };
  } catch (err) {
    return { status: 'unhealthy', message: err.message };
  }
};

const checkMemory = () => {
  try {
    const free = os.freemem();
    const total = os.totalmem();
    const usagePercent = ((total - free) / total) * 100;
    return {
      status: usagePercent < 90 ? 'healthy' : 'warning',
      memoryUsage: `${usagePercent.toFixed(1)}%`,
    };
  } catch {
    return { status: 'unknown' };
  }
};

const healthCheck = async (req, res) => {
  const startTime = Date.now();

  const checks = await Promise.allSettled([
    checkMongo(),
    // checkRedis(req.app.get('redis')),
    // checkSequelize(req.app.get('sequelize')),
  ]);

  const results = {
    mongo: checks[0]?.value || { status: 'error' },
    // redis: checks[1]?.value || { status: 'error' },
    // sql: checks[2]?.value || { status: 'error' },
    memory: checkMemory(),
  };

  const allHealthy = Object.values(results).every((r) => r.status === 'healthy');

  res.status(allHealthy ? 200 : 503).json({
    status: allHealthy ? 'healthy' : 'degraded',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    responseTime: `${Date.now() - startTime}ms`,
    version: process.env.APP_VERSION || '1.0.0',
    checks: results,
  });
};

const livenessCheck = (req, res) => res.status(200).json({ status: 'alive' });
const readinessCheck = healthCheck;

export { healthCheck, livenessCheck, readinessCheck };

// app.get('/health', healthCheck);
// app.get('/health/live', livenessCheck);
// app.get('/health/ready', readinessCheck);
