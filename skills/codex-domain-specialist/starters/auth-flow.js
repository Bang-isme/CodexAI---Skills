// ============================================
// AUTH FLOW STARTER - JWT + Refresh Token
// ============================================
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';

const JWT_SECRET = process.env.JWT_SECRET; // 256-bit random
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH; // different secret
const ACCESS_TTL = '15m';
const REFRESH_TTL = '7d';
const SALT_ROUNDS = 12;

// --- Token Generation ---
const generateTokens = (user) => ({
  accessToken: jwt.sign(
    { id: user._id, role: user.role, email: user.email },
    JWT_SECRET,
    { expiresIn: ACCESS_TTL }
  ),
  refreshToken: jwt.sign(
    { id: user._id, version: user.tokenVersion || 0 },
    JWT_REFRESH_SECRET,
    { expiresIn: REFRESH_TTL }
  ),
});

// --- Signup ---
const signup = async (req, res, next) => {
  try {
    const { email, password, firstName, lastName } = req.body;
    const existing = await User.findOne({ email: email.toLowerCase() });
    if (existing) {
      throw BadRequest('Email already registered');
    }

    const hashedPassword = await bcrypt.hash(password, SALT_ROUNDS);
    const user = await User.create({
      email: email.toLowerCase(),
      password: hashedPassword,
      firstName,
      lastName,
    });

    const tokens = generateTokens(user);
    // Store refreshToken hash in DB or Redis for revocation
    res.status(201).json({ success: true, data: { user: sanitize(user), ...tokens } });
  } catch (error) {
    next(error);
  }
};

// --- Signin ---
const signin = async (req, res, next) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email: email.toLowerCase() }).select('+password');
    if (!user) {
      throw Unauthorized('Invalid credentials');
    }

    const valid = await bcrypt.compare(password, user.password);
    if (!valid) {
      throw Unauthorized('Invalid credentials');
    }

    const tokens = generateTokens(user);
    res.json({ success: true, data: { user: sanitize(user), ...tokens } });
  } catch (error) {
    next(error);
  }
};

// --- Refresh Token ---
const refresh = async (req, res, next) => {
  try {
    const { refreshToken } = req.body;
    if (!refreshToken) {
      throw Unauthorized('No refresh token');
    }

    const decoded = jwt.verify(refreshToken, JWT_REFRESH_SECRET);
    const user = await User.findById(decoded.id);
    if (!user || user.tokenVersion !== decoded.version) {
      throw Unauthorized('Token revoked');
    }

    const tokens = generateTokens(user);
    res.json({ success: true, data: tokens });
  } catch (error) {
    next(error);
  }
};

// --- Logout (revoke refresh token) ---
const logout = async (req, res, next) => {
  try {
    // Increment tokenVersion to invalidate all existing refresh tokens
    await User.findByIdAndUpdate(req.user.id, { $inc: { tokenVersion: 1 } });
    res.json({ success: true, message: 'Logged out' });
  } catch (error) {
    next(error);
  }
};

// --- RBAC Middleware ---
const requireRole = (...roles) => (req, res, next) => {
  if (!req.user || !roles.includes(req.user.role)) {
    return next(Forbidden());
  }
  next();
};

// Usage: router.delete('/users/:id', authenticate, requireRole('admin'), deleteUser);
const sanitize = (user) => {
  const obj = user.toObject ? user.toObject() : { ...user };
  delete obj.password;
  delete obj.tokenVersion;
  delete obj.__v;
  return obj;
};
