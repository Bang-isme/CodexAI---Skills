# Mobile Rules

## Scope and Triggers

Use this reference when tasks target mobile apps, mobile web behavior, offline reliability, or platform-specific UX constraints.

Primary triggers:
- React Native, Flutter, iOS, Android, or cross-platform task keywords
- files in mobile app folders, navigation stacks, native bridges
- user complaints around startup lag, battery drain, offline bugs

Secondary triggers:
- backend contract changes affecting sync or mobile APIs
- push notification behavior and background processing updates
- cross-device rendering or input behavior regressions

Out of scope:
- desktop-only frontend work with no mobile path
- backend-only work without mobile consumption impact

## Core Principles

- Design for constrained network and battery conditions first.
- Keep startup path minimal and avoid heavy synchronous initialization.
- Prioritize predictable navigation and stable gesture behavior.
- Build touch targets and spacing for real-world thumb usage.
- Treat offline support as core reliability, not optional feature.
- Respect platform conventions instead of forcing one-platform behavior.
- Limit bridge crossings and expensive background tasks.
- Keep local persistence and sync conflict strategy explicit.
- Optimize perceived performance with progressive feedback.
- Include crash and performance telemetry by default.

## Decision Tree

### Decision Tree A: Data and Connectivity Strategy

- If user action must work offline, persist intent locally first.
- If operation is critical and conflict-prone, use explicit sync state machine.
- If data is read-heavy and stale-safe, cache with background refresh.
- If data is sensitive, use secure storage and encrypted at-rest policy.
- If sync can fail silently, expose status indicators and retry controls.
- If operation spans multiple resources, define conflict resolution policy.

### Decision Tree B: Platform and UX Matrix

| Scenario | Preferred Pattern | Avoid |
| --- | --- | --- |
| long list with mixed row heights | virtualized list with key extractor | full ScrollView rendering |
| complex navigation flow | explicit stack and route guards | implicit deep-link side effects |
| media-heavy feed | lazy image loading and placeholders | eager full-resolution decoding |
| unstable network | offline queue with retries | blocking UI until network recovers |
| sensitive auth screens | secure input and device-safe storage | plain-text tokens in local storage |
| background sync | bounded job scheduling | uncontrolled polling loops |

## Implementation Patterns

- Use navigation architecture that separates auth, onboarding, and main app flows.
- Keep feature modules isolated with clear boundary contracts.
- Use centralized network layer with retry/backoff and timeout policy.
- Store sync queue metadata with deterministic replay ordering.
- Track app lifecycle transitions for pause/resume safety.
- Use skeleton UI and partial rendering for slow data dependencies.
- Prefer cached read paths with stale-while-revalidate behavior.
- Minimize bridge calls by batching and reducing high-frequency chatter.
- Defer non-critical work after first meaningful paint.
- Instrument startup, screen transitions, and API latency metrics.
- Apply platform-specific UI conventions for Android and iOS differences.
- Handle permission prompts with clear pre-permission rationale screens.
- Use device capability checks before enabling heavy features.
- Add crash-safe persistence for in-progress user work.
- Provide explicit recovery actions for failed sync and auth refresh.

## Anti-Patterns

1. ❌ Bad: Loading full app data synchronously on launch.
   ✅ Good: Load critical startup data first and defer non-essential sync to background tasks.

2. ❌ Bad: Using non-virtualized lists for large dynamic data.
   ✅ Good: Use list virtualization (`FlatList`/RecyclerView) with windowing and stable keys.

3. ❌ Bad: Ignoring app lifecycle and background transition edge cases.
   ✅ Good: Handle foreground/background/resume transitions with persisted pending work state.

4. ❌ Bad: Running infinite polling loops in background tasks.
   ✅ Good: Schedule bounded background retries with exponential backoff and stop conditions.

5. ❌ Bad: Hardcoding platform behavior without feature checks.
   ✅ Good: Gate platform-specific behavior using capability checks and runtime platform APIs.

6. ❌ Bad: Storing auth tokens in insecure plain storage.
   ✅ Good: Store tokens in secure storage (Keychain/Keystore) with rotation and revocation support.

7. ❌ Bad: Designing interactions that require tiny tap targets.
   ✅ Good: Keep touch targets at least 44x44 points and ensure adequate spacing.

8. ❌ Bad: Blocking UI thread with heavy computation or parsing.
   ✅ Good: Move expensive parsing and computation to background workers or native modules.

9. ❌ Bad: Hiding offline failures without user-visible sync state.
   ✅ Good: Display offline state, queued actions, and explicit retry controls to users.

10. ❌ Bad: Mixing navigation and business logic in one file.
   ✅ Good: Keep navigation routes separate from business services and side-effect orchestration.

11. ❌ Bad: Ignoring battery impact of location or sensor listeners.
   ✅ Good: Throttle sensors and stop listeners when app is backgrounded or inactive.

12. ❌ Bad: Using network-only strategy for critical user actions.
   ✅ Good: Queue critical writes offline and reconcile when connectivity returns.

13. ❌ Bad: Handling conflicts with last-write-wins without policy review.
   ✅ Good: Implement deterministic conflict resolution rules and log manual-review conflicts.

14. ❌ Bad: Shipping push notification logic without opt-out controls.
   ✅ Good: Provide user-controlled notification preferences and enforce opt-out in client and backend.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Are lifecycle transitions (background, foreground, resume) explicitly handled?
- [ ] Yes/No: Is offline queue and conflict policy defined for critical write actions?
- [ ] Yes/No: Are platform-specific paths gated by capability checks instead of hardcoded assumptions?
- [ ] Yes/No: Is secure storage used for tokens and other sensitive data?
- [ ] Yes/No: Are battery and performance impacts considered for background sensors/tasks?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Are startup-time and interaction metrics within budget on low-end test devices?
- [ ] Yes/No: Are offline/online sync and conflict-resolution scenarios tested end-to-end?
- [ ] Yes/No: Are background task retry and stop conditions tested for stability?
- [ ] Yes/No: Are notification opt-in/out and deep-link routes verified on both platforms?
- [ ] Yes/No: Is battery usage profiled for features using location or sensor listeners?

## Cross-References

- `performance-rules.md` for startup and runtime budget policies.
- `testing-rules.md` for mobile unit, integration, and e2e strategy.
- `security-rules.md` for auth, storage, and transport hardening.
- `api-design-rules.md` for mobile-facing API contract stability.
- `backend-rules.md` for sync-safe service and idempotency design.
- `accessibility-rules.md` for assistive interaction requirements.

### Scenario Walkthroughs

- Scenario: Offline order submission creates duplicates after reconnect.
  - Action: Add client-generated idempotency keys and reconcile queued actions on reconnect.
  - Action: Add integration tests that replay reconnect events and assert single order creation.
- Scenario: Low-end Android devices freeze during feed load.
  - Action: Move JSON parsing to background thread and paginate initial payload.
  - Action: Profile frame drops before and after optimization on target low-end hardware.
- Scenario: Push notification opens wrong screen when app is cold-started.
  - Action: Normalize deep-link payload format and route through a single navigation resolver.
  - Action: Add cold-start notification tests for both Android and iOS.

### Delivery Notes

- Keep mobile telemetry dashboards segmented by platform and app version.
- Stage high-risk releases with phased rollout and rollback guardrails.
- Keep conflict resolution rules documented for support and QA teams.
- Align mobile API expectations with backend idempotency guarantees.

- Revalidate this domain checklist after each major release cycle.
- Capture one representative example per recurring issue class.
- Ensure cross-reference links stay consistent with routing table updates.
