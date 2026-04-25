# Skill Evolution Spec

## Purpose

Track which skills are used and how effective they are so the skill pack can be improved with real usage evidence instead of assumptions.

## When To Record

- After task completion, when context allows.
- After explicit skill invocations (`$rigor`, `$debug`, `$plan`, etc.).
- After notable partial or failed outcomes to capture improvement notes.
- When user corrects or overrides a skill's recommended behavior.

## Usage Record Schema

```json
{
  "record_id": "use-2026-04-25-001",
  "timestamp": "2026-04-25T14:30:00Z",
  "skill": "codex-reasoning-rigor",
  "invocation": "$rigor",
  "task_type": "architecture-decision",

  "outcome": "success",
  "effectiveness": 4,

  "context": {
    "project": "my-project",
    "task": "Choose between microservices vs monolith for MVP",
    "files_affected": 0,
    "duration_minutes": 15
  },

  "notes": "Decision matrix was useful. Evidence ladder pushed for Tier 3 verification which wasn't applicable for architecture decisions — could add guidance for non-code decisions.",

  "improvement_suggestion": "Add 'Architecture Decision' contract type to output-contracts.md for decisions that can't be verified with commands"
}
```

## Outcome Categories

| Outcome | Definition | Example |
|---|---|---|
| `success` | Skill produced useful, actionable output | Reasoning brief led to clear decision |
| `partial` | Useful but needed significant manual adjustment | Plan was good structure but wrong scope |
| `failure` | Skill output was rejected or rewritten entirely | Generated tests didn't match project patterns |
| `skipped` | Skill was activated but user bypassed it | User said "skip the brief, just do it" |
| `override` | User explicitly overrode skill recommendation | Skill said "use Redis", user chose in-memory cache |

## Effectiveness Scale

| Score | Meaning |
|---|---|
| 5 | Perfect — output used as-is |
| 4 | Good — minor adjustments needed |
| 3 | Adequate — significant but manageable rework |
| 2 | Poor — more work to fix than to redo |
| 1 | Harmful — output was misleading or wrong |

## Aggregate Report Schema

```json
{
  "period": "2026-04-01 to 2026-04-30",
  "total_invocations": 156,

  "by_skill": [
    {
      "skill": "codex-reasoning-rigor",
      "invocations": 28,
      "avg_effectiveness": 4.2,
      "success_rate": 0.89,
      "top_task_types": ["architecture-decision", "review", "debugging"],
      "improvement_themes": ["Needs non-code decision support"]
    },
    {
      "skill": "codex-test-driven-development",
      "invocations": 34,
      "avg_effectiveness": 3.8,
      "success_rate": 0.76,
      "top_task_types": ["unit-test", "integration-test", "regression"],
      "improvement_themes": ["Test pattern detection could be better", "Needs Playwright E2E support"]
    },
    {
      "skill": "codex-document-writer",
      "invocations": 22,
      "avg_effectiveness": 4.5,
      "success_rate": 0.95,
      "top_task_types": ["report", "README", "handoff"],
      "improvement_themes": []
    }
  ],

  "least_used_skills": [
    { "skill": "codex-git-worktrees", "invocations": 2 },
    { "skill": "codex-doc-renderer", "invocations": 3 }
  ],

  "most_improved": "codex-document-writer (3.2 → 4.5 over 3 months)",
  "needs_attention": "codex-test-driven-development (effectiveness trending down)",

  "recommendations": [
    "Add architecture decision contract to reasoning-rigor",
    "Improve test pattern detection for Playwright",
    "Consider merging git-worktrees into git-autopilot (low standalone usage)"
  ]
}
```

## When To Report

- Monthly (recommended).
- Before planning skill-pack upgrades.
- Before deprecating or promoting specific skills.
- When effectiveness for any skill drops below 3.0 average.

## How AI Uses It

1. Record usage outcomes via `track_skill_usage.py --record`.
2. Generate aggregate insights via `track_skill_usage.py --report`.
3. Prioritize updates for low-success or high-failure skills.
4. Flag unused skills for potential deprecation.
5. Cite usage data when proposing skill improvements: "Based on 28 invocations with 4.2 avg effectiveness..."

## Data Privacy

- Analytics data is local-only under `<skills-root>/.analytics/` by default.
- Users control retention and deletion of usage logs.
- No data is sent externally.
- Aggregate reports can be shared for skill-pack improvement discussions.
