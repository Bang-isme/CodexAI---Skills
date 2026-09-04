# Design Knowledge Provenance

This document records where CodexAI 16.0 design guidance came from and what was written new. Canonical skill source remains `skills/`. Antigravity packages are built from that source.

## License posture

- The plugin stays MIT (`LICENSE`).
- Third-party notices live in `THIRD_PARTY_NOTICES.md`.
- No Impeccable source, Chrome extension, live-mode adapters, Neuform sync, GSAP/Three runtimes, or 81 style presets are vendored.
- If Apache-2.0 code is ever vendored later, it must live under `third_party/` with its LICENSE/NOTICE and a local modification marker. Default is not to vendor.

## Source map

| Topic | Origin | What landed here | What was excluded |
| --- | --- | --- | --- |
| Product truth vs visual truth | Impeccable skill principles (Apache-2.0) rewritten | `codex-creative-direction`, `codex-design-system` grammar | Verbatim Impeccable prose, extension runtime, paid-service assumptions |
| Visitor / surface modes `persuade\|operate\|read\|experience` | Impeccable visitor-mode idea rewritten | `codex-design-system/references/grammar.md` | Chrome live-mode, framework adapters |
| Design-first prompting and bounded questions | Skills-main agent-skills + existing Codex intent skill | `codex-intent-context-analyzer` sparse interview | Long interviews on narrow tasks |
| Art direction, originality, category-default resistance | Impeccable + Skills-main originality principles rewritten | `codex-creative-direction` | 81 style presets, trend-year catalogs |
| Motion as purpose, not decoration | Impeccable motion discipline rewritten | `codex-design-system/references/motion.md` | Bundled GSAP/Three runtimes |
| Detector categories (hierarchy, density, contrast, states) | Impeccable detector *categories* only | `codex-visual-quality-gate` mechanical checks | `impeccable detect` as a required runtime; no auto-install |
| Landing/pricing structure and Awwwards-quality workflow | Skills-main site workflow rewritten as grammar | `codex-ui-ux-design`, composition/layout references | Game/social/media automation skills |
| Optical balance / squint test / spacing rhythm | New CodexAI design, informed by the sources above | `codex-design-system/references/composition.md` | Fake numeric “absolute balance” scores |
| Product/surface context files | New CodexAI design | `.codex/design/PRODUCT.md`, `.codex/design/surfaces/<slug>.md` | Writes without `--apply` |
| Optional local Node detector | New adapter around an optional local binary | `visual_quality_gate.py` doctor `available\|skipped\|failed` | Network install, npx install, blocking Python core |

## Conditional grammar, not style catalogs

Presets in `codex-design-system/references/palettes.md` and `typography.md` remain optional catalogs. They lose to:

1. Product facts in the brief or `.codex/design/PRODUCT.md`
2. An incumbent design system / `DESIGN.md`
3. Surface mode (`persuade|operate|read|experience`)
4. Change mode (`extend|refine|redesign|new`)

Do not claim aesthetic objectivity from mechanical checks. Mechanical evidence is source-provable. Rendered visual judgment requires independent review or an explicit `DEGRADED` disclosure.
