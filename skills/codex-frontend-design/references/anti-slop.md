# Contextual UI Quality Audit

This is an evidence-based review method, not a blacklist, style preference, or numerical “AI slop” score. A familiar technique is not a defect by itself. Inspect the actual product, route, viewport, and state before judging it.

## 1. Establish the reference frame

Before calling something generic or gimmicky, identify:

- **Product job:** what users need to understand, decide, or do here.
- **Surface mode:** persuade, operate, read, or experience; use the contract and existing product as authority.
- **Hierarchy thesis:** what should attract attention first, what supports it, and what should remain quiet.
- **Observed evidence:** exact route, state, viewport, and source location or capture key.

Do not infer product fit from a trendy technique or a screenshot in isolation. If product context is missing, describe the uncertainty instead of presenting taste as fact.

## 2. Separate defects from pattern risk

### High-confidence defects

Fix before handoff, or record a concrete product/accessibility constraint explaining the exception:

- Content or controls are clipped, overlap, or cause unintended horizontal scrolling.
- The primary task/action is hidden, ambiguous, unreachable, or loses its hierarchy at a required viewport.
- A visible control promises an action but does nothing, has no feedback, or has an unreachable focus state.
- Content, error, empty, loading, or success states contradict the UX contract.
- Text or essential icons are unreadable; keyboard/focus order is broken; meaningful imagery lacks accessible text.
- Page failure, missing asset/font, or responsive transition prevents task completion.

Tie each finding to an image/route/state/viewport or interaction and say what user task it harms. Mechanical source heuristics may point to a place to inspect; a heuristic warning alone does not prove an aesthetic defect.

### Contextual pattern risk

Treat a pattern as a question, not a verdict. Ask whether the specific choice:

1. Communicates product identity, hierarchy, status, grouping, feedback, or task structure?
2. Helps the intended user complete this task at this viewport?
3. Has sufficient contrast, restraint, performance, and accessibility for its role?
4. Would removing or replacing it make the task clearer without losing needed meaning?

If it has a clear job and survives these checks, keep it even if it is common. If no product job can be named, simplify it. Record product-specific reasons for exceptions.

## 3. Look for unsupported clusters

One common choice is weak evidence. Raise a stronger “template/gimmick” concern when several choices appear together without a reason tied to this product, for example:

- A generic hero claim, decorative glow/gradient, repeated equal feature cards, and pill CTAs all appear unchanged across a product that needs operational clarity.
- Every group is placed in a rounded card with equal padding, even though groups have different relationships or importance.
- Motion, parallax, custom cursor, glass, or hover spectacle competes with task feedback or adds no information.
- Center alignment or asymmetric collage is applied everywhere without serving reading order, content, or navigation.
- A type/color/material combination is selected from a trend label while ignoring an existing system or audience.

These are examples of combinations to interrogate, not forbidden styles. Identify the cluster, cite the render, and explain the product mismatch. Avoid comments such as “looks AI-generated” without observable evidence.

## 4. Evidence record

For each material finding include:

- `captureKey` or source file/line, plus route, state, and viewport;
- observed behavior/appearance (not an inference stated as fact);
- user impact and severity;
- action: fixed, accepted with product rationale, or still open.

Do not average findings into a score. A visual review is complete only after every required capture was inspected. See `responsive-evidence.md` for coverage and `.codex/design/reviews/` for the project evidence convention.
