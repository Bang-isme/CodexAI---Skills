# Contextual UI Quality Audit & Anti-Slop Enforcement

This is an evidence-based review method and anti-slop filter. Inspect the actual product, route, viewport, and state before judging it, while actively rejecting lazy template habits and meaningless UI gimmicks.

---

## 1. Establish the Reference Frame

Before evaluating a surface, identify:

- **Product job:** what users need to understand, decide, or do here.
- **Surface mode:** `persuade`, `operate`, `read`, or `experience`; use the UX contract and existing product as authority.
- **Hierarchy thesis:** what must attract attention first, what supports it, and what must remain quiet.
- **Observed evidence:** exact route, state, viewport, and source location or capture key.

Do not infer product fit from a trendy technique or a screenshot in isolation. If product context is missing, describe the uncertainty instead of presenting taste as fact.

---

## 2. Separate High-Confidence Defects from Pattern Risk

### High-Confidence Defects (Must Fix Before Handoff)

- Content or controls are clipped, overlap, or cause unintended horizontal scrolling at any viewport between `320px` and `2560px`.
- Sections use rigid `height: 100vh` with `overflow: hidden` that truncates real copy on laptop or mobile landscape screens.
- The primary task/action is hidden, ambiguous, unreachable, or loses its hierarchy at a required viewport.
- A visible control promises an action (`Filter`, `Export`, `Save`, `Search`, pagination, tabs) but is inert, does nothing, or lacks focus/feedback states.
- Content, error, empty, loading, or success states contradict the UX contract or `SILC-###` API contract.
- Text or essential icons fail contrast; keyboard/focus order is broken; meaningful imagery lacks accessible text.

### Contextual Pattern Risk

Treat a visual device as a design hypothesis that must justify its existence. Ask whether the specific choice:

1. Communicates product identity, hierarchy, status, grouping, feedback, or task structure?
2. Helps the intended user complete this task at this viewport?
3. Has sufficient contrast, restraint, performance, and accessibility for its role?
4. Would removing or replacing it make the task clearer without losing needed meaning?

If it has a clear job and survives these checks, keep it. If no product job can be named, strip it out.

---

## 3. The 12-Point AI Slop & Gimmick Rejection Matrix

Flag and eliminate these 12 recurring AI UI/UX slop and gimmick clusters whenever they appear without explicit product justification:

| # | Slop / Gimmick Pattern | Why It Fails Users | Required Engineering Replacement |
| --- | --- | --- | --- |
| 1 | **Bento / 3-Equal-Card Soup** | Wrapping every feature or metric in identical 3-column rounded cards erases hierarchy | Use asymmetric spans (`7:5`, `8:4`), open divider rows, or a primary focal showcase + compact list |
| 2 | **AI Neon Dark-Mode Cliché** | Defaulting to `#080c14` dark background with purple/cyan/indigo glowing blobs on utility or business products | Use product-appropriate light or calibrated dark OKLCH surfaces with tinted neutrals |
| 3 | **Icon-in-a-Rounded-Box Above Every Heading** | Decorative badge + icon box + bold title + 2-line gray text repeated endlessly | Let typographic scale, numbering (`01`, `02`), or real product UI artifacts carry the structure |
| 4 | **Decorative Gradient Text on Headings/Metrics** | `background-clip: text` gradients reduce legibility and scream "template generator" | Use high-contrast solid ink tokens and strong display typography |
| 5 | **Custom Cursor Hijacking & Particle Trails** | Hiding native OS cursor (`cursor: none`) or attaching lagging blend-mode followers harms usability and a11y | Keep native OS cursor; use crisp element-local `:hover` and `:focus-visible` states |
| 6 | **Forced `100vh` Section Clipping** | Locking every section to `100vh` clips content when font size, copy length, or viewport ratio varies | Use `min-height` only when required and let intrinsic content height govern flow |
| 7 | **Unjustified Smooth-Scroll Hijacking** | Forcing heavy scroll-jacking libraries on operational or reading pages breaks find-in-page and keyboard nav | Keep native browser scroll; use scroll-linked motion only on explicit narrative beats with reduced-motion bypass |
| 8 | **Fake Sparklines & Ornamental Charts** | Rendering hardcoded SVG waves or meaningless progress rings just to "look like a dashboard" | Bind charts to real data with labeled axes, units, and timeframes, or use clean tabular numbers |
| 9 | **Fabricated Social Proof & Fake Metrics** | Inventing "10,000+ happy teams", fake company logos, or `99.99%` claims not in the product brief | Use authentic product workflow proof, live interactive demos, or explicitly labeled placeholders |
| 10 | **Nested Card-in-Card Chrome** | Putting bordered cards inside bordered containers inside a bordered sidebar creates visual claustrophobia | Limit container nesting to 1 level; use spacing and hairline dividers inside containers |
| 11 | **Bounce / Elastic Easing & Confetti Gimmicks** | Cartoony overshoot or random tilt/confetti on serious workflows feels amateurish and slow | Use fast exponential deceleration (`cubic-bezier(0.22, 1, 0.36, 1)`, `150ms–280ms`) |
| 12 | **Inert / Dead-End Chrome** | Rendering search bars, notification bells, or filter pills that have no working state or outcome | Either wire the control to real state/filtering or remove unrequested decorative chrome |

---

## 4. Evidence Record

For each material finding include:

- `captureKey` or source file/line, plus route, state, and viewport;
- observed behavior/appearance (not an inference stated as fact);
- user impact and severity;
- action: fixed, accepted with product rationale, or still open.

Do not average findings into a single numeric score. A visual review is complete only after every required capture was inspected. See `responsive-evidence.md` for coverage and `.codex/design/reviews/` for the project evidence convention.

## 5. Originality Evidence, Not Taste

Apply the Originality Evidence Ladder and the similarity dial in `grammar.md` when a surface sits close to a reference. False-Positive Exclusions are not plagiarism findings: a black-and-white palette, a single accent, hero+FAQ order, a standard fade, or the label "Learn more".

Do not "repair" a copied price by nudging `$49` to `$47`. Record the rung, the shared evidence, and the user impact. A generic convention with a product-specific thesis is not a defect.
