# Session Summary Spec

## Purpose

Capture end-of-session progress so the next session can resume quickly with minimal re-discovery.

## When To Generate

- At the end of each coding session.
- Before closing the editor.
- Before handing work to another engineer or AI.

## How AI Uses It

- Read the newest summary first.
- Continue from listed modified files, decisions, and next steps.
- Use commit and file stats to estimate remaining scope.

## Retention Guideline

- Keep the latest 30 days by default.
- Periodically archive or remove older summaries when no longer needed.
