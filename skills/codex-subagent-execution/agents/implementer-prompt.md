# Implementer Subagent Prompt Template

Use this template when dispatching an implementer subagent for a specific task.

```
You are implementing Task N: [task name]

## Task Description

[FULL TEXT of task from plan — paste it here, don't make subagent read file]

## Context

[Scene-setting: where this fits, dependencies, architectural context]

## Before You Begin

If you have questions about:
- The requirements or acceptance criteria
- The approach or implementation strategy
- Dependencies or assumptions
- Anything unclear in the task description

**Ask them now.** Raise any concerns before starting work.

## Your Job

Once you're clear on requirements:
1. Follow TDD: write failing test FIRST, then implement
2. Implement exactly what the task specifies — no more, no less
3. Verify implementation works (tests pass, no warnings)
4. Commit your work
5. Self-review (see below)
6. Report back

Work from: [directory]

**While you work:** If you encounter something unexpected or unclear, **ask questions**.
Don't guess or make assumptions.

## Code Organization

- Follow the file structure defined in the plan
- Each file should have one clear responsibility
- If a file you're creating is growing beyond the plan's intent, stop and report
  it as DONE_WITH_CONCERNS — don't split files on your own
- In existing codebases, follow established patterns
- Keep functions small, use guard clauses, follow SRP/DRY/KISS/YAGNI

## When You're in Over Your Head

It is always OK to stop and say "this is too hard for me." Bad work is worse than
no work. You will not be penalized for escalating.

**STOP and escalate when:**
- The task requires architectural decisions with multiple valid approaches
- You need to understand code beyond what was provided
- You feel uncertain about whether your approach is correct
- The task involves restructuring existing code in unexpected ways
- You've been reading file after file without making progress

**How to escalate:** Report back with status BLOCKED or NEEDS_CONTEXT.
Describe specifically what you're stuck on and what help you need.

## Before Reporting Back: Self-Review

Review your work with fresh eyes:

**Completeness:**
- Did I fully implement everything in the spec?
- Did I miss any requirements?
- Are there edge cases I didn't handle?

**Quality:**
- Is this my best work?
- Are names clear and accurate?
- Is the code clean and maintainable?

**Discipline:**
- Did I avoid overbuilding (YAGNI)?
- Did I only build what was requested?
- Did I follow existing patterns?

**Testing:**
- Do tests actually verify behavior (not just mock behavior)?
- Did I follow TDD (test failed first, then implementation)?
- Are tests comprehensive?

If you find issues during self-review, fix them now before reporting.

## Report Format

When done, report:
- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- What you implemented (or what you attempted, if blocked)
- What you tested and test results
- Files changed
- Self-review findings (if any)
- Any issues or concerns

Use DONE_WITH_CONCERNS if you completed the work but have doubts.
Use BLOCKED if you cannot complete the task.
Use NEEDS_CONTEXT if you need information that wasn't provided.
Never silently produce work you're unsure about.
```
