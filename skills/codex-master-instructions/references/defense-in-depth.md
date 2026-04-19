# Defense in Depth

> **Canonical reference:** See `codex-systematic-debugging/references/defense-in-depth.md` for the full version with 4-layer validation pattern and Python/TypeScript examples.

After fixing root cause, add validation at multiple layers to prevent recurrence.

## Quick Summary

| Layer | Purpose | Example |
|-------|---------|---------|
| **1. Entry Point** | Reject obviously invalid input | `if not path: raise ValueError(...)` |
| **2. Business Logic** | Ensure data makes sense for operation | Domain-specific checks |
| **3. Environment Guard** | Prevent dangerous ops in contexts | Block git init outside tmpdir in tests |
| **4. Debug Instrumentation** | Capture context for forensics | Stack trace logging before dangerous ops |

## Full Reference

For complete documentation including:
- Python and TypeScript code examples for each layer
- Why multiple layers are necessary
- Step-by-step application process

→ See `codex-systematic-debugging/references/defense-in-depth.md`
