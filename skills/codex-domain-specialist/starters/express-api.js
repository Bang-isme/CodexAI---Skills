// ============================================
// EXPRESS API STARTER - Production-Ready
// ============================================
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { body, param, query, validationResult } from 'express-validator';

const app = express();

// --- Middleware Stack (order matters) ---
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN || '*', credentials: true }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  standardHeaders: true,
});
app.use('/api/', limiter);

// --- Validation Middleware Factory ---
const validate = (validations) => async (req, res, next) => {
  for (const validation of validations) {
    await validation.run(req);
  }

  const errors = validationResult(req);
  if (errors.isEmpty()) {
    return next();
  }

  return res.status(422).json({
    success: false,
    message: 'Validation failed',
    errors: errors.array().map((e) => ({ field: e.path, message: e.msg })),
  });
};

// --- AppError Class ---
class AppError extends Error {
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR') {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = true;
  }
}

const NotFound = (resource) => new AppError(`${resource} not found`, 404, 'NOT_FOUND');
const BadRequest = (msg) => new AppError(msg, 400, 'BAD_REQUEST');
const Unauthorized = (msg = 'Unauthorized') => new AppError(msg, 401, 'UNAUTHORIZED');
const Forbidden = (msg = 'Forbidden') => new AppError(msg, 403, 'FORBIDDEN');

// --- Auth Middleware Template ---
const authenticate = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) {
      throw Unauthorized('No token provided');
    }

    // const decoded = jwt.verify(token, process.env.JWT_SECRET);
    // req.user = await User.findById(decoded.id).select('-password');
    // if (!req.user) throw Unauthorized('User not found');

    next();
  } catch (error) {
    next(error);
  }
};

const authorize = (...roles) => (req, res, next) => {
  if (!roles.includes(req.user?.role)) {
    return next(Forbidden('Insufficient permissions'));
  }
  next();
};

// --- Route Example ---
app.get(
  '/api/v1/items',
  authenticate,
  validate([
    query('page').optional().isInt({ min: 1 }),
    query('limit').optional().isInt({ min: 1, max: 100 }),
  ]),
  async (req, res, next) => {
    try {
      const page = parseInt(req.query.page, 10) || 1;
      const limit = parseInt(req.query.limit, 10) || 20;
      // const items = await ItemService.findAll({ page, limit });
      res.json({ success: true, data: [], meta: { page, limit, total: 0 } });
    } catch (error) {
      next(error);
    }
  }
);

// --- Centralized Error Handler (MUST be last) ---
app.use((err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  const response = {
    success: false,
    message: err.isOperational ? err.message : 'Internal server error',
    code: err.code || 'INTERNAL_ERROR',
  };

  if (process.env.NODE_ENV === 'development') {
    response.stack = err.stack;
  }

  if (!err.isOperational) {
    console.error('UNHANDLED ERROR:', err);
  }

  res.status(statusCode).json(response);
});

// --- Start ---
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
