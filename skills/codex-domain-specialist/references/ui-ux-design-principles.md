# UI/UX Design Principles for Frontend Developers

## Scope and Triggers

Use this reference when:
- Building new UI components, pages, or layouts from scratch.
- Choosing colors, typography, or spacing for any project.
- Reviewing or refactoring visual consistency of an existing interface.
- Keywords: `ui design`, `ux design`, `visual hierarchy`, `color theory`, `typography`, `layout`, `whitespace`, `aesthetics`, `beautiful`, `gestalt`.

**Core Rule**: Design is not decoration. Every pixel communicates hierarchy, relationship, and intent. When this reference is loaded, evaluate every visual choice against a design principle — not just "does it work?" but "does it communicate correctly?"

---

## 1. Visual Hierarchy & Composition

The eye does not scan a page randomly. It follows patterns dictated by size, weight, color, contrast, and position. Control these and you control the user's attention.

### The Hierarchy Stack (Strongest → Weakest)

| Rank | Signal | Example |
| --- | --- | --- |
| 1 | **Size** | A 72px heading dominates everything below it |
| 2 | **Color / Contrast** | A bright CTA button on a muted background |
| 3 | **Weight / Boldness** | Bold label vs. regular body text |
| 4 | **Spatial Position** | Top-left content is read first (in LTR) |
| 5 | **Whitespace** | Isolated elements attract attention |
| 6 | **Depth / Elevation** | Elevated cards (shadow) feel "on top" |

**Rule**: Use **at most 3 levels of visual hierarchy** per section. If everything is bold, nothing is bold.

### Gestalt Principles (How the Brain Groups Elements)

| Principle | What It Means | CSS/Layout Implication |
| --- | --- | --- |
| **Proximity** | Elements close together are perceived as related | Use `gap` to group related items; use larger `margin` to separate unrelated groups |
| **Similarity** | Elements that look alike are perceived as related | Same `border-radius`, `color`, `font-size` for items in the same category |
| **Continuity** | The eye follows lines and curves | Align elements along a shared axis; use `grid` alignment |
| **Closure** | The brain completes incomplete shapes | Icons and logos can use open shapes; card outlines can be partial |
| **Figure-Ground** | The brain separates foreground from background | Use contrast, elevation (`box-shadow`), or blur (`backdrop-filter`) to establish layers |

### Reading Patterns

- **F-Pattern**: For text-heavy pages (blogs, docs). Users scan the top line, then the left edge. Place key info at the start of paragraphs.
- **Z-Pattern**: For minimal pages (landing pages, hero sections). Eye moves: top-left logo → top-right nav → diagonal to bottom-left content → bottom-right CTA.
- **Gutenberg Diagram**: For balanced layouts. The top-left is the "Primary Optical Area" (highest attention), bottom-right is the "Terminal Area" (CTA placement).

```
┌──────────────────────────────┐
│  ★ Primary Optical Area      │  👁️ Strong Fallow Area │
│  (Logo, headline)            │  (Navigation, search)   │
│──────────────────────────────│
│  👁️ Weak Fallow Area         │  ★ Terminal Area        │
│  (Secondary content)         │  (CTA, submit button)   │
└──────────────────────────────┘
```

**Rule**: Always place the primary CTA in the Terminal Area (bottom-right or center-bottom of the viewport).

---

## 2. Color Theory for UI

### The 60-30-10 Rule

Every interface should follow this ratio:

| Proportion | Role | Example |
| --- | --- | --- |
| **60%** | Dominant / Background | `--surface-0` (white or dark base) |
| **30%** | Secondary / Supporting | `--surface-1`, `--surface-2` (cards, sidebars) |
| **10%** | Accent / Action | `--brand-primary` (CTAs, links, active states) |

### Use HSL, Not HEX

HSL (Hue, Saturation, Lightness) is the designer's color model. It lets you create harmonious palettes by manipulating one axis at a time.

