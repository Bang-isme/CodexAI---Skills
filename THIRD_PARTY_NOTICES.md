# Third-Party Notices

CodexAI Skill Pack is licensed under the MIT License. This file records third-party material that influenced the pack. No third-party source is copied verbatim into this repository.

## Impeccable

- Project: Impeccable (`impeccable-ext`)
- License: Apache License 2.0
- Use in this pack: design *principles* were rewritten into original CodexAI skills and references (product vs visual truth, visitor/surface modes, art direction, motion purpose, originality boundaries, detector categories).
- Not included: Chrome extension, live-mode framework adapters, Neuform sync, bundled runtimes, paid-service assumptions, or any Apache source under `third_party/`.
- Optional runtime: if a user already has a local `impeccable` CLI, `visual_quality_gate.py` may invoke `npx --no-install impeccable detect` or that local binary. The pack never installs the package and never treats the detector as required.

## Skills (Meng To / agent-skills)

- Project: Skills-main `Skills/agent-skills`
- License: MIT
- Use in this pack: design-first prompting, originality, landing/pricing structure, and bounded verification *principles* were rewritten into CodexAI skills.
- Not included: game, social, or media automation skills; Codex-browser-only flows; Managed Agents API deployment.

## Google Antigravity

- Project: Antigravity IDE/CLI plugin format
- Use in this pack: native plugin templates, builder, installer, and validators target locally documented Antigravity surfaces (`plugin.json`, `skills/`, `agents/`, `rules/`, `hooks.json`).
- Status: the built plugin is a **native package candidate** until live IDE and CLI smoke is recorded. Documentation must not claim “fully native” before that evidence exists.

## Notice on future Apache vendoring

This release does not vendor Apache-2.0 code. If a later release vendors any Apache file, it must be placed under `third_party/`, keep upstream LICENSE and NOTICE, and mark locally modified files.
