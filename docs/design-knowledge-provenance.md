# Design Knowledge Provenance

This document records where CodexAI 17.0 design guidance came from and what was written new. Canonical skill source remains `skills/`. Antigravity packages are built from that source.

## License posture

- The plugin stays MIT (`LICENSE`).
- Third-party notices live in `THIRD_PARTY_NOTICES.md`.
- No Impeccable source, Chrome extension, live-mode adapters, Neuform sync, GSAP/Three runtimes, or 81 style presets are vendored.
- Curated MengTo craft is SKILL.md text plus snippets only. Demo HTML and vendored JS were not copied.
- If Apache-2.0 code is ever vendored later, it must live under `third_party/` with its LICENSE/NOTICE and a local modification marker. Default is not to vendor.

## Source map

| Topic | Origin | What landed here | What was excluded |
| --- | --- | --- | --- |
| Fast vs studio frontend path | CodexAI 17 rewrite | `codex-frontend-design` | Five-skill ceremony before pixels |
| Product truth vs visual truth | Impeccable skill principles (Apache-2.0) rewritten | `codex-frontend-design/references/grammar.md` | Verbatim Impeccable prose, extension runtime |
| Visitor / surface modes | Impeccable visitor-mode idea rewritten | `codex-frontend-design/references/grammar.md` | Chrome live-mode, framework adapters |
| Art direction and originality | Impeccable + Skills-main principles rewritten | `codex-frontend-design` studio mode | 81 style presets |
| Motion as purpose | Impeccable motion discipline rewritten | `codex-frontend-design/references/motion.md` | Bundled GSAP/Three runtimes |
| Detector categories | Impeccable detector categories only | `codex-visual-quality-gate` mechanical checks | `impeccable detect` as a required runtime |
| Landing/pricing structure | Skills-main site workflow rewritten | `codex-frontend-design/references/landing-page-anatomy.md` | Game/social/media automation skills |
| Frontend craft recipes | [MengTo/Skills](https://github.com/MengTo/Skills) curated SKILL.md, imported 2026-09-20 | `codex-frontend-implementation/craft/` + `PROVENANCE.md` | Demo HTML, vendored JS, remaining ~120 skills |
| 17 refinement dials | Impeccable dials rewritten as workflows | `codex-frontend-design/references/refinement-dials.md`, `.workflows/refine.md` | Chrome live-mode |
| Full-page capture helper | MengTo stitched-full-page-capture, ported to Playwright | `codex-visual-quality-gate/scripts/stitch_full_page_capture.mjs` | macOS `sips` dependency, auto-install |
| Optical balance / squint test | New CodexAI design | `codex-frontend-design/references/composition.md` | Fake numeric absolute-balance scores |
| Product/surface context files | New CodexAI design | `.codex/design/PRODUCT.md`, `.codex/design/surfaces/<slug>.md` | Writes without `--apply` |
| Optional local Node detector | New adapter around an optional local binary | `visual_quality_gate.py` doctor `available|skipped|failed` | Network install, blocking Python core |

## Conditional grammar, not style catalogs

Presets in `codex-frontend-design/references/palettes.md` and `typography.md` remain optional catalogs. They lose to:

1. Product facts in the brief or `.codex/design/PRODUCT.md`
2. An incumbent design system / `DESIGN.md`
3. Surface mode (`persuade|operate|read|experience`)
4. Change mode (`extend|refine|redesign|new`)

Do not claim aesthetic objectivity from mechanical checks. Mechanical evidence is source-provable. Rendered visual judgment requires independent review or an explicit `DEGRADED` disclosure.