```css
:root {
  /* Base brand hue: 220 (blue) */
  --brand-h: 220;
  --brand-s: 85%;
  
  /* Generate palette by varying lightness */
  --brand-50:  hsl(var(--brand-h), var(--brand-s), 97%); /* Tint (bg) */
  --brand-100: hsl(var(--brand-h), var(--brand-s), 93%);
  --brand-200: hsl(var(--brand-h), var(--brand-s), 82%);
  --brand-300: hsl(var(--brand-h), var(--brand-s), 70%);
  --brand-400: hsl(var(--brand-h), var(--brand-s), 58%);
  --brand-500: hsl(var(--brand-h), var(--brand-s), 50%); /* Base */
  --brand-600: hsl(var(--brand-h), var(--brand-s), 42%);
  --brand-700: hsl(var(--brand-h), var(--brand-s), 33%);
  --brand-800: hsl(var(--brand-h), var(--brand-s), 24%);
  --brand-900: hsl(var(--brand-h), var(--brand-s), 15%); /* Shade (text) */
}
```

**Rule**: To create dark mode, do NOT just invert colors. Keep the same hue, reduce saturation by 10-20%, and flip the lightness scale (light backgrounds become dark, dark text becomes light).

### Contrast Ratios (WCAG)

| Element | Minimum Ratio | Target |
| --- | --- | --- |
| Body text | 4.5:1 | 7:1 (AAA) |
| Large text (≥ 18px bold, ≥ 24px regular) | 3:1 | 4.5:1 |
| UI components (borders, icons) | 3:1 | — |
| Decorative elements | No requirement | — |

**Rule**: Never use light gray text (`#ccc`) on white backgrounds. The minimum usable gray on white is approximately `#767676` (4.54:1 ratio).

### Emotional Color Mapping

| Emotion | Hue Range | Usage |
| --- | --- | --- |
| Trust, Calm | Blue (210-230) | Fintech, SaaS, Enterprise |
| Energy, Urgency | Red-Orange (0-30) | E-commerce CTAs, Alerts |
| Growth, Health | Green (120-160) | Wellness, Sustainability |
| Premium, Luxury | Purple (270-300) or Black/Gold | Fashion, High-end SaaS |
| Warmth, Friendliness | Yellow-Orange (30-50) | Food, Social, Community |
| Neutrality, Sophistication | Desaturated tones | Minimal portfolios, Editorial |

---

## 3. Typography Deep Dive

Typography is not "picking a font". It is controlling rhythm, scale, and readability.

### The Typographic Scale

Use a **modular scale** (ratio-based) instead of arbitrary sizes. Common ratios:

| Ratio | Name | Feel |
| --- | --- | --- |
| 1.200 | Minor Third | Compact, Dense UI |
| 1.250 | Major Third | Balanced, Readable |
| 1.333 | Perfect Fourth | Spacious, Editorial |
| 1.414 | Augmented Fourth | Dramatic, Creative |
| 1.618 | Golden Ratio | Classical, Luxurious |

```css
/* Major Third (1.250) scale from 16px base */
:root {
  --text-xs:   0.64rem;   /* 10.24px */
  --text-sm:   0.80rem;   /* 12.80px */
  --text-base: 1.00rem;   /* 16.00px */
  --text-lg:   1.25rem;   /* 20.00px */
  --text-xl:   1.563rem;  /* 25.00px */
  --text-2xl:  1.953rem;  /* 31.25px */
  --text-3xl:  2.441rem;  /* 39.06px */
  --text-4xl:  3.052rem;  /* 48.83px */
}
```

### Line Height (Leading) Formula

| Context | Line Height | Why |
| --- | --- | --- |
| Body text (14-18px) | 1.5–1.75 | Readability for long paragraphs |
| UI labels (12-14px) | 1.25–1.4 | Compact, fits in buttons/badges |
| Headings (24px+) | 1.1–1.25 | Large text needs tighter leading to look cohesive |
| Display text (48px+) | 0.9–1.1 | Massive text must feel like a block, not floating lines |

**Rule**: As font size increases, line height ratio **decreases**. A heading with `line-height: 1.75` looks disconnected.

### Letter Spacing (Tracking)

