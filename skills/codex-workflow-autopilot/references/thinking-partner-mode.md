# Thinking Partner Mode

## Purpose

Use this reference when the user wants collaborative reasoning before execution. The goal is to help the user choose a direction with explicit tradeoffs.

## Trigger Signals

- "think with me"
- "help me decide"
- "compare options"
- "what approach should we take"
- uncertainty about constraints, sequencing, or architecture choice

## Operating Protocol

1. Clarify decision boundaries.
2. List 2-4 realistic options (not theoretical options).
3. Evaluate each option against explicit criteria.
4. Recommend one option and explain why now.
5. Convert recommendation to an execution workflow.

## Clarifying Questions

- What is the main success metric for this task?
- What cannot be changed (constraints)?
- What is the acceptable risk level?
- What is the time budget?
- What is the rollback tolerance if the plan fails?

## Option Evaluation Matrix

| Option | Benefit | Risk | Cost | Time | Reversibility |
| --- | --- | --- | --- | --- | --- |
| A | what improves immediately | key failure mode | engineering effort | expected duration | easy/medium/hard |
| B | what improves immediately | key failure mode | engineering effort | expected duration | easy/medium/hard |
| C | what improves immediately | key failure mode | engineering effort | expected duration | easy/medium/hard |

## Decision Rules

- If requirements are ambiguous and risk is high, choose smallest reversible option.
- If risk is low and value is high, choose faster delivery path.
- If compatibility impact is broad, prefer additive rollout over replacement.
- If observability is weak, add verification steps before large changes.

## Output Contract

When this mode is active, respond with:

1. Decision summary (one paragraph)
2. Option matrix (compact)
3. Recommended option with rationale
4. Workflow steps generated from the selected option
5. Exit criteria and known risks

## Avoid

- Giving one option only.
- Repeating generic advice with no tradeoff math.
- Recommending irreversible high-risk changes without rollback path.
