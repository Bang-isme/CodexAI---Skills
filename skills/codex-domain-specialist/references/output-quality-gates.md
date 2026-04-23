# Output Quality Gates — Anti-Generic Guardrails

## Scope and Triggers

> **This reference is MANDATORY.** It must be consulted before generating ANY code, schema, API, or UI component. It is not signal-dependent — it applies to every task across every domain.

**Purpose**: Prevent the AI from outputting the first generic pattern it was trained on. Force deliberate, project-specific thinking before every output.

---

## 1. The 3-Second Rule (Before ANY Output)

Before writing a single line of code, UI, or schema — STOP and answer these 3 questions silently:

| # | Question | If You Can't Answer |
|---|---|---|
| 1 | **What is unique about THIS project's requirements?** | Re-read the task. Don't generate until you understand the specific context. |
| 2 | **How would a senior engineer at THIS company solve this differently from a tutorial?** | Your output should NOT look like a Medium tutorial or StackOverflow answer. |
| 3 | **If I swap the project name, would this code still make sense for any random project?** | If YES → your output is generic. Refactor to be project-specific. |

**Rule**: If your output could be copy-pasted into any project and still work without modification, it is generic. Generic = failure.

---

## 2. Scope Fit Gate (Anti-Overengineering)

Before adding abstractions, dependencies, services, queues, caches, event buses, design systems, framework changes, or new architecture layers, answer these questions:

| # | Question | If You Can't Answer |
|---|---|---|
| 1 | **What exact requirement, bug, scale constraint, or repo pattern needs this complexity?** | Use the simpler local change. |
| 2 | **What simpler option was considered and why does it fail here?** | Do not introduce the complex option. |
| 3 | **How will this extra complexity be verified and maintained?** | Add verification first or shrink the design. |

**Rule**: Complexity must buy a named benefit in this repo. If the benefit is only "future flexibility", "best practice", or "scalability" without measurable demand, it is overengineering.

### Complexity Budget

| Change Type | Allowed When |
|---|---|
| New helper/function | The same logic repeats or the local flow becomes harder to read. |
| New module/service | There is a clear domain boundary, multiple call sites, or existing project convention. |
| New dependency | Existing standard library or installed stack cannot solve the requirement safely. |
| New queue/cache/worker | There is measured latency, reliability, throughput, or async processing need. |
| New architecture layer | The task changes a boundary, ownership model, deployment surface, or long-lived contract. |

### Scope Fit Output Requirement

If you choose the more complex option, include a short note with:

- `Why simpler option fails`
- `What this complexity buys`
- `How we will verify it`

If you cannot write that note concretely, use the simpler solution.

---

## 3. Frontend Quality Gate

Before outputting any UI component, page, or layout:

### The Visual Uniqueness Test

| Check | Generic Output (❌) | Quality Output (✅) |
|---|---|---|
| **Colors** | Default framework colors (`#007bff`, `blue-500`) | Custom HSL palette derived from brand identity |
| **Typography** | System fonts or single-font everything | Intentional font pairing with modular scale |
| **Layout** | Every section = same heading + 3-column cards | Varied layouts per section (split, bento, sticky, horizontal) |
| **Spacing** | Random pixel values (`margin: 15px 22px`) | 8px grid system with design tokens |
| **Hover states** | None, or just `opacity: 0.8` | Custom transitions (scale, color shift, underline slide) |
| **Loading states** | Plain spinner or nothing | Skeleton screens matching actual content shape |
| **Empty states** | "No data found" text | Illustrated empty state with action CTA |
| **Dark mode** | Just invert colors | Intentional palette with reduced saturation |
| **Responsive** | Breaks or stacks awkwardly | Fluid typography (`clamp()`), container queries, touch targets |
| **Animation** | None, or everything bounces the same way | Purposeful motion with varied easing and timing |

### FE "Screenshot Test"

> Take a mental screenshot of your output. If the screenshot could be ANY landing page / ANY dashboard / ANY CRUD app — your output is generic. Add the project's 10% Signature.

---

## 4. Backend Quality Gate

Before outputting any API endpoint, service, or controller:

### The API Intentionality Test

| Check | Generic Output (❌) | Quality Output (✅) |
|---|---|---|
| **Route naming** | `/api/items`, `/api/users` (tutorial names) | Domain-specific: `/api/v1/campaigns`, `/api/v1/enrollments` |
| **Error messages** | `"Something went wrong"`, `"Error"` | Contextual: `"Campaign budget cannot be negative"`, `"Enrollment period has ended"` |
| **Validation** | Only `required: true` | Business-rule validation: min/max, cross-field, conditional |
| **Response shape** | Raw database document as response | Mapped DTO with only client-needed fields |
| **Status codes** | Everything returns 200 or 500 | Correct semantics: 201 Created, 204 No Content, 409 Conflict, 422 Unprocessable |
| **Pagination** | No pagination, or basic offset | Cursor-based with sort, filter, and total count |
| **Middleware** | Copy-paste auth from tutorial | Project-specific: role-based access, tenant isolation, rate limits |
| **Logging** | `console.log("error:", e)` | Structured logger with correlation ID, actor, and operation context |
| **Comments** | `// TODO: implement later` | Why-comments explaining business decisions |

