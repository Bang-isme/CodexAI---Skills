---
name: backlog-refinement
description: Refine vague requests into sprint-ready stories with acceptance criteria, dependencies, and risk notes.
---

# Backlog Refinement

## Lead

`product-owner`

## Support

`scrum-master`, `solution-architect`, optional `ux-researcher`

## Time-Box

30-60 minutes per session. Refine enough stories for 1-2 sprints ahead.

## Steps

1. **Capture value:** Identify user problem, desired outcome, and business value.
2. **Split scope:** Break into story-sized increments using splitting techniques.
3. **Define acceptance criteria:** Write testable conditions using Given/When/Then or checklist format.
4. **Assess dependencies:** Identify technical dependencies, external blockers, and cross-team needs.
5. **Estimate effort:** Use relative sizing (S/M/L or story points) — not hours.
6. **Risk check:** Note risks, open questions, and unknowns that could block implementation.
7. **Ready decision:** Apply INVEST criteria to confirm story is sprint-ready.

## Story Splitting Techniques

| Technique | When to Use | Example |
|---|---|---|
| By workflow step | Feature has multiple user actions | "Add to cart" vs "Checkout" vs "Payment" |
| By data variation | Different data types need different handling | "Import CSV" vs "Import JSON" |
| By business rule | Complex rules can be delivered incrementally | "Basic discount" vs "Tiered discount" |
| By interface | Multiple UIs serve same backend | "Web form" vs "Mobile form" |
| By operation | CRUD operations are natural splits | "Create order" vs "Edit order" vs "Cancel order" |
| Spike first | High uncertainty needs research | "Spike: evaluate Stripe vs PayPal" → "Implement payment" |

## INVEST Criteria

| Criterion | Question | Red Flag |
|---|---|---|
| **I**ndependent | Can this be delivered without another story? | "Blocked by Story X" |
| **N**egotiable | Can scope be adjusted during sprint? | Rigid spec with no flexibility |
| **V**aluable | Does this deliver value to users or business? | "Refactor internals" with no user impact |
| **E**stimable | Can the team estimate effort? | "We don't know how this works yet" → spike first |
| **S**mall | Can this fit in one sprint? | Estimated > 50% of sprint capacity |
| **T**estable | Can we verify it's done? | No acceptance criteria defined |

## Acceptance Criteria Format

```markdown
### Story: As a [user], I want to [action] so that [benefit]

**Acceptance Criteria:**
- [ ] Given [precondition], when [action], then [expected result]
- [ ] Given [edge case], when [action], then [graceful handling]
- [ ] Performance: [action] completes in < [threshold]
- [ ] Error: When [failure], user sees [specific message]
```

## Deliverables

- Prioritized story packet with acceptance criteria
- Dependency notes and risk flags
- Ready / not-ready decision per story
- Spike stories created for high-uncertainty items

## Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| Stories without acceptance criteria | Never mark as "ready" without testable criteria |
| Refining stories during sprint | Refine 1-2 sprints ahead, not during implementation |
| Technical tasks disguised as stories | Reframe as user value or attach to a user-facing story |
| Skipping estimation | Even rough sizing prevents overcommitment |
