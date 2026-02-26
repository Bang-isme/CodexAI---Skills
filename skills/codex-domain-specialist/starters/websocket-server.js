// ============================================
// WEBSOCKET SERVER STARTER - Socket.IO
// ============================================
import { Server } from 'socket.io';

const initializeWebSocket = (httpServer) => {
  const io = new Server(httpServer, {
    cors: { origin: process.env.CORS_ORIGIN || '*', credentials: true },
    pingTimeout: 60000,
    pingInterval: 25000,
  });

  io.use(async (socket, next) => {
    try {
      const token = socket.handshake.auth.token;
      if (!token) return next(new Error('Authentication required'));
      // const user = jwt.verify(token, JWT_SECRET);
      // socket.user = user;
      return next();
    } catch (err) {
      return next(new Error('Invalid token'));
    }
  });

  io.on('connection', (socket) => {
    console.log(`Connected: ${socket.id} (user: ${socket.user?.id})`);

    socket.join(`user:${socket.user?.id}`);
    if (socket.user?.role === 'admin') socket.join('admins');

    socket.on('join:room', (roomId) => {
      socket.join(roomId);
      socket.to(roomId).emit('user:joined', { userId: socket.user?.id });
    });

    socket.on('leave:room', (roomId) => {
      socket.leave(roomId);
      socket.to(roomId).emit('user:left', { userId: socket.user?.id });
    });

    socket.on('message:send', async (data, callback) => {
      try {
        // const message = await MessageService.create(data);
        io.to(data.roomId).emit('message:received', {});
        callback({ success: true });
      } catch (err) {
        callback({ success: false, error: err.message });
      }
    });

    socket.on('typing:start', (roomId) => {
      socket.to(roomId).emit('typing:update', { userId: socket.user?.id, typing: true });
    });

    socket.on('typing:stop', (roomId) => {
      socket.to(roomId).emit('typing:update', { userId: socket.user?.id, typing: false });
    });

    socket.on('disconnect', (reason) => {
      console.log(`Disconnected: ${socket.id} (${reason})`);
    });

    socket.on('error', (err) => {
      console.error(`Socket error: ${socket.id}`, err);
    });
  });

  return io;
};

export default initializeWebSocket;

// Client sample:
// const socket = io(WS_URL, { auth: { token }, reconnection: true, reconnectionDelay: 1000 });
