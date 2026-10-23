# Composition, Spatial Rhythm, and Optical Balance

These are observable engineering and design gates, not a fake numerical balance score.

---

## 1. Hierarchy & The Squint Test

Squint or shrink the viewport to 25% zoom. The **primary task, claim, or focal workspace** must remain the single dominant anchor. If two regions shout at the same volume, reduce one. Scale contrast, typographic weight, negative space, and spatial position beat extra accent colors every time.

---

## 2. Spatial Grouping & Anti-Card-Soup Discipline

- Related controls share a cluster: same inset, same background plane, one clear heading.
- Unrelated actions never share a card.
- **Do not wrap every peer group in a bordered/shadowed card:** When spacing and a `1px` structural hairline divider (`border-top: 1px solid var(--border-subtle)`) already separate items, omit card chrome.
- Lists of features or metrics need a structural reason to be a list; otherwise use an asymmetric narrative split, a comparison matrix, or a primary-plus-detail layout.

---

## 3. Mathematical Spacing Rhythm

Use a strict geometric/modular spacing scale (`4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96px`) and repeat it consistently:
- **Intra-element gap** (icon to label, label to input): `4px–8px`
- **Component internal padding**: `12px–24px` (scaled by density mode)
- **Group-to-group separation**: `24px–32px`
- **Section-to-section rhythm**: `clamp(3.5rem, 7vw, 6.5rem)`

Arbitrary pixel values (`13px`, `19px`, `37px`, mixed `gap` and `margin` with no scale) fail the mechanical gate. Adjacent levels of hierarchy must differ by at least one full scale step so proximity clearly signals relationship.

---

## 4. Optical Alignment & Keylines

Align to a crisp structural keyline first, then apply optical corrections:
- **Vertical Keyline Continuity:** The left edges of headings, body copy, tables, and primary containers in a column must share an exact vertical axis unless a deliberate break is the composition thesis.
- **Optical Icon & Play-Button Centering:** Icons inside circular or square hit targets must be optically centered; tabular numbers (`font-variant-numeric: tabular-nums`) must right-align in tables and stat comparisons.
- **Never center-align multi-line body copy (> 2 lines):** Left-align body paragraphs (`60ch–70ch` max measure) for effortless eye return.

---

## 5. Surface Density Calibration

- **`operate` surfaces** (dashboards, admin consoles, IDEs) may be high-density (`13px–14px` UI controls, `8px–12px` cell padding) provided grouping and keylines are rock-solid.
- **`persuade` and `read` surfaces** require generous open canvas (at least 35%–45% open background/whitespace in the primary viewport) so the core claim and proof breathe.
- Repeated cards are valid only for genuinely parallel items; when items differ in importance, vary column span (`7:5` or `8:4`) or elevation rather than forcing equal tiles.

---

## 6. Distinctiveness Without Visual Clutter

For a substantial redesign, give the page one product-fit signature: for example, a data visualization that explains change, an editorial split that pairs a decision with its evidence, or a workspace arrangement that keeps a frequent task in reach. State what it helps the user notice or do. Let the rest of the composition support that move with a clear hierarchy and familiar interaction patterns. Creative structure can come from scale, alignment, negative space, grouping, or information geometry; it does not need extra cards, gradients, shadows, or motion. Keep any device whose product job is clear, and simplify the rest.

Before accepting a new composition, check the same hierarchy in realistic short and long content. Long labels, controls, data, and media must reflow or use a deliberate local scroll/crop behavior; they must not overlap neighboring content or hide the primary task. See `layout-decision-framework.md` for the layout contract and `layout-adaptation.md` for content-safe responsive behavior.

---

## 7. Narrative Sequence When It Serves the User

Use narrative structure for content-led experiences when staged understanding improves the task: a launch story, editorial explanation, learning flow, onboarding, or a product journey with meaningful discovery. Before arranging sections, write a compact **narrative spine** in the existing brief or UX contract:

`user question → essential context/proof → discovery or decision → useful next action`

Expand that spine into only the beats the product needs. Each beat should answer a distinct user question, contribute new evidence or meaning, and make the next step easier to anticipate. Connect sections through information and visual continuity when that relationship helps comprehension. Use contrast and breathing room to pace attention; resolve any question the page raises, and keep essential details such as safety, price, or caveats visible rather than hiding them for suspense.

If a user skips to a later section, the heading and nearby context should still orient them. If the experience is primarily operational, use its task sequence, current state, feedback, and next action as the structure. Do not force an emotional arc or a cinematic climax onto a utility-heavy surface.

---

## 8. Responsive Reflow, Focus Order, Contrast, States & Motion

- **Responsive reflow:** Desktop and narrow viewports (`320px–2560px`) are both first-class. Reflow must preserve hierarchy: the primary action stays reachable; secondary nav collapses cleanly; tables get a stacked or local horizontal-scroll plan. Never force `height: 100vh` on content sections that can clip on short screens.
- **Focus order:** DOM order matches visual reading order. Skip links and semantic landmarks (`<header>`, `<main>`, `<nav>`, `<aside>`) exist on complex pages. Modals trap focus and restore it on close.
- **Contrast:** Text and essential icons meet WCAG AA/AAA contrast for the chosen surface.
- **States:** Every interactive control documents `default`, `hover`, `focus-visible`, `disabled`, `loading`, `error`, and `empty`. `operate` flows also include `success` and `permission-denied`.
- **Reduced motion:** Transforms and fades have a `prefers-reduced-motion: reduce` alternative: instant state change or opacity-only transition, no large spatial movement.
