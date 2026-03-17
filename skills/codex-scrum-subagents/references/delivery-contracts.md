# Delivery Contracts

Use these contracts so work can move cleanly from planning to implementation to release.

## Definition of Ready

A story is ready when all of these are true:

- user value is clear in one sentence
- acceptance criteria are testable
- dependencies are named
- affected domains are known
- security or compliance concerns are called out
- the likely verification path is known

## Definition of Done

A story is done when all of these are true:

- implementation matches acceptance criteria
- relevant tests or checks were executed
- known risks are documented
- docs impact was reviewed
- rollback or mitigation is understood
- Product Owner accepts the outcome or explicitly defers acceptance

## Handoff Matrix

| From | To | Handoff Artifact |
| --- | --- | --- |
| `product-owner` | `scrum-master` | prioritized story with acceptance criteria and business context |
| `scrum-master` | delivery specialists | sprint goal, scope boundaries, dependency notes |
| `solution-architect` | delivery specialists | architecture notes, module boundaries, trade-offs |
| delivery specialist | `qa-engineer` | changed areas, expected behavior, edge cases |
| delivery specialist | `security-engineer` | security-sensitive surfaces, assumptions, secret handling |
| `qa-engineer` + `security-engineer` | `devops-engineer` | ship blockers, test evidence, release conditions |
| `devops-engineer` | `product-owner` + `scrum-master` | release result, rollback status, follow-up actions |

## Story Packet Template

Use a lightweight packet with these fields:

1. `story_id`
2. `goal`
3. `acceptance_criteria`
4. `scope_in`
5. `scope_out`
6. `dependencies`
7. `verification`
8. `risks`
9. `owner`

## Anti-Drift Rules

- Do not hand off raw intuition without a written artifact.
- Do not mark a story ready if verification is unknown.
- Do not mark a story done if review evidence is missing.
- Do not let the Scrum Master absorb Product Owner decisions or technical design ownership.
