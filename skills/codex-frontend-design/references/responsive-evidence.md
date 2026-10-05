# Responsive Visual Evidence

The visual gate consumes evidence produced by `codex-visual-quality-gate/scripts/capture_responsive_matrix.mjs`. It must not infer that a page passed from a single viewport screenshot or source inspection.

In the commands below, `<SKILLS_ROOT>` is the installed pack directory containing `codex-visual-quality-gate/`; `<APP_ROOT>` is the app being prototyped. The fixture manifest and resulting captures live inside `<APP_ROOT>`.

## 1. Define routes, breakpoints, and states

Create a project-relative JSON input file (for example `.codex/design/reviews/responsive/capture-plan.json`):

```json
{
  "baseUrl": "http://127.0.0.1:3000",
  "routes": [
    { "id": "home", "path": "/" },
    { "id": "checkout", "path": "/checkout" }
  ],
  "breakpoints": [768, 1024],
  "breakpointSources": ["src/styles/tokens.css: @media 768px, 1024px"],
  "states": [
    { "id": "default", "routeId": "home", "actions": [] },
    {
      "id": "menu-open", "routeId": "home",
      "viewportIds": ["tablet-portrait", "mobile-portrait"],
      "actions": [{ "type": "click", "selector": "[data-testid=menu-trigger]" }]
    },
    { "id": "default", "routeId": "checkout", "actions": [] }
  ],
  "flows": [
    { "id": "primary-checkout", "routeIds": ["home", "checkout"], "summary": "Choose an item, enter details, and reach confirmation." }
  ],
  "provenance": {
    "appRevision": "local working tree",
    "references": [".codex/design/DIRECTION.md"]
  }
}
```

List **every route** in the prototype and a `default` state per route. Add interaction states that materially affect the design (menu open, dialog, validation error, empty results, loading, success, and so on) and choose the viewport IDs on which each state matters. Define each primary UX flow with a unique ID and every route it touches. Supported actions: `click`, `fill`, `press`, `check`, `uncheck`, `select`, and `waitFor`; each requires a CSS `selector`.

Derive breakpoint values from the actual CSS/framework configuration and record their source. Do not guess familiar framework defaults. `breakpoints: []` is valid when the app has none; the full scan and anchor captures still run.

## 2. Check browser prerequisites and validate the plan

The capture runner resolves Playwright from the application project and requires its Chromium browser. It never installs packages or browsers automatically. If either is missing, install them using the project's existing package manager and record the resulting versions; for an npm project, run these from the app root:

```powershell
npm install --save-dev playwright
npx playwright install chromium
```

If installing a browser dependency is outside the task scope, keep the result `DEGRADED` and say which prerequisite is missing. `--plan-only` validates route/state coverage without launching a browser.

### Windows PowerShell

```powershell
$skillsRoot = "C:\path\to\CodexAI---Skills\skills"
$appRoot = "C:\path\to\my-app"
$captureRunner = Join-Path $skillsRoot "codex-visual-quality-gate/scripts/capture_responsive_matrix.mjs"
node $captureRunner --project-root $appRoot --manifest ".codex/design/reviews/responsive/capture-plan.json" --plan-only
```

### macOS or Linux

```sh
SKILLS_ROOT="/path/to/CodexAI---Skills/skills"
APP_ROOT="/path/to/my-app"
node "$SKILLS_ROOT/codex-visual-quality-gate/scripts/capture_responsive_matrix.mjs" --project-root "$APP_ROOT" --manifest ".codex/design/reviews/responsive/capture-plan.json" --plan-only
```

## 3. Capture all required evidence

Run the same command with `--plan-only` removed. For example, in PowerShell:

```powershell
node $captureRunner --project-root $appRoot --manifest ".codex/design/reviews/responsive/capture-plan.json"
```

The script opens every route and:

- scans CSS widths 320–2560 inclusive at 64 px steps, plus -1, exact, and +1 at each discovered breakpoint;
- captures full-page evidence for every route at 1280×800, 1440×900, 1920×1080, 768×1024, 1024×768, 390×844, and 844×390;
- captures each declared state at its selected anchor viewports and each route at breakpoint widths ±1;
- records and captures any sweep width with horizontal overflow or browser errors;
- flags interactive controls outside the viewport and captures those widths for contextual clipping review (the signal alone is not a defect);
- warms the page by scrolling before capture to activate lazy content, then waits for fonts/images;
- saves original viewport-sized PNG slices with overlapping coverage and stitches the non-duplicated slices into a full-page PNG.

All dimensions are CSS pixels at `deviceScaleFactor: 1`. These are browser viewport emulations, not physical-device certification. Very tall/large images may hit the helper's memory cap; report that as failed or degraded evidence instead of silently substituting a cropped image.

## 4. Inspect and record the evidence

Open and inspect **every** `stitched.png` and its numbered `slice-*.png` files. Slices reveal fixed/sticky repetition and details that a long stitched image can obscure. Confirm the top, middle, bottom, all sections, footer, overlays, navigation, and state-specific content. For a scroll-driven scene, compare slices' `sourceScrollY` values to the scene progress map. A stitched page is not proof of a particular animated frame; when a material entry/build/peak/release checkpoint falls between slices, capture an extra viewport PNG at that mapped scroll position and record its project-relative path, route, state, viewport, and scroll position with the review. If the last image looks clipped, verify the final slice against the document height.

Edit the emitted `capture-manifest.json` review section after inspection:

```json
{
  "visualReview": {
    "status": "complete",
    "reviewer": "fresh-eyes reviewer",
    "summary": "Routes and required states checked at every listed viewport.",
    "checkedCaptureKeys": ["home|default|desktop-laptop"],
    "findings": []
  },
  "functionalReview": {
    "status": "complete",
    "checkedFlowIds": ["primary-checkout"],
    "checkedRouteStateKeys": ["home|default", "home|menu-open", "checkout|default"],
    "mainFlowStatus": "pass",
    "accessibilityStatus": "pass",
    "findings": []
  }
}
```

List every required capture key under `checkedCaptureKeys`. In `functionalReview`, record every UX-contract flow and route/state exercised, plus the result of the primary journey and accessibility review (semantic structure, keyboard and focus, labels, contrast, and reduced motion as applicable). Findings must include exact route, state, viewport/capture key or test evidence, observed issue, severity, and whether it was fixed or accepted with a product rationale. Do not write `complete` until every image and flow was actually inspected/exercised.

## 5. Run the final gate

In PowerShell:

```powershell
$visualGate = Join-Path $skillsRoot "codex-visual-quality-gate/scripts/visual_quality_gate.py"
python $visualGate --project-root $appRoot --capture-manifest ".codex/design/reviews/responsive/<run>/capture-manifest.json" --format json
```

On macOS or Linux:

```sh
python3 "$SKILLS_ROOT/codex-visual-quality-gate/scripts/visual_quality_gate.py" --project-root "$APP_ROOT" --capture-manifest ".codex/design/reviews/responsive/<run>/capture-manifest.json" --format json
```

Pass means the evidence manifest covers the required routes/states/viewports and UX flows, the primary path and accessibility review pass, PNG dimensions and overlapping slice ranges are continuous to the measured document height, every responsive width sample exists without unaddressed overflow, and the rendered review is recorded complete. A missing file, browser, route, flow, state, capture, segment, width, functional review, or image review returns `DEGRADED` or fail; it never means “approved”. Fix or explain high-confidence issues before handoff.
