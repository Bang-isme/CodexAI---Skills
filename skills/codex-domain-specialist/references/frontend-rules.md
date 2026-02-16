# Frontend Rules

## Core Principles

- Build component-first and keep components focused.
- Treat accessibility as mandatory.
- Use type safety to reduce runtime bugs.
- Design mobile-first and verify responsive behavior.
- Treat performance as part of correctness.

## Design Decisions

Before creating a component:

1. decide reusable vs one-off placement
2. decide local vs shared vs server state
3. assess rerender and rendering-cost risks

## Implementation Rules

- Keep component files under 150 lines where practical.
- Extract hooks for complex state/side effects.
- Prefer composition over prop drilling.
- Handle loading, error, and empty states.
- Use project-native styling approach.

## Testing

- Unit test hooks/utilities.
- Integration test key interactions.
- E2E test critical user flows.
