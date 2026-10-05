# Existing Product Audit and Redesign

Use this workflow when the user asks for a broad redesign, UX/quality audit, or substantial improvement to a working product. It distills a reusable audit process; it is not a checklist that every UI task must complete.

## Match the audit to the request

- For one component or page, inspect that surface, its nearby consumers, and the behavior the change can affect. Do not audit the whole application or create a dossier for a narrow change.
- For a new page or prototype, inspect the relevant product constraints and incumbent design authority. Do not audit unrelated routes.
- For a cross-route or product-wide improvement, map the affected routes and shared components before proposing broad changes.

Ask only for missing information that could change the product decision. Mark assumptions that affect user goals, content, or behavior; do not invent product facts, capabilities, analytics, or customer evidence.

For deadline-driven work, timebox the baseline to affected routes and shared consumers, then prioritize by user harm and how widely a fix helps. Defer lower-priority scope explicitly when the deadline requires it; a short deadline is not a reason to skip the minimum baseline needed to preserve working behavior or to mark incomplete evidence as approved.

## Establish a baseline

Inspect the relevant routes, source, shared components, tokens, assets, tests, and project run commands. Follow the actual user journey where possible. Record what is working and classify relevant behavior as **verified**, **incomplete**, **mocked**, **broken**, or **unknown**. Treat project docs and references as evidence to confirm against the implementation, not proof by themselves.

For each material finding, record enough to trace a decision:

| Field | What to record |
| --- | --- |
| Priority | P0 critical, P1 primary journey, P2 repeated friction, or P3 polish; adapt to product risk |
| Evidence | Route, state, viewport/capture key, interaction, source location, or reproducible check |
| Observed symptom | What actually happened or appeared |
| Root cause | Confirmed cause or a clearly labeled hypothesis |
| User impact | Which task or user is affected and how |
| Change and verification | Smallest coherent correction and how its outcome will be checked |
| Status | Fixed and verified, implemented but unverified, accepted with product rationale, open, or deferred |

Do not promote a visual hunch, source-pattern match, or untested assumption into a confirmed defect. Use `anti-slop.md` for the contextual design test.

For broad work that needs persistent state, keep a **single consolidated note** at `.codex/design/reviews/<slug>-audit.md`. Use it for:

- scope, product model, constraints, and **confirmed / assumed / unknown** facts;
- the prioritized findings ledger above, including a root-cause class where useful (content, information architecture, visual hierarchy, interaction, responsive, accessibility, performance, state, component/design system, motion, or assets);
- major decisions, rejected alternatives, expected outcome, and actual outcome;
- material dependencies, regression risk and rollback, mitigation, and ordered next actions;
- verification and regression matrix: affected route/consumer, check performed, result, and evidence.

Update that note across the work. Keep using the repository's existing `.codex/design/` contract, direction, and capture locations; do not split the same working state into separate `CONTEXT.md`, `PRODUCT_MODEL.md`, `DECISION_LOG.md`, `TODO.md`, and verification files. Link to the UX contract, direction, and capture manifest instead of copying their route/state table, tokens, or capture inventory into the audit note. Reuse an established project convention if one already exists. A narrow issue can keep its concise findings in the handoff without creating a note.

## Diagnose and choose a direction

Audit only the categories that can affect the requested scope:

- Product purpose, information architecture, discoverability, and critical task steps.
- Visual hierarchy, content fit, consistency, and product-specific identity.
- Control behavior, feedback, validation, recovery, and meaningful UI states.
- Responsive composition, keyboard/touch operation, and relevant accessibility barriers.
- Frontend architecture, route/state regressions, or performance only when evidence shows they affect this experience or can be measured in the available environment.

Prioritize user harm and dependencies before polish. Fix a confirmed root cause instead of restyling its symptom. For each major area, choose **KEEP** when it is working, **REFINE** when the idea fits but execution does not, **RECOMPOSE** when hierarchy or flow is the cause, and **REBUILD** only when evidence shows the current approach cannot support the job. Preserve strengths, valid behavior, and the existing identity unless evidence shows they are causing the problem.

