# Frontend Design Blueprint (`/codex-frontend` Fast Path)

Complete this 7-point Blueprint before writing any `.tsx`, `.jsx`, `.vue`, or `.css` code. For single-page or component scope, include it concisely in your response or design note without an extended interview. For multi-route prototypes, persist the full UX contract under `.codex/design/surfaces/<slug>.md`.

---

## The 7-Point Frontend Design Blueprint

1. **Audience & Core Job:** Who uses this surface, in what moment, and what is the single primary task or decision that must succeed?
2. **Surface Mode & Change Mode:**
   - Surface Mode: `persuade` (landing/pricing) | `operate` (dashboard/workbench) | `read` (docs/editorial) | `experience` (interactive showcase)
   - Change Mode: `extend` | `refine` | `redesign` | `new`
3. **Composition Thesis & Layout Mathematics:**
   - One-sentence spatial thesis (e.g., *"An asymmetric 7:5 split where live cost simulation anchors the right pane while the left column sequences the pricing tiers"*).
   - Grid geometry: explicit column ratio (`7:5`, `8:4`, `12-col intrinsic`, `split workbench`, or `single-column editorial 65ch`), never an unexamined 3-equal-column card row.
4. **Typography & Perceptual Color Strategy (OKLCH):**
   - Font hierarchy: Display/Heading + Body + Tabular Monospace (`font-variant-numeric: tabular-nums` for all metrics/prices/timestamps).
   - Surface palette: Tinted OKLCH neutrals (`--surface-canvas`, `--surface-1`, `--surface-2`, `--border-subtle`) + one deliberate primary action hue.
5. **The 10% Signature Move:**
   - One memorable, product-specific detail or interaction that earns attention and directly serves the user's task (with its expected user benefit).
6. **6-State Interactive Matrix (`SILC-###` Aligned):**
   - How this surface renders: `Default`, `Hover / Focus-Visible`, `Loading (layout-matched skeleton)`, `Empty (guided activation CTA)`, `Error (diagnostic + retry path)`, and `Success / Permission-Denied`.
7. **Anti-Slop & Anti-Gimmick Guardrails:**
   - Explicitly list 2–3 category clichés this implementation will **reject** (e.g., no purple-to-cyan neon dark mode, no identical 3-card icon-box rows, no custom cursor hijacking, no forced `100vh` section clipping, no invented metrics/logos).
