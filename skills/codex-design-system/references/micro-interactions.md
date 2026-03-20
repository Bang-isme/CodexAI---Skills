# Micro-Interactions

## Hover Lift
- Use when: clickable cards, list rows, feature tiles.
- CSS:
```css
.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 48px rgba(8, 15, 32, 0.18);
}
```
- Do not use on: dense tables where motion would create jitter.

## Entrance Fade-Up
- Use when: hero sections, cards, dashboard widgets.
- CSS:
```css
.fade-up {
  opacity: 0;
  transform: translateY(20px);
  animation: fade-up 480ms cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}
@keyframes fade-up {
  to { opacity: 1; transform: translateY(0); }
}
```
- Do not use on: every element on long pages.

## Button Press
- Use when: primary actions, icon buttons, segmented controls.
- CSS:
```css
.press:active {
  transform: scale(0.97);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.16);
}
```
- Do not use on: destructive buttons that need a stable target.

## Skeleton Pulse
- Use when: async content cards, data tables, charts.
- CSS:
```css
.skeleton {
  background: linear-gradient(90deg, rgba(255,255,255,0.04), rgba(255,255,255,0.16), rgba(255,255,255,0.04));
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}
@keyframes shimmer {
  to { background-position: -200% 0; }
}
```
- Do not use on: loads shorter than about 300ms.

## Scroll Reveal
- Use when: storytelling sections and staggered content blocks.
- CSS:
```css
.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 420ms ease, transform 420ms ease;
}
.reveal.is-visible {
  opacity: 1;
  transform: translateY(0);
}
```
- Do not use on: every list item inside scrolling containers.

## Toast Slide-In
- Use when: save success, background task updates, undo affordances.
- CSS:
```css
.toast {
  transform: translateX(24px);
  opacity: 0;
  animation: toast-in 240ms ease forwards;
}
@keyframes toast-in {
  to { transform: translateX(0); opacity: 1; }
}
```
- Do not use on: blocking error states that need inline treatment.

## Accordion Expand
- Use when: FAQs, settings groups, filters.
- CSS:
```css
.panel {
  max-height: 0;
  overflow: hidden;
  transition: max-height 260ms ease;
}
.panel[aria-hidden="false"] {
  max-height: 480px;
}
```
- Do not use on: highly variable content taller than your max-height cap.

## Focus Ring Glow
- Use when: keyboard navigation, forms, command palettes.
- CSS:
```css
.focus-ring:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.16), 0 0 0 6px rgba(16,185,129,0.28);
}
```
- Do not use on: mouse-only hover states.

## Loading Spinner
- Use when: compact async actions and inline fetches.
- CSS:
```css
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.18);
  border-top-color: currentColor;
  border-radius: 999px;
  animation: spin 700ms linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
```
- Do not use on: long page loads where skeletons communicate better.

## Page Transition
- Use when: route transitions, modal swaps, multi-step flows.
- CSS:
```css
.page-enter {
  opacity: 0;
}
.page-enter-active {
  opacity: 1;
  transition: opacity 220ms ease;
}
```
- Do not use on: dense apps where every navigation would feel slowed down.
