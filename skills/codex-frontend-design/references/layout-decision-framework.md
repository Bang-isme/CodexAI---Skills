# Layout Decision Framework

Use this to find a composition that fits the information and task. It is a way to generate and compare layouts, not a gallery of styles to copy. Compare structural options privately; present several only when the user asks for alternatives.

## Start from content relationships

For each route, list the primary action/claim, the content that supports it, secondary tasks, and the expected reading/task order. Identify what is truly parallel, sequential, comparable, measurable, or exploratory. Layout should make those relationships visible without decoration doing the job of information architecture.

## Generate structural candidates

Choose candidates that reflect the content, then test them against `references/composition.md` and the existing product system:

| Content/task relationship | Layout structures to consider | Fit signal |
| --- | --- | --- |
| A user operates a dense tool | Persistent app shell with work area; split navigation/detail; table or list with a focused inspector | Repeated operations need stable orientation and scan speed |
| A user compares choices | Comparison table; aligned option columns with one recommended choice; attribute/value layout | Differences are easier to compare when corresponding facts share an axis |
| A user follows a sequence | Stepper plus focused task panel; timeline; vertical narrative with checkpoints | Order and progress change what the user should do next |
| A user reads or evaluates evidence | Editorial column with supporting media; asymmetrical text/evidence split; chart with nearby explanation | Reading order and evidence relationships matter more than equal card sizes |
| A page sells one clear proposition | Claim-led split with real product proof; full-width editorial section; offer and proof in a deliberate sequence | One claim and its proof dominate the decision path |
| A user explores a collection | Variable-span grid; filterable list with preview pane; grouped catalog | Items vary in importance or need rapid scanning/filtering |
| A user monitors changing data | Summary strip plus one dominant chart/table; timeline with event detail; status-first operations board | Current state, change, and response should be easy to locate |

These are options, not required patterns. A plain list, single-column form, or one strong image may be the most expressive and efficient structure.

## Compare before committing

For at least two plausible structural candidates, ask:

1. Does it expose the primary task or claim first?
2. Does it preserve the real hierarchy and grouping of the content?
3. Can realistic long labels, dense values, empty states, and errors fit without flattening everything into identical containers?
4. Does it remain understandable at tablet and phone widths, including short landscape viewports?
5. Is it consistent with incumbent navigation and design tokens, or is a deliberate exception justified?

Choose the one with the clearest task flow and strongest content fit. State one composition thesis and a short rationale in the direction file. Do not change only the palette and call that a different layout.

## Adapt and customize

- Name tokens for roles (`surface`, `text-muted`, `action-primary`, `space-section`) rather than visual trends.
- Reuse components when behavior and hierarchy match; let width, span, density, and media differ when content relationships differ.
- Keep the approved direction stable through implementation; refine one observable issue at a time.
- If a user asks for alternatives, make the directions structurally distinct: change content geometry, hierarchy, and navigation strategy, not just colors or corner radius.
