// ============================================
// HEALTH CHECK STARTER — Separate Liveness (/health/live) vs Readiness (/health/ready)
// ============================================
let isDraining = false;

export const setShutdownDraining = (draining) => {
  isDraining = Boolean(draining);
};

export const isShutdownDraining = () => isDraining;

// Liveness Probe: Checks process event-loop responsiveness ONLY.
// Never check external DB/APIs here, or a brief DB blip will trigger cascading container restarts.
export const livenessCheck = (_req, res) => {
  res.status(200).json({
    status: 'alive',
    uptimeSeconds: Math.floor(process.uptime()),
  });
};

// Readiness Probe: Checks shutdown drain flag + bounded dependency ping (1500ms timeout).
export const createReadinessCheck = ({ pingDatabase, pingCache } = {}) => async (_req, res) => {
  if (isDraining) {
    return res.status(503).json({
      status: 'draining',
      ready: false,
    });
  }

  const withTimeout = (promise, ms = 1500) =>
    Promise.race([
      promise,
      new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms)),
    ]);

  const checks = {};
  let ready = true;

  if (typeof pingDatabase === 'function') {
    try {
      await withTimeout(pingDatabase(), 1500);
      checks.database = 'healthy';
    } catch {
      checks.database = 'unhealthy';
      ready = false;
    }
  }

  if (typeof pingCache === 'function') {
    try {
      await withTimeout(pingCache(), 1500);
      checks.cache = 'healthy';
    } catch {
      checks.cache = 'unhealthy';
      ready = false;
    }
  }

  return res.status(ready ? 200 : 503).json({
    status: ready ? 'ready' : 'not_ready',
    ready,
    checks,
  });
};
