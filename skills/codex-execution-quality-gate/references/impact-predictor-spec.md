# Impact Predictor Spec

## Purpose

Predict blast radius before editing files by estimating direct and indirect dependents.

## When To Use

- Before refactoring shared models or interfaces.
- Before changing utility modules consumed in many places.
- Before touching routing, middleware, or entry-point code.

## How AI Uses It

1. Run `predict_impact.py` with intended target files.
2. Review direct and indirect dependents.
3. Surface affected tests and recommend verification scope before edits.

## Integration Behavior

- Trigger on `$impact` or "what will this affect".
- Prefer auto-run when changes involve `models`, `interfaces`, shared `utils`, or config files.
- Treat output as advisory (non-blocking) for planning and risk communication.

## Output Intent

- Provide quick blast-radius confidence before implementation.
- Help developers choose safer sequencing and test strategy.
