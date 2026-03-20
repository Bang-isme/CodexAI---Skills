# Patterns

## Bento Grid
- Use when: feature dashboards, AI tool hubs, product landing pages.
- CSS:
```css
.grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 24px;
}
.feature-lg { grid-column: span 7; }
.feature-sm { grid-column: span 5; }
```
- Avoid: equal-height cards with no dominant tile.

## Asymmetric Hero
- Use when: launch pages, premium app intros.
- CSS:
```css
.hero {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 40px;
  align-items: end;
}
```
- Avoid: perfectly centered headline plus button plus stock screenshot.

## Split Screen
- Use when: onboarding, auth, product + narrative pairing.
- CSS:
```css
.split {
  display: grid;
  grid-template-columns: minmax(320px, 520px) 1fr;
  min-height: 100vh;
}
```
- Avoid: both columns carrying equal visual weight.

## Floating Cards
- Use when: metrics, testimonials, modular content.
- CSS:
```css
.stack {
  position: relative;
}
.card {
  position: absolute;
  backdrop-filter: blur(20px);
  transform: rotate(var(--tilt));
}
```
- Avoid: flat cards with generic `box-shadow: 0 4px 12px rgba(0,0,0,.1)`.

## Layered Depth
- Use when: premium dashboards, fintech, hero callouts.
- CSS:
```css
.layer {
  position: relative;
  isolation: isolate;
}
.layer::before {
  content: "";
  position: absolute;
  inset: -12%;
  filter: blur(80px);
  z-index: -1;
}
```
- Avoid: single flat background.

## Sidebar + Content
- Use when: admin tools, settings, docs.
- CSS:
```css
.shell {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  min-height: 100vh;
}
```
- Avoid: collapsing everything into one long column on desktop.

## Dashboard Mosaic
- Use when: KPI-heavy apps with mixed chart/table/card density.
- CSS:
```css
.mosaic {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 20px;
}
.wide { grid-column: span 4; }
.tall { grid-row: span 2; }
```
- Avoid: same-size widgets everywhere.

## Timeline Flow
- Use when: onboarding steps, release histories, project status.
- CSS:
```css
.timeline {
  display: grid;
  gap: 16px;
  position: relative;
}
.timeline::before {
  content: "";
  position: absolute;
  left: 12px;
  top: 0;
  bottom: 0;
  width: 2px;
}
```
- Avoid: plain unordered list with timestamps bolted on.

## Tabs + Panel
- Use when: settings, segmented reports, multi-state tools.
- CSS:
```css
.tabs {
  display: inline-flex;
  gap: 8px;
  padding: 6px;
  border-radius: 999px;
}
.panel {
  margin-top: 24px;
  border-radius: 24px;
}
```
- Avoid: default browser tabs styling.

## Full-Bleed Sections
- Use when: narrative marketing pages with pacing.
- CSS:
```css
.section {
  padding: 96px clamp(24px, 6vw, 96px);
}
.section--bleed {
  margin-inline: calc(50% - 50vw);
  padding-inline: clamp(24px, 8vw, 120px);
}
```
- Avoid: wrapping every section in the same centered max-width box.

## Sticky Nav + Scroll
- Use when: docs, long-form landing pages, changelogs.
- CSS:
```css
.toc {
  position: sticky;
  top: 24px;
  align-self: start;
}
```
- Avoid: sticky nav with no active-section signal.

## Command Palette
- Use when: productivity apps, admin tools, search-centric products.
- CSS:
```css
.palette {
  width: min(720px, calc(100vw - 32px));
  border-radius: 28px;
  overflow: hidden;
}
```
- Avoid: treating it like a plain modal.
