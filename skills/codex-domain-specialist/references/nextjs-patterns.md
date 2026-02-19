# Nextjs Patterns

## Scope and Triggers

Use this reference for Next.js architecture choices: App Router, server and client boundaries, caching, rendering mode, and route composition.

Primary triggers:
- requests mentioning App Router, layouts, route handlers, middleware
- server component vs client component uncertainty
- SSR, SSG, ISR, and revalidation strategy decisions
- fetch caching, route segment performance, and SEO concerns

Secondary triggers:
- migration from pages router to app router
- hydration mismatch, edge runtime behavior, or streaming UI issues

Out of scope:
- non-Next.js React projects with no framework routing/runtime use

## Core Principles

- Default to server components for data-heavy, non-interactive UI.
- Add client boundary only when interactivity requires browser APIs.
- Keep data fetching near server boundary for cache control.
- Choose rendering mode by freshness, personalization, and cost.
- Keep route segment structure aligned with feature ownership.
- Use metadata APIs consistently for crawlability and sharing.
- Revalidation policy should be explicit and measurable.
- Middleware should stay lightweight and deterministic.
- Minimize unnecessary client bundle weight.
- Treat runtime choice (edge/node) as an architectural decision.

## Decision Tree

### Decision Tree A: Rendering Mode Selection

- If page is mostly static and updates rarely, use SSG with periodic revalidate.
- If content is user-specific per request, use SSR with auth-aware server logic.
- If content can be stale briefly and traffic is high, use ISR with revalidation strategy.
- If data is highly dynamic and compliance-sensitive, avoid stale caching.
- If route mixes static shell and dynamic blocks, stream dynamic sections separately.
- If external data source has strict quotas, increase cache reuse windows.

### Decision Tree B: Server/Client Boundary Matrix

| Requirement | Preferred Boundary | Avoid |
| --- | --- | --- |
| form with browser events | client component for interaction | server component with client hacks |
| heavy data aggregation | server component fetch and transform | client-side bulk fetch at mount |
| reusable static section | server component with memoized data | client-only for simple static block |
| auth-protected route | server-side guard in layout/handler | client redirect as only protection |
| seo metadata page | server metadata generation | client-only metadata mutation |
| low-latency edge need | edge runtime with compatible deps | forcing node-only APIs on edge |

## Implementation Patterns

- Structure routes by domain with nested layouts for shared concerns.
- Keep server data fetching in route-level boundaries.
- Use `generateMetadata` for dynamic metadata tied to route params.
- Prefer route handlers for backend-like APIs close to route context.
- Use cache tags or revalidate paths for controlled invalidation.
- Use loading and error boundaries per route segment.
- Keep client components focused on interaction and local state.
- Move expensive transforms to server side when possible.
- Use dynamic import for client-heavy optional widgets.
- Normalize external data before passing to client components.
- Keep middleware small and avoid heavy network calls.
- Evaluate edge runtime compatibility before adoption.
- Use segment config intentionally (`dynamic`, `revalidate`, etc.).
- Ensure canonical URL and metadata consistency across dynamic routes.
- Add observability around cache miss rates and response times.

## Anti-Patterns

1. ❌ Bad: Marking entire app as client components by default.
   ✅ Good: Default to server components and mark only interactive leaf nodes with `'use client'`.

2. ❌ Bad: Fetching identical data in multiple child components.
   ✅ Good: Fetch shared data once in route/layout and pass it down as props or context.

3. ❌ Bad: Mixing mutable global client state with server-fetched truths.
   ✅ Good: Treat server data as source of truth and sync client cache via explicit invalidation.

4. ❌ Bad: Ignoring cache invalidation strategy.
   ✅ Good: Define per-route cache and revalidation policy with explicit freshness requirements.

5. ❌ Bad: Using middleware for business logic that belongs in handlers.
   ✅ Good: Keep middleware for lightweight routing/auth checks and move business logic to handlers/services.

6. ❌ Bad: Treating ISR as real-time data source.
   ✅ Good: Use ISR for mostly-static content and choose dynamic rendering for real-time requirements.

7. ❌ Bad: Forcing SSR for content that can be statically generated.
   ✅ Good: Use SSG for stable content and reserve SSR for request-specific personalization.

8. ❌ Bad: Ignoring hydration mismatch warnings.
   ✅ Good: Align server and client render output and isolate browser-only logic to client-only hooks.

9. ❌ Bad: Shipping bloated client bundles from unnecessary client boundaries.
   ✅ Good: Move non-interactive logic to server components and use dynamic imports for heavy client code.

10. ❌ Bad: Using dynamic rendering without monitoring cost impact.
   ✅ Good: Enable dynamic rendering only on routes that require it and monitor latency/cost metrics.

11. ❌ Bad: Duplicating metadata logic in many route files.
   ✅ Good: Centralize metadata generation in shared helpers and route-level config conventions.

12. ❌ Bad: Using edge runtime with unsupported dependencies.
   ✅ Good: Run Node-only dependencies in Node runtime routes and keep Edge routes dependency-safe.

13. ❌ Bad: Blocking rendering on unrelated client-side effects.
   ✅ Good: Render server content first and run non-critical client effects after initial paint.

14. ❌ Bad: Ignoring SEO implications of route canonicalization.
   ✅ Good: Define canonical URLs and normalize route variants to prevent duplicate indexing.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Are server and client component boundaries intentional and minimal?
- [ ] Yes/No: Is shared data fetched once at route or layout level instead of duplicated?
- [ ] Yes/No: Is caching and revalidation policy explicit for changed routes?
- [ ] Yes/No: Are canonical, metadata, and hreflang rules centralized and consistent?
- [ ] Yes/No: Is runtime selection (Edge vs Node) compatible with imported dependencies?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Are hydration mismatch warnings absent in build and runtime logs?
- [ ] Yes/No: Are ISR, SSR, or SSG behaviors tested against required freshness windows?
- [ ] Yes/No: Is client bundle size verified against budget after the change?
- [ ] Yes/No: Do middleware and route-handler tests cover auth and cache behavior?
- [ ] Yes/No: Do SEO snapshot tests verify metadata and canonical tags on affected routes?

## Cross-References

- `frontend-rules.md` for shared UI architecture standards.
- `react-patterns.md` for hooks and composition inside client components.
- `performance-rules.md` for route and caching performance budgets.
- `seo-rules.md` for metadata and indexability policy.
- `accessibility-rules.md` for semantic and keyboard-safe UI behavior.
- `api-design-rules.md` for route handler contract consistency.

### Scenario Walkthroughs

- Scenario: Product page needs fresh inventory every 30 seconds.
  - Action: Keep page server-rendered with route-level revalidation tuned to inventory freshness.
  - Action: Add monitoring for response latency and cache hit rate after rollout.
- Scenario: Team accidentally marked entire app tree as client components.
  - Action: Move layout and non-interactive sections back to server components.
  - Action: Run bundle analyzer and set PR gate for client bundle size budget.
- Scenario: Edge route crashes due to Node-only dependency.
  - Action: Move route to Node runtime or replace dependency with Edge-compatible alternative.
  - Action: Add runtime compatibility check in CI for routes declared as Edge.

### Delivery Notes

- Keep this reference aligned with project conventions and postmortems.
- Update checklists when recurring defects reveal missing guardrails.
- Prefer incremental adoption over large risky rewrites.
