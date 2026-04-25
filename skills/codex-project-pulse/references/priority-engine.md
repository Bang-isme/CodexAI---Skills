# Priority Engine

Rules for calculating, ordering, and maintaining the priority queue that tells the agent what to work on next.

## Priority Score Formula

```
final_score = base_score + modifiers

base_score = story_priority_score
modifiers  = urgency_bonus + dependency_bonus + deadline_bonus 
           + quality_bonus + blocker_penalty + staleness_bonus
```

### Base Scores

| Priority Level | Base Score | When to Assign |
|---|---|---|
| `critical` | 100 | Production broken, data loss, security breach |
| `high` | 70 | Sprint goal dependency, customer-facing blocker |
| `medium` | 40 | Normal feature work within sprint commitment |
| `low` | 10 | Cleanup, nice-to-have, stretch goals |

### Modifiers

| Modifier | Condition | Score Change | Rationale |
|---|---|---|---|
| **Dependency bonus** | Other stories depend on this completing | +30 | Unblocks downstream work |
| **Deadline bonus (urgent)** | Related milestone < 3 days | +40 | Time pressure |
| **Deadline bonus (approaching)** | Related milestone < 7 days | +20 | Upcoming pressure |
| **Deadline bonus (normal)** | Related milestone < 14 days | +10 | Awareness |
| **Quality regression** | Test failures or critical debt introduced | +35 | Quality before features |
| **Staleness bonus** | WIP > 3 days without progress | +20 | Avoid stale work |
| **Blocker penalty** | Story is currently blocked | -50 | Don't schedule blocked work |
| **Review waiting** | PR open > 24h without review | +15 | Unblock review pipeline |

### Score Examples

```
PAY-001 (critical, blocked, deadline 4d):
  base: 100 + deadline(+20) + blocker(-50) = 70
  → But blocker itself gets score:
  UNBLOCK-PAY-001: 100 + dependency(+30) + deadline(+20) = 150 → TOP PRIORITY

CART-005 (medium, in_progress, no deadline):
  base: 40 + staleness(0, only 1 day) = 40

ORDER-002 (medium, todo, no dependency):
  base: 40 = 40
```

## Queue Generation Algorithm

```
function generateQueue(sprint_state, blockers, risks, milestones):
  queue = []

  # Step 1: Add unblock tasks for active blockers
  for blocker in blockers.active:
    queue.add({
      type: "unblock",
      id: blocker.story_id,
      score: calculate_unblock_score(blocker, milestones),
      action: suggest_unblock_action(blocker)
    })

  # Step 2: Add quality fixes if quality is degrading
  quality = check_quality_signals()
  if quality.test_failures > 0:
    queue.add({ type: "fix", score: 135, action: "Fix failing tests before new work" })
  if quality.critical_security > 0:
    queue.add({ type: "fix", score: 150, action: "Fix critical security finding" })

  # Step 3: Add in-progress stories (continue work)
  for story in sprint_state.stories where status == "in_progress":
    queue.add({
      type: "continue",
      id: story.id,
      score: calculate_story_score(story, milestones)
    })

  # Step 4: Add in-review stories (review waiting)
  for story in sprint_state.stories where status == "in_review":
    queue.add({
      type: "review",
      id: story.id,
      score: story.base_score + 15  # review bonus
    })

  # Step 5: Add todo stories (start new work)
  for story in sprint_state.stories where status == "todo":
    queue.add({
      type: "start",
      id: story.id,
      score: calculate_story_score(story, milestones)
    })

  # Step 6: Sort by score descending
  queue.sort(by: score, descending)

  # Step 7: Apply WIP limit
  wip_count = count(queue where type in ["continue", "start"] and not blocked)
  if wip_count > 3:
    warn("WIP limit: consider finishing in-progress before starting new")

  return queue
```

## WIP (Work-In-Progress) Limits

| Team Size | Recommended WIP Limit | Rationale |
|---|---|---|
| 1 person | 2 stories max | Focus prevents context switching |
| 2-3 people | 3-4 stories max | Some parallelism, but finish before starting |
| 4+ people | N stories (1 per person + 1 buffer) | Buffer for blocked items |

**Hard rule:** If WIP > limit, the priority queue should NOT recommend starting new stories. Instead, it should recommend finishing or unblocking existing work.

## Reordering Rules

Users can override the calculated order with `$priority reorder`:

```
$priority reorder
> Current queue:
> 1. UNBLOCK PAY-001 (score: 150)
> 2. CONTINUE CART-005 (score: 40)
> 3. START ORDER-002 (score: 40)
>
> Enter new order (comma-separated IDs) or 'keep':
> PAY-001, ORDER-002, CART-005
```

Manual overrides are recorded with timestamp and reason:

```json
{
  "override": {
    "timestamp": "2026-04-21T09:30:00Z",
    "previous_order": ["PAY-001", "CART-005", "ORDER-002"],
    "new_order": ["PAY-001", "ORDER-002", "CART-005"],
    "reason": "User: ORDER-002 has customer demo dependency"
  }
}
```

## Priority Queue Refresh

The queue should be regenerated:

| Event | Action |
|---|---|
| `$today` / `$pulse` | Full regeneration |
| `$done <id>` | Remove from queue, recalculate |
| `$block <id>` | Add blocker penalty, add unblock task |
| `$unblock <id>` | Remove blocker penalty, remove unblock task |
| `$milestone` added/changed | Recalculate deadline bonuses |
| Quality regression detected | Add quality fix task |

## Special Queue Items

### Morning First Task

The first item in the queue gets special treatment:

```markdown
## 🎯 Start Here

**[UNBLOCK PAY-001]** — Contact @team-lead for Stripe API key

Why this first: PAY-001 has been blocked 3 days. PAY-002 and PAY-003 depend on it 
(8 story points). Sprint demo deadline in 4 days.

Estimated time: 15 minutes
Then move to: CART-005 (continue rounding fix)
```

### End-of-Day Review

Before session end, if `$today` ran that morning, suggest:

```markdown
## 📝 End-of-Day Check

- [ ] Did you complete today's #1 priority?
- [ ] Any new blockers to log? ($block)
- [ ] Any stories to mark done? ($done)
- [ ] Any new risks identified? ($risk)
- [ ] Generate session summary? ($session-summary)
```

## Decision: What If No Sprint Exists?

If `.codex/pulse/sprint-state.json` doesn't exist, priority engine operates in **kanban mode**:

1. Read recent git activity for project awareness
2. Check for TODO/FIXME annotations
3. Run quality signals
4. Present project health without sprint framing
5. Suggest: "Would you like to initialize sprint tracking? Use `$sprint-init`"

This ensures `$today` always produces useful output, even without formal sprint management.
