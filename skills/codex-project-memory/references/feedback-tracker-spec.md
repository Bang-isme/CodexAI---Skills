# Feedback Tracker Spec

## Purpose

Track user fixes made on AI-generated code so future generations can avoid repeated mistakes. The feedback loop turns manual corrections into learned patterns.

## When To Log Feedback

- When user rewrites AI output for correctness.
- When user changes generated logic for edge cases or performance.
- When user enforces naming/style conventions AI missed.
- When user adds error handling AI omitted.
- When user restructures AI-generated code organization.

## Feedback Entry Schema

```json
{
  "id": "fb-2026-04-25-001",
  "timestamp": "2026-04-25T14:30:00Z",
  "file": "src/services/order.service.ts",
  "category": "error-handling",
  "severity": "medium",

  "original": "const order = await prisma.order.create({ data: orderData });",
  "corrected": "try { const order = await prisma.order.create({ data: orderData }); } catch (e) { if (e.code === 'P2002') throw new ConflictError('Duplicate order'); throw e; }",

  "lesson": "Always wrap Prisma mutations in try/catch and map P2002 to domain-specific ConflictError",
  "tags": ["prisma", "error-handling", "p2002"],
  "applies_to": "All Prisma create/update calls"
}
```

## Feedback Categories

| Category | Description | Example |
|---|---|---|
| `logic` | Incorrect business logic | Wrong calculation, missing condition |
| `error-handling` | Missing or incorrect error handling | No try/catch, wrong error type |
| `security` | Security issues in generated code | SQL injection, missing auth check |
| `naming` | Wrong naming convention | camelCase when project uses snake_case |
| `style` | Code style/formatting mismatch | Wrong import order, missing semicolons |
| `performance` | Inefficient code | N+1 query, unnecessary re-renders |
| `types` | Type errors or missing types | `any` instead of proper type, missing null check |
| `testing` | Test quality issues | Missing edge case, wrong assertion |
| `architecture` | Wrong structural pattern | Wrong layer, circular dependency |

## Aggregate Report Schema

```json
{
  "period": "2026-04-01 to 2026-04-25",
  "total_feedback": 23,

  "by_category": {
    "error-handling": 8,
    "naming": 5,
    "types": 4,
    "logic": 3,
    "security": 2,
    "style": 1
  },

  "top_lessons": [
    { "lesson": "Wrap Prisma mutations in try/catch with error code mapping", "occurrences": 4 },
    { "lesson": "Use project's custom AppError, not generic Error", "occurrences": 3 },
    { "lesson": "Check for null before accessing nested properties", "occurrences": 3 }
  ],

  "most_corrected_files": [
    { "file": "src/services/*.service.ts", "corrections": 9 },
    { "file": "src/controllers/*.controller.ts", "corrections": 6 }
  ],

  "trend": "error-handling corrections decreasing (8 → 5 → 3 over last 3 months)"
}
```

## How AI Uses It

1. Run `track_feedback.py --aggregate` at the start of complex tasks.
2. Identify repeated categories (logic/style/security/etc.).
3. Apply lessons before generating new code, especially on files with frequent feedback.
4. Proactively mention: "Based on previous feedback, I'm adding Prisma error handling."

## Integration Behavior

- AI should propose feedback logging when it detects user corrections to generated code.
- AI should summarize recent feedback trends before major implementation phases.
- AI should cite specific feedback entries when applying learned patterns.

## Privacy

- Feedback is stored locally in `<project-root>/.codex/feedback/`.
- Users control what gets logged and shared.
- No feedback is sent externally unless user explicitly exports it.