| Context | Tracking | CSS |
| --- | --- | --- |
| Body text | 0 (normal) | `letter-spacing: 0` |
| Headings (lowercase) | Slightly negative | `letter-spacing: -0.02em` |
| ALL CAPS labels | Positive | `letter-spacing: 0.05em–0.1em` |
| Display / Hero text | Tight negative | `letter-spacing: -0.03em` |

**Rule**: UPPERCASE text without extra tracking looks cramped and amateur.

### Font Pairing Strategy

| Combination | When to Use | Example |
| --- | --- | --- |
| Sans + Sans (different weights) | Clean, modern SaaS | `Inter` 700 headings + `Inter` 400 body |
| Serif heading + Sans body | Editorial, premium | `Playfair Display` + `Inter` |
| Geometric heading + Humanist body | Tech, startup | `Outfit` or `Montserrat` + `Source Sans 3` |
| Mono accent + Sans body | Dev tools, technical | `JetBrains Mono` labels + `Inter` body |

**Rule**: Never pair two decorative fonts. At most one "personality" font, paired with a neutral workhorse.

---

## 4. Whitespace (Negative Space)

Whitespace is not "empty" space. It is an active design element that creates breathing room, focus, and premium feel.

### Macro vs. Micro Whitespace

| Type | Where | Purpose |
| --- | --- | --- |
| **Macro** | Between sections, around hero, page margins | Creates rhythm and separation between major content blocks |
| **Micro** | Inside components (button padding, card spacing, line-height) | Creates comfort and readability within elements |

### The 8px Grid System

All spacing should be multiples of 8px. This creates visual consistency.

```css
:root {
  --space-1:  4px;   /* Exception: tight micro-spacing */
  --space-2:  8px;
  --space-3:  12px;  /* Exception: 1.5× for fine-tuning */
  --space-4:  16px;
  --space-5:  24px;
  --space-6:  32px;
  --space-8:  48px;  /* Section internal padding */
  --space-10: 64px;  /* Between sections */
  --space-12: 80px;  /* Hero padding */
  --space-16: 128px; /* Page-level vertical rhythm */
}
```

### The "Squint Test"

Blur your eyes (or apply a 10px Gaussian blur to a screenshot). If you can still identify the visual hierarchy and section boundaries, your whitespace and contrast are working. If everything blends into one gray block, you need more contrast and spacing.

**Rule**: When in doubt, add **more** whitespace. Cheap designs look cheap because things are too close together. Premium designs breathe.

---

## 5. Optical Alignment & Visual Balance

Mathematical centering is not always visual centering. The human eye perceives weight and balance differently from a ruler.

### Optical Centering Rules

| Scenario | Problem | Fix |
| --- | --- | --- |
| Text in a button | Text looks too low because descenders (g, p, y) pull the baseline down | Add 1-2px more `padding-top` than `padding-bottom` |
| Play icon (▶) in a circle | Triangle's center of mass is left of its bounding box center | Shift the icon ~2px to the right: `transform: translateX(2px)` |
| Icon + Text alignment | Icon sits on the baseline but looks too high | Align icons to `vertical-align: -0.125em` or use flexbox with `align-items: center` |
| Circle vs. Square at same size | Circle looks smaller than the square | Make circles ~6% larger to match perceived size |

### Visual Weight Hierarchy

| Element | Visual Weight | Implication |
| --- | --- | --- |
| Dark, saturated colors | Heavy | Use for anchoring elements (headers, CTAs) |
| Light, desaturated colors | Light | Use for backgrounds, secondary info |
| Dense textures / patterns | Heavy | Use sparingly; they compete for attention |
| Large elements | Heavy | Balance with whitespace on opposite side |
| Isolated elements | Heavy (by contrast) | An element surrounded by whitespace draws the eye |

**Rule**: Balance a page like a seesaw. If the left side has a heavy image, the right side needs either a heavy heading or ample whitespace to counterbalance.

---

## 6. Viewport-Fit Section Design (One Screen = One Section)

> **This is the most violated layout principle in developer-generated UI.** Each section of a page must be a self-contained, complete visual unit that fits within one viewport frame at 100% zoom (1920×1080 reference resolution). The user should never need to scroll *within* a section to understand its content.

