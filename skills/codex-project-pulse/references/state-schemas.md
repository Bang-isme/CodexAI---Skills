# State Schemas

JSON schemas for all `.codex/pulse/` state files. These schemas define the persistent project state that powers the daily brief and autonomous decision-making.

## sprint-state.json

```json
{
  "sprint": {
    "name": "Sprint 3",
    "number": 3,
    "goal": "Complete checkout and payment flow",
    "start_date": "2026-04-14",
    "end_date": "2026-04-25",
    "status": "active"
  },

  "stories": [
    {
      "id": "AUTH-003",
      "title": "JWT refresh token rotation",
      "status": "done",
      "priority": "high",
      "points": 3,
      "owner": "@dev-a",
      "started_at": "2026-04-14",
      "completed_at": "2026-04-16",
      "verification": "npm test -- --grep 'refresh token' → 5/5 pass",
      "pr": "#42",
      "notes": ""
    },
    {
      "id": "PAY-001",
      "title": "Stripe checkout integration",
      "status": "blocked",
      "priority": "critical",
      "points": 5,
      "owner": "@dev-b",
      "started_at": "2026-04-17",
      "completed_at": null,
      "verification": null,
      "pr": null,
      "blocked_by": "Waiting for Stripe API key from team lead",
      "blocked_since": "2026-04-18",
      "notes": "UI ready, backend waiting on credentials"
    },
    {
      "id": "CART-005",
      "title": "Fix cart total rounding",
      "status": "in_progress",
      "priority": "medium",
      "points": 2,
      "owner": "@dev-a",
      "started_at": "2026-04-20",
      "completed_at": null,
      "verification": null,
      "pr": null,
      "notes": "Rounding issue with 3+ decimal currencies"
    }
  ],

  "metrics": {
    "total_points": 21,
    "completed_points": 8,
    "stories_total": 7,
    "stories_done": 3,
    "stories_in_progress": 2,
    "stories_blocked": 1,
    "stories_todo": 1
  },

  "velocity_history": [
    { "sprint": "Sprint 1", "planned": 15, "delivered": 13 },
    { "sprint": "Sprint 2", "planned": 18, "delivered": 17 }
  ]
}
```

### Story Status Values

| Status | Meaning | Transitions From | Transitions To |
|---|---|---|---|
| `todo` | Not started, in sprint backlog | — | `in_progress` |
| `in_progress` | Actively being worked on | `todo`, `blocked` | `in_review`, `blocked`, `done` |
| `in_review` | PR created, waiting for review | `in_progress` | `in_progress` (changes requested), `done` |
| `blocked` | Cannot proceed, external dependency | `in_progress`, `todo` | `in_progress` (unblocked) |
| `done` | Completed and verified | `in_review`, `in_progress` | — |
| `carried_over` | Not completed, moved to next sprint | any | — |

### Priority Values

| Priority | Score | Use When |
|---|---|---|
| `critical` | 100 | System broken, data loss, security vulnerability |
| `high` | 70 | Sprint goal dependency, deadline-bound |
| `medium` | 40 | Normal feature work |
| `low` | 10 | Nice-to-have, cleanup, minor improvements |

## priority-queue.json

```json
{
  "generated_at": "2026-04-21T09:00:00Z",
  "queue": [
    {
      "rank": 1,
      "id": "PAY-001",
      "title": "Unblock: Get Stripe API key",
      "type": "unblock",
      "score": 130,
      "reason": "Critical priority + dependency blocker. PAY-002 and PAY-003 depend on this.",
      "action": "Contact team lead for Stripe API key. If unavailable, create test-mode key.",
      "estimated_effort": "15 min"
    },
    {
      "rank": 2,
      "id": "CART-005",
      "title": "Continue: Fix cart rounding",
      "type": "continue",
      "score": 60,
      "reason": "In progress for 1 day. Medium priority, no blockers.",
      "action": "Complete rounding fix in src/utils/currency.ts. Write regression test.",
      "estimated_effort": "2h"
    },
    {
      "rank": 3,
      "id": "ORDER-002",
      "title": "Start: Order confirmation email",
      "type": "start",
      "score": 40,
      "reason": "Next story in backlog. No dependencies.",
      "action": "Set up Resend integration in src/services/email.ts.",
      "estimated_effort": "4h"
    }
  ]
}
```

### Queue Entry Types

| Type | Meaning | Icon |
|---|---|---|
| `unblock` | Remove a blocker — highest urgency | 🔴 |
| `fix` | Fix a bug or quality issue | 🔴 |
| `continue` | Resume in-progress work | 🟡 |
| `start` | Begin new work item | 🟢 |
| `review` | Review someone's PR or work | 🔵 |
| `quality` | Address tech debt or quality regression | ⚪ |

## blockers.json

