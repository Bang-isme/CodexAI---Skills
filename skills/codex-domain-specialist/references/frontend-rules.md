# Frontend Rules

## Scope and Triggers

Use this reference when tasks include UI behavior, component structure, client state, rendering performance, or user-facing flow quality.

Primary triggers:
- requests touching `.tsx`, `.jsx`, `.vue`, `.svelte`
- changes under `components/`, `pages/`, `app/`, `ui/`
- issues such as rerender storms, stale UI state, visual regressions
- requests mentioning accessibility, responsiveness, interaction quality

Secondary triggers:
- backend or API change that alters frontend contract behavior
- design-system updates that impact multiple pages
- hydration mismatch or runtime client rendering warnings

Out of scope:
- deep backend architecture decisions unless API contract is impacted
- infra-only deployment concerns without UI impact

## Core Principles

- Build by responsibility boundaries: view, state orchestration, side effects, and data access should be explicit.
- Prefer composition over inheritance and over implicit coupling.
- Treat accessibility as correctness, not optional enhancement.
- Prefer predictable state transitions over ad hoc local fixes.
- Keep render path lightweight; expensive work should be memoized or moved.
- Define measurable render and interaction budgets for critical views.
- Maintain visual and behavioral consistency through shared primitives.
- Model loading, error, empty, and success states intentionally.
- Keep dependency graphs shallow and avoid circular UI imports.
- Optimize developer experience with clear naming and colocated tests.
- Respect existing project conventions before introducing new patterns.

## Decision Tree

### Decision Tree A: Component and State Placement

- If logic is purely presentational and reused across pages, create reusable UI component.
- If logic is presentational but unique to one page, colocate component with page feature folder.
- If state is local and ephemeral, use local state (`useState` or equivalent).
- If state spans siblings with same lifecycle, lift state to closest common parent.
- If state spans many branches and business logic is non-trivial, use dedicated store/context with selectors.
- If data originates from server and needs caching, use query layer instead of custom effect chains.
- If state transitions are complex, use reducer-style state machine over scattered booleans.

### Decision Tree B: Rendering and Data Flow Matrix

| Scenario | Preferred Pattern | Avoid |
| --- | --- | --- |
| Frequent list updates | key-stable list + memoized rows | index keys and inline heavy mapping |
| Form-heavy page | controlled inputs + validation schema | mixed controlled/uncontrolled chaos |
| Shared async data | query cache with invalidation policy | duplicated fetch logic per component |
| Heavy derived values | memoized selectors | recompute in render on each change |
| Expensive interaction | split components + event throttling | monolithic component rerendering everything |
| Partial screen fallback | skeleton and progressive render | blocking spinner for entire page |

## Implementation Patterns

- Use feature folders that colocate UI, hooks, tests, and docs by concern.
- Split container and presentational responsibilities when component complexity grows.
- Use typed props and avoid implicit `any` through strict component interfaces.
- For forms, centralize validation rules and unify error display semantics.
- Prefer custom hooks for side-effect orchestration and data synchronization.
- Normalize API response mapping at boundary layer before reaching UI tree.
- Use stable callback contracts for child components with performance-sensitive paths.
- Introduce memoization only after identifying re-render hotspots.
- Use virtualization for long lists and large table datasets.
- Set route-level budget targets for bundle size and interaction latency.
- Lazy-load route-level chunks and non-critical components.
- Keep design tokens centralized and avoid magic spacing/color values.
- Use CSS variables or theme object for dark/light and brand variants.
- Add explicit empty-state content and actionable recovery options.
- Use optimistic updates only when rollback strategy exists.
- Capture analytics and telemetry at meaningful UX milestones.

## Visual Design System

### Design Tokens

Use centralized design tokens for all visual values. Never use magic numbers.

#### Spacing Scale (8px grid)

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-8: 48px;
  --space-10: 64px;
  --space-12: 80px;
}
```

#### Typography Scale

```css
:root {
  /* 12px - captions, badges */
  --font-xs-size: 0.75rem;
  --font-xs-line: 1rem;
  /* 14px - body small, table cells */
  --font-sm-size: 0.875rem;
  --font-sm-line: 1.25rem;
  /* 16px - body default */
  --font-base-size: 1rem;
  --font-base-line: 1.5rem;
  /* 18px - section headers */
  --font-lg-size: 1.125rem;
  --font-lg-line: 1.75rem;
  /* 20px - page headers */
  --font-xl-size: 1.25rem;
  --font-xl-line: 1.75rem;
  /* 24px - modal/card titles */
  --font-2xl-size: 1.5rem;
  --font-2xl-line: 2rem;
  /* 30px - page titles */
  --font-3xl-size: 1.875rem;
  --font-3xl-line: 2.25rem;
}
```

Font families: use system font stack or `Inter`, `Roboto`, `Outfit` from Google Fonts.

#### Color System

```css
:root {
  /* Brand */
  --brand-primary: hsl(160, 100%, 20%);
  /* Surfaces */
  --surface-0: #ffffff;
  --surface-1: #f8f9fa;
  --surface-2: #f1f3f5;
  /* Text */
  --text-primary: #1a1a2e;
  --text-secondary: #6c757d;
  --text-muted: #adb5bd;
  /* Status */
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #3b82f6;
  /* Borders */
  --border-light: #e9ecef;
  --border-default: #dee2e6;
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}
```

#### Border Radius

```css
:root {
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
}
```

### Layout Patterns

#### Sidebar + Main (Enterprise Dashboard)

```css
.layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
}

.sidebar {
  background: var(--surface-1);
  border-right: 1px solid var(--border-light);
  padding: var(--space-4);
}

