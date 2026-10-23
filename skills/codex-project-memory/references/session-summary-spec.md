# Session Summary Spec

## Purpose

Capture end-of-session progress so the next session can resume quickly with minimal re-discovery.

## When To Generate

- At the end of each coding session.
- At a natural checkpoint before pausing multi-step work, context compaction, or a task handoff.
- Before closing the editor.
- Before handing work to another engineer or AI.

## Output Schema

```json
{
  "session_id": "2026-04-25-a",
  "started_at": "2026-04-25T09:00:00Z",
  "ended_at": "2026-04-25T14:30:00Z",
  "goal": "Implement user authentication module",
  "status": "in_progress",
  "branch": "feature/auth-refresh",
  "git_root": "C:/work/auth-app",
  "head": "a1b2c3d4",
  "checkpoint_created": "2026-04-25T14:30:00+00:00",
  "history_range": "9f8e7d6c..HEAD",

  "completed": [
    "JWT token generation and validation",
    "Login/register API endpoints",
    "Password hashing with bcrypt"
  ],

  "in_progress": [
    "Refresh token rotation — endpoint exists, needs testing"
  ],

  "blocked": [],

  "files_modified": [
    { "path": "src/auth/jwt.service.ts", "change": "New file — token generation" },
    { "path": "src/auth/auth.controller.ts", "change": "Added login/register handlers" },
    { "path": "prisma/schema.prisma", "change": "Added User model with password field" }
  ],

  "decisions": [
    {
      "decision": "Use httpOnly cookies for refresh tokens instead of localStorage",
      "reason": "Prevents XSS token theft",
      "alternatives_rejected": ["localStorage", "in-memory only"]
    }
  ],

  "commands_verified": [
    { "command": "npm test", "result": "18/18 pass" },
    { "command": "npx prisma migrate dev", "result": "Migration applied" }
  ],

  "working_tree": {
    "staged": ["config/auth.yml"],
    "unstaged": ["src/auth/refresh.ts"],
    "untracked": ["tmp/refresh-repro.ts"]
  },

  "next_steps": [
    "Write integration tests for refresh token rotation",
    "Add rate limiting to login endpoint",
    "Add forgot-password flow"
  ],

  "open_questions": [
    "Should we support OAuth providers in this sprint?"
  ]
}
```

## Markdown Output Format

When the session summary is rendered as Markdown (for handoff or review):

```markdown
# Session Summary: 2026-04-25

## Overview
- Checkpoint created: 2026-04-25T14:30:00+00:00
- Branch: feature/auth-refresh
- Git root: C:\work\auth-app
- HEAD: a1b2c3d4
- History range: 9f8e7d6c..HEAD
- Duration: 09:00 – 14:30 (5.5h)
- Commits: 1
- Files changed: 3
- Working tree files: 3

## Task State
- Goal: Implement user authentication module
- Status: in_progress

## Completed
- Login/register API endpoints

## In Progress
- Refresh token rotation — endpoint exists; integration test is the resume point

## Blocked
- None

## Recent Commits
- `a1b2c3d4` 2026-04-25 — feat: add authentication endpoints

## Changes Made
### Modified
- `src/auth/auth.controller.ts` (+12/-2)

### New Files
- `src/auth/jwt.service.ts`

### Deleted Files
- None

## Working Tree
### Staged Changes
- `config/auth.yml`

### Unstaged Changes
- `src/auth/refresh.ts`

### Untracked Files
- `tmp/refresh-repro.ts`

## Decisions Made
- Use httpOnly cookies for refresh tokens — prevents XSS token theft

## Commands Verified
- `npm test` → 18/18 pass
- `npx prisma migrate dev` → migration applied

## Next Steps
- Write integration tests for refresh token rotation
- Add rate limiting to login endpoint
- Add forgot-password flow

## Open Questions
- Should we support OAuth providers in this sprint?
```

## How AI Uses It

1. When resuming a named task, locate its latest `in_progress` summary by matching the Goal, branch, and repository; `last-session` selects a Git-history boundary, not a task narrative. Confirm the recorded HEAD is still in the current branch history and reconcile the commit range and working-tree snapshot. For a first checkpoint spanning days, use the task's start time as `--since`; follow-up checkpoints can use `last-session` after the previous summary is complete.
2. Before handing it off, replace every bracketed prompt with the goal, status, completed work, exact resume point, blockers, verified commands, next steps, and open questions from the current session. Use `in_progress` for a resumable pause.
3. Expand each generated decision title with its reason and any relevant rejected alternative, using the matching `.codex/decisions/` record or current conversation; never infer rationale from a title.
4. Record only commands actually run and their observed results; do not infer task status from commits alone.
5. The worktree section records paths, not status codes or file contents. Inspect `git diff --cached` and `git diff` separately for staged/unstaged changes, and inspect untracked files before resuming.
6. Each generator run creates a new file and reserves its filename exclusively so concurrent runs cannot replace each other's checkpoint. When refreshing a checkpoint, carry forward the task narrative and verified commands, then fill all prompts in the new file. The `Checkpoint created` timestamp is fixed at generation to whole-second precision; edits to the summary do not move it. For a committed recorded HEAD, commit history is the exact `checkpoint HEAD..current HEAD` range, including descendants whose committer dates predate the checkpoint. If the prior checkpoint says `HEAD: unborn`, all commits reachable from current HEAD are included. `last-session` only considers checkpoints for the current Git branch and repository whose recorded HEAD is an ancestor of current HEAD, and rejects the newest matching summary while its generated prompts remain. When no prior checkpoint exists, the generator falls back to the explicit date/time cutoff; legacy summaries without a timestamp use midnight on the date in their filename for that fallback. Legacy summaries must still contain matching branch identity, a valid HEAD (or `unborn`), and complete task-state fields. Rootless legacy summaries are trusted only when their summary directory is inside the current repository.
7. If the recipient uses another checkout, transfer the matching branch/commit or an authorized patch separately.
8. Continue from the listed resume point after confirming the relevant files and decisions still match.
9. Avoid re-asking questions already answered in `decisions`.

## Quality Rules

- Every session summary must have at least: goal, status, files modified, next steps, and (when a spec or multi-domain flow is active) the active `SPEC.md` / plan path, completed vs pending `AC-###` / `SILC-###` IDs, and integration seam state.
- A checkpoint must describe staged, unstaged, and untracked files as captured at generation time; refresh it if the worktree changes afterward.
- Decisions must include the reason — not just the choice.
- Commands must include actual output, not "should pass."
- Next steps should be actionable (verb + object + exact file or ticket ID), not vague ("continue working on auth").
- Before presenting a summary as a handoff, replace all bracketed prompts; use `None` when a section has no entries.
- A path-only worktree snapshot is not a portable copy of uncommitted changes.
- Confirm the recorded branch, HEAD, and `--since` window cover the task before relying on the checkpoint.

## Retention Guideline

- Keep the latest five summaries regardless of age; archive older summaries only when they are more than 90 days old, matching `context-compactor-spec.md`.
- The compactor preserves compact change history, not a resumable task checkpoint. Move milestone knowledge that must persist into human-owned project docs before old summaries are archived.
