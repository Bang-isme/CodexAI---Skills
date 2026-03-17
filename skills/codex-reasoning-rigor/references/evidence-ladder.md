# Evidence Ladder

Use stronger evidence whenever the task has meaningful cost, risk, or ambiguity.

## Weak

- intuition
- generic framework knowledge
- "this usually works"

## Medium

- repo file inspection
- command output from local tooling
- version and count comparisons
- existing patterns in nearby files

## Strong

- tests passing now
- validators passing now
- runtime checks or smoke checks
- diffs showing the intended change landed

## Rule

The bigger the change or the claim, the higher up the ladder the answer should climb.

- small wording fix: medium evidence may be enough
- workflow or release advice: medium plus monitoring signals
- "done", "fixed", "safe to ship": strong evidence required
