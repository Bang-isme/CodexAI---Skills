# Complete Interactive Component State Matrix

Every interactive surface, route, and control must implement the **6-State Completeness Matrix** aligned with the UX contract and any `SILC-###` API/data seam. Never ship happy-path-only UI.

---

## 1. The 6 Required Surface & Control States

| State | Visual & Structural Requirement | Copy & Recovery Requirement |
| --- | --- | --- |
| **1. Default / Rest** | Clear visual hierarchy; primary CTA uses `--action-primary`; secondary actions use quiet borders or ghost treatments; hit targets `>= 44×44px` on touch | Action-oriented verbs (`Create Workspace`, `Export CSV`), never generic (`Submit`, `Click Here`) |
| **2. Hover / Focus-Visible / Active** | `:hover` shifts surface/border subtly; `:focus-visible` shows a `2px–3px` high-contrast ring with `outline-offset: 2px`; `:active` applies subtle `translateY(1px)` press feedback | Tooltip or `aria-label` on icon-only controls; keyboard Tab order strictly matches visual order |
| **3. Loading / Pending (`aria-busy="true"`)** | **Zero layout shift:** buttons lock width and disable repeat clicks while showing an inline indicator; data regions render layout-matched skeletons (never a lone page-blocking spinner) | Communicate what is happening (`Saving changes…`, `Syncing 142 records…`) |
| **4. Empty / Zero-Data** | Never render a blank box or raw `"No data found"`. Provide a structured empty state inside the container that previews the value of the feature | Explain **why** it is empty and provide a direct **primary activation CTA** (`Import first dataset`, `Reset active filters`) |
| **5. Error / Validation / Degraded** | Preserve user input (never wipe a form on error); highlight invalid fields with `--status-danger` border + icon + `aria-describedby` message | State **what failed**, **why**, and **how to recover** (`Retry request`, `Check API key`, inline field hint) |
| **6. Success / Optimistic / Permission-Denied** | Confirm completed mutations with inline status, toast with undo, or highlighted row update; for `403 / permission-denied`, show a locked state rather than a broken crash | Provide reversible undo (`Archive complete — Undo`) or clear escalation instructions (`Request Admin Access`) |

---

## 2. Stress & Edge-Case Resilience Checklist

Before passing `$visual-gate`, verify that every component survives:

- **Long Content Stress:** 80-character titles, unbreakable URLs/emails (`overflow-wrap: anywhere`), and localized strings (such as Vietnamese diacritics or German compounds) without overlapping adjacent controls.
- **Numeric Alignment:** Prices, percentages, counters, and timestamps use `font-variant-numeric: tabular-nums` so live updates never jitter horizontally.
- **Double-Submit Protection:** Async mutation triggers immediately transition to `disabled` / `aria-busy="true"` until the `SILC-###` response resolves.
- **Reduced Motion Parity:** Under `@media (prefers-reduced-motion: reduce)`, skeleton shimmers stop moving and state transitions switch to instant or opacity-only changes.
