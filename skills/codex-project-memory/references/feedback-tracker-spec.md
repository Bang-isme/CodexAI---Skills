# Feedback Tracker Spec

## Purpose

Track user fixes made on AI-generated code so future generations can avoid repeated mistakes.

## When To Log Feedback

- When user rewrites AI output for correctness.
- When user changes generated logic for edge cases or performance.
- When user enforces naming/style conventions AI missed.

## How AI Uses It

1. Run `track_feedback.py --aggregate` at the start of complex tasks.
2. Identify repeated categories (logic/style/security/etc.).
3. Apply lessons before generating new code, especially on files with frequent feedback.

## Privacy

- Feedback is stored locally in `<project-root>/.codex/feedback/`.
- Users control what gets logged and shared.

## Integration Behavior

- AI should propose feedback logging when it detects user corrections to generated code.
- AI should summarize recent feedback trends before major implementation phases.
