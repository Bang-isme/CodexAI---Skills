# Editorial Review Spec

## Purpose

Evaluate whether a written deliverable reads like a decision-ready engineering artifact rather than generic AI-safe prose.

This check complements `output_guard.py`:

- `output_guard.py` asks: "Is this grounded and specific enough?"
- `editorial_review.py` asks: "Does this read like a human-made, accountable deliverable?"

## What It Scores

The rubric is split into 5 dimensions:

1. `decision_clarity`
   - names the chosen path, verdict, or current state
   - does not hide the recommendation behind vague framing

2. `grounding`
   - cites real files, scripts, commands, identifiers, or counts
   - rewards repo-grounded evidence when `--repo-root` is provided

3. `tradeoff_awareness`
   - names risks, blast radius, rollback, blockers, or follow-up actions
   - treats uncertainty as an explicit engineering surface

4. `structure`
   - is easy to scan under time pressure
   - uses short sections, bullets, or headings instead of one large wall of text

5. `editorial_tone`
   - penalizes AI-safe phrasing, hedging, and meta framing
   - rewards direct, confident, accountable writing

## Hard-Fail Conditions

Editorial review should fail when:

- score is below threshold
- strict deliverables (`plan`, `review`, `handoff`) do not clearly name the decision surface
- grounding is too weak to support trust

## Why This Exists

Many weak outputs can pass a genericity check but still read like:

- a model summary instead of a recommendation
- a polished paragraph without accountability
- a checklist with no owner, no tradeoff, and no real judgment

Editorial review exists to push the pack toward:

- stronger engineering judgment
- better handoffs
- less interchangeable "AI voice"
- more human-quality deliverables under repeated use
