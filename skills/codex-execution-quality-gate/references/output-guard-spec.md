# Output Guard Spec

`output_guard.py` evaluates whether a written deliverable is specific, evidence-backed, and structurally accountable enough to avoid generic model output.

## Use Cases

- review a generated plan, summary, or recommendation before sharing it
- catch filler language before declaring a task complete
- compare whether a response is grounded in real repo artifacts
- enforce higher output quality for high-stakes or repeated workflows

## Scoring Signals

Positive:

- exact file or artifact references
- commands or validation steps
- numbers, versions, or counts
- explicit sections for decision, evidence, risks, and next steps

Negative:

- filler phrases like "best practices" or "improve quality"
- no repo or artifact grounding
- no verification evidence
- weak structure that hides uncertainty

## Passing Guidance

A good pass result should usually include:

- at least one runnable command or validator invocation
- at least one concrete file, script, or identifier
- at least two structural signals such as decision plus evidence
- little or no filler language

The guard does not treat prose mentions such as "we should use git" or "python packaging matters" as verification evidence.
For evidence credit, the command should appear as a runnable snippet such as `python skills/tests/smoke_test.py` or on its own command line.

## Repo-Aware Grounding

When `--repo-root` is provided, the guard also checks whether:

- referenced file paths actually exist under that repo root
- path-like command arguments such as `python scripts/check.py` or `pytest skills/tests` point to real files or directories

This lets the guard catch deliverables that sound specific but reference stale or invented paths.

## Limitation

The script scores text heuristically. A pass is not proof of correctness.
Use it as a guardrail against generic wording, not as a replacement for real verification.
