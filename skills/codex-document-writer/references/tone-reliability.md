# Tone And Reliability

Reliable writing is neither overconfident nor timid. It states what is known, what is inferred, and what still needs verification.

## Confidence Levels

| Confidence | Use When | Wording |
| --- | --- | --- |
| Verified | You ran a command, inspected a file, or have direct evidence | `Verified by <command/source>.` |
| Evidence-backed | You have strong artifacts but no final verification | `The available evidence supports <claim>.` |
| Inferred | You are reasoning from patterns or partial context | `This appears likely because <evidence>, but <gap> remains unchecked.` |
| Unknown | The information is missing | `This is not confirmed yet because <missing evidence>.` |

## Humble But Useful Wording

Use direct language without pretending certainty.

```text
Weak: This definitely fixes the issue.
Better: This change addresses the observed failure path. The fix is verified only after the regression test passes.
```

```text
Weak: Clearly, the best solution is to rewrite the module.
Better: The lower-risk path is to isolate the parser first because the current failure is limited to input normalization.
```

## Avoid Unsupported Absolutes

Do not use these unless evidence justifies them:

- definitely
- guaranteed
- always
- never
- obviously
- clearly
- perfect
- complete
- no risk

## Evidence Phrases

Use these when the document needs credibility:

- `Verified by: <command/source/result>.`
- `Evidence: <file/log/data point>.`
- `Not verified: <missing check>.`
- `Assumption: <condition that must be true>.`
- `Risk if wrong: <consequence>.`
- `Next verification: <command or review step>.`

## Accountability Tone

Prefer accountable sentences:

```text
Good: The team should keep the old endpoint for one release because mobile clients may still call it.
Weak: It may be useful to consider keeping compatibility.
```

```text
Good: The report should state the cost impact before the technical background.
Weak: The report could maybe be reorganized a little.
```
