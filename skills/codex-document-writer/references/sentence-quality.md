# Sentence Quality

Clear writing does not mean short writing. A sentence may be long when it carries one complete idea and the relationships between clauses are explicit.

## Core Pattern

Use this default shape:

```text
<Actor> <action> <object> so that <outcome>.
```

Examples:

- Good: `The release owner should run python skills/tests/smoke_test.py before publishing the changelog so the release note reflects verified behavior.`
- Weak: `Run checks to ensure quality.`

## Complete Meaning Checklist

A sentence is complete when it answers:

- Who or what is acting?
- What action happened or should happen?
- What object, file, system, reader, or process is affected?
- Why does it matter in this context?
- What changes after the action?

## Compact Detail

Use detail when it changes action or interpretation.

```text
Too vague: The report should be improved for clarity.
Better: The report should move the recommendation above the background section because the director only needs the decision, risk, and budget impact in the first read.
```

```text
Too long: The system has many issues that make it hard to maintain and should be improved by applying better practices.
Better: The system repeats validation logic in three services, so the next edit should extract the shared rule into one validator and add one regression test for each service.
```

## Paragraph Rule

Each paragraph should have one job:

- explain context
- state a decision
- prove a claim
- describe risk
- give an instruction

If a paragraph does two unrelated jobs, split it.

## Words To Replace

| Weak Wording | Better Wording |
| --- | --- |
| improve quality | name the quality dimension: accuracy, readability, reliability, latency |
| ensure | verify, enforce, block, require, test |
| optimize | reduce, remove, cache, compress, simplify |
| robust | name the failure it survives |
| user-friendly | name the user action that becomes easier |
| comprehensive | list the coverage boundary |

## Reader Effort Rule

Do not force the reader to infer the missing point.

```text
Weak: This approach is better for maintainability.
Better: This approach is easier to maintain because the routing rule lives in one file instead of being copied across three workflows.
```
