---
name: daily-scrum
description: Run a lightweight progress and blocker check that keeps sprint flow healthy.
---

# Daily Scrum

## Lead

`scrum-master`

## Support

All active sprint contributors

## Time-Box

15 minutes maximum. Stand-up format.

## Steps

1. **Progress check:** Each contributor reports: done since last standup, plan for today.
2. **Blocker surface:** Identify anything preventing progress — be specific.
3. **Dependency update:** Flag dependencies that changed or became urgent.
4. **Sprint board update:** Move cards to reflect actual state.
5. **Replan if needed:** If a blocker can't be resolved today, adjust sprint plan.

## Format

Each contributor answers (30-60 seconds each):

```
1. What I completed since last standup:
   - [specific deliverable or task]

2. What I'm working on today:
   - [specific task with expected outcome]

3. Blockers:
   - [blocker description + who can help]
   or
   - None
```

## Blocker Resolution Protocol

| Blocker Type | Action | Owner |
|---|---|---|
| Technical (need help with code) | Pair session after standup | Developer + helper |
| External (waiting on API, credentials) | Escalate immediately | Scrum Master |
| Knowledge (don't understand requirement) | Clarify with PO after standup | PO + developer |
| Infrastructure (CI broken, env down) | Fix or workaround within 2h | DevOps / team |

**Rule:** If a blocker persists > 1 day, it becomes an impediment and goes on the risk register.

## Async Daily Scrum (Remote Teams)

When synchronous standup isn't possible, post in team channel by 10:00 AM local time:

```
🟢 Done: [completed items]
🔄 Today: [planned items]
🔴 Blocked: [blockers] or None
```

## Deliverables

- Daily status captured (board updated)
- Blockers identified with owners
- Replan decisions documented (if any)
- Impediment log updated

## Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| Status report to manager | Peer-to-peer sync, not top-down reporting |
| Problem-solving during standup | Note the issue, schedule follow-up after standup |
| Exceeding 15 minutes | Each person: 60 seconds max. Details offline. |
| Skipping when "nothing changed" | Still sync — blockers emerge from brief check-ins |
| No board update | Update cards during or right after standup |
