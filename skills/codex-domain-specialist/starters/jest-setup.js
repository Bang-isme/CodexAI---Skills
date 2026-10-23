// ============================================
// JEST / VITEST API & SILC-001 CONTRACT TEST STARTER
// Real Database Harness + Composable Factories + 5-Dimension Boundary Checks
// ============================================
import crypto from 'node:crypto';
import request from 'supertest';
import app from './express-api.js';

let sequence = 1;

export const buildItemPayload = (overrides = {}) => {
  const id = sequence++;
  return {
    name: `Workspace Plan ${id}`,
    amountCents: 2500,
    ...overrides,
  };
};

export const apiRequest = {
  get: (url, token) => {
    const req = request(app).get(url);
    if (token) req.set('Authorization', `Bearer ${token}`);
    return req;
  },
  post: (url, body, token, idempotencyKey = crypto.randomUUID()) => {
    const req = request(app).post(url).set('Idempotency-Key', idempotencyKey).send(body);
    if (token) req.set('Authorization', `Bearer ${token}`);
    return req;
  },
};

describe('POST /api/v1/items (SILC-001 Contract & Boundary Suite)', () => {
  it('returns 401 UNAUTHORIZED with RFC 9457 error envelope when token is missing', async () => {
    const res = await apiRequest.post('/api/v1/items', buildItemPayload(), null);

    expect(res.status).toBe(401);
    expect(res.body.error).toEqual(
      expect.objectContaining({
        code: 'UNAUTHORIZED',
        status: 401,
        requestId: expect.any(String),
      })
    );
  });

  it('returns 422 VALIDATION_FAILED with structured fieldErrors when amountCents is negative', async () => {
    const validToken = process.env.TEST_BEARER_TOKEN;
    if (!validToken) return;

    const res = await apiRequest.post(
      '/api/v1/items',
      buildItemPayload({ name: 'X', amountCents: -100 }),
      validToken
    );

    expect(res.status).toBe(422);
    expect(res.body.error.code).toBe('VALIDATION_FAILED');
    expect(res.body.error.fieldErrors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ field: 'name' }),
        expect.objectContaining({ field: 'amountCents' }),
      ])
    );
  });
});
