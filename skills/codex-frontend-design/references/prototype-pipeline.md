# Multi-Screen Prototype Pipeline

Use this when the request spans a product flow, multiple routes, or coordinated interaction states. The output is a runnable prototype with reviewable design evidence, not a pile of disconnected screen mocks.

## Stage 1 — Product and users

Inspect the relevant app surface and repository files, user request, design references, and existing `.codex/design/` files. For a new prototype, inspect the constraints and shared patterns it will use; do not audit unrelated product areas. When redesigning a working product broadly, follow `existing-product-audit.md` first and keep its product context, evidence, decisions, risks, and verification in the same scoped audit note. Record:

- primary user and the moment/task they are in;
- desired outcome and observable success signal;
- business/product constraints, existing patterns, and technical constraints;
- content facts, proof, and assets available;
- which in-scope flows are verified, incomplete, mocked, broken, or unknown, and what working behavior must be preserved;
- assumptions that could change layout or flow.

Ask only for missing facts that would materially change a decision. Do not invent customer quotes, metrics, product capabilities, or claims. Use realistic placeholder content and label it when facts are unavailable.

## Stage 2 — UX contract and coverage map

Create `.codex/design/surfaces/<slug>.md` using `../ux-contract.md`. Include a route and state table before coding:

| Route/state | User goal | Main action | Required content | Failure/empty/success behavior | Viewports |
| --- | --- | --- | --- | --- | --- |

Define the happy path and at least the failure or recovery paths that matter to task completion. For every interactive control, specify behavior, feedback, disabled/loading behavior, and keyboard operation. Capture all important states, but do not multiply decorative states with no product value.

For a content-led journey that benefits from staged understanding, add a compact **narrative beats** table to this same UX contract: beat/section, user question, content or proof, what the user learns or does, and the transition to the next beat. Use only relevant stages; a utility-heavy product follows its task and feedback sequence. Do not create a separate storyboard file or hide essential information behind a reveal.

Include realistic short and long content, navigation transitions, page titles/landmarks, focus order, responsive reflow, reduced-motion needs, and accessibility constraints. Avoid new visual decisions in this file.

## Stage 3 — One visual thesis and reusable system

Inspect incumbent tokens and note which ones remain authoritative. Compare at least two structural layout hypotheses against the route's content and user task, then choose one using `layout-decision-framework.md`. Write a concise direction file under `.codex/design/` (for example `DIRECTION.md`) containing:

- one sentence stating what the composition must prove;
- why its layout family and density fit the job and content;
- hierarchy, grid/spacing/type/color/material/motion tokens;
- responsive behavior and component grammar;
- image, icon, font, and reference provenance. For a custom asset, include its user-facing role, reason it improves the product, focal/safe area, intended rendered size/crop, responsive behavior, and fallback as described in `imagery.md`;
- intentional exceptions and their product rationale.

Keep asset decisions inside this direction file; do not create a separate asset inventory.

Choose one direction by default. Generate three alternatives only for an explicit request for options/new identity; compare meaningful layout and hierarchy decisions, then select one before implementation. Do not implement all directions or blend incompatible art directions.

## Stage 4 — Runnable prototype

Implement a small but complete vertical slice across the route map:

- navigation reaches each route and the main journey can be completed;
- controls work and show feedback;
- critical empty, loading, error, success, and permission states are represented where the product needs them;
- copy, tables, charts, and imagery use realistic ranges, including long text;
- design tokens and shared components express the chosen system without flattening meaningful route differences;
- route, feature, shared-component, and asset ownership follow the repository's existing structure. Promote code only when the prototype has a real shared behavior or consumer; do not reorganize the project scaffold just to impose an architecture template;
- custom assets, if justified, are integrated at their real component size with semantic content and interactions kept in the UI layer;
- layout reflows instead of merely shrinking; no essential task disappears at narrow or short viewports.

Prefer native controls and semantic structure. Preserve existing behavior and stack constraints. A prototype may use local/static data, but the main path must work and unavailable integrations must be clearly identified. Do not replace a working product integration with mock data merely to simplify the design.

## Stage 5 — Two bounded review rounds

1. Run mechanical UI and accessibility checks and exercise the main flow.
2. Create the route × viewport × state capture manifest in `../responsive-evidence.md` and capture evidence.
3. Inspect each full-page stitched image and its original viewport slices. Compare before and after at the same route, state, and viewport when baseline evidence exists. On each major route, check whether the first visual anchor, primary information/action, current location, and next step are clear. For a narrative journey, verify that each beat adds context or meaning and still makes sense after a quick scroll, a backward scroll, or a direct anchor jump; essential information must not depend on motion. Review first-time-user clarity, returning-user efficiency, relevant shared-component consumers, and contextual pattern risks. Record finding evidence by capture key.
4. Fix high-confidence defects first. For contextual pattern risks, apply the removal/product-job test in `anti-slop.md`.
5. Capture and review changes in a second round if needed. Stop after two inspect/fix rounds; report remaining issues with evidence.

Do not claim approval when any required route, state, width, segment, or review is missing. Missing browser support or images means `DEGRADED`. The browser exercise is CSS viewport emulation, not certification on physical devices.

## Stage 6 — Handoff dossier

Keep the design record small and project-specific. Use the three working artifacts below; for a broad redesign of an existing product, update one consolidated audit note in place. The UX contract is the source for route/state requirements, the direction file holds the visual thesis and tokens, the capture manifest records actual evidence, and the audit note tracks findings, decisions, risks, and verification by reference. Do not duplicate route/state details, tokens, or capture inventories across them. Do not create separate context, product-model, decision-log, TODO, and verification files for the same work:

- `.codex/design/surfaces/<slug>.md` — user and UX contract;
- `.codex/design/DIRECTION.md` (or the existing `DESIGN.md`) — thesis, tokens, component rules, provenance;
- `.codex/design/reviews/responsive/<run>/capture-manifest.json` and its image folder — responsive capture and review evidence.

Keep major decisions traceable in the audit note: state the observable problem, root-cause evidence, selected change and expected outcome, then record the actual outcome after verification. Include material regression risks, rollback, and shared consumers. For narrow tasks, keep the rationale in the handoff instead of creating an audit note.

When a deadline limits scope, timebox the baseline and implementation effort, prioritize the highest user-impact findings, and state what was deferred. Never imply complete review when required capture or inspection is missing; report the coverage gap as `DEGRADED`. Handoff route/state coverage, how to run the prototype, chosen direction, assumptions, checks actually run, review status, known limits, and the exact evidence path. Do not duplicate the entire brief across files.
