# Root Cause Tracing

> **Canonical reference:** See `codex-systematic-debugging/references/root-cause-tracing.md` for the full version with backward tracing technique, test pollution bisection, and real examples.

Technique for tracing backward from symptom to source.

## Quick Summary

```
Found immediate cause → Can trace one level up?
  |- Yes → Trace backwards → Is this the source?
  |   |- No → Keep tracing
  |   `- Yes → Fix at source → Add validation at each layer
  |
  `- No → NEVER fix just the symptom
```

## The Key Principle

**NEVER fix just where the error appears.** Trace back to find the original trigger.

## Full Reference

For complete documentation including:
- 5-step tracing process
- Adding stack traces for instrumentation
- Finding test pollution with bisection
- Real-world example (empty projectDir bug)
- Tips for Python and TypeScript

→ See `codex-systematic-debugging/references/root-cause-tracing.md`
