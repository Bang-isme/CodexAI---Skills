# Testing Strategy

**Load when:** planning test coverage, choosing test types, building test infrastructure, or deciding what to mock.

## Test Pyramid

```
        ┌─────────┐
        │  E2E    │  ~10% — Critical user journeys only
        │  Tests  │  Slow, expensive, high confidence
        ├─────────┤
        │ Integra-│  ~20% — Module boundaries, DB, API
        │  tion   │  Medium speed, real dependencies
        ├─────────┤
        │  Unit   │  ~70% — Pure logic, transformations
        │  Tests  │  Fast, isolated, deterministic
        └─────────┘
```

## What to Test at Each Layer

| Layer | Test Type | What to Test | What NOT to Test |
| --- | --- | --- | --- |
| Utils/helpers | Unit | Pure transformations, edge cases | Framework internals |
| Validation | Unit | Valid/invalid inputs, error messages | Database constraints |
| Services | Unit + Integration | Business logic, state transitions | UI rendering |
| API Routes | Integration | Status codes, response shape, auth | Frontend behavior |
| UI Components | Integration | User interactions, conditional renders | CSS pixel values |
| Critical Flows | E2E | Login → action → verify → logout | Every page/variation |

## Test Data Factory Pattern

```javascript
// test-utils/factories.js — Never hardcode test data inline
const createUser = (overrides = {}) => ({
  id: `user-${Date.now()}`,
  name: 'Test User',
  email: `test-${Date.now()}@example.com`,
  role: 'user',
  isActive: true,
  createdAt: new Date(),
  ...overrides,
});

const createOrder = (overrides = {}) => ({
  id: `order-${Date.now()}`,
  userId: createUser().id,
  items: [{ productId: 'prod-1', quantity: 1, price: 29.99 }],
  total: 29.99,
  status: 'pending',
  createdAt: new Date(),
  ...overrides,
});

// Usage in tests
test('calculates order total', () => {
  const order = createOrder({
    items: [
      { productId: 'a', quantity: 2, price: 10 },
      { productId: 'b', quantity: 1, price: 5 },
    ],
  });
  expect(calculateTotal(order)).toBe(25);
});
```

## Mocking Decision Table

| Dependency | Mock? | Why |
| --- | --- | --- |
| External API (Stripe, SendGrid) | ✅ Always | Slow, costs money, flaky |
| Database (unit tests) | ✅ Yes | Speed, isolation |
| Database (integration tests) | ❌ No | Test real queries |
| File system | 🔶 Depends | Mock for unit, real for integration |
| Time/Date | ✅ Yes | Deterministic tests |
| Internal modules | ❌ No | Test real behavior |
| Logger | ✅ Yes | Suppress noise, verify calls |

### Mocking Rules

```javascript
// ❌ BAD: Mock everything "to be safe"
jest.mock('./database');
jest.mock('./cache');
jest.mock('./logger');
jest.mock('./validator');
// Testing what? The mock wiring.

// ✅ GOOD: Mock only external boundaries
jest.mock('./emailProvider'); // External service
// Let database, cache, validator run for real

// ❌ BAD: Mock the unit under test
jest.spyOn(userService, 'create');
userService.create(data);
expect(userService.create).toHaveBeenCalled(); // Of course it was!

// ✅ GOOD: Test observable behavior
const user = await userService.create({ name: 'Alice' });
expect(user.name).toBe('Alice');
expect(await db.users.findById(user.id)).toBeTruthy();
```

## Contract Tests (API Boundary Testing)

```javascript
// When multiple services depend on an API contract
describe('GET /api/users/:id contract', () => {
  test('returns required fields', async () => {
    const res = await request(app).get('/api/users/1');
    
    // Contract: these fields MUST exist
    expect(res.body).toHaveProperty('id');
    expect(res.body).toHaveProperty('name');
    expect(res.body).toHaveProperty('email');
    expect(res.body).toHaveProperty('role');
    
    // Contract: types MUST match
    expect(typeof res.body.id).toBe('string');
    expect(typeof res.body.name).toBe('string');
  });

  test('error response follows envelope', async () => {
    const res = await request(app).get('/api/users/nonexistent');
    expect(res.body).toHaveProperty('success', false);
    expect(res.body).toHaveProperty('message');
    expect(res.body).toHaveProperty('code');
  });
});
```

## Snapshot Testing Rules

| Use For | Don't Use For |
| --- | --- |
| Serialized data structures | UI components (brittle) |
| API response shapes | Dynamic content (dates, IDs) |
| Error messages | Large objects (hard to review) |
| Config/schema output | Anything that changes frequently |

```javascript
// ✅ GOOD: Snapshot for stable shapes
expect(transformConfig(input)).toMatchInlineSnapshot(`
  {
    "host": "localhost",
    "port": 3000,
    "debug": false,
  }
`);

// ❌ BAD: Snapshot for dynamic content
expect(createUser()).toMatchSnapshot(); // Changes every run (IDs, dates)
```

## Test Isolation Checklist

| Check | Action |
| --- | --- |
| Tests pass in any order | No shared mutable state |
| Tests pass in parallel | No port/file conflicts |
| Tests pass on clean DB | Setup/teardown in each test |
| Tests don't leak timers | `jest.useFakeTimers()` + cleanup |
| Tests don't leak listeners | Remove event listeners in `afterEach` |

## Coverage Guidance

| Code Area | Line Coverage Target | Branch Coverage Target |
| --- | --- | --- |
| Security/auth | 90%+ | 85%+ |
| Payment/billing | 90%+ | 85%+ |
| Validation logic | 85%+ | 80%+ |
| Business services | 80%+ | 70%+ |
| UI components | 70%+ | 60%+ |
| Utils/helpers | 90%+ | 80%+ |
| Config/setup | 50%+ | N/A |

**Coverage ≠ quality.** 100% coverage with bad assertions is worse than 70% with meaningful tests.

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
| --- | --- | --- |
| Testing implementation | Breaks on refactor | Test behavior, not internals |
| Shared mutable state | Order-dependent failures | Isolate per test |
| Sleep-based waits | Flaky, slow | Condition-based waiting |
| Giant test functions | Hard to diagnose | One assertion per test |
| No test data factories | Duplicated setup, brittle | Factory pattern |
| Mock the unit under test | Proves nothing | Mock boundaries only |
