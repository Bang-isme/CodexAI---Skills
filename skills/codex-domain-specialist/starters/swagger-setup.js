// ============================================
// OPENAPI 3.1 / SWAGGER STARTER — SILC-001 & RFC 9457 Compliant
// ============================================
import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';

const options = {
  definition: {
    openapi: '3.1.0',
    info: {
      title: 'Service API Contract (SILC-001)',
      version: '1.0.0',
      description: 'Contract-first REST API with cursor pagination, Idempotency-Key, and RFC 9457 error envelopes.',
    },
    servers: [
      { url: 'http://localhost:3000', description: 'Local Development' },
    ],
    components: {
      securitySchemes: {
        bearerAuth: { type: 'http', scheme: 'bearer', bearerFormat: 'JWT' },
      },
      parameters: {
        IdempotencyKeyHeader: {
          name: 'Idempotency-Key',
          in: 'header',
          required: true,
          schema: { type: 'string', format: 'uuid' },
          description: 'Unique UUID key for safe mutation retries.',
        },
      },
      schemas: {
        FieldError: {
          type: 'object',
          required: ['field', 'code', 'message'],
          properties: {
            field: { type: 'string', example: 'budgetCents' },
            code: { type: 'string', example: 'MIN_VALUE' },
            message: { type: 'string', example: 'Campaign budget must be at least 500 cents.' },
          },
        },
        ErrorEnvelope: {
          type: 'object',
          required: ['error'],
          properties: {
            error: {
              type: 'object',
              required: ['code', 'title', 'status', 'requestId', 'fieldErrors'],
              properties: {
                code: { type: 'string', example: 'VALIDATION_FAILED' },
                title: { type: 'string', example: 'Request validation failed' },
                status: { type: 'integer', example: 422 },
                requestId: { type: 'string', example: 'req_01J8Z9X2' },
                fieldErrors: {
                  type: 'array',
                  items: { $ref: '#/components/schemas/FieldError' },
                },
              },
            },
          },
        },
        CursorPaginationMeta: {
          type: 'object',
          required: ['limit', 'nextCursor', 'hasMore'],
          properties: {
            limit: { type: 'integer', example: 25 },
            nextCursor: { type: ['string', 'null'], example: 'eyJjcmVhdGVkQXQiOiIyMDI2LTEwLTIzIn0=' },
            hasMore: { type: 'boolean', example: true },
          },
        },
      },
    },
    security: [{ bearerAuth: [] }],
  },
  apis: ['./src/routes/*.js', './src/modules/**/*.ts'],
};

const specs = swaggerJsdoc(options);

export const setupSwagger = (app) => {
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(specs, { explorer: true }));
  app.get('/api-docs.json', (_req, res) => res.json(specs));
};

export default setupSwagger;