.main {
  padding: var(--space-6);
  overflow-y: auto;
}
```

#### Dashboard Grid

```css
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-5);
}
```

#### Card Component

```css
.card {
  background: var(--surface-0);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
}
```

### Animation Patterns

```css
:root {
  --transition-fast: 150ms ease;
  --transition-default: 200ms ease;
  --transition-slow: 300ms ease;
}

.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.pressable:active {
  transform: scale(0.98);
}
```

### Component Specs

| Component | Height | Padding | Font | Radius |
| --- | --- | --- | --- | --- |
| Button (sm) | 32px | 8px 12px | 14px/500 | radius-md |
| Button (md) | 40px | 10px 16px | 14px/600 | radius-md |
| Button (lg) | 48px | 12px 24px | 16px/600 | radius-md |
| Input | 40px | 10px 12px | 14px | radius-md |
| Badge | 22px | 2px 8px | 12px/500 | radius-full |
| Table row | 48px | 12px 16px | 14px | none |

### Responsive Breakpoints

```css
:root {
  --bp-sm: 640px;
  --bp-md: 768px;
  --bp-lg: 1024px;
  --bp-xl: 1280px;
  --bp-2xl: 1536px;
}
```

## Anti-Patterns

1. ❌ Bad: Building 300+ line components with mixed responsibilities.
   ✅ Good: Split the component into container, presentational view, and custom hook with clear interfaces.

2. ❌ Bad: Passing props through many levels when composition can remove drilling.
   ✅ Good: Use composition slots or localized context selectors near consumers instead of deep prop chains.

3. ❌ Bad: Keeping duplicated state in multiple siblings without sync strategy.
   ✅ Good: Choose one source of truth and derive sibling state through selectors or lifted ownership.

4. ❌ Bad: Fetching data in every component that needs the same resource.
   ✅ Good: Centralize fetching in a shared query hook or data provider and consume cached results.

5. ❌ Bad: Running expensive array transforms directly in render path.
   ✅ Good: Memoize expensive transforms with `useMemo` or precompute in selectors.

6. ❌ Bad: Using unstable keys for dynamic lists.
   ✅ Good: Use stable domain identifiers as keys and avoid index keys for mutable lists.

7. ❌ Bad: Hiding accessibility issues with visual-only fixes.
   ✅ Good: Fix semantic structure, labels, and focus behavior instead of cosmetic-only adjustments.

8. ❌ Bad: Ignoring keyboard interaction contracts for custom controls.
   ✅ Good: Implement keyboard handlers (`Enter`, `Space`, `Esc`, arrows) matching expected control behavior.

9. ❌ Bad: Shipping forms without validation and error recovery states.
   ✅ Good: Provide field validation, server error display, retry actions, and success confirmation states.

10. ❌ Bad: Using inline styles for structural layout across the codebase.
   ✅ Good: Adopt shared styling system (tokens, modules, utilities) for structural layout consistency.

11. ❌ Bad: Using `useEffect` as default for derived state that should be computed.
   ✅ Good: Compute derived values directly from source state or memoized selectors instead of effect mirroring.

12. ❌ Bad: Introducing new state libraries without migration plan.
   ✅ Good: Define migration boundaries, adapter layer, and rollback strategy before adopting a new state library.

13. ❌ Bad: Coupling API response shape directly to low-level UI components.
   ✅ Good: Map API DTOs to view models in an adapter layer before passing props to UI components.

14. ❌ Bad: Triggering full-page spinner for small local async updates.
   ✅ Good: Show localized loading indicators only for affected regions to keep the rest of UI interactive.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Is component architecture split by responsibility (container, view, hook) where needed?
- [ ] Yes/No: Is state ownership clear and single-source for shared UI state?
- [ ] Yes/No: Are dynamic lists keyed with stable domain identifiers?
- [ ] Yes/No: Are loading, error, empty, and success states implemented for changed flows?
- [ ] Yes/No: Are accessibility and keyboard interaction requirements satisfied for custom controls?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Do UI tests cover loading, error, empty, and success states for changed screens?
- [ ] Yes/No: Are form validation and recovery paths tested with real user interactions?
- [ ] Yes/No: Are render-performance-sensitive paths tested for large lists or frequent updates?
- [ ] Yes/No: Do accessibility checks pass for modified components and pages?
- [ ] Yes/No: Do end-to-end tests verify localized async updates without full-page blocking indicators?

## Cross-References

- `react-patterns.md` for hooks architecture and rendering control.
- `nextjs-patterns.md` for App Router and server/client boundaries.
- `typescript-rules.md` for strict component and DTO typing.
- `performance-rules.md` for profiling, budgets, and optimization policy.
- `accessibility-rules.md` for WCAG and assistive tech expectations.
- `seo-rules.md` for metadata and crawlability implications.
- `testing-rules.md` for unit, integration, and e2e strategy.

### Scenario Walkthroughs

- Scenario: Dashboard list stutters when filters change rapidly.
  - Action: Memoize derived row data and stabilize callback props passed to row items.
  - Action: Add performance test to track rerender count before and after optimization.
- Scenario: Multi-step form loses user input after server validation error.
  - Action: Persist form state locally and map server errors to field-level messages.
  - Action: Add integration test covering retry flow after failed submit.
- Scenario: Custom dropdown works with mouse but fails with keyboard.
  - Action: Implement arrow-key navigation, `Enter` select, and `Esc` close behavior.
  - Action: Add accessibility test asserting focus order and selection announcements.

### Delivery Notes

- Record major frontend architecture decisions in project decision journal.
- For high-risk refactors, split work into behavior-preserving phases.
- Require visual and interaction regression checks for shared components.
- Pair UI changes with docs updates when user behavior is altered.
