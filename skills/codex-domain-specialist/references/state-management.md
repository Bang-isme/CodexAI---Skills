# State Management

## Scope and Triggers

Use when designing client-side state architecture in React apps, including cache strategy, shared state, and side-effect orchestration.

## Core Principles

- Keep state as local as possible, as global as necessary.
- Separate server state from UI state.
- Derive values instead of duplicating state.
- Prefer explicit state transitions over ad hoc mutations.
- Optimize correctness first, then performance.

## State Taxonomy

| State Type | Examples | Best Home |
| --- | --- | --- |
| Local UI state | modal open, input draft | component `useState` |
| Shared UI state | sidebar collapsed, theme | context/store |
| Server state | users, orders, dashboards | React Query/TanStack Query |
| URL state | filters, page, sort | router query params |
| Form state | values, dirty, errors | form library + local state |

## React Context Patterns

### When to Use

- Low update frequency state.
- Broad app-level concerns (theme, locale, auth user shell).

### Pattern

- Split context by concern.
- Expose selector hooks to reduce rerenders.
- Memoize provider value.

### Avoid

- Putting rapidly changing data into one giant context.

## Redux Toolkit Setup

### Use When

- Complex business workflows with many events.
- Need explicit event history and predictable reducers.
- Multiple teams touching same app state.

### Baseline Structure

- `store.ts`: configureStore
- `features/<domain>/slice.ts`
- async thunks or RTK Query where appropriate
- typed hooks (`useAppDispatch`, `useAppSelector`)

### Rules

- Keep reducers pure.
- Use normalized entities for large collections.
- Avoid over-using global store for ephemeral UI state.

## Zustand Setup

### Use When

- Lightweight global state with minimal boilerplate.
- Need simple shared UI state and local persistence.

### Rules

- Create multiple small stores, not one mega store.
- Use selectors + shallow compare.
- Keep side effects outside setter where possible.

## React Query / TanStack Query

### Use When

- Any server data with caching/invalidation needs.

### Key Concepts

- query key conventions
- staleTime and gcTime tuning
- mutation invalidation strategy
- optimistic updates with rollback

### Rules

- Query keys must include all parameters.
- Invalidate only affected keys.
- Use prefetch for likely next screens.
- Handle error/loading/empty states consistently.

## Decision Matrix

| Scenario | Recommended |
| --- | --- |
| Simple form page | local state + form lib |
| Shared preferences | Context or Zustand |
| Complex app workflows | Redux Toolkit |
| API-driven dashboard | React Query + local UI state |
| Multi-tab sync needed | Zustand + storage/event sync |

## State Colocation Rules

1. Keep state nearest component that needs it.
2. Lift only when two or more siblings need same source.
3. Promote to global store only when many branches consume it.
4. Keep server cache out of Redux unless strong reason exists.

## Anti-Patterns

1. Duplicating same entity in multiple stores.
2. Mirroring query cache into local state by default.
3. Storing derived values that can be computed.
4. One global context with mixed concerns.
5. Business logic inside presentation components.

## Performance Practices

- Use memoized selectors.
- Split components by render boundaries.
- Avoid inline object/function props in hot paths.
- Virtualize large lists.
- Measure rerenders with profiling tools.

## Error Handling in State

- Distinguish transport errors vs domain errors.
- Show stale-but-usable data when possible.
- Preserve previous data during background refetch.
- Use retries with bounded attempts for transient failures.

## Testing Strategy

- Unit test reducers/selectors.
- Integration test store + component interaction.
- Mock network for query hooks.
- Add regression tests for race conditions.

## Practical Starter Choices

- Small app: Context + React Query.
- Medium app: Zustand + React Query.
- Large app: Redux Toolkit + RTK Query/React Query split by domain.

## Review Checklist

- Is server state separated from UI state?
- Are query keys stable and parameterized?
- Is state colocated before globalizing?
- Are store boundaries aligned to features/domains?
- Are rerender hotspots measured and mitigated?
