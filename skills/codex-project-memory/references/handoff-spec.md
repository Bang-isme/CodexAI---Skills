# Handoff Spec

## Purpose

Generate a portable handoff document that can be pasted into any AI assistant and provide enough project context to continue work without repeated discovery questions.

## When To Generate

- Before switching AI tools.
- Before onboarding a new teammate.
- Before asking for deep code review from an external assistant.

## How To Use

1. Run `generate_handoff.py`.
2. Open the generated `handoff.md`.
3. Copy the content into the next AI chat with the task request.

## Recommended Update Frequency

- Regenerate after major architecture changes.
- Regenerate after dependency migrations.
- Regenerate after large refactors or release branches.

## Privacy Note

Review the handoff before sharing. It can include sensitive details from config files, git history, or local project metadata.
