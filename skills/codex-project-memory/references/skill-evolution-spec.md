# Skill Evolution Spec

## Purpose

Track which skills are used and how effective they are so the skill pack can be improved with real usage evidence.

## When To Record

- After task completion, when context allows.
- After explicit skill invocations.
- After notable partial or failed outcomes to capture improvement notes.

## When To Report

- Monthly (recommended).
- Before planning skill-pack upgrades.
- Before deprecating or promoting specific skills.

## How AI Uses It

1. Record usage outcomes via `track_skill_usage.py --record`.
2. Generate aggregate insights via `track_skill_usage.py --report`.
3. Prioritize updates for low-success or high-failure skills.

## Data Privacy

- Analytics data is local-only under `<skills-root>/.analytics/` by default.
- Users control retention and deletion of usage logs.
