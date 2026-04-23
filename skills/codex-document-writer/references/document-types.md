# Document Types

Use the structure that matches the document's purpose. A good document removes guesswork: the reader should know why the document exists, what changed, what evidence supports it, and what action is expected.

## Decision Report

Use when the reader must approve, reject, or choose a direction.

```markdown
# <Decision Topic>

## Purpose
This report explains <decision needed> so <reader/audience> can <expected action>.

## Recommendation
Choose <option> because <primary reason tied to goal>.

## Context
- Current state: <what is true now>
- Constraint: <what cannot change>
- Success condition: <how the decision will be judged>

## Options
| Option | Benefit | Cost | Risk | Evidence |
| --- | --- | --- | --- | --- |
| <A> | <specific gain> | <specific cost> | <specific risk> | <file/data/source> |

## Risks And Mitigation
- Risk: <what could fail>. Mitigation: <concrete control>.

## Next Action
<Owner> should <action> by <date or checkpoint>.
```

## Technical Report

Use when the reader needs facts, implementation status, or verified findings.

```markdown
# <Technical Topic>

## Summary
<One paragraph with outcome, scope, and verified status.>

## Findings
| Finding | Evidence | Impact | Recommendation |
| --- | --- | --- | --- |
| <specific issue> | <command/file/log> | <effect> | <action> |

## Verification
- Command: `<exact command>`
- Result: <pass/fail/count/output summary>

## Limitations
- <What was not checked or cannot be concluded yet.>

## Next Steps
- <Concrete action with owner or trigger.>
```

## Business Memo

Use when the reader needs a concise update with implications.

```markdown
# <Memo Title>

## Situation
<What happened and why it matters now.>

## Impact
- Operational impact: <effect>
- Customer impact: <effect>
- Cost or timeline impact: <effect>

## Recommendation
<Action the team should take and why.>

## Open Questions
- <Question that changes the decision or timeline.>
```

## User Guide

Use when the reader must complete a task.

```markdown
# <Task Name>

## Before You Start
- Requirement: <tool/account/file>
- Expected result: <what success looks like>

## Steps
1. <Action verb + object + context.>
2. <Action verb + object + expected result.>

## Verify
- Check: <observable condition>
- If it fails: <next diagnostic action>

## Notes
- <Only include notes that prevent mistakes.>
```

## Session Handoff

Use when another person or future AI session must continue work.

```markdown
# Session Handoff

## Current State
<What is complete and what is still pending.>

## Changed Files
| File | Purpose |
| --- | --- |
| `<path>` | <why it changed> |

## Evidence
- `<command>` -> <result>

## Decisions
- <Decision and reason.>

## Risks
- <Risk and concrete follow-up.>

## Next Step
<The next person should do this first.>
```

## Executive Summary

Use when the reader needs the conclusion before details.

```markdown
# Executive Summary

## Bottom Line
<Decision, status, or recommendation in 2-3 sentences.>

## Why It Matters
<Business, user, technical, or operational impact.>

## Evidence
- <Measured result, file, command, or source.>

## Required Decision
<Approve, reject, defer, fund, assign, or monitor.>
```
