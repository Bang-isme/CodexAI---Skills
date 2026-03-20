# Composition

This file is the decision layer for non-designers. Use it before selecting component styles so the UI has hierarchy, breathing room, and narrative flow instead of a "developer default" look.

## Visual Hierarchy
- Start with one focal point per viewport: the headline, the hero visual, or the primary metric. Do not let all three compete.
- Create hierarchy with four levers:
  - Size: `48-72px` for hero headlines, `28-40px` for section headings, `16-18px` for body.
  - Weight: reserve `700-800` for primary emphasis; use `400-500` for body.
  - Color: strongest contrast belongs to the most important action or heading.
  - Spacing: give focal content more surrounding space than supporting content.
- If everything looks equally loud, reduce at least one of: color saturation, font size, or motion frequency.

## Whitespace
- Use a simple spacing scale: `4, 8, 12, 16, 24, 32, 48, 64, 96`.
- Common defaults:
  - inside compact controls: `8-12px`
  - card padding: `20-32px`
  - section spacing: `64-120px`
  - layout gaps: `16-32px`
- Use more whitespace for premium, editorial, and luxury surfaces. Use tighter spacing only for dense dashboards or data tables.
- Empty space is not wasted space if it makes the call to action easier to spot.

## Alignment and Grids
- Use an `8px` grid for most product UI. If the product is type-heavy, a `4px` baseline helps text rhythm.
- Responsive breakpoints:
  - mobile: `0-639px`
  - tablet: `640-1023px`
  - laptop: `1024-1439px`
  - desktop: `1440px+`
- Align components to shared edges. Misaligned cards, labels, and buttons are one of the fastest ways to make a UI feel amateur.
- Limit page widths:
  - reading content: `60-72ch`
  - dashboard canvas: `1200-1440px`
  - marketing hero: `1100-1280px`

## Contrast and Emphasis
- Maintain clear text/background contrast. Body copy should hit at least WCAG AA on its base surface.
- Use contrast in different dimensions, not only color:
  - large heading + quiet subcopy
  - bold CTA + muted secondary action
  - large card + two small supporting cards
- If the interface already has strong color, use size or spacing to create emphasis instead of adding more accent colors.

## Repetition and Consistency
- Reuse tokens:
```css
:root {
  --space-2: 8px;
  --space-4: 16px;
  --space-6: 24px;
  --radius-lg: 24px;
  --shadow-soft: 0 18px 48px rgba(15, 23, 42, 0.12);
}
```
- Repetition builds trust. Reuse the same radius family, shadow family, heading scale, and interaction timings.
- Do not change spacing or border radius arbitrarily between sibling components.

## Proximity and Grouping
- Items placed near each other are read as related. Use this deliberately:
  - label + helper text should sit closer together than label + next form group
  - card title + stat should sit closer than one card to the next
- Use Gestalt principles in plain terms:
  - proximity = related
  - similarity = same behavior or type
  - continuity = guide the eye across steps or flows
  - closure = let the user infer a group from a shared boundary or background

## Color Psychology
- Warm colors: energetic, urgent, emotional. Good for commerce, media, campaigns.
- Cool colors: calm, trustworthy, technical. Good for SaaS, fintech, dashboards.
- Neutrals: stable, premium, understated. Good for luxury, editorial, internal tools.
- Bright accents should be sparse. If everything is accent-colored, nothing is important.

## Visual Storytelling
- Landing-page sequence:
  1. hero: what this is
  2. problem: why it matters
  3. solution: how it works
  4. proof: data, customers, screenshots
  5. CTA: what to do next
- Product page sequence:
  1. task framing
  2. primary workflow
  3. supporting features
  4. objections / FAQ
  5. conversion or onboarding action

## F-Pattern and Z-Pattern
- Use F-pattern for dense text pages, docs, and blog content. Keep left alignment strong and headings scannable.
- Use Z-pattern for simple landing pages: top-left identity, top-right utility, central hero, bottom-right CTA.
- If the layout is visual-first, keep the CTA on the natural reading exit path.

## Progressive Disclosure
- Show the essential action first, then reveal depth through tabs, accordions, drawers, or secondary panels.
- Good examples:
  - compact summary card -> "View details"
  - settings overview -> advanced options drawer
  - pricing headline -> expandable plan details
- Avoid exposing every control by default when the main user task only needs three or four.

## Emotional Design
- Delight comes from restraint: one polished hover, one strong empty state, one friendly success state is enough.
- Add personality through:
  - headline tone
  - accent motion
  - illustration framing
  - microcopy around CTA or state changes
- Do not turn serious workflows into playful motion playgrounds.

## Image and Illustration Framing
- Recommended aspect ratios:
  - hero mockups: `16:10` or `4:3`
  - editorial images: `3:4` or `4:5`
  - testimonial avatars: `1:1`
- Use overlays when images are busy:
```css
.image-overlay::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(10, 15, 24, 0) 20%, rgba(10, 15, 24, 0.56) 100%);
}
```
- Do not stretch imagery to fill arbitrary boxes. Crop intentionally and preserve a single visual focal point.
