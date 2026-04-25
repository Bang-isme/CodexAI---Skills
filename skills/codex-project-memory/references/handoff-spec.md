# Handoff Spec

## Purpose

Generate a portable handoff document that can be pasted into any AI assistant or shared with team members, providing enough project context to continue work without repeated discovery questions.

## When To Generate

- Before switching AI tools (ChatGPT → Codex, Codex → Claude, etc.).
- Before onboarding a new teammate.
- Before asking for deep code review from an external assistant.
- At sprint boundaries for cross-team handoffs.

## Output Schema

```json
{
  "project": {
    "name": "my-project",
    "description": "E-commerce API with React frontend",
    "repo": "https://github.com/user/my-project",
    "primary_language": "TypeScript",
    "framework": "Next.js 14 + Express.js"
  },

  "architecture": {
    "structure": "monorepo (apps/web + apps/api)",
    "frontend": "Next.js 14 App Router + Tailwind CSS",
    "backend": "Express.js + Prisma ORM",
    "database": "PostgreSQL 16",
    "auth": "JWT with httpOnly cookie refresh tokens",
    "deployment": "Docker → AWS ECS"
  },

  "current_state": {
    "branch": "feature/checkout-flow",
    "sprint": "Sprint 3",
    "sprint_goal": "Complete checkout and payment flow",
    "completed_features": [
      "User authentication (login/register/refresh)",
      "Product catalog with search and filters",
      "Shopping cart with persistence"
    ],
    "in_progress": [
      "Checkout flow — UI complete, payment integration pending"
    ],
    "known_issues": [
      "Cart total calculation rounds incorrectly for 3+ decimal currencies"
    ]
  },

  "conventions": {
    "naming": "camelCase for variables, PascalCase for components/types",
    "file_structure": "feature-based folders (src/features/auth/, src/features/cart/)",
    "testing": "Jest + Supertest for API, Playwright for E2E",
    "commits": "Conventional Commits (feat/fix/docs/refactor)",
    "pr_process": "Branch → PR → 1 review → squash merge"
  },

  "key_files": [
    { "path": "prisma/schema.prisma", "purpose": "Database schema — all models" },
    { "path": "src/middleware/auth.ts", "purpose": "JWT verification middleware" },
    { "path": "src/routes/index.ts", "purpose": "API route registry" },
    { "path": ".env.example", "purpose": "Required environment variables" }
  ],

  "recent_decisions": [
    {
      "decision": "Use Stripe Checkout Session instead of custom payment form",
      "reason": "Reduces PCI compliance scope",
      "date": "2026-04-20"
    }
  ],

  "next_priorities": [
    "Integrate Stripe Checkout Session API",
    "Add order confirmation email via Resend",
    "Write E2E test for full purchase flow"
  ],

  "setup_commands": [
    "npm install",
    "cp .env.example .env",
    "npx prisma migrate dev",
    "npm run dev"
  ]
}
```

## Markdown Output Format

```markdown
# Project Handoff — my-project

## Project Overview
E-commerce API with React frontend. Built with Next.js 14 + Express.js + PostgreSQL.

## Architecture
```
apps/
├── web/          # Next.js 14 App Router + Tailwind CSS
└── api/          # Express.js + Prisma ORM
    ├── src/
    │   ├── features/   # Feature-based modules
    │   ├── middleware/  # Auth, error handling
    │   └── routes/     # API route registry
    └── prisma/         # Database schema + migrations
```

## Current State
- **Branch:** `feature/checkout-flow`
- **Sprint:** Sprint 3 — Complete checkout and payment flow
- **Status:** UI complete, payment integration pending

## What's Done
- ✅ User authentication (login/register/refresh)
- ✅ Product catalog with search and filters
- ✅ Shopping cart with persistence

## What's In Progress
- 🔄 Checkout flow — UI complete, payment integration pending

## Known Issues
- ⚠️ Cart total calculation rounds incorrectly for 3+ decimal currencies

## Key Decisions
| Decision | Reason | Date |
|---|---|---|
| Stripe Checkout Session over custom form | Reduces PCI compliance scope | 2026-04-20 |

## Key Files
| File | Purpose |
|---|---|
| `prisma/schema.prisma` | Database schema |
| `src/middleware/auth.ts` | JWT verification |
| `src/routes/index.ts` | API route registry |

## Setup
```bash
npm install && cp .env.example .env && npx prisma migrate dev && npm run dev
```

## Next Priorities
1. Integrate Stripe Checkout Session API
2. Add order confirmation email via Resend
3. Write E2E test for full purchase flow

## Conventions
- Naming: camelCase vars, PascalCase components
- Commits: Conventional Commits
- PRs: Branch → PR → 1 review → squash merge
```

## How To Use

1. Run `generate_handoff.py`.
2. Open the generated `handoff.md`.
3. Copy the content into the next AI chat with the task request.

## Quality Rules

- Handoff must be self-contained — reader should not need to ask "what's the stack?" or "where do I start?"
- Include setup commands that work on a fresh clone.
- List key files with purpose, not just paths.
- Include recent decisions with reasons — prevents the next person from re-debating.
- Flag known issues — prevents wasted time debugging known problems.

## Recommended Update Frequency

- Regenerate after major architecture changes.
- Regenerate after dependency migrations.
- Regenerate after large refactors or release branches.
- Regenerate at sprint boundaries.

## Privacy Note

Review the handoff before sharing. It can include sensitive details from config files, git history, or local project metadata. Remove API keys, passwords, and internal URLs before sharing externally.
