# Playwright Runner Spec

## Purpose

`playwright_runner.py` provides three utility modes:

1. `check`: verify Playwright installation and local test inventory
2. `generate`: scaffold E2E skeleton tests for a URL
3. `run`: execute Playwright tests and summarize results

## When to Run

- `check`: project setup and CI onboarding
- `generate`: bootstrap E2E baseline for new pages
- `run`: verify critical user journeys before handoff

## Input

- `--project-root` (required)
- `--mode` (`check|generate|run`) required
- `--url` required only for `generate`
- `--test-dir` optional override
- `--browser` optional (`chromium|firefox|webkit`)

## Behavior

- Missing Playwright tool returns helpful install instructions as JSON.
- `generate` creates test folder if missing.
- `generate` without `--url` fails with explicit guidance.
- `run` parses JSON reporter output and returns pass/fail/skipped summary.

## Output Patterns

- `check`: installation + browser readiness snapshot
- `generate`: generated file path and test count
- `run`: totals, duration, failures list, summary string

## Integration Notes

- Advisory check in MVP (non-blocking by default).
- Use with UI-critical flows and smoke checks.
