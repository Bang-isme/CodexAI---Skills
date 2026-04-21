# DESIGN.md Integration Playbook

## Role Split Inside This Skill Pack

Use the two design skills together, but for different jobs:

| Skill | Job |
| --- | --- |
| `codex-design-system` | choose palettes, fonts, layout patterns, motion, composition, anti-pattern avoidance |
| `codex-design-md` | turn those choices into a durable, lintable, exportable contract |

## When To Reach For DESIGN.md

Use `DESIGN.md` when at least one of these is true:

- the project will span multiple UI sessions and needs continuity
- multiple agents or contributors need the same visual contract
- you want a machine-readable bridge to Tailwind or DTCG
- UI output drift has become a recurring problem

Do not force `DESIGN.md` for a tiny one-off tweak where no persistent design contract is needed.

## Pack-Specific Workflow

1. Use `codex-design-system` to choose a palette, typography pair, and layout language.
2. Run `design_contract.py scaffold` to create `DESIGN.md`.
3. Replace scaffold defaults with the chosen tokens and rationale.
4. Run `design_contract.py lint DESIGN.md`.
5. Keep the contract under version control and review `diff` output for regressions.
6. Export to Tailwind or DTCG only after the contract is stable.

## Suggested Placement In App Repos

- put `DESIGN.md` at the project root when it is a top-level product contract
- keep exported `tailwind.theme.json` or `tokens.json` adjacent to the consuming config if needed
- if a monorepo has multiple brands, keep one `DESIGN.md` per product surface instead of one overstuffed global file

## Good Contract Characteristics

- exact token values, not abstract adjectives
- clear section rationale that explains how and when to use tokens
- component-level examples for the highest-risk UI surfaces such as buttons, cards, and navigation
- small enough to review, strong enough to guide generation

## Common Failure Modes

- copying palette values into prose but not tokens
- skipping component tokens for core surfaces
- writing a beautiful contract but never linting it
- exporting to Tailwind before the contract is stable
- using `DESIGN.md` as a dumping ground instead of a design source of truth
