// ============================================
// AUTH FLOW STARTER — HttpOnly Cookie Session + Refresh Rotation
// Unified Env Keys (JWT_SECRET, JWT_REFRESH_SECRET) + DTO Mapping + RFC 9457 Errors
// ============================================
import crypto from 'node:crypto';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { AppError } from './express-api.js';

const JWT_SECRET = process.env.JWT_SECRET;
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET;
const ACCESS_TTL = '15m';
const REFRESH_TTL = '7d';
const PASSWORD_COST = 12;

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax',
  path: '/api/v1/auth',
  maxAge: 7 * 24 * 60 * 60 * 1000,
};

export const toUserDto = (user) => ({
  id: String(user.id || user._id),
  tenantId: String(user.tenantId),
  email: user.email,
  firstName: user.firstName,
  lastName: user.lastName,
  role: user.role,
});

export const hashToken = (token) => crypto.createHash('sha256').update(token).digest('hex');

export const issueSessionTokens = (user) => {
  const sub = String(user.id || user._id);
  const accessToken = jwt.sign(
    { sub, tenantId: user.tenantId, role: user.role },
    JWT_SECRET,
    { expiresIn: ACCESS_TTL }
  );
  const refreshToken = jwt.sign(
    { sub, tenantId: user.tenantId, version: user.tokenVersion || 0, jti: crypto.randomUUID() },
    JWT_REFRESH_SECRET,
    { expiresIn: REFRESH_TTL }
  );
  return { accessToken, refreshToken };
};

export const signupHandler = (UserRepo) => async (req, res, next) => {
  try {
    const email = String(req.body.email || '').trim().toLowerCase();
    const existing = await UserRepo.findByEmail(email);
    if (existing) {
      throw new AppError('EMAIL_CONFLICT', 'Email is already registered', 409, [
        { field: 'email', code: 'CONFLICT', message: 'Email is already registered' },
      ]);
    }

    const passwordHash = await bcrypt.hash(req.body.password, PASSWORD_COST);
    const user = await UserRepo.create({
      email,
      passwordHash,
      firstName: req.body.firstName.trim(),
      lastName: req.body.lastName.trim(),
      role: 'user',
      tokenVersion: 0,
    });

    const { accessToken, refreshToken } = issueSessionTokens(user);
    await UserRepo.storeRefreshTokenHash(user.id, hashToken(refreshToken));
    res.cookie('refreshToken', refreshToken, COOKIE_OPTIONS);

    res.status(201).json({
      data: { user: toUserDto(user), accessToken },
      meta: { requestId: req.id },
    });
  } catch (error) {
    next(error);
  }
};

export const signinHandler = (UserRepo) => async (req, res, next) => {
  try {
    const email = String(req.body.email || '').trim().toLowerCase();
    const user = await UserRepo.findByEmailWithPassword(email);
    if (!user || !(await bcrypt.compare(req.body.password, user.passwordHash))) {
      throw new AppError('INVALID_CREDENTIALS', 'Invalid email or password', 401);
    }

    const { accessToken, refreshToken } = issueSessionTokens(user);
    await UserRepo.storeRefreshTokenHash(user.id, hashToken(refreshToken));
    res.cookie('refreshToken', refreshToken, COOKIE_OPTIONS);

    res.status(200).json({
      data: { user: toUserDto(user), accessToken },
      meta: { requestId: req.id },
    });
  } catch (error) {
    next(error);
  }
};

export const refreshHandler = (UserRepo) => async (req, res, next) => {
  try {
    const presentedToken = req.cookies?.refreshToken;
    if (!presentedToken) {
      throw new AppError('REFRESH_TOKEN_MISSING', 'Refresh cookie is missing', 401);
    }

    let decoded;
    try {
      decoded = jwt.verify(presentedToken, JWT_REFRESH_SECRET);
    } catch {
      throw new AppError('REFRESH_TOKEN_INVALID', 'Refresh token is invalid or expired', 401);
    }

    const user = await UserRepo.findById(decoded.sub);
    const presentedHash = hashToken(presentedToken);
    if (!user || user.tokenVersion !== decoded.version || user.refreshTokenHash !== presentedHash) {
      if (user) await UserRepo.incrementTokenVersion(user.id);
      res.clearCookie('refreshToken', COOKIE_OPTIONS);
      throw new AppError('REFRESH_TOKEN_REVOKED', 'Session has been revoked; please sign in again', 401);
    }

    // Rotate refresh token on every use
    const nextUser = await UserRepo.incrementTokenVersion(user.id);
    const { accessToken, refreshToken } = issueSessionTokens(nextUser);
    await UserRepo.storeRefreshTokenHash(nextUser.id, hashToken(refreshToken));
    res.cookie('refreshToken', refreshToken, COOKIE_OPTIONS);

    res.status(200).json({
      data: { accessToken },
      meta: { requestId: req.id },
    });
  } catch (error) {
    next(error);
  }
};

export const logoutHandler = (UserRepo) => async (req, res, next) => {
  try {
    if (req.actor?.userId) {
      await UserRepo.incrementTokenVersion(req.actor.userId);
    }
    res.clearCookie('refreshToken', COOKIE_OPTIONS);
    res.status(204).end();
  } catch (error) {
    next(error);
  }
};
