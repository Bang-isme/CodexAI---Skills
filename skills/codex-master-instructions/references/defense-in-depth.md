# Defense in Depth

After fixing root cause, add validation at multiple layers to prevent recurrence.

## The Pattern

1. Fix the ROOT CAUSE (Phase 4 of Systematic Debugging)
2. Then add defensive checks at EACH layer the bad value passed through:
   - Input validation at API boundary
   - Type assertion at function entry
   - Null guard before property access
   - Error message that explains WHAT went wrong

## Rule

- Defense in depth is SUPPLEMENTARY to root cause fix
- Never use it AS the fix (that's symptom treatment)
- Each layer should fail with a clear, actionable error message
