---
name: sprint-review
description: Inspect the increment, capture stakeholder feedback, and convert outcomes into backlog decisions.
---

# Sprint Review

## Lead

`product-owner`

## Support

`scrum-master`, delivery leads, `qa-engineer`, optional `ux-researcher`

## Time-Box

1 hour for a 2-week sprint.

## Steps

1. **State sprint goal:** Remind everyone what the sprint aimed to achieve.
2. **Demo tested increments only:** Show working software, not slides.
3. **Walk through each completed story:** Show the feature, explain the value.
4. **Capture stakeholder feedback:** Record reactions, questions, and requests.
5. **Separate accepted from future work:** Don't let feedback become immediate scope.
6. **Update backlog:** Convert feedback into new stories or adjust priorities.
7. **Review metrics:** Sprint velocity, burndown, any quality signals.
8. **Confirm release status:** Is this increment shippable? What's blocking release?

## Demo Script Template

For each completed story:

```markdown
### Story: [Story title]

**Value:** [Why this matters to users/business]

**Demo steps:**
1. [Action] → [Expected visible result]
2. [Action] → [Expected visible result]

**Technical notes:** [Brief architecture/implementation note if relevant]

**Known limitations:** [Any caveats for stakeholders]
```

## Feedback Capture Format

| # | Feedback | Source | Category | Action |
|---|---|---|---|---|
| 1 | "Can we filter by date?" | Stakeholder A | Feature request | → New story in backlog |
| 2 | "Loading feels slow" | QA | Performance | → Investigate in next sprint |
| 3 | "Great UX on the form" | UX Lead | Positive | → Note in retro |

**Categories:** Feature request, Bug, Performance, UX, Positive, Question

## Sprint Metrics to Share

| Metric | This Sprint | Previous | Trend |
|---|---|---|---|
| Stories completed | X / Y committed | A / B | ↑ / ↓ / → |
| Story points delivered | N | M | ↑ / ↓ / → |
| Bugs found in review | N | M | ↓ is good |
| Sprint goal met? | Yes / Partial / No | — | — |

## Deliverables

- Accepted increment list (what's done and approved)
- Feedback backlog (new stories from stakeholder feedback)
- Updated backlog priorities
- Follow-up actions assigned
- Release decision (if applicable)

## Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| Showing unfinished work | Only demo stories that meet DoD |
| Slide deck instead of live demo | Show working software |
| Feedback becomes instant commitment | Capture as backlog items, prioritize later |
| Skipping metrics review | Velocity trends reveal capacity patterns |
| No stakeholder attendance | Schedule in advance, share async recording if needed |
