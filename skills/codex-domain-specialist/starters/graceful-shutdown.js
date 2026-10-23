// ============================================
// GRACEFUL SHUTDOWN STARTER — Drain Readiness First, Then Await Server & Pools
// ============================================
import { setShutdownDraining } from './health-check.js';

export const gracefulShutdown = (server, { closeDatabase, closeCache, queues = [], drainDelayMs = 2000 } = {}) => {
  let isShuttingDown = false;

  const shutdown = async (signal) => {
    if (isShuttingDown) return;
    isShuttingDown = true;

    // 1. Flip readiness flag so load balancer stops routing new requests
    setShutdownDraining(true);

    const forceExitTimer = setTimeout(() => {
      process.exit(1);
    }, 25000);
    forceExitTimer.unref?.();

    try {
      // Allow load balancer health probe interval to observe 503 draining state
      if (drainDelayMs > 0) {
        await new Promise((resolve) => setTimeout(resolve, drainDelayMs));
      }

      // 2. Stop accepting new HTTP connections and await in-flight requests
      await new Promise((resolve, reject) => {
        server.close((err) => (err ? reject(err) : resolve()));
      });

      // 3. Drain background queues before closing persistence pools
      for (const queue of queues) {
        if (typeof queue?.close === 'function') {
          await queue.close();
        }
      }

      // 4. Close database and cache pools cleanly
      if (typeof closeDatabase === 'function') {
        await closeDatabase();
      }
      if (typeof closeCache === 'function') {
        await closeCache();
      }

      clearTimeout(forceExitTimer);
      process.exit(0);
    } catch {
      clearTimeout(forceExitTimer);
      process.exit(1);
    }
  };

  process.on('SIGTERM', () => void shutdown('SIGTERM'));
  process.on('SIGINT', () => void shutdown('SIGINT'));
};

export default gracefulShutdown;
