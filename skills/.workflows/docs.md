---
name: docs
trigger: $docs
loads: [codex-document-writer, codex-project-memory, codex-workflow-autopilot, codex-execution-quality-gate]
---

# Workflow Alias: $docs

## Trigger

Alias of `$handoff` for documentation-first work: guides, READMEs, and session transfer docs.

## Step Outline

Follow `.workflows/handoff.md` and load `codex-document-writer` when the user asked for a written deliverable.

## Exit Criteria

Same as `$handoff`, plus the requested document exists.
