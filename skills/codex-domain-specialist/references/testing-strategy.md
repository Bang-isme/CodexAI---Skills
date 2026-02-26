# Testing Strategy

## Test Pyramid

- Unit tests (~70%): fast, isolated logic.
- Integration tests (~20%): module boundaries and DB/API behavior.
- E2E tests (~10%): critical user journeys.

## Layer Coverage

| Layer | Test Type | Example |
| --- | --- | --- |
| Utils | Unit | `formatCurrency(1234)` |
| Validation | Unit | invalid schema input |
| Services | Unit/integration | business workflow |
| API Routes | Integration | HTTP status + response envelope |
| UI Components | Integration | render + interaction |
| Critical Flows | E2E | login -> action -> verify |

## Mocking Rules

- Always mock external providers (email, payment, third-party APIs).
- Use in-memory DB for integration when possible.
- Do not mock the unit under test.

## Coverage Guidance

- Target around 80% line and 70% branch.
- Enforce higher coverage for security/payment/validation code.
