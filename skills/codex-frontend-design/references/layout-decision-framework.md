# Layout Decision Framework & Spatial Mathematics

Use this framework to engineer a composition that fits the information architecture and user task. Compare structural options privately; present multiple options only when the user asks for alternatives (`studio`).

---

## 1. Start from Content Relationships

For each route or surface, list:
- **Primary Focal Anchor:** The single claim, workspace canvas, or primary action that must dominate the first 3 seconds.
- **Supporting Evidence / Context:** What proves the claim or informs the operator's action.
- **Secondary Controls & Navigation:** Filters, settings, or secondary actions that must stay quiet until needed.
- **Reading & Task Axis:** Identify what is sequential, parallel, comparable, hierarchical, or real-time. Layout geometry must make those relationships visible without relying on decorative borders or card chrome.

---

## 2. Structural Layout Mathematics Matrix

Select a structural candidate from real content relationships, then test it against `references/composition.md` and the incumbent system:

| Content / Task Relationship | Layout Structure & Column Ratio | CSS / Spatial Mathematics | Fit Signal |
| --- | --- | --- | --- |
| **User operates a dense tool (`operate`)** | Persistent App Shell + Split Workbench (`240px–280px` rail + `minmax(0, 1fr)` canvas + optional `360px` inspector) | `grid-template-columns: 260px minmax(0, 1fr);` local scroll regions, sticky table headers | Repeated operations need zero-shift orientation and high scan speed |
| **User compares choices or tiers** | Aligned Comparison Matrix or Asymmetric Recommendation Split (`4:4:4` with 1 elevated anchor or `5:7` configurator) | Shared horizontal row axes for attributes; `tabular-nums` for all figures | Differences are effortless to compare when corresponding facts share an axis |
| **User follows a multi-step sequence** | Stepper Rail + Focused Task Surface (`3:9` or `4:8` split) | `grid-template-columns: minmax(220px, 3fr) minmax(0, 9fr);` | Order, progress, and live validation change what the user does next |
| **User reads or evaluates evidence (`read`)** | Editorial Column + Margin/Evidence Track (`8:4` or `7:5` asymmetric split) | Body measure locked to `60ch–70ch`; sticky or adjacent proof figure | Reading rhythm and evidence proximity matter more than equal card widths |
| **Page sells one clear proposition (`persuade`)** | Claim-Led Asymmetric Hero (`7:5` or `6:6` bottom-aligned) + Live Product Proof | `grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.95fr);` | One claim and authentic product proof dominate the decision path |
| **User explores a heterogeneous collection** | Variable-Span Asymmetric Grid (`7+5` lead row, `4+4+4` secondary row) | `repeat(12, minmax(0, 1fr))` with intentional span hierarchy (`span 7`, `span 5`) | Items vary in importance; avoids monotonous "Bento Soup" |
| **User monitors changing telemetry** | KPI Summary Strip (no cards, divider-separated) + 1 Dominant Chart/Table (`8:4` with event stream) | Open summary strip at top; primary chart spans 8 cols, anomaly feed spans 4 cols | Current status, delta, and drill-down action are immediately locatable |

These are structural options, not mandatory templates. A single-column form or an open table with clean dividers often outperforms a complex grid.

---

## 3. Compare Before Committing

For at least two plausible structural candidates, ask:

1. Does it expose the primary task or claim first without visual competition?
2. Does it preserve the real hierarchy and grouping of the content?
3. Can realistic long labels, dense values, empty states, and errors fit using intrinsic sizing (`minmax(0, 1fr)` and `min-width: 0`) without clipping or horizontal overflow?
4. Does it remain understandable at tablet and phone widths (`320px–2560px`), including short landscape viewports?
5. Is it consistent with incumbent navigation and design tokens, or is a deliberate exception justified?

Choose the candidate with the clearest task flow and strongest content fit. State one composition thesis and a short rationale in the direction file or blueprint. Never change only the palette and call that a different layout.

---

## 4. Explore Creatively Without Losing the Layout (`Layout Contract`)

For a substantial visual or structural change, record a compact **layout contract** in the existing direction file or UX contract (do not create a separate document). Separate:

- **Must hold:** primary task and action, route/navigation behavior, content meaning and reading order, control semantics, data behavior, keyboard access, and product-specific elements users rely on.
- **Safe to explore:** grid geometry, column proportions, density, grouping, typographic scale, chart/data presentation, imagery, and surface treatment when the content and product purpose support the choice.

Choose one **signature move** that makes the product more recognizable or the task easier to understand. Name its expected user benefit and evidence. It can be a distinctive data composition, a stronger editorial hierarchy, a purposeful asymmetry, or a more useful navigation/workspace arrangement. Avoid novelty whose only benefit is looking different. Keep the established shell and familiar patterns around the new move when they help users stay oriented.

For the contract, state the desktop and narrow-screen content order; what may stack, collapse, or move; and how long labels, dense data, and media wrap, crop, or scroll. Derive breakpoints from the real styles and content fit. During exploration, vary one major layout decision at a time so a comparison can reveal what helped or hurt. Keep the best product-fit move and discard variants that weaken an invariant or fail at a target width.

Use this depth only for a substantial layout change. For a narrow refinement, make the smallest supported adjustment and record only a short rationale when needed.

---

## 5. Adapt and Customize

- Name tokens for semantic roles (`surface-canvas`, `surface-elevated`, `text-muted`, `action-primary`, `space-section`) rather than visual trends.
- Reuse components when behavior and hierarchy match; let width, span, density, and media differ when content relationships differ.
- Keep the approved direction stable through implementation; refine one observable issue at a time.
- If a user asks for alternatives (`studio`), make the directions structurally distinct: change content geometry, hierarchy, and navigation strategy, not just colors or corner radius.
