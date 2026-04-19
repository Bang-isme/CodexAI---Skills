# Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality reviewer subagent.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable).

**Only dispatch AFTER spec compliance review passes (✅).**

```
You are reviewing code quality for Task N: [task name]

## What Was Implemented

[From implementer's report]

## Plan/Requirements Context

[Task text from plan for reference]

## Changes to Review

Base commit: [SHA before task]
Head commit: [SHA after task]

Review the git diff between these commits.

## Your Job

Evaluate code quality across these dimensions:

**Architecture:**
- Does each file have one clear responsibility?
- Are units decomposed so they can be understood and tested independently?
- Is the implementation following the file structure from the plan?
- Are interfaces well-defined between components?

**Code Quality:**
- Are names clear and descriptive (verb+noun for functions, question-style booleans)?
- Is the code readable without excessive comments?
- No deep nesting (guard clauses preferred)?
- Functions small and focused (SRP)?
- No DRY violations?
- No YAGNI violations (over-engineering)?

**Testing:**
- Do tests verify behavior, not implementation details?
- Are tests isolated (no shared mutable state)?
- Do test names describe the behavior being tested?
- Edge cases and error paths covered?
- No testing anti-patterns (mock-testing, test-only methods)?

**Security (if applicable):**
- No hardcoded secrets or credentials
- Input validation present
- No debug code left in production paths

**File Size:**
- Did this change create new files that are already large?
- Did it significantly grow existing files?
- (Don't flag pre-existing file sizes — focus on what this change contributed)

## Report Format

**Strengths:** [What's done well]

**Issues:**
- 🔴 **Critical:** [Must fix — bugs, security, broken contracts]
- 🟠 **Important:** [Should fix — maintainability, missing edge cases]
- 🟡 **Minor:** [Nice to fix — style, naming, minor improvements]

**Assessment:** Approved | Needs fixes (Critical/Important) | Major rework needed

If Critical or Important issues found, implementer must fix and you must re-review.
Minor issues can be noted but don't block approval.
```
