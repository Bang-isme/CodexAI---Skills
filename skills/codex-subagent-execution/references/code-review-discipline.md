# Code Review Reception Discipline

**Load this reference when:** receiving code review feedback, whether from a subagent reviewer, human reviewer, or external source.

## Overview

Code review requires technical evaluation, not emotional performance or blind agreement.

**Core principle:** Verify before implementing. Ask before assuming. Technical correctness over social comfort.

## The Response Pattern

```
WHEN receiving code review feedback:

1. READ: Complete feedback without reacting
2. UNDERSTAND: Restate requirement in own words (or ask)
3. VERIFY: Check against codebase reality
4. EVALUATE: Technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback
6. IMPLEMENT: One item at a time, test each
```

## Forbidden Responses

**NEVER:**
- "You're absolutely right!" — performative, not evidence-based
- "Great point!" / "Excellent feedback!" — sycophantic
- "Let me implement that now" — before verification

**INSTEAD:**
- Restate the technical requirement
- Ask clarifying questions
- Push back with technical reasoning if wrong
- Just start working (actions > words)

## Handling Unclear Feedback

```
IF any item is unclear:
  STOP — do not implement anything yet
  ASK for clarification on unclear items

WHY: Items may be related. Partial understanding = wrong implementation.
```

## Implementation Order

```
FOR multi-item feedback:
  1. Clarify anything unclear FIRST
  2. Then implement in this order:
     - Blocking issues (breaks, security)
     - Simple fixes (typos, imports)
     - Complex fixes (refactoring, logic)
  3. Test each fix individually
  4. Verify no regressions
```

## When To Push Back

Push back when:
- Suggestion breaks existing functionality
- Reviewer lacks full context
- Violates YAGNI (unused feature)
- Technically incorrect for this stack
- Conflicts with user's architectural decisions

**How to push back:**
- Use technical reasoning, not defensiveness
- Reference working tests/code
- Ask specific questions

## YAGNI Check

```
IF reviewer suggests "implementing properly" something:
  - Check: Is this feature actually used?
  - IF unused: "This isn't called anywhere. Remove it (YAGNI)?"
  - IF used: Then implement properly
```

## Acknowledging Correct Feedback

```
✅ "Fixed. [Brief description of what changed]"
✅ "Good catch — [specific issue]. Fixed in [location]."
✅ [Just fix it and show the change]

❌ "You're absolutely right!"
❌ "Great point!"
❌ "Thanks for catching that!"
❌ ANY gratitude expression without substance
```

## Gracefully Correcting Your Pushback

If you pushed back and were wrong:
```
✅ "Verified — you're correct. Implementing now."
❌ Long apology or over-explaining
```

State the correction factually and move on.

## Quick Reference

| Mistake | Fix |
|---------|-----|
| Performative agreement | State requirement or just act |
| Blind implementation | Verify against codebase first |
| Batch without testing | One at a time, test each |
| Assuming reviewer is right | Check if breaks things |
| Avoiding pushback | Technical correctness > comfort |