### The Golden Rule

> **One scroll stop = one complete thought.** If a section requires scrolling to see its footer, CTA, or conclusion, the section is too tall. Reduce content, split into two sections, or restructure the layout.

### Content Budget Per Section

At 100% zoom on a 1920×1080 viewport, usable height ≈ **900px** (after browser chrome). Budget content accordingly:

| Section Type | Max Content Elements | Height Budget |
| --- | --- | --- |
| **Hero** | 1 heading + 1 subtitle + 1 CTA + 1 visual | `100vh` (full viewport) |
| **Feature showcase** | 1 heading + 3-4 feature cards (horizontal) | `100vh` |
| **Social proof / Testimonials** | 1 heading + 3 testimonial cards | `100vh` |
| **Stats / Metrics** | 1 heading + 4-6 stat counters (horizontal) | `60vh–80vh` |
| **CTA / Footer** | 1 heading + 1 CTA + contact info | `50vh–70vh` |

**Rule**: If you count more than **5 distinct visual elements** vertically stacked in a section, the section WILL overflow. Restructure horizontally or split.

### CSS Patterns for Viewport-Fit Sections

```css
/* Base section: exactly one viewport tall */
.section-viewport {
  min-height: 100vh;
  min-height: 100dvh; /* Dynamic viewport height (accounts for mobile toolbar) */
  max-height: 100vh;  /* CRITICAL: prevent overflow beyond viewport */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: clamp(2rem, 5vh, 5rem) clamp(1rem, 5vw, 6rem);
  overflow: hidden;   /* Clip anything that overflows */
}

/* Hero: MUST be exactly one viewport */
.hero {
  height: 100vh;
  height: 100dvh;
  display: grid;
  grid-template-rows: auto 1fr auto; /* nav / content / scroll-hint */
  padding: var(--space-5) var(--space-6);
}

/* Responsive font sizing that scales WITH viewport */
.hero h1 {
  font-size: clamp(2rem, 5vw + 1rem, 5rem); /* Scales with viewport */
  line-height: 1.05;
}
```

### The Viewport Overflow Audit

Before finalizing any section, verify:

1. **Resolution test**: Open browser at exactly 1920×1080 (100% zoom). Does every section fit completely without scrolling within it?
2. **Content count**: Count vertical elements. More than 5 stacked? → Restructure to horizontal layout or split.
3. **Font size check**: Is the heading so large that it pushes content below the fold? → Use `clamp()` with `vw` units.
4. **Padding check**: Is there excessive padding eating viewport space? → Use `clamp()` for responsive padding.
5. **Card overflow**: Do cards stack vertically on desktop? → Force horizontal layout with `grid-template-columns` at desktop widths.

### Layout Restructuring Strategies (When Content Overflows)

| Problem | Solution |
| --- | --- |
| Hero has heading + subtitle + tags + CTA + stats | Move stats to a separate section below hero |
| Too many feature cards stacking vertically | Use horizontal grid (`repeat(3, 1fr)` or `repeat(4, 1fr)`) |
| Long descriptions pushing content down | Truncate to 1-2 lines; use tooltips or expandable panels for details |
| Multiple CTA buttons + explanatory text | Keep 1 primary CTA + 1 secondary link; remove bullet-point explanations |
| Navigation sidebar + main content both too tall | Make sidebar sticky (`position: sticky; top: 0; height: 100vh`) |

### The Hero Section Budget (Specific)

The Hero is the most critical section. It MUST contain exactly:
1. **One** primary heading (large, bold)
2. **One** supporting subtitle (1-2 lines max)
3. **One** primary CTA button (+ optional secondary link)
4. **One** visual element (image, 3D, animation, or illustration)

**DO NOT put** in the hero: stats counters, bullet point lists, multiple tag badges, social proof, secondary navigation, or explanatory paragraphs. Those belong in subsequent sections.