```json
{
  "active_blockers": [
    {
      "id": "BLK-001",
      "story_id": "PAY-001",
      "description": "Waiting for Stripe API key from team lead",
      "created_at": "2026-04-18T10:00:00Z",
      "age_days": 3,
      "owner": "@dev-b",
      "escalation_contact": "@team-lead",
      "category": "external",
      "attempted_resolution": [
        { "date": "2026-04-18", "action": "Messaged team lead on Slack" },
        { "date": "2026-04-19", "action": "Followed up, no response" }
      ],
      "stale": true,
      "impact": "Blocks PAY-002 and PAY-003 (8 story points total)"
    }
  ],

  "resolved_blockers": [
    {
      "id": "BLK-000",
      "story_id": "AUTH-003",
      "description": "Redis not configured in dev environment",
      "created_at": "2026-04-14T10:00:00Z",
      "resolved_at": "2026-04-14T14:00:00Z",
      "resolution": "Added Redis to docker-compose.yml"
    }
  ]
}
```

### Blocker Categories

| Category | Meaning | Resolution Path |
|---|---|---|
| `external` | Waiting on external party (API key, access, approval) | Escalate to contact |
| `technical` | Technical problem blocking progress | Debug or pair-program |
| `knowledge` | Don't understand requirement or approach | Clarify with PO or architect |
| `dependency` | Waiting on another story to complete | Reprioritize or parallelize |
| `infrastructure` | CI, deploy, or environment issue | DevOps or self-fix |

### Stale Detection

A blocker becomes "stale" when:
- Age > 2 days for `external` or `dependency`
- Age > 1 day for `technical` or `knowledge`
- Age > 4 hours for `infrastructure`

Stale blockers get automatic escalation flag in daily brief.

## risk-register.json

```json
{
  "active_risks": [
    {
      "id": "RISK-001",
      "description": "Payment integration may not complete before demo deadline",
      "severity": "high",
      "probability": "medium",
      "impact": "Demo will show mock payment instead of real Stripe flow",
      "mitigation": "Prepare mock payment fallback demo. Prioritize PAY-001 unblocking.",
      "owner": "@dev-b",
      "created_at": "2026-04-18",
      "last_reviewed": "2026-04-21",
      "related_stories": ["PAY-001", "PAY-002", "PAY-003"],
      "status": "monitoring"
    }
  ],

  "resolved_risks": []
}
```

### Severity × Probability Matrix

```
              Probability
              Low    Medium    High
Severity  ┌────────┬──────────┬──────────┐
  High    │ 🟡 Med │ 🔴 High  │ 🔴 Crit  │
  Medium  │ 🟢 Low │ 🟡 Med   │ 🔴 High  │
  Low     │ 🟢 Low │ 🟢 Low   │ 🟡 Med   │
          └────────┴──────────┴──────────┘
```

### Risk Status Values

| Status | Meaning |
|---|---|
| `identified` | Newly logged, needs review |
| `monitoring` | Actively tracked, mitigation in place |
| `escalated` | Requires immediate attention |
| `resolved` | No longer a risk |
| `accepted` | Risk accepted with documented reasoning |

## milestones.json

```json
{
  "milestones": [
    {
      "id": "MS-001",
      "name": "Sprint 3 Demo",
      "date": "2026-04-25",
      "description": "Show checkout flow to stakeholders",
      "status": "upcoming",
      "days_remaining": 4,
      "dependencies": ["PAY-001", "PAY-002", "CART-005"],
      "readiness": "at_risk",
      "readiness_reason": "PAY-001 blocked, 4 days remaining"
    },
    {
      "id": "MS-002",
      "name": "MVP Launch",
      "date": "2026-05-15",
      "description": "First public release",
      "status": "upcoming",
      "days_remaining": 24,
      "dependencies": [],
      "readiness": "on_track",
      "readiness_reason": ""
    }
  ]
}
```

### Milestone Readiness Values

| Readiness | Condition | Icon |
|---|---|---|
| `on_track` | All dependencies progressing, time sufficient | 🟢 |
| `at_risk` | Some dependencies blocked or behind schedule | 🟡 |
| `critical` | Major dependency blocked, insufficient time | 🔴 |
| `completed` | Milestone achieved | ✅ |
| `missed` | Date passed, not completed | ❌ |

### Deadline Proximity Alerts

| Days Remaining | Alert Level | Action |
|---|---|---|
| > 14 | None | Normal work |
| 7-14 | 🟡 Mention | Include in brief |
| 3-7 | 🟡 Flag | Prioritize related stories |
| 1-3 | 🔴 Urgent | Escalate blockers, consider scope cut |
| 0 | 🔴 Due today | Final push or scope decision |
| < 0 | ❌ Overdue | Post-mortem trigger |

## File Lifecycle

```
$sprint-init
  → Creates sprint-state.json, priority-queue.json, blockers.json,
    risk-register.json, milestones.json (empty/initial)

$today / $pulse (daily)
  → Reads all files → generates daily-brief.md

$done / $wip / $block / $unblock (during day)
  → Updates sprint-state.json + priority-queue.json + blockers.json

$sprint-close
  → Calculates velocity → archives to .codex/pulse/archive/sprint-N/
  → Resets for next sprint
```