Before a major refactor or new dependency, state the observable problem and outcome, why the current approach is insufficient, affected consumers, regression risk, rollback path, and verification. For a dependency, add its purpose, alternatives, and tradeoff to the audit note. Prefer the simplest change that resolves the root cause; reduce scope if the justification is weak. Separate data, state, presentation, and behavior only where it improves clarity. Reuse components when consumers need consistent behavior; avoid both duplicate implementations and abstractions that merely add configuration.

For a substantive layout change, write one product-specific composition thesis and identify a small set of product-fit identity anchors (for example, information geometry, typography, imagery, interaction, data presentation, or motion). Compare structural candidates when that helps explain the choice. Do not require multiple directions, a new design system, or new abstractions for routine work.

## Implement without hollowing out the product

Keep existing routes, API contracts, authentication boundaries, data flow, and successful workflows unless the requested change specifically requires an evidenced change. Identify consumers of shared components before changing them, then include those consumers in regression review.

Do not replace functioning integrations or real content with static demo data just to make a screen easier to style. When a prototype must use mocked data or unavailable services, label that boundary and do not describe it as verified end-to-end behavior. Give each visible control a real outcome or present it as unavailable; cover loading, empty, error, success, and disabled states where the product needs them.

Reuse the stack and abstractions that fit. Add dependencies, tokens, or shared components only when repeated product needs justify them. Keep shared interaction states coherent across consumers. Keep motion purposeful, interruptible, and compatible with reduced-motion settings; advanced effects need a product job, not novelty. See `motion.md` and `component-states.md` for detailed interaction guidance.

## Verify and refine

Use project-native lint, type, test, and build commands that exist and apply to the changed behavior. Exercise the critical affected flow and relevant failure/recovery states. Where relevant and reproducible, include slow loading, failed requests, empty or invalid data, long content, missing assets, repeated actions, resize, or route changes during motion. Use only states that matter to the product; do not invent state requirements.

For substantial UI, run `codex-visual-quality-gate` and inspect the actual captures; source checks alone cannot verify appearance. Compare before and after at the same route, state, and viewport when baseline captures exist. On each major route, check whether the first visual anchor, primary information/action, current location, and next step are clear. Review both first-time understanding and repeat-task efficiency where those users exist. Review changed routes and shared consumers at target responsive widths. Make performance or accessibility claims only to the extent the corresponding checks were actually performed.

Review from the perspectives relevant to the finding: product fit, a first-time user's understanding, a returning user's task efficiency, visual/interaction craft, implementation maintainability, keyboard and assistive-technology use, and regression risk. Every finding must point to observable evidence and a user consequence; do not manufacture review comments to fill out a role list.

At each iteration, take the highest-priority unresolved finding, make the smallest coherent change, re-run its verification, inspect affected consumers, and update the expected versus actual outcome in the same audit note. Continue while meaningful, actionable issues remain within scope and available tools; stop when P0 issues are fixed or clearly blocked, P1 issues are fixed or justified, and remaining work is lower value or out of scope. Do not create artificial work to keep iterating. For substantial visual work, allow at most two capture-based inspect/fix rounds; unresolved findings remain explicit rather than being declared approved.

When blocked by unavailable backend, assets, credentials, browser tooling, or unclear product behavior, record the blocker and what it prevents, continue unaffected work safely, and avoid a workaround that changes product semantics. Ask the user only when competing interpretations have materially different consequences or business behavior cannot be inferred safely.

## Handoff

Summarize the initial problem and root cause, the choices and files changed, what was preserved, checks actually run, regression checks, findings by status, and remaining risks or limitations. Keep **fixed and verified**, **implemented but unverified**, **mocked**, **blocked**, and **deferred** distinct. Do not claim the page merely “looks modern,” a build succeeded, or a screenshot looks good as proof of product quality. Link the relevant contract, audit note, or capture manifest when one exists.
