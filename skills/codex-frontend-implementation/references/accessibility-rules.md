# Accessibility Rules

## Scope and Triggers

Use this reference when tasks involve interactive UI, form controls, navigation, semantic structure, or compliance-focused quality checks.

Primary triggers:
- accessibility audit or WCAG compliance requests
- custom components replacing native controls
- keyboard navigation, focus management, or screen reader issues
- color contrast and motion sensitivity concerns

Secondary triggers:
- redesign of global layout, menus, dialogs, and forms
- localization changes that affect labels and content structure

Out of scope:
- backend-only changes with no user-facing interaction layer

## Core Principles

- Accessibility is part of correctness and UX quality.
- Prefer semantic HTML before ARIA augmentation.
- Keyboard access must be equivalent to pointer interaction.
- Focus order should follow visual and logical workflow.
- Labels, names, and roles should be explicit and reliable.
- Announce dynamic state changes meaningfully.
- Contrast and readability should support real-world conditions.
- Motion should respect reduced-motion preferences.
- Error feedback should be perceivable and actionable.
- Accessibility should be tested continuously, not only at release.

## Decision Tree

### Decision Tree A: Semantic vs Custom Control Strategy

- If native element satisfies behavior, use native element.
- If custom control is required, implement equivalent role, state, and keyboard support.
- If dynamic updates occur, add live region or explicit announcements as needed.
- If modal or overlay appears, trap focus and restore focus on close.
- If control has icon-only appearance, provide accessible name.
- If color conveys meaning, provide non-color fallback cues.

### Decision Tree B: Interaction Accessibility Matrix

| Component Type | Required Baseline | Avoid |
| --- | --- | --- |
| button-like control | focusable, keyboard activatable, named | clickable div with no role |
| form field | label association + error description | placeholder-only labeling |
| dialog/modal | focus trap + escape support + aria labeling | opening modal without focus management |
| navigation menu | keyboard traversal and state announcements | hover-only navigation |
| toast/alert | polite or assertive announcement strategy | silent status updates |
| data table | semantic headers and readable structure | layout table used for data grid semantics |

## Implementation Patterns

- Use semantic landmarks (`header`, `main`, `nav`, `footer`) consistently.
- Ensure all interactive controls are reachable by keyboard.
- Keep visible focus indicators and avoid disabling outlines globally.
- Use proper label association for input and form controls.
- Provide descriptive link and button text.
- Use ARIA only when semantic elements are insufficient.
- Keep heading hierarchy logical and non-skipping where possible.
- Associate errors with fields and provide summary for complex forms.
- Support reduced motion for transitions and animations.
- Ensure sufficient color contrast for text and controls.
- Provide alt text for informative images and empty alt for decorative images.
- Handle dynamic content announcements with live regions where needed.
- Validate tab order after conditional rendering changes.
- Ensure touch targets are large enough on mobile interfaces.
- Include accessibility checks in CI and release gates.

## Anti-Patterns

1. ❌ Bad: Replacing native controls without equivalent accessibility behavior.
   ✅ Good: Use native `button`, `input`, and `select` controls, or implement the full ARIA pattern including role, keyboard handling, and state attributes.

2. ❌ Bad: Removing focus outlines globally.
   ✅ Good: Keep visible focus indicators and style `:focus-visible` with at least a 2px outline and sufficient contrast.

3. ❌ Bad: Using placeholder text as sole label.
   ✅ Good: Render persistent labels with `<label for>` and use placeholders only for examples or hints.

4. ❌ Bad: Relying on color alone to convey status.
   ✅ Good: Pair color with text or icon cues and announce status updates through an `aria-live` region.

5. ❌ Bad: Failing to manage focus when opening modals.
   ✅ Good: Move focus to the first actionable element on open and return focus to the trigger on close.

6. ❌ Bad: Creating keyboard traps with no escape path.
   ✅ Good: Support `Esc` to close overlays and maintain a valid tab order that users can exit cleanly.

7. ❌ Bad: Using ARIA roles incorrectly to mimic semantics.
   ✅ Good: Prefer semantic HTML first, then add ARIA only when no native element can express the behavior.

8. ❌ Bad: Ignoring heading structure and document landmarks.
   ✅ Good: Use one logical `h1`, descending heading hierarchy, and landmark regions like `main`, `nav`, and `footer`.

