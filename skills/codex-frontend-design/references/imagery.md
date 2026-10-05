# Imagery and Visual Assets

Use this reference when selecting, generating, or integrating product imagery, illustrations, icons, textures, or motion assets. The goal is a deliberate, usable visual system; asset generation is not the default.

## Decide whether an asset helps

Inspect the incumbent design authority, available project assets, icon and font sets, and their provenance first. Give each candidate a user-facing role: for example, prove a claim, explain information, show a real product in use, orient a narrative, or provide atmosphere. Create or source an asset only when it materially improves communication, identity, interaction, or product fit over the best existing asset or a simpler HTML/CSS/native-control treatment.

- `persuade`: imagery must support a credible product claim or show the product in use; do not fabricate customers, product screens, logos, testimonials, or outcomes.
- `operate`: keep task controls and data legible; use the existing coherent icon set, aligned optically. A chart or status meaning should remain real interface content, not decorative artwork.
- `read`: prefer a clear diagram or labeled data visualization when it explains a relationship; avoid decoration that competes with reading.
- `experience`: atmosphere and narrative imagery are appropriate when they serve the user’s context; give meaningful images a caption or specific alternative text.

If no image-generation or source asset is available, do not imply one was created. Use an existing licensed asset, a simple CSS treatment, a semantic diagram, or a clearly identified placeholder when that is appropriate to the prototype.

## Brief an asset for its actual UI role

For a generated or newly sourced asset, capture these decisions in the prompt and in the existing `.codex/design/DIRECTION.md`, scoped audit note, or narrow-task handoff:

- user-facing role, target route/state, intended subject or action, and the benefit over the simpler alternative;
- visual family, material, lighting, texture, and palette that fit the selected direction;
- composition, focal point, negative space, and safe area for adjacent copy or controls;
- aspect ratio, transparency/background, intended rendered dimensions, and how the crop behaves;
- behavior at the project’s desktop, tablet, and mobile breakpoints: scale, crop, reposition, swap to a distinct art direction, simplify, or remove;
- format and approximate weight based on the actual use, plus source, license, generation provenance, and any fallback.

When prompting an image tool, describe the subject and function, art direction, composition and focal point, safe space, target placement/crop, palette/material, and production constraints. Keep essential product copy, prices, chart labels, and control text in HTML. Do not create near-duplicate files for each button or arbitrary width when responsive layout or CSS can solve it.

Do not create a separate asset inventory for the same work. Keep asset decisions and provenance with the existing direction, audit, or handoff; use the existing capture manifest for rendered evidence.

## Build the interface around the asset

HTML, CSS, and native components own layout, text, controls, focus, validation, loading, disabled and selected states, and interaction. Assets may provide real content, illustration, iconography, texture, or a decorative layer; they do not replace semantic controls or flatten a whole functional component into an image. A control must remain labeled and usable without its visual asset.

Choose the simplest suitable representation for the job. Use CSS for basic geometry, DOM text for UI copy, and a consistent source icon system for interface actions. Use raster imagery for photographic or painterly content when it improves the result; use vector formats for scalable geometry when appropriate. Pick formats and responsive variants from real browser support, transparency, rendered size, and measured delivery needs rather than a blanket conversion rule.

## Inspect before and after integration

1. Inspect a new asset by itself for the intended subject, composition, crop-safe area, artifacts, transparency, and consistency with the chosen visual direction. Reject or revise it if the result is misleading, ambiguous, visually incoherent, or unreadable at its intended size.
2. Integrate it into the real component and inspect the rendered page/state at the actual rendered size. Check the focal point and crop, neighboring copy, contrast, surrounding whitespace, and whether the asset supports the hierarchy instead of competing with it.
3. Check the chosen desktop, tablet, and mobile viewports, including project breakpoint edges when the asset materially affects layout. Verify the specified crop/reposition/swap behavior; do not assume scaling the desktop image is sufficient.
4. Exercise image-load failure or unavailable-source behavior where relevant. Preserve layout and essential content with a deliberate fallback. Confirm animated assets have a useful static or reduced-motion equivalent.
5. Check file size, decode, memory, or animation cost when measurable and material to the page. Simplify or remove an expensive layer if it harms responsiveness or task clarity.

Record a visual finding against the route, state, viewport, and capture key in the existing review evidence. A thumbnail or isolated asset preview alone does not verify its use in the interface.

## Accessibility and provenance

- Give meaningful images concise, purpose-specific alt text; avoid repeating nearby copy. Decorative images use empty alt (and decorative SVGs may be hidden from assistive technology).
- Icon-only controls need an accessible name from the semantic control. Never rely on an image, color, animation, or pointer effect as the only signal for a control or state.
- Keep essential instructions and product facts available as real text. Maintain text contrast when copy overlays imagery, and ensure keyboard focus and hit areas are not obscured.
- Record whether an asset is user-supplied, generated for this project, licensed, or from a named icon/open set. Verify license and permitted use for external assets; do not present unknown provenance as verified.

## Icons

Prefer one coherent icon family and optical size per surface. Mixing unrelated stroke weights or filled/outline styles weakens grouping unless the difference has a clear semantic role. Use accessible labels on icon-only actions.
