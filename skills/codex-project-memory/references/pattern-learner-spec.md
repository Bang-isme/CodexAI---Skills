# Pattern Learner Spec

## Purpose

Analyze project conventions and coding patterns, then write `.codex/project-profile.json` so AI can match the codebase style before generating new code.

## When To Run

- At the start of a new project.
- When generated code keeps drifting from team conventions.
- After major architecture or style changes.

## How AI Uses It

1. Run `analyze_patterns.py`.
2. Read `.codex/project-profile.json` before implementation.
3. Match naming, imports, formatting, and dominant framework patterns from the profile.

## Update Frequency

- Re-run after significant folder structure changes.
- Re-run after migrations (framework, ORM, routing, auth).
- Re-run after style/lint rule changes.

## Override

Users can manually edit `.codex/project-profile.json` to enforce explicit team preferences.