9. ❌ Bad: Auto-playing motion-heavy content without user control.
   ✅ Good: Default motion-heavy media to paused, add a visible pause control, and honor `prefers-reduced-motion`.

10. ❌ Bad: Hiding error messages from assistive tech.
   ✅ Good: Bind error text with `aria-describedby` and announce validation failures using `role="alert"`.

11. ❌ Bad: Using icon-only controls without accessible name.
   ✅ Good: Provide visible text or `aria-label` for icon-only buttons and verify spoken output.

12. ❌ Bad: Treating accessibility checks as optional after feature completion.
   ✅ Good: Run automated accessibility checks in CI and block release on unresolved critical violations.

13. ❌ Bad: Skipping screen-reader checks on critical user flows.
   ✅ Good: Validate core journeys with NVDA or VoiceOver before merge and log defects as release blockers.

14. ❌ Bad: Shipping inaccessible custom widgets in design systems.
   ✅ Good: Document keyboard interaction contracts for each custom widget and cover them with component tests.

## Code Review Checklist

- [ ] Yes/No: Does this change stay within the scope and triggers defined in this reference?
- [ ] Yes/No: Is each major decision traceable to an explicit if/then or matrix condition in the Decision Tree section?
- [ ] Yes/No: Are ownership boundaries and dependencies explicit?
- [ ] Yes/No: Are high-risk failure paths guarded by validations, limits, or fallbacks?
- [ ] Yes/No: Is there a documented rollback or containment path if production behavior regresses?
- [ ] Yes/No: Are all interactive elements reachable by keyboard in a logical tab order?
- [ ] Yes/No: Do custom controls expose role, name, value, and state correctly?
- [ ] Yes/No: Do dialogs and popovers restore focus to the invoking control on close?
- [ ] Yes/No: Are field-level error messages programmatically associated with their inputs?
- [ ] Yes/No: Do animations and transitions respect user reduced-motion settings?

## Testing and Verification Checklist

- [ ] Yes/No: Is there at least one positive-path test that verifies intended behavior?
- [ ] Yes/No: Is there at least one negative-path test that verifies rejection/failure handling?
- [ ] Yes/No: Is a regression test added for the highest-risk scenario touched?
- [ ] Yes/No: Do tests cover boundary inputs and edge conditions relevant to this change?
- [ ] Yes/No: Are integration boundaries verified where this change crosses module/service/UI layers?
- [ ] Yes/No: Did automated accessibility scanning (for example axe or lighthouse) pass with no critical violations?
- [ ] Yes/No: Were critical flows validated with at least one screen reader (NVDA or VoiceOver)?
- [ ] Yes/No: Is keyboard-only navigation passing on the main task journeys?
- [ ] Yes/No: Do changed screens meet WCAG contrast requirements for text and controls?
- [ ] Yes/No: Are focus trap and escape behaviors tested for every dialog or modal touched?

## Cross-References

- `frontend-rules.md` for component architecture alignment.
- `react-patterns.md` for interactive component behavior.
- `testing-rules.md` for accessibility test layering.
- `performance-rules.md` for balancing motion/performance tradeoffs.
- `seo-rules.md` for semantic structure and crawlability synergy.

### Scenario Walkthroughs

- Scenario: Checkout modal traps keyboard users on the payment step.
  - Action: Move initial focus to the first invalid field and trap focus within the dialog only while it is open.
  - Action: Add `Esc` close behavior and assert focus returns to the checkout button after close.
- Scenario: Icon-only toolbar buttons are unreadable to screen readers.
  - Action: Add explicit accessible names with visible text or `aria-label` and verify spoken labels in NVDA.
  - Action: Add component tests that fail when icon buttons render without accessible names.
- Scenario: Auto-rotating carousel causes motion sickness complaints.
  - Action: Disable auto-rotate by default and expose Play/Pause controls in the UI.
  - Action: Respect `prefers-reduced-motion` and verify the reduced-motion path in browser emulation.

### Delivery Notes

- Keep this reference aligned with project conventions and postmortems.
- Update checklists when recurring defects reveal missing guardrails.
- Prefer incremental adoption over large risky rewrites.
