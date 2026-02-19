# React Patterns

## Scope and Triggers

Use this reference for React component architecture, hooks composition, client data orchestration, and rerender control.

Primary triggers:
- hooks complexity, stale closure bugs, effect ordering issues
- state ownership uncertainty in feature modules
- excessive rerenders or expensive derived state paths
- component API design and composition tradeoff discussions

Secondary triggers:
- migration from class or legacy patterns to functional patterns
- integration with query cache, forms, and UI libraries

Out of scope:
- non-React frontend frameworks without React runtime usage

## Core Principles

- Hooks encode behavior contracts and should remain deterministic.
- State ownership should follow data lifetime and update locality.
- Component API should favor explicit props over hidden side effects.
- Effects must synchronize with external systems, not derive local values.
- Derivations belong in pure computation or memoized selectors.
- Co-locate behavior where ownership is clear, extract only when reusable.
- Rendering optimization should be evidence-based, not superstition.
- Prefer stable interfaces between container and leaf components.
- Keep test strategy aligned with component responsibility.
- Favor readability and maintainability over clever abstractions.

## Decision Tree

### Decision Tree A: Hook and State Ownership

- If state is only used in one component and no sibling needs it, keep local state.
- If state is shared by close siblings in same lifecycle, lift to common parent.
- If state is remote and cacheable, use query cache layer instead of custom effects.
- If transitions are complex and event-driven, use reducer or state machine.
- If hook logic is duplicated across modules, extract custom hook with typed contract.
- If hook side effect depends on unstable objects, stabilize dependencies first.

### Decision Tree B: Composition and Rendering Matrix

| Scenario | Preferred Pattern | Avoid |
| --- | --- | --- |
| reusable interaction block | compound components with typed slots | one giant prop bag |
| expensive list rows | memoized row + stable props | anonymous callbacks per row |
| deep tree shared behavior | context selector or state store | prop drilling across many levels |
| derived display data | memoized selector from source state | duplicated derived state in effects |
| async request UI | query cache + status boundary | manual isLoading booleans everywhere |
| form state with validation | dedicated form abstraction | ad hoc validation in each handler |

## Implementation Patterns

- Use custom hooks for side-effect orchestration and shared behavior.
- Keep hooks pure with explicit inputs and outputs.
- Use `useEffect` only for external synchronization tasks.
- Use memoization for high-cost computations and high-frequency rerender paths.
- Keep callback identity stable when passed to memoized children.
- Use reducer pattern for complex local transitions.
- Prefer controlled components for predictable form behavior.
- Build reusable primitives for loading, error, and empty states.
- Normalize API data before it enters component tree.
- Use suspense or boundary patterns where supported by app architecture.
- Use composition pattern (children, render props, slots) for flexibility.
- Keep component files focused and move heavy logic to hooks.
- Add typed event and callback contracts for public components.
- Use test IDs sparingly and only for critical e2e selectors.
- Add guard rails for stale async responses and race conditions.

## Anti-Patterns

1. ❌ Bad: Calling hooks conditionally.
   ✅ Good: Always call hooks at the top level; move branch logic inside the hook body or returned JSX.

2. ❌ Bad: Overusing context for rapidly changing local state.
   ✅ Good: Keep high-frequency UI state local or use selector-based stores to avoid broad rerenders.

3. ❌ Bad: Using effect to mirror props into state without need.
   ✅ Good: Derive values directly from props/state and reserve `useEffect` for external synchronization.

4. ❌ Bad: Updating state during render path.
   ✅ Good: Trigger state updates in event handlers or effects, never during render execution.

5. ❌ Bad: Passing inline heavy objects to memoized children.
   ✅ Good: Create stable object references with `useMemo` before passing to memoized children.

6. ❌ Bad: Building monolithic components with mixed concerns.
   ✅ Good: Split logic into focused hooks and presentational components with explicit boundaries.

7. ❌ Bad: Triggering multiple requests for same resource.
   ✅ Good: Use a query cache with stable query keys to deduplicate concurrent requests.

8. ❌ Bad: Ignoring stale closure issues in async handlers.
   ✅ Good: Use functional state updates or refs to read latest values in async callbacks.

9. ❌ Bad: Using global state for transient local UI details.
   ✅ Good: Keep transient UI state (modal open, hover, draft text) inside local component scope.

10. ❌ Bad: Memoizing everything without profiling evidence.
   ✅ Good: Memoize only proven hotspots and remove unused memoization layers.

11. ❌ Bad: Mixing data-fetching concerns directly inside leaf components.
   ✅ Good: Fetch data in container components or hooks and pass prepared props to leaves.

12. ❌ Bad: Encoding business logic in anonymous inline callbacks.
   ✅ Good: Move business logic into named handlers or hooks to keep behavior testable.

13. ❌ Bad: Recreating selectors in render without memoization.
   ✅ Good: Define selectors outside render or memoize selector creation with stable dependencies.

14. ❌ Bad: Skipping tests for custom hooks with complex effects.
   ✅ Good: Add hook tests covering success, failure, cancellation, and race conditions.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Are hooks called unconditionally at the top level of each component and hook?
- [ ] Yes/No: Is state ownership (local, lifted, global) clearly justified?
- [ ] Yes/No: Are effects used only for side effects rather than derived state mirroring?
- [ ] Yes/No: Are memoization choices backed by profiling evidence?
- [ ] Yes/No: Is data fetching isolated to containers or dedicated hooks instead of leaf components?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Are custom hooks tested for success, failure, and cancellation paths?
- [ ] Yes/No: Are stale-closure and race-condition cases covered for async handlers?
- [ ] Yes/No: Are rerender-sensitive components tested where memoization was introduced?
- [ ] Yes/No: Are composition boundaries validated with integration tests?
- [ ] Yes/No: Are query deduplication and cache invalidation behaviors verified?

## Cross-References

- `frontend-rules.md` for domain-level UI architecture decisions.
- `nextjs-patterns.md` for server/client boundary in Next.js React apps.
- `typescript-rules.md` for hook and component typing discipline.
- `testing-rules.md` for layered component and hook testing.
- `performance-rules.md` for render and interaction optimization workflow.
- `accessibility-rules.md` for semantic and keyboard behavior guarantees.

### Scenario Walkthroughs

- Scenario: Search panel triggers duplicate fetches on rapid typing.
  - Action: Move requests to a cached query hook keyed by normalized search term.
  - Action: Add test asserting concurrent identical queries result in one network call.
- Scenario: Form submit handler uses stale state after async validation.
  - Action: Replace captured state reads with functional updates or ref-backed latest values.
  - Action: Add regression test reproducing rapid edit + submit race condition.
- Scenario: Large dashboard component is difficult to maintain and rerenders often.
  - Action: Split dashboard into data container, memoized sections, and focused custom hooks.
  - Action: Add component tests for each section and benchmark rerender counts before/after.

### Delivery Notes

- Keep this reference aligned with project conventions and postmortems.
- Update checklists when recurring defects reveal missing guardrails.
- Prefer incremental adoption over large risky rewrites.
