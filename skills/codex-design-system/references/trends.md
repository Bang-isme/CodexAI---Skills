# Trends

Current trend synthesis from [Awwwards](https://www.awwwards.com/), [Webflow](https://webflow.com/blog/web-design-trends), [Framer](https://www.framer.com/blog/), motion libraries, and 2025-2026 design roundups. Use trends as a direction, not as a blanket style preset.

## 1. Glassmorphism
- Description: Frosted surfaces, translucent panels, and strong separation between foreground and atmospheric background remain common in premium SaaS and finance marketing, especially when paired with dark themes and mesh light.
- Code signature:
```css
.glass {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(22px);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
}
```
- Use when: premium marketing, dashboards, hero callouts.
- Avoid when: content density is high or browser support/performance is tight.
- Example site: [https://www.framer.com/](https://www.framer.com/)

## 2. Neubrutalism
- Description: Heavy outlines, flat fills, hard shadows, and intentionally raw composition push interfaces away from polished corporate sameness.
- Code signature:
```css
.brutal {
  border: 3px solid #111827;
  border-radius: 20px;
  box-shadow: 8px 8px 0 #111827;
}
```
- Use when: playful brands, experimental products, portfolios.
- Avoid when: fintech, healthcare, or formal enterprise trust is the priority.
- Example site: [https://www.awwwards.com/](https://www.awwwards.com/)

## 3. Bento Grid
- Description: Feature blocks of different sizes remain one of the defining SaaS patterns because they communicate range without a repetitive card wall.
- Code signature:
```css
.bento {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 24px;
}
```
- Use when: launch pages, AI tools, product storytelling.
- Avoid when: long-form editorial copy is primary.
- Example site: [https://linear.app/](https://linear.app/)

## 4. Aurora / Mesh Gradients
- Description: Soft blended gradients replace flat single-color fills and make otherwise minimal interfaces feel current and atmospheric.
- Code signature:
```css
.aurora {
  background:
    radial-gradient(circle at 20% 20%, rgba(34, 211, 238, 0.32), transparent 30%),
    radial-gradient(circle at 80% 20%, rgba(168, 85, 247, 0.28), transparent 32%),
    radial-gradient(circle at 50% 80%, rgba(16, 185, 129, 0.26), transparent 28%),
    #0b1020;
}
```
- Use when: hero backgrounds, empty states, premium dashboards.
- Avoid when: brand requires flat, restrained, low-chroma surfaces.
- Example site: [https://vercel.com/](https://vercel.com/)

## 5. 3D Elements
- Description: Lightweight 3D icons, floating product objects, and volumetric illustrations are showing up in campaigns and AI products to make abstract concepts feel tangible.
- Code signature:
```css
.float-3d {
  transform: perspective(1200px) rotateX(8deg) rotateY(-12deg);
  filter: drop-shadow(0 24px 48px rgba(15, 23, 42, 0.22));
}
```
- Use when: concept-heavy products need a memorable visual anchor.
- Avoid when: performance, realism, or art direction budget is limited.
- Example site: [https://www.airbnb.com/](https://www.airbnb.com/)

## 6. AI-Native Interfaces
- Description: Prompt bars, suggested actions, chat-plus-canvas layouts, and confidence/explanation blocks are becoming a recognizable interface language for AI products.
- Code signature:
```css
.assistant-shell {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 24px;
}
```
- Use when: AI copilots, research assistants, search experiences.
- Avoid when: the product is not genuinely conversational or generative.
- Example site: [https://www.perplexity.ai/](https://www.perplexity.ai/)

## 7. Dark Mode First
- Description: More products now treat dark surfaces as the primary art direction instead of an optional theme, especially in devtools, AI, and creator software.
- Code signature:
```css
:root {
  color-scheme: dark;
  --bg: #0b1020;
  --surface: #11182d;
  --text: #e5eef8;
}
```
- Use when: OLED-heavy audiences, technical products, motion-rich UIs.
- Avoid when: long-form reading and daylight usage dominate.
- Example site: [https://linear.app/](https://linear.app/)

## 8. Micro-Animations Everywhere
- Description: Small, purposeful transitions now do more trust-building than flashy full-screen animations. Users expect polished hover, focus, and state changes.
- Code signature:
```css
.interactive {
  transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
}
```
- Use when: product UI, conversion flows, premium brand touches.
- Avoid when: every element already animates and cognitive load is high.
- Example site: [https://www.raycast.com/](https://www.raycast.com/)

## 9. Variable Fonts
- Description: Variable fonts are increasingly practical on the web because they reduce payload fragmentation while letting designers tune optical size, softness, width, and weight.
- Code signature:
```css
.headline {
  font-family: "Fraunces", serif;
  font-variation-settings: "SOFT" 50, "WONK" 0;
}
```
- Use when: typography is part of the brand story.
- Avoid when: the browser target or build pipeline cannot reliably handle font loading.
- Example site: [https://fonts.google.com/variablefonts](https://fonts.google.com/variablefonts)

## 10. Claymorphism
- Description: Soft extruded surfaces and rounded, tactile cards still appear in playful consumer apps, though they now work best in moderation rather than as a full UI system.
- Code signature:
```css
.clay {
  border-radius: 28px;
  background: #f5f7fb;
  box-shadow: 14px 14px 28px rgba(148, 163, 184, 0.25), -10px -10px 20px rgba(255, 255, 255, 0.7);
}
```
- Use when: playful onboarding, education, kid-facing products.
- Avoid when: dense information, dark mode, or accessibility contrast are more important.
- Example site: [https://dribbble.com/tags/claymorphism](https://dribbble.com/tags/claymorphism)

## 11. Retro / Y2K Revival
- Description: Chrome gradients, pixel-ish details, reflective metal effects, and loud accent color pairings are back, especially in music, fashion, and campaign work.
- Code signature:
```css
.y2k {
  background: linear-gradient(180deg, #f8d8ff 0%, #a5f3fc 100%);
  border: 1px solid rgba(255,255,255,0.6);
}
```
- Use when: campaigns, entertainment, fashion, youth brands.
- Avoid when: you need timelessness or enterprise trust.
- Example site: [https://open.spotify.com/](https://open.spotify.com/)

## 12. Kinetic Typography
- Description: Headline motion, text wipes, and animated word swaps are increasingly used as the hero itself, replacing static illustrations.
- Code signature:
```css
.kinetic span {
  display: inline-block;
  animation: lift 700ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
```
- Use when: copy is the core brand asset.
- Avoid when: motion distracts from task completion or accessibility is not addressed.
- Example site: [https://www.apple.com/](https://www.apple.com/)

## 13. Oversized Typography
- Description: Huge type blocks anchor the layout and reduce dependence on decorative graphics. This is especially common in agency, editorial, and premium SaaS sites.
- Code signature:
```css
.display {
  font-size: clamp(3.5rem, 8vw, 8rem);
  line-height: 0.92;
  letter-spacing: -0.04em;
}
```
- Use when: a strong statement or category claim matters more than showing many features above the fold.
- Avoid when: the copy is long, technical, or translation-heavy.
- Example site: [https://stripe.com/](https://stripe.com/)

## 14. Organic / Blob Shapes
- Description: Soft asymmetric shapes, rounded masks, and freeform backplates keep layouts from feeling too boxed-in.
- Code signature:
```css
.blob {
  border-radius: 45% 55% 60% 40% / 42% 38% 62% 58%;
}
```
- Use when: consumer, wellness, creative, or playful products.
- Avoid when: the product language should feel precise and strict.
- Example site: [https://mailchimp.com/](https://mailchimp.com/)

## 15. Grain / Noise Textures
- Description: Subtle grain overlays add tactile richness to otherwise flat surfaces and help gradients or large color fields feel less synthetic.
- Code signature:
```css
.grain::after {
  content: "";
  position: absolute;
  inset: 0;
  opacity: 0.08;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)' opacity='.5'/%3E%3C/svg%3E");
  pointer-events: none;
}
```
- Use when: editorial, luxury, campaign, dark hero sections.
- Avoid when: the UI already has too much visual texture or needs extreme sharpness.
- Example site: [https://pitch.com/](https://pitch.com/)
