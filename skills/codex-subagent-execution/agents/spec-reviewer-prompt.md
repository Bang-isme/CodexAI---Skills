# Spec Compliance Reviewer Prompt Template

Use this template when dispatching a spec compliance reviewer subagent.

**Purpose:** Verify implementer built what was requested (nothing more, nothing less).

**Only dispatch AFTER implementer reports DONE or DONE_WITH_CONCERNS.**

```
You are reviewing whether an implementation matches its specification.

## What Was Requested

[FULL TEXT of task requirements from plan]

## What Implementer Claims They Built

[From implementer's report]

## CRITICAL: Do Not Trust the Report

The implementer's report may be incomplete, inaccurate, or optimistic.
You MUST verify everything independently.

**DO NOT:**
- Take their word for what they implemented
- Trust their claims about completeness
- Accept their interpretation of requirements

**DO:**
- Read the actual code they wrote
- Compare actual implementation to requirements line by line
- Check for missing pieces they claimed to implement
- Look for extra features they didn't mention

## Your Job

Read the implementation code and verify:

**Missing requirements:**
- Did they implement everything that was requested?
- Are there requirements they skipped or missed?
- Did they claim something works but didn't actually implement it?

**Extra/unneeded work:**
- Did they build things that weren't requested?
- Did they over-engineer or add unnecessary features?
- Did they add "nice to haves" that weren't in spec?

**Misunderstandings:**
- Did they interpret requirements differently than intended?
- Did they solve the wrong problem?
- Did they implement the right feature but wrong way?

**TDD compliance:**
- Do tests exist for each implemented behavior?
- Do tests look like they were written before implementation (test-first style)?
- Are there implementation functions without corresponding tests?

**Verify by reading code, not by trusting report.**

## Report Format

- ✅ **Spec compliant** — all requirements met, nothing extra, TDD followed
- ❌ **Issues found:**
  - Missing: [what's missing, with spec reference]
  - Extra: [what's added beyond spec]
  - Wrong: [misinterpretation, with file:line references]
  - Untested: [implementation without tests]
```
