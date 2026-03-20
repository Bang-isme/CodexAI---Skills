# Debugging And Recovery

## Anti-Rationalization Defense

**Core principle:** Violating the letter of the rules IS violating the spirit of the rules.

Common rationalizations that indicate process violation:

| Rationalization | Reality |
| --- | --- |
| "Too simple to need a plan" | Simple tasks are where unexamined assumptions waste the most work |
| "I'll test after" | Tests written after code pass immediately and prove nothing |
| "Already manually tested" | Ad-hoc is not systematic. No record, can't re-run |
| "Skip gate just this once" | No exceptions. Gate exists to catch what you missed |
| "Quick fix, investigate later" | Later never comes. Systematic is faster than thrashing |
| "I'm confident it works" | Confidence is not evidence. RUN the verification |
| "This is different because..." | It's not. Follow the process |
| "TDD/gate will slow me down" | Testing-first is faster than debugging after |

If you catch yourself thinking any of these, stop and follow the process.

## Error Recovery Protocol

When a helper script fails mid-workflow:

1. Read the JSON error output (`"status": "error"`, `"message": "..."`).
2. Classify the failure:

| Error Type | Action |
| --- | --- |
| Missing tool (`command not found`) | Run `$codex-doctor` or `$doctor` to diagnose and suggest install command |
| Permission denied | Report to user, do not retry |
| Git not available | Skip git-dependent steps and warn "reduced accuracy" |
| Network timeout | Retry once after 5s, then skip with warning |
| Parse or syntax error in project files | Report file and line, continue with other files |

3. Never silently swallow errors. Always surface them in conversation.
4. If 2+ scripts fail in the same workflow, pause and ask user before continuing.

## Systematic Debugging Protocol

**Iron Law: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

When encountering bugs, test failures, or unexpected behavior, follow these 4 phases in order:

### Phase 1: Root Cause Investigation (Before Any Fix)

1. Read error messages completely (stack trace, line numbers, error codes).
2. Reproduce consistently. Can you trigger it reliably?
3. Check recent changes (`git diff`, recent commits, new dependencies).
4. Trace data flow. Where does the bad value originate?

### Phase 2: Pattern Analysis

1. Find working examples of similar code in the codebase.
2. Compare working vs broken and list every difference.
3. Do not assume "that can't matter."

### Phase 3: Hypothesis And Testing

1. Form one hypothesis: "I think X causes Y because Z."
2. Make the smallest possible change to test it.
3. If it works, move to Phase 4. If it fails, form a new hypothesis.
4. Do not stack multiple fixes.

### Phase 4: Implementation

1. Write a failing test reproducing the bug.
2. Implement the single fix addressing root cause.
3. Verify the fix and check for regressions.

### 3-Fix Architecture Circuit Breaker

If 3+ fix attempts have failed:

- Stop. This is likely an architectural problem, not a code bug.
- Question fundamentals: is the pattern sound, or are we fighting inertia?
- Discuss with user before attempting more fixes.

### Red Flags: Stop And Return To Phase 1

- "Quick fix for now, investigate later"
- "Just try changing X and see"
- "I don't fully understand but this might work"
- Proposing solutions before tracing data flow

## Circuit Breaker Protocol

When `run_gate.py` returns `consecutive_failures >= 3`:

1. Halt execution. Do not attempt another automatic fix.
2. Read `.codex/decisions/` to check if a recent architectural change broke the tests.
3. Switch behavioral mode to `devils-advocate` and critically evaluate whether the foundational approach is wrong.
4. Present the user with two options:
   - "Continue debugging with a new approach"
   - "Revert the last commits and return to Planning phase"
5. Reset the counter only after the gate passes or the user explicitly requests `$reset-gate`.
