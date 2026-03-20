# Patterns

Derived from current layout conventions seen in [Awwwards](https://www.awwwards.com/), [Webflow's design trend library](https://webflow.com/blog/web-design-trends), Framer sites, editorial landing pages, and product homes such as Linear, Stripe, Notion, and Raycast. These are implementation patterns, not vague style notes.

## 1. Bento Grid
- Description: Uneven grid with one dominant card and several supporting tiles. Good for feature storytelling without repeating identical cards.
- Use when: AI tools, product launch pages, multi-feature SaaS homepages.
- Do not use when: content is mostly long-form copy or every item has equal importance.
- HTML:
```html
<section class="bento">
  <article class="tile tile--hero"></article>
  <article class="tile tile--wide"></article>
  <article class="tile"></article>
</section>
```
- CSS:
```css
.bento {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 24px;
}
.tile { grid-column: span 4; min-height: 220px; }
.tile--wide { grid-column: span 5; }
.tile--hero { grid-column: span 7; min-height: 360px; }
@media (max-width: 900px) { .tile, .tile--wide, .tile--hero { grid-column: 1 / -1; } }
```
- Inspiration: Bento grid trend, Linear-style feature storytelling.

## 2. Asymmetric Hero
- Description: Text block and visual block have intentionally different widths and vertical alignment so the hero feels directed, not centered by default.
- Use when: premium launch pages, creative SaaS, portfolio intros.
- Do not use when: legal, docs, or internal tools need immediate scanning.
- HTML:
```html
<section class="hero">
  <div class="hero__copy"></div>
  <figure class="hero__visual"></figure>
</section>
```
- CSS:
```css
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.85fr);
  gap: clamp(24px, 5vw, 72px);
  align-items: end;
}
@media (max-width: 900px) { .hero { grid-template-columns: 1fr; } }
```
- Inspiration: Editorial launch pages and Framer portfolio sites.

## 3. Split Screen
- Description: Two-column shell where one side carries narrative and the other side carries utility, imagery, or product interaction.
- Use when: auth, onboarding, product explainer + form.
- Do not use when: both sides fight for the same level of attention.
- HTML:
```html
<main class="split">
  <section class="split__story"></section>
  <section class="split__task"></section>
</main>
```
- CSS:
```css
.split {
  display: grid;
  grid-template-columns: minmax(340px, 520px) minmax(0, 1fr);
  min-height: 100vh;
}
@media (max-width: 860px) { .split { grid-template-columns: 1fr; } }
```
- Inspiration: Product onboarding flows and modern auth screens.

## 4. Floating Cards
- Description: Cards overlap a background plane with controlled rotation and offset. Creates energy without breaking layout order.
- Use when: testimonials, KPI callouts, visual proof clusters.
- Do not use when: dense data tables or accessibility-sensitive reading surfaces.
- HTML:
```html
<section class="stack">
  <article class="stack__card stack__card--a"></article>
  <article class="stack__card stack__card--b"></article>
</section>
```
- CSS:
```css
.stack { position: relative; min-height: 420px; }
.stack__card {
  position: absolute;
  width: min(320px, 82vw);
  backdrop-filter: blur(20px);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
}
.stack__card--a { top: 0; left: 0; transform: rotate(-4deg); }
.stack__card--b { right: 0; top: 72px; transform: rotate(5deg); }
```
- Inspiration: Glassy marketing pages and motion-heavy portfolios.

## 5. Layered Z-Depth
- Description: Background glow, foreground surface, and one floating annotation layer create depth without resorting to fake skeuomorphism.
- Use when: premium dashboards, fintech landing pages, hero sections.
- Do not use when: the brand is intentionally flat or brutalist.
- HTML:
```html
<section class="depth">
  <div class="depth__glow"></div>
  <article class="depth__surface"></article>
  <aside class="depth__annotation"></aside>
</section>
```
- CSS:
```css
.depth { position: relative; isolation: isolate; }
.depth__glow {
  position: absolute;
  inset: 10% auto auto 8%;
  width: 360px;
  aspect-ratio: 1;
  filter: blur(96px);
  z-index: -1;
}
.depth__annotation { position: absolute; right: -16px; bottom: 24px; }
```
- Inspiration: Aurora-gradient fintech and AI SaaS visuals.

## 6. Magazine / Editorial
- Description: Big headline, narrow text column, pulled quote or image block breaking the rhythm.
- Use when: storytelling, case studies, long-form marketing.
- Do not use when: users need to compare features quickly.
- HTML:
```html
<article class="editorial">
  <header class="editorial__hero"></header>
  <div class="editorial__body"></div>
  <aside class="editorial__pullquote"></aside>
</article>
```
- CSS:
```css
.editorial {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(220px, 320px);
  gap: clamp(24px, 4vw, 64px);
}
.editorial__body { max-width: 68ch; }
@media (max-width: 900px) { .editorial { grid-template-columns: 1fr; } }
```
- Inspiration: Typewolf lookbook layouts and magazine-style landing pages.

## 7. Dashboard Mosaic
- Description: Mixed-width and mixed-height widgets create a task-first dashboard instead of a same-sized-card wall.
- Use when: analytics, admin panels, operational reporting.
- Do not use when: the dashboard has no real prioritization.
- HTML:
```html
<section class="mosaic">
  <div class="widget widget--xl"></div>
  <div class="widget widget--wide"></div>
  <div class="widget widget--tall"></div>
</section>
```
- CSS:
```css
.mosaic {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 20px;
}
.widget { grid-column: span 3; min-height: 180px; }
.widget--wide { grid-column: span 6; }
.widget--xl { grid-column: span 8; min-height: 280px; }
.widget--tall { grid-row: span 2; }
@media (max-width: 960px) { .widget, .widget--wide, .widget--xl { grid-column: 1 / -1; } }
```
- Inspiration: Enterprise dashboards and BI products.

## 8. Sidebar Rail
- Description: Narrow navigation rail plus generous content panel. Keeps orientation persistent while letting content breathe.
- Use when: settings, docs, internal tools, account areas.
- Do not use when: navigation is shallow enough for tabs.
- HTML:
```html
<div class="shell">
  <nav class="shell__rail"></nav>
  <main class="shell__content"></main>
</div>
```
- CSS:
```css
.shell {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  min-height: 100vh;
}
.shell__rail { position: sticky; top: 0; height: 100vh; }
@media (max-width: 860px) { .shell { grid-template-columns: 1fr; } .shell__rail { height: auto; position: static; } }
```
- Inspiration: Productivity apps with compact navigation.

## 9. Full-Bleed Sections
- Description: Alternating full-width bands reset the eye and help sequence narrative content.
- Use when: marketing pages, product stories, release pages.
- Do not use when: every section looks identical and the bleed adds no pacing.
- HTML:
```html
<section class="band band--bleed"></section>
<section class="band"></section>
```
- CSS:
```css
.band { padding: clamp(72px, 10vw, 120px) clamp(24px, 6vw, 96px); }
.band--bleed {
  margin-inline: calc(50% - 50vw);
  padding-inline: clamp(24px, 8vw, 120px);
}
```
- Inspiration: Stripe-style storytelling bands.

## 10. Sticky Header + Scroll Spy
- Description: Sticky top bar paired with a secondary nav or section indicator that tracks reading progress.
- Use when: docs, changelogs, long-form landing pages.
- Do not use when: the page is short enough that sticky chrome only steals space.
- HTML:
```html
<header class="topbar"></header>
<div class="content-shell">
  <nav class="content-shell__toc"></nav>
  <article class="content-shell__article"></article>
</div>
```
- CSS:
```css
.topbar { position: sticky; top: 0; z-index: 30; }
.content-shell {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 32px;
}
.content-shell__toc { position: sticky; top: 88px; align-self: start; }
@media (max-width: 960px) { .content-shell { grid-template-columns: 1fr; } .content-shell__toc { display: none; } }
```
- Inspiration: Docs sites and changelog experiences.

## 11. Command Palette Shell
- Description: Search-first app shell with a centered command layer, keyboard hints, and a dense results stack.
- Use when: productivity tools, admin apps, search-heavy products.
- Do not use when: users primarily browse visually.
- HTML:
```html
<div class="palette">
  <div class="palette__input"></div>
  <ul class="palette__results"></ul>
</div>
```
- CSS:
```css
.palette {
  width: min(720px, calc(100vw - 32px));
  border-radius: 28px;
  overflow: hidden;
  box-shadow: 0 28px 80px rgba(15, 23, 42, 0.24);
}
.palette__results { max-height: min(60vh, 520px); overflow: auto; }
```
- Inspiration: Raycast and command-driven product patterns.

## 12. Carousel Flow
- Description: Horizontal list with snapping, partial preview of next slide, and strong text hierarchy outside the slide frame.
- Use when: product screenshots, testimonials, showcases.
- Do not use when: users need precise comparison across all items at once.
- HTML:
```html
<section class="carousel">
  <div class="carousel__track">
    <article class="carousel__slide"></article>
  </div>
</section>
```
- CSS:
```css
.carousel__track {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(280px, 48vw);
  gap: 20px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
}
.carousel__slide { scroll-snap-align: start; }
```
- Inspiration: Product galleries and app showcase strips.

## 13. Timeline / Process
- Description: Vertical process line with numbered steps and detail cards offset from the main rail.
- Use when: implementation steps, onboarding, project phases.
- Do not use when: there are only two steps and a simple stack would suffice.
- HTML:
```html
<ol class="timeline">
  <li class="timeline__step"></li>
</ol>
```
- CSS:
```css
.timeline {
  display: grid;
  gap: 20px;
  position: relative;
  padding-left: 32px;
  counter-reset: item;
}
.timeline::before {
  content: "";
  position: absolute;
  left: 11px;
  top: 8px;
  bottom: 8px;
  width: 2px;
}
.timeline__step::before { content: counter(item); counter-increment: item; }
```
- Inspiration: Onboarding and roadmap views.

## 14. Pricing Table
- Description: Three-to-four pricing columns with one highlighted offer and a tight feature rhythm below the price block.
- Use when: SaaS tiers, memberships, service packages.
- Do not use when: pricing depends on custom quotes or complex matrix logic.
- HTML:
```html
<section class="pricing">
  <article class="plan plan--featured"></article>
  <article class="plan"></article>
</section>
```
- CSS:
```css
.pricing {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
}
.plan--featured { transform: translateY(-12px); }
@media (max-width: 960px) { .pricing { grid-template-columns: 1fr; } .plan--featured { transform: none; } }
```
- Inspiration: Modern SaaS pricing pages.

## 15. Feature Comparison Matrix
- Description: Sticky row or column headers help compare plans or product capabilities without losing context.
- Use when: plan comparisons, tool comparisons, evaluation pages.
- Do not use when: there are fewer than five comparable criteria.
- HTML:
```html
<div class="matrix">
  <div class="matrix__head"></div>
  <div class="matrix__body"></div>
</div>
```
- CSS:
```css
.matrix { overflow: auto; }
.matrix table { min-width: 720px; border-collapse: collapse; }
.matrix thead th {
  position: sticky;
  top: 0;
  z-index: 2;
}
.matrix tbody th {
  position: sticky;
  left: 0;
  z-index: 1;
}
```
- Inspiration: Comparison-led landing pages.

## 16. Testimonial Wall
- Description: A masonry-like quote wall mixes avatar, quote length, and proof snippets without feeling like repeated cards.
- Use when: social proof, community-led products, customer stories.
- Do not use when: there are only one or two testimonials.
- HTML:
```html
<section class="wall">
  <blockquote class="wall__item wall__item--tall"></blockquote>
</section>
```
- CSS:
```css
.wall {
  columns: 3 280px;
  column-gap: 20px;
}
.wall__item {
  break-inside: avoid;
  margin-bottom: 20px;
}
```
- Inspiration: Community-first product pages.

## 17. Animated Hero
- Description: Hero with moving backdrop, floating label chips, or motion-led product preview as a single focal object.
- Use when: launch pages, premium product reveals.
- Do not use when: performance budget is tight or content is compliance-heavy.
- HTML:
```html
<section class="animated-hero">
  <div class="animated-hero__copy"></div>
  <div class="animated-hero__scene"></div>
</section>
```
- CSS:
```css
.animated-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 520px);
  gap: 48px;
  align-items: center;
}
.animated-hero__scene { min-height: 420px; position: relative; overflow: clip; }
@media (max-width: 960px) { .animated-hero { grid-template-columns: 1fr; } }
```
- Inspiration: Motion-led product marketing pages.

## 18. Stats Counter Strip
- Description: Short metric strip pairs three-to-six numbers with concise proof text and a strong baseline rhythm.
- Use when: KPI proof, investor messaging, trust-building.
- Do not use when: metrics are weak or unverifiable.
- HTML:
```html
<section class="stats">
  <article class="stats__item"></article>
</section>
```
- CSS:
```css
.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}
@media (max-width: 860px) { .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) { .stats { grid-template-columns: 1fr; } }
```
- Inspiration: B2B landing pages and annual reports.

## 19. FAQ Accordion Stack
- Description: Accordion list with summary row, divider rhythm, and a right-side affordance that telegraphs open/closed state.
- Use when: FAQs, support, pricing objections.
- Do not use when: users need to search answers instead of scanning them.
- HTML:
```html
<section class="faq">
  <details class="faq__item">
    <summary></summary>
    <div class="faq__panel"></div>
  </details>
</section>
```
- CSS:
```css
.faq { display: grid; gap: 12px; }
.faq__item {
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 20px;
  padding: 20px 24px;
}
.faq__item[open] { box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08); }
```
- Inspiration: Product FAQ and pricing objection handling.

## 20. Footer Ecosystem
- Description: Footer behaves like a mini sitemap plus social proof strip, secondary CTA, and dense link groups.
- Use when: mature products with multiple entry points.
- Do not use when: the site is a one-page microsite with only two links.
- HTML:
```html
<footer class="ecosystem">
  <div class="ecosystem__cta"></div>
  <nav class="ecosystem__links"></nav>
</footer>
```
- CSS:
```css
.ecosystem {
  display: grid;
  gap: 40px;
  padding: 56px clamp(24px, 5vw, 80px);
}
.ecosystem__links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 24px;
}
```
- Inspiration: Stripe, Vercel, and ecosystem-heavy product sites.
