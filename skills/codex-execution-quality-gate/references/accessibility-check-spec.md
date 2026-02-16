# Accessibility Check Spec

## Purpose

`accessibility_check.py` runs static WCAG-oriented checks (A/AA/AAA profile) against markup and style files.

## When to Run

- Before releasing public-facing UI.
- During accessibility-focused fixes.
- As an advisory pass for UI pull requests.

## WCAG Criteria Coverage

- `1.1.1`: images with alt text
- `1.3.1`: semantic structure hints
- `1.4.3`: color contrast (static CSS parsing)
- `2.1.1`: keyboard accessibility for clickable non-semantic elements
- `2.4.1`: skip navigation / main landmark
- `2.4.2`: page title presence (HTML)
- `2.4.4`: descriptive link text
- `3.1.1`: `lang` on `<html>`
- `3.3.2`: form label association
- `4.1.1`: duplicate IDs
- `4.1.2`: ARIA role/attribute validity heuristics

## Output Contract

- `status`: `checked`
- `level`: `A|AA|AAA`
- `files_scanned`
- `total_issues`
- `by_wcag`
- `issues[]` with `file/line/wcag/severity/message/suggestion`
- `compliance_score`
- `summary`
- optional `warnings` for unsupported CSS patterns or parse fallbacks

## Scoring

- `compliance_score = max(0, 100 - critical*8 - warning*3 - info*1)`

## Limitations

- Static regex-based checks cannot resolve dynamic runtime DOM mutations.
- Contrast parser supports common hex/rgb declarations only.
