// ============================================
// WEBSOCKET SERVER STARTER — Verified JWT Auth + Room Authorization + Structured Errors
// ============================================
import { Server } from 'socket.io';
import jwt from 'jsonwebtoken';

export const initializeWebSocket = (httpServer, { verifyRoomMembership } = {}) => {
  const allowedOrigins = process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : [];
  const io = new Server(httpServer, {
    cors: {
      origin: allowedOrigins.length > 0 ? allowedOrigins : false,
      credentials: true,
    },
    pingTimeout: 60000,
    pingInterval: 25000,
  });

  // Fail-closed JWT handshake verification
  io.use((socket, next) => {
    const token = socket.handshake.auth?.token;
    if (!token || typeof token !== 'string') {
      return next(new Error('UNAUTHORIZED: Authentication token required'));
    }
    try {
      const payload = jwt.verify(token, process.env.JWT_SECRET);
      socket.actor = {
        userId: String(payload.sub),
        tenantId: String(payload.tenantId),
        role: String(payload.role || 'user'),
      };
      return next();
    } catch {
      return next(new Error('INVALID_TOKEN: Token verification failed'));
    }
  });

  io.on('connection', (socket) => {
    const { userId, tenantId, role } = socket.actor;
    socket.join(`tenant:${tenantId}:user:${userId}`);
    if (role === 'admin') {
      socket.join(`tenant:${tenantId}:admins`);
    }

    socket.on('join:room', async (roomId, callback) => {
      try {
        const normalizedRoom = String(roomId || '').trim();
        if (!normalizedRoom) {
          return callback?.({ error: { code: 'INVALID_ROOM', message: 'Room ID is required' } });
        }
        if (typeof verifyRoomMembership === 'function') {
          const allowed = await verifyRoomMembership({ tenantId, userId, roomId: normalizedRoom });
          if (!allowed) {
            return callback?.({ error: { code: 'FORBIDDEN_ROOM', message: 'Access to room denied' } });
          }
        }
        const scopedRoom = `tenant:${tenantId}:room:${normalizedRoom}`;
        await socket.join(scopedRoom);
        socket.to(scopedRoom).emit('user:joined', { userId });
        callback?.({ data: { joined: normalizedRoom } });
      } catch {
        callback?.({ error: { code: 'JOIN_FAILED', message: 'Unable to join room' } });
      }
    });

    socket.on('message:send', async (payload, callback) => {
      try {
        const roomId = String(payload?.roomId || '').trim();
        const text = String(payload?.text || '').trim();
        if (!roomId || !text) {
          return callback?.({ error: { code: 'VALIDATION_FAILED', message: 'roomId and text are required' } });
        }
        const scopedRoom = `tenant:${tenantId}:room:${roomId}`;
        if (!socket.rooms.has(scopedRoom)) {
          return callback?.({ error: { code: 'FORBIDDEN_ROOM', message: 'Join the room before sending messages' } });
        }
        const event = {
          id: crypto.randomUUID(),
          roomId,
          senderId: userId,
          text,
          sentAt: new Date().toISOString(),
        };
        io.to(scopedRoom).emit('message:received', event);
        callback?.({ data: event });
      } catch {
        callback?.({ error: { code: 'MESSAGE_SEND_FAILED', message: 'Unable to send message' } });
      }
    });
  });

  return io;
};

export default initializeWebSocket;
