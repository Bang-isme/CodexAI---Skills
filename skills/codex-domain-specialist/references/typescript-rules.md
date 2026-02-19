# Typescript Rules

## Scope and Triggers

Use this reference when tasks involve type safety, generic design, contract modeling, and compile-time correctness.

Primary triggers:
- type errors, inference failures, generic API design requests
- DTO modeling, discriminated union workflows, strict mode enforcement
- refactors where type contracts are likely to drift

Secondary triggers:
- API client/server shared contracts
- migration from loose typing to strict typed boundaries

Out of scope:
- dynamic scripts with no maintained TypeScript surface

## Core Principles

- Prefer explicit domain types over implicit structural guesses.
- Keep type boundaries close to IO boundaries.
- Use strict compiler settings for maintainable evolution.
- Model impossible states out of runtime with unions and narrowing.
- Keep generic abstractions constrained and purposeful.
- Preserve public type contracts during refactors.
- Avoid `any` and unsafe assertions unless isolated and documented.
- Use type-level helpers to remove duplication and drift.
- Encode nullability and optionality intentionally.
- Let runtime validation back critical trust boundaries.

## Decision Tree

### Decision Tree A: Type Modeling Strategy

- If value domain has finite states, use discriminated union.
- If entity evolves through lifecycle stages, use state-specific interfaces.
- If function shape repeats with variance, use constrained generics.
- If type is derived from source object, use mapped and utility types.
- If external input is unknown, validate at runtime then narrow type.
- If cross-module contract is public, create stable exported type module.

### Decision Tree B: Safety Matrix for Common Tradeoffs

| Problem | Preferred Pattern | Avoid |
| --- | --- | --- |
| optional API fields | explicit optional + default normalization | non-null assertions everywhere |
| shared response contract | source-of-truth type + schema | duplicate manual interfaces |
| overloaded function behavior | discriminated options object | broad union without narrowing |
| reusable transformations | generic with constraints | unconstrained generic magic |
| partial updates | `Partial<T>` at edge then normalize | persisting partials into domain core |
| unknown external data | zod/io-ts validation then infer | cast unknown to trusted type |

## Implementation Patterns

- Use `strict`, `noImplicitAny`, and `exactOptionalPropertyTypes` where feasible.
- Keep DTO types separate from domain model types.
- Use branded types for IDs and high-risk opaque strings.
- Prefer unions over boolean flag combinations for state modeling.
- Use exhaustive switch with `never` checks for union coverage.
- Centralize API contract types and reuse across client/server.
- Derive helper types with `Pick`, `Omit`, `Record`, and mapped types.
- Keep generic constraints narrow and documented.
- Use readonly typing for immutable data flow boundaries.
- Encapsulate unsafe casts in one boundary function.
- Add parser/validator wrappers for untrusted data.
- Encode error types with discriminated result unions.
- Use utility helpers for deep partial or patch operations carefully.
- Keep type aliases and interface naming consistent by domain.
- Add type tests for critical generic utilities.

## Anti-Patterns

1. ❌ Bad: Using `any` as default escape hatch.
   ✅ Good: Prefer precise types or `unknown` with explicit narrowing instead of defaulting to `any`.

2. ❌ Bad: Casting unknown input directly to trusted types.
   ✅ Good: Validate external input with schema parsing before converting to trusted domain types.

3. ❌ Bad: Modeling state with multiple unsynced booleans.
   ✅ Good: Use discriminated unions for state machines to enforce valid combinations.

4. ❌ Bad: Sharing one giant interface for unrelated entities.
   ✅ Good: Split interfaces by bounded context and compose shared primitives where needed.

5. ❌ Bad: Overusing conditional types without readability controls.
   ✅ Good: Use named helper types with tests and keep conditional type depth manageable.

6. ❌ Bad: Ignoring compiler warnings with broad suppressions.
   ✅ Good: Use targeted `@ts-expect-error` with reason comments and follow-up cleanup tasks.

7. ❌ Bad: Repeating API contract types in multiple files.
   ✅ Good: Generate shared API types from OpenAPI/schema source and import from one package.

8. ❌ Bad: Using non-null assertion to silence true nullability risk.
   ✅ Good: Handle nullability with guards, defaults, or explicit error paths.

9. ❌ Bad: Writing unconstrained generics that accept everything.
   ✅ Good: Constrain generics with `extends` and defaults to preserve type safety.

10. ❌ Bad: Treating runtime validation as unnecessary in external boundaries.
   ✅ Good: Validate runtime data at IO boundaries even when compile-time types exist.

11. ❌ Bad: Forgetting to enforce exhaustive union handling.
   ✅ Good: Use exhaustive `switch` with `never` checks so new union members fail compilation.

12. ❌ Bad: Allowing partial objects to leak into core business logic.
   ✅ Good: Convert partial inputs to validated full domain objects before core processing.

13. ❌ Bad: Coupling persistence schema directly to UI component types.
   ✅ Good: Separate persistence, transport, and UI types with explicit mapper functions.

14. ❌ Bad: Breaking exported public types without migration notes.
   ✅ Good: Version exported types, provide deprecation aliases, and document migration steps.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Is strict typing preserved without broad `any` or unsafe casts?
- [ ] Yes/No: Are external inputs validated before type narrowing into trusted models?
- [ ] Yes/No: Are unions and generics constrained for exhaustiveness and correctness?
- [ ] Yes/No: Are shared contract types centralized instead of duplicated?
- [ ] Yes/No: Are exported type changes versioned with migration guidance?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Do compile-time checks or type tests cover key generic and union behavior?
- [ ] Yes/No: Are runtime schema validations tested for external inputs and API responses?
- [ ] Yes/No: Are exhaustive switch paths enforced with `never` checks in changed code?
- [ ] Yes/No: Are nullability edge cases tested where optional data is consumed?
- [ ] Yes/No: Do contract tests verify generated/shared types remain synchronized with API schema?

## Cross-References

- `api-design-rules.md` for contract-level API stability.
- `react-patterns.md` for typed hooks and component APIs.
- `backend-rules.md` for service DTO and domain boundary practices.
- `testing-rules.md` for compile-time and runtime verification layering.
- `database-rules.md` for persistence model and migration-safe typing.

### Scenario Walkthroughs

- Scenario: API client breaks after backend adds new union variant.
  - Action: Add discriminated union member and exhaustive switch handling in all affected reducers.
  - Action: Add compile-time tests that fail when union variants are unhandled.
- Scenario: Developer uses `any` to bypass complex generic errors.
  - Action: Replace `any` with constrained generic and helper type aliases for readability.
  - Action: Add type tests demonstrating accepted and rejected generic usage.
- Scenario: Runtime crash occurs from malformed external payload despite compile success.
  - Action: Add schema validation at boundary and map parse failures to safe error handling.
  - Action: Add tests for malformed payloads and assert graceful rejection.

### Delivery Notes

- Keep this reference aligned with project conventions and postmortems.
- Update checklists when recurring defects reveal missing guardrails.
- Prefer incremental adoption over large risky rewrites.