```
┌─────────────────────────────────────────────────────┐
│  [Nav]                                    [CTA Nav] │ ← 60px
│                                                     │
│  HEADING (large, clamp-sized)                       │
│  Subtitle (1-2 lines)             [Visual/3D/Image] │ ← 500-600px
│  [Primary CTA]  [Secondary Link]                    │
│                                                     │
│  ↓ Scroll indicator                                 │ ← 40px
└─────────────────────────────────────────────────────┘
  TOTAL: ≤ 100vh (≈ 900px usable at 1080p)
```

---

## 7. Layout Patterns Beyond the Grid

### The Bento Grid

Popularized by Apple. Irregular grid cells of varying sizes create visual interest while maintaining alignment.

```css
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: auto;
  gap: var(--space-4);
}

.bento-grid .feature-large {
  grid-column: span 2;
  grid-row: span 2;
}

.bento-grid .feature-wide {
  grid-column: span 2;
}

.bento-grid .feature-tall {
  grid-row: span 2;
}
```

### The Asymmetric Split

Instead of equal 50/50 columns, use 60/40 or 65/35. The asymmetry creates visual tension and directs the eye.

```css
.split-layout {
  display: grid;
  grid-template-columns: 1.6fr 1fr; /* Golden-ratio-ish split */
  gap: var(--space-8);
  align-items: center;
}
```

### The Full-Bleed + Contained Hybrid

Alternate between full-width immersive sections and contained, readable content sections.

```css
.section-full {
  width: 100vw;
  margin-left: calc(-50vw + 50%);
  padding: var(--space-16) var(--space-6);
}

.section-contained {
  max-width: 72rem; /* 1152px */
  margin-inline: auto;
  padding: var(--space-10) var(--space-6);
}
```

---

## 8. Imagery & Visual Assets

### Image Treatment Rules

| Context | Treatment |
| --- | --- |
| Hero background | Darken overlay (`rgba(0,0,0,0.4)`) + blur for text readability |
| Product showcase | Clean white/gradient background, consistent lighting, slight shadow |
| Avatar / Profile | Always circular (`border-radius: 50%`), consistent size, fallback initials |
| Decorative illustration | Use SVG for crisp scaling; match brand colors |
| Screenshot / UI preview | Add a subtle shadow + rounded corners to frame it; never flat-embed |

### The "No Placeholder" Rule

Never use gray boxes or `placeholder.com` images. Every image should either be:
1. A real, relevant image.
2. A generated image (use image generation tools).
3. A styled gradient or abstract SVG pattern.

---

## 9. Responsive Design Philosophy

### Content-First Breakpoints

Do not use arbitrary breakpoints (640px, 768px, 1024px) by default. Instead:
1. Start with the smallest screen.
2. Resize until the layout breaks.
3. Add a breakpoint at **that** width.

### Component-Level Responsiveness

Use `container queries` (modern CSS) instead of viewport media queries when the component's own size determines its layout:

```css
.card-container {
  container-type: inline-size;
}

@container (min-width: 400px) {
  .card {
    flex-direction: row; /* Horizontal layout when card container is wide enough */
  }
}
```

### Touch Target Size

| Device | Minimum Touch Target | Recommended |
| --- | --- | --- |
| Mobile | 44×44px (Apple HIG) | 48×48px (Material) |
| Tablet | 44×44px | 44×44px |
| Desktop pointer | 32×32px | 40×40px |

---

## 10. Shadows & Depth System

### Layered Shadow Technique

A single `box-shadow` looks flat. Use **multiple layered shadows** for realistic depth:

```css
:root {
  /* Elevation 1: Subtle lift (cards, inputs) */
  --shadow-1:
    0 1px 2px rgba(0, 0, 0, 0.04),
    0 1px 3px rgba(0, 0, 0, 0.06);

  /* Elevation 2: Raised (dropdowns, popovers) */
  --shadow-2:
    0 2px 4px rgba(0, 0, 0, 0.04),
    0 4px 8px rgba(0, 0, 0, 0.06),
    0 8px 16px rgba(0, 0, 0, 0.04);

  /* Elevation 3: Floating (modals, dialogs) */
  --shadow-3:
    0 4px 8px rgba(0, 0, 0, 0.04),
    0 8px 16px rgba(0, 0, 0, 0.06),
    0 16px 32px rgba(0, 0, 0, 0.08),
    0 32px 64px rgba(0, 0, 0, 0.06);
}
```