### BE "Swap Test"

> If you replace every model name in your backend code with "Item" / "User", and the code still makes perfect sense — your output is a tutorial CRUD, not a production API. Add business-specific logic.

---

## 5. Database Quality Gate

Before outputting any schema, migration, or query:

### The Schema Intentionality Test

| Check | Generic Output (❌) | Quality Output (✅) |
|---|---|---|
| **Field naming** | `data`, `info`, `metadata`, `type` | Domain-specific: `enrollment_status`, `campaign_budget_cents`, `last_login_ip` |
| **Indexes** | No indexes or only `_id` | Workload-driven: compound indexes for actual query patterns |
| **Relationships** | Everything is a separate table/collection | Embed vs. Reference decision based on access patterns (see `database-rules.md`) |
| **Constraints** | No constraints (rely on app validation) | Schema-level: `NOT NULL`, `CHECK`, `UNIQUE`, `ENUM` |
| **Timestamps** | Only `createdAt` | Full audit: `createdAt`, `updatedAt`, `deletedAt` (soft delete), `createdBy` |
| **Enums** | String fields with no validation | `ENUM` type or check constraint with all valid values |
| **Default values** | None | Sensible defaults: `status: 'draft'`, `role: 'user'`, `isActive: true` |
| **Migration** | Inline `db.createCollection()` | Versioned migration file with up/down, idempotent |

### DB "Real Data Test"

> Imagine populating your schema with 100,000 real records. Do the fields make sense? Are the queries you'd run covered by indexes? If your schema would work equally well for a blog, a CRM, and an e-commerce site — it's too generic.

---

## 6. Universal Anti-Generic Checklist

Run this **after** generating output, **before** presenting it:

| # | Question | If YES → Fix |
|---|---|---|
| 1 | Does this look like the first page of a "Build X with React/Express" tutorial? | Rewrite with project-specific business logic |
| 2 | Could this code/design be used in ANY project without changes? | Add project-specific naming, validation, and structure |
| 3 | Are all variable/function names generic? (`data`, `items`, `handleClick`) | Rename to domain terms: `campaigns`, `enrollments`, `handleEnrollmentSubmit` |
| 4 | Is the error handling just `try/catch → console.log`? | Add structured error classes, user-facing messages, and recovery paths |
| 5 | Does the UI use default framework styling without customization? | Apply design tokens from CSS architecture reference |
| 6 | Are there placeholder texts? (`Lorem ipsum`, `Your text here`, `TODO`) | Replace with realistic, project-specific content |
| 7 | Is there only one state? (success path only) | Add loading, error, empty, partial states |
| 8 | Does the API return the raw database model? | Map to a DTO with only the fields the client needs |
| 9 | Would a PM read this code and have no idea what business problem it solves? | Add business-context comments and meaningful naming |
| 10 | Is the heading font the same size as body text? | Apply typographic scale (see `ui-ux-design-principles.md`) |
| 11 | Did you add a dependency, queue, cache, service, or abstraction without evidence? | Remove it or add the Scope Fit note with proof |
| 12 | Did you solve a one-file issue with a platform-wide architecture change? | Shrink to the local change unless a boundary or scale signal requires more |

---

## 7. The "Why" Mandate

Every major decision in output must be traceable to a project-specific reason:

```
❌ Generic thinking:
"I'll use a 3-column grid because that's the standard."

✅ Project-specific thinking:
"This campaign dashboard has 4 KPIs, so I'll use a Bento grid with 1 large stat 
card (most important: conversion rate) and 3 smaller cards. The large card uses 
the brand accent color to draw attention."
```

```
❌ Generic thinking:
"I'll create a POST /api/users endpoint with name and email."

✅ Project-specific thinking:
"The enrollment flow requires email + phone verification before activation,
so I'll create POST /api/v1/enrollments with a 'pending_verification' status
and a separate PATCH /api/v1/enrollments/:id/verify endpoint."
```

---

## 8. Framework & Library Defaults Are NOT Your Defaults

| What AI Was Trained On | What You Should Actually Do |
|---|---|
| Express default error handler | Custom `AppError` class with codes and user-safe messages |
| React `useState` for everything | Evaluate: server state (React Query) vs. client state (Zustand) vs. URL state |
| MongoDB `save()` without validation | Mongoose schema with validators, pre-hooks, and virtual fields |
| CSS `text-align: center` everywhere | Intentional alignment: left-aligned content, centered heroes, right-aligned CTAs |
| `<button>Click</button>` | `<button>Start Free Trial</button>` with hover, focus, active, disabled states |
| `console.log(error)` | Winston/Pino logger with JSON format, levels, and context |
| Default `border-radius: 4px` | Design-token-driven: `--radius-sm: 6px`, `--radius-md: 12px`, `--radius-lg: 24px` |

---

## Cross-References

- `creative-development.md` for Creative Brief Decoder and 10% Signature Rule.
- `ui-ux-design-principles.md` for visual hierarchy and viewport-fit section design.
- `backend-rules.md` for API architecture patterns and layered design.
- `database-rules.md` for schema modeling and index strategy.
- `frontend-rules.md` for component architecture and design tokens.
- `css-architecture.md` for design token structure.
