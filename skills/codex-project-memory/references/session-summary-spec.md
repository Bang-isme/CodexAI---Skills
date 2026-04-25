# Session Summary Spec

## Purpose

Capture end-of-session progress so the next session can resume quickly with minimal re-discovery.

## When To Generate

- At the end of each coding session.
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
# Session Summary — 2026-04-25

**Goal:** Implement user authentication module
**Status:** 🔄 In Progress
**Duration:** 09:00 – 14:30 (5.5h)

## Completed
- ✅ JWT token generation and validation
- ✅ Login/register API endpoints
- ✅ Password hashing with bcrypt

## In Progress
- 🔄 Refresh token rotation — endpoint exists, needs testing

## Files Modified
| File | Change |
|---|---|
| `src/auth/jwt.service.ts` | New — token generation |
| `src/auth/auth.controller.ts` | Added login/register handlers |
| `prisma/schema.prisma` | Added User model |

## Decisions
- **Use httpOnly cookies for refresh tokens** (not localStorage) — prevents XSS token theft

## Verification
- `npm test` → 18/18 pass
- `npx prisma migrate dev` → applied

## Next Steps
1. Write integration tests for refresh token rotation
2. Add rate limiting to login endpoint
3. Add forgot-password flow

## Open Questions
- Should we support OAuth providers in this sprint?
```

## How AI Uses It

1. Read the newest summary first.
2. Continue from listed modified files, decisions, and next steps.
3. Use commit and file stats to estimate remaining scope.
4. Avoid re-asking questions already answered in `decisions`.
5. Run `commands_verified` to check if previous state still holds.

## Quality Rules

- Every session summary must have at least: goal, status, files modified, next steps.
- Decisions must include the reason — not just the choice.
- Commands must include actual output, not "should pass."
- Next steps should be actionable (verb + object), not vague ("continue working on auth").

## Retention Guideline

- Keep the latest 30 days by default.
- Periodically archive or remove older summaries when no longer needed.
- For long-running projects, keep milestone summaries permanently.