### Colored Shadows

For a premium, modern feel, tint shadows with the element's dominant color:

```css
.card-blue {
  background: hsl(220, 85%, 50%);
  box-shadow:
    0 4px 12px hsla(220, 85%, 40%, 0.25),
    0 12px 24px hsla(220, 85%, 30%, 0.15);
}
```

**Rule**: Never use pure black shadows (`rgba(0,0,0,...)`) on colored elements. Tint the shadow to match the object's hue for realism.

---

## 11. Border & Divider Strategy

### The "Less Borders, More Space" Rule

Borders are the most overused element in developer-designed UIs. Reduce them:

| Instead Of | Use |
| --- | --- |
| `border: 1px solid #ccc` between cards | `gap: var(--space-5)` with whitespace |
| `border-bottom` between list items | Alternating `background-color` (zebra striping) or just spacing |
| `border` around inputs | `box-shadow` focus ring + subtle background color |
| `border` to separate sidebar | Background color difference or elevation (shadow) |

```css
/* Instead of this: */
.input-bordered {
  border: 1px solid #ccc;
}

/* Do this: */
.input-elevated {
  background: var(--surface-1);
  box-shadow: var(--shadow-1);
  border: 1px solid transparent; /* Reserve for focus state */
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-elevated:focus {
  border-color: var(--brand-500);
  box-shadow: 0 0 0 3px hsla(var(--brand-h), var(--brand-s), 50%, 0.15);
}
```

---

## 12. Anti-Patterns (Developer Design Sins)

1. ❌ **Bad**: Using the same font size for everything (16px body, 18px heading).
   ✅ **Good**: Use a modular scale with at least 3 distinct hierarchy levels (body, subhead, heading).

2. ❌ **Bad**: Gray text on gray background (`#999 on #f5f5f5` = 2.8:1 ratio, fails WCAG).
   ✅ **Good**: Check contrast ratio. Minimum `#767676` on white (4.54:1).

3. ❌ **Bad**: Equal padding on all sides of a button (looks vertically off-center).
   ✅ **Good**: Add 1-2px more top padding to optically center the text baseline.

4. ❌ **Bad**: Using 12 different spacing values across the page (14px, 17px, 22px, 25px...).
   ✅ **Good**: Stick to the 8px grid. Every spacing value must be a multiple of 4 or 8.

5. ❌ **Bad**: Centering every section on the page (creates a "word document" feel).
   ✅ **Good**: Mix left-aligned content with center-aligned hero. Use asymmetric splits.

6. ❌ **Bad**: Using borders to separate every component.
   ✅ **Good**: Use whitespace, background color differences, or subtle shadows instead.

7. ❌ **Bad**: Making all interactive elements the same primary color.
   ✅ **Good**: Primary CTA gets the accent color. Secondary actions get a ghost/outline style. Tertiary actions get text-only style.

8. ❌ **Bad**: Ignoring hover/focus/active states ("the button just sits there").
   ✅ **Good**: Every interactive element needs at minimum: `hover`, `focus-visible`, `active`, and `disabled` states.

9. ❌ **Bad**: Using stock photos of people shaking hands or pointing at screens.
   ✅ **Good**: Use product screenshots, custom illustrations, or abstract gradients. Authenticity > generic stock.

10. ❌ **Bad**: Designing only for the "happy path" (full data, everything loaded).
    ✅ **Good**: Design empty states, loading skeletons, error states, and edge cases (long names, missing images).

---

## Cross-References

- `creative-ui-ux.md` for animation orchestration, GSAP, Three.js, and storytelling flow.
- `css-architecture.md` for CSS token structure and style organization.
- `frontend-rules.md` for component architecture and rendering performance.
- `accessibility-rules.md` for semantic HTML and WCAG compliance alongside visual design.
- `vietnamese-typography.md` for Vietnamese-specific font and encoding rules.
- `performance-rules.md` for image optimization and rendering budgets.
