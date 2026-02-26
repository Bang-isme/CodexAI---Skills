// ============================================
// JEST CONFIG + SETUP STARTER
// ============================================

// jest.config.js
export default {
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.test.{js,ts}', '**/*.test.{js,ts}'],
  transform: { '^.+\\.(ts|tsx|js|jsx)$': 'babel-jest' },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{js,ts,jsx,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.{js,ts}',
    '!src/**/__tests__/**',
  ],
  coverageThresholds: {
    global: { branches: 70, functions: 75, lines: 80, statements: 80 },
  },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  clearMocks: true,
  restoreMocks: true,
};

// jest.setup.js
import { MongoMemoryServer } from 'mongodb-memory-server';
import mongoose from 'mongoose';
import request from 'supertest';

// Replace with your app path
import app from '../src/app.js';

let mongoServer;

beforeAll(async () => {
  mongoServer = await MongoMemoryServer.create();
  await mongoose.connect(mongoServer.getUri());
});

afterEach(async () => {
  const collections = mongoose.connection.collections;
  for (const key of Object.keys(collections)) {
    await collections[key].deleteMany({});
  }
});

afterAll(async () => {
  await mongoose.disconnect();
  await mongoServer.stop();
});

// Test helper utilities
export const createTestUser = (overrides = {}) => ({
  firstName: 'Test',
  lastName: 'User',
  email: `test-${Date.now()}@example.com`,
  password: 'TestPass123!',
  role: 'user',
  ...overrides,
});

export const api = {
  get: (url, token) => {
    const req = request(app).get(url);
    if (token) req.set('Authorization', `Bearer ${token}`);
    return req;
  },
  post: (url, body, token) => {
    const req = request(app).post(url).send(body);
    if (token) req.set('Authorization', `Bearer ${token}`);
    return req;
  },
  put: (url, body, token) => {
    const req = request(app).put(url).send(body);
    if (token) req.set('Authorization', `Bearer ${token}`);
    return req;
  },
  delete: (url, token) => {
    const req = request(app).delete(url);
    if (token) req.set('Authorization', `Bearer ${token}`);
    return req;
  },
};

// Example only: wire your own User model + bcrypt in real project
// export const loginAs = async (role = 'user') => {
//   const userData = createTestUser({ role });
//   const user = await User.create({ ...userData, password: await bcrypt.hash(userData.password, 10) });
//   const res = await api.post('/api/auth/login', { email: userData.email, password: userData.password });
//   return { user, token: res.body.data.accessToken };
// };

/*
TESTING PATTERNS:

describe('UserService', () => {
  describe('createUser', () => {
    it('should create user with valid data', async () => { ... });
    it('should reject duplicate email', async () => { ... });
    it('should hash password before saving', async () => { ... });
  });
});

Naming: "should [expected behavior] when [condition]"
Good: "should return 404 when user not found"
Bad:  "test get user error"
*/
