# Multi-Screen Prototype Pipeline

Use this when the request spans a product flow, multiple routes, or coordinated interaction states. The output is a runnable prototype with reviewable design evidence, not a pile of disconnected screen mocks.

## Stage 1 — Product and users

Inspect the app, repository, user request, design references, and existing `.codex/design/` files. Record:

- primary user and the moment/task they are in;
- desired outcome and observable success signal;
- business/product constraints, existing patterns, and technical constraints;
- content facts, proof, and assets available;
- assumptions that could change layout or flow.

Ask only for missing facts that would materially change a decision. Do not invent customer quotes, metrics, product capabilities, or claims. Use realistic placeholder content and label it when facts are unavailable.

## Stage 2 — UX contract and coverage map

Create `.codex/design/surfaces/<slug>.md` using `../ux-contract.md`. Include a route and state table before coding:

| Route/state | User goal | Main action | Required content | Failure/empty/success behavior | Viewports |
| --- | --- | --- | --- | --- | --- |

Define the happy path and at least the failure or recovery paths that matter to task completion. For every interactive control, specify behavior, feedback, disabled/loading behavior, and keyboard operation. Capture all important states, but do not multiply decorative states with no product value.

Include realistic short and long content, navigation transitions, page titles/landmarks, focus order, responsive reflow, reduced-motion needs, and accessibility constraints. Avoid new visual decisions in this file.

## Stage 3 — One visual thesis and reusable system

Inspect incumbent tokens and note which ones remain authoritative. Compare at least two structural layout hypotheses against the route's content and user task, then choose one using `layout-decision-framework.md`. Write a concise direction file under `.codex/design/` (for example `DIRECTION.md`) containing:

- one sentence stating what the composition must prove;
- why its layout family and density fit the job and content;
- hierarchy, grid/spacing/type/color/material/motion tokens;
- responsive behavior and component grammar;
- image, icon, font, and reference provenance;
- intentional exceptions and their product rationale.

Choose one direction by default. Generate three alternatives only for an explicit request for options/new identity; compare meaningful layout and hierarchy decisions, then select one before implementation. Do not implement all directions or blend incompatible art directions.

## Stage 4 — Runnable prototype

Implement a small but complete vertical slice across the route map:

- navigation reaches each route and the main journey can be completed;
- controls work and show feedback;
- critical empty, loading, error, success, and permission states are represented where the product needs them;
- copy, tables, charts, and imagery use realistic ranges, including long text;
- design tokens and shared components express the chosen system without flattening meaningful route differences;
- layout reflows instead of merely shrinking; no essential task disappears at narrow or short viewports.

Prefer native controls and semantic structure. Preserve existing behavior and stack constraints. A prototype may use local/static data, but the main path must work and unavailable integrations must be clearly identified.

## Stage 5 — Two bounded review rounds

1. Run mechanical UI and accessibility checks and exercise the main flow.
2. Create the route × viewport × state capture manifest in `../responsive-evidence.md` and capture evidence.
3. Inspect each full-page stitched image and its original viewport slices. Record finding evidence by capture key.
4. Fix high-confidence defects first. For contextual pattern risks, apply the removal/product-job test in `anti-slop.md`.
5. Capture and review changes in a second round if needed. Stop after two inspect/fix rounds; report remaining issues with evidence.

Do not claim approval when any required route, state, width, segment, or review is missing. Missing browser support or images means `DEGRADED`. The browser exercise is CSS viewport emulation, not certification on physical devices.

## Stage 6 — Handoff dossier

Keep the design record small and project-specific:

- `.codex/design/surfaces/<slug>.md` — user and UX contract;
- `.codex/design/DIRECTION.md` (or the existing `DESIGN.md`) — thesis, tokens, component rules, provenance;
- `.codex/design/reviews/responsive/<run>/capture-manifest.json` and its image folder — responsive capture and review evidence.

Handoff the route/state coverage, how to run the prototype, chosen direction, assumptions, checks actually run, review status, known limits, and the exact evidence path. Do not duplicate the entire brief across files.
