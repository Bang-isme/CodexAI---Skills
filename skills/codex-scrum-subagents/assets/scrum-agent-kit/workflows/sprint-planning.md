---
name: sprint-planning
description: Turn ready stories into a sprint goal, sprint backlog, ownership plan, and risk register.
---

# Sprint Planning

## Lead

`scrum-master`

## Support

`product-owner`, delivery specialists, optional `solution-architect`

## Time-Box

1-2 hours for a 2-week sprint.

## Steps

1. **Confirm sprint goal:** One sentence describing the sprint's primary outcome.
2. **Review velocity:** Check previous sprint's actual velocity for capacity planning.
3. **Select stories:** Pull from top of refined backlog. Only select stories marked "ready."
4. **Capacity check:** Compare total estimate vs available capacity (minus PTO, meetings, overhead).
5. **Assign ownership:** Assign lead for each story. Identify support roles.
6. **Capture dependencies:** Map inter-story and external dependencies.
7. **Identify risks:** Flag stories with high uncertainty or external blockers.
8. **Confirm verification:** Each story has clear acceptance criteria and verification approach.

## Capacity Planning

```
Available capacity = (team_size × sprint_days × hours_per_day) × focus_factor

Focus factor:
- New team / high meeting load: 0.5-0.6
- Established team: 0.7-0.8
- Experienced team, low overhead: 0.8-0.9
```

**Rule of thumb:** Don't commit to more than 80% of previous sprint's actual velocity.

## Sprint Goal Template

```markdown
**Sprint Goal:** By the end of Sprint [N], [target users] can [key capability],
enabling [business outcome].

**Success Metric:** [Measurable condition that proves the goal is met]
```

**Example:**
> Sprint Goal: By the end of Sprint 3, customers can complete checkout with Stripe payment, enabling revenue collection.
> Success Metric: E2E test passes for full purchase flow from cart to payment confirmation.

## Sprint Backlog Format

| Priority | Story | Points | Owner | Dependencies | Status |
|---|---|---|---|---|---|
| P1 | Stripe checkout integration | 5 | @dev-a | Stripe API key | Ready |
| P2 | Order confirmation email | 3 | @dev-b | Email service setup | Ready |
| P3 | Order history page | 2 | @dev-a | — | Ready |
| Buffer | Fix cart rounding bug | 1 | @dev-b | — | Ready |

## Deliverables

- Sprint goal statement
- Sprint backlog with ownership and estimates
- Dependency map
- Impediment / risk list
- Capacity calculation showing commitment is feasible

## Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| No sprint goal — just a list of stories | Always define one cohesive goal |
| Committing to 100%+ capacity | Leave 10-20% buffer for bugs and unexpected work |
| Selecting stories not marked "ready" | Send back to refinement first |
| Assigning all stories to one person | Distribute to build shared knowledge |
| No verification plan for stories | Each story needs testable acceptance criteria |
