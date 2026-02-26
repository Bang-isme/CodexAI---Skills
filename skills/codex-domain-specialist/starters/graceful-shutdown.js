// ============================================
// GRACEFUL SHUTDOWN STARTER
// ============================================

const gracefulShutdown = (server, { mongoose, sequelize, redis, io, queues = [] }) => {
  let isShuttingDown = false;

  const shutdown = async (signal) => {
    if (isShuttingDown) return;
    isShuttingDown = true;
    console.log(`\n${signal} received. Starting graceful shutdown...`);

    server.close(() => console.log('HTTP server closed'));

    if (io) {
      io.close(() => console.log('WebSocket server closed'));
    }

    const timeout = setTimeout(() => {
      console.error('Forced shutdown after 30s timeout');
      process.exit(1);
    }, 30000);

    try {
      for (const queue of queues) {
        await queue.close();
        console.log(`Queue "${queue.name}" closed`);
      }

      if (mongoose) {
        await mongoose.disconnect();
        console.log('MongoDB disconnected');
      }

      if (sequelize) {
        await sequelize.close();
        console.log('SQL disconnected');
      }

      if (redis) {
        await redis.quit();
        console.log('Redis disconnected');
      }

      clearTimeout(timeout);
      console.log('Graceful shutdown complete');
      process.exit(0);
    } catch (err) {
      console.error('Error during shutdown:', err);
      clearTimeout(timeout);
      process.exit(1);
    }
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));

  process.on('unhandledRejection', (reason) => {
    console.error('UNHANDLED REJECTION:', reason);
    shutdown('unhandledRejection');
  });

  process.on('uncaughtException', (err) => {
    console.error('UNCAUGHT EXCEPTION:', err);
    shutdown('uncaughtException');
  });
};

export default gracefulShutdown;

// Usage:
// const server = app.listen(PORT);
// gracefulShutdown(server, { mongoose, redis, io, queues: [emailQueue, reportQueue] });
