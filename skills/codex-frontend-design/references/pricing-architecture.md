# Pricing Architecture

Use this contract before drawing a pricing surface. Landing order stays in `landing-page-anatomy.md`. Spatial shells live in `patterns.md`. A price, limit, or savings figure must be source-matched to the offer. Do not invent a cheaper number to make a layout look original.

## Four pricing shapes

| Shape | When it fits | Constraint |
| --- | --- | --- |
| `three tier cards` | A small set of comparable packages | At most three peer plans, one of them highlighted |
| `usage/value slider` | Price or quota changes with a stated formula | One control, one visible result, and the arithmetic written next to the slider |
| `two-path split` | Self-serve versus a guided path | Two paths, not four peer cards. Both paths still answer the same five FAQ topics |
| `enterprise last-mile` | Procurement, invoicing, or a security review follows a normal plan choice | Peer plans stay at or below three. The enterprise path is the last mile, not a fourth peer card |

## Numeric rules

- At most `3` peer plans by default. A fourth peer plan fails unless the brief records why that plan is a real buying path (`peer_plan_exception`). An enterprise last-mile link is not a peer plan.
- Each plan shows `3–6` quota/limit rows and `3–6` included feature rows. Fewer rows hide the deal. More rows become a spreadsheet.
- Exactly one plan is the highlighted recommended plan.
- Monthly/annual billing is a real toggle. The annual state shows explicit savings math, such as `12 months for the price of 10 (save 17%)`. The word "save" without a number is not math.
- Every peer-plan CTA uses the identical action verb. `Start trial` and `Start team` match. `Start trial` and `Contact sales` do not. The enterprise last-mile may be a secondary link only when it is not presented as a peer plan.
- At `390px`, plans reflow to stacked cards. A horizontal-scrolling comparison table fails. Do not keep a wide matrix and expect the thumb to pan it.
- The pricing FAQ covers five topics: `refund policy`, `trial terms`, `cancellation behavior`, `seat/usage definition`, and `procurement/invoicing`. Missing one of them fails the contract.

## Indexing

Follow the landing indexing rule. An evergreen offer is indexable. A time-bound campaign is `noindex`. A campaign price page without `noindex` fails even when the plan math is valid.

## Mobile shape

```css
.pricing-plans {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
}

@media (max-width: 390px) {
  .pricing-plans {
    grid-template-columns: minmax(0, 1fr);
  }
}
```

The `390px` layout is stacked cards. It is not `overflow-x: auto` on a comparison table.
