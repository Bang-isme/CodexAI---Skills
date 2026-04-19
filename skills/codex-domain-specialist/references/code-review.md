# Code Review Guidelines

**Load when:** reviewing PRs, receiving code review feedback, or setting up review standards for a team.

## Review Philosophy

- **Technical correctness over social comfort.** If something is wrong, say so clearly.
- **Specific, actionable comments with rationale.** Not "this is bad" but "this creates N+1 queries because..."
- **Code review is about the code, not the person.** Avoid "you" — prefer "this function" or "this approach".

## Review Checklist

### Correctness

| Check | What to Look For |
| --- | --- |
| Behavior matches intent | Does the code do what the PR description claims? |
| Edge cases | Empty inputs, null values, boundary conditions, concurrent access |
| Error handling | Explicit failure paths, not silent swallows |
| Off-by-one errors | Loop bounds, array indexing, pagination math |
| Race conditions | Concurrent writes, shared mutable state |
| Data consistency | Transactions for multi-step operations |

### Security

| Check | Red Flags |
| --- | --- |
| No secrets in code | Hardcoded API keys, passwords, tokens |
| Input validation | User input used without sanitization |
| Auth/authz enforced | Missing middleware on protected routes |
| Injection vectors | String concatenation in queries |
| Sensitive data exposure | PII in logs, verbose error messages |

### Performance

| Check | Red Flags |
| --- | --- |
| N+1 queries | Loop with DB query inside |
| Unnecessary rerenders | Missing memo on expensive React subtrees |
| Large array operations | `.filter().map().sort()` on 10K+ items |
| Missing pagination | Unbounded `SELECT *` or `.find()` |
| Blocking operations | Sync file I/O or crypto in request handler |

### Maintainability

| Check | Guidance |
| --- | --- |
| Function size | Target < 50 lines; extract if larger |
| File size | Target < 500 lines; split by responsibility |
| Naming | Does the name tell you what it does without reading the body? |
| Dead code | No commented-out production code. Delete it (git has history). |
| DRY violations | Same logic in 2+ places → extract |
| YAGNI violations | Features not needed for the current task |

### Testing

| Check | Guidance |
| --- | --- |
| New behavior has tests | Every new function/feature covered |
| Edge cases tested | Invalid inputs, empty states, errors |
| Tests are deterministic | No time-dependent or order-dependent tests |
| Tests verify behavior | Not testing internal implementation details |
| No test anti-patterns | See `codex-test-driven-development/references/testing-anti-patterns.md` |

## PR Size Guidance

| Lines Changed | Category | Review Time | Action |
| --- | --- | --- | --- |
| < 50 | Tiny | ~10 min | Quick approval |
| 50-200 | Small | ~30 min | Standard review |
| 200-500 | Medium | ~1 hour | Schedule focused time |
| 500-1000 | Large | ~2 hours | Consider splitting |
| > 1000 | Too large | 3+ hours | **Must split before review** |

## How to Read Diffs Effectively

1. **Read PR description first** — understand intent before code.
2. **Check file list** — understand scope (which layers affected?).
3. **Read tests first** — tests reveal intent better than implementation.
4. **Review bottom-up**: utilities → services → routes → UI.
5. **Flag major issues early** — don't nitpick formatting if architecture is wrong.

## Feedback Classification

```markdown
<!-- Comment template -->
🔴 **Critical** (must fix): [Specific issue]. Because: [why it breaks].
🟠 **Important** (should fix): [Issue]. Because: [maintenance/perf/security risk].
🟡 **Nit** (won't block): [Suggestion]. Because: [readability/style preference].
💡 **Suggestion** (non-blocking): [Alternative approach]. Because: [trade-off].
❓ **Question**: [What I don't understand]. Needed for: [context].
```

### Anti-Patterns in Feedback

| Anti-Pattern | Fix |
| --- | --- |
| "This is wrong" (no rationale) | Explain WHY and suggest the fix |
| "I would do it differently" | Only flag if current approach has a real problem |
| Bikeshedding (formatting, naming preferences) | Mark as nit, don't block |
| Rubber-stamping ("LGTM" without reading) | Read every changed file, check tests |
| Rewriting in review (style change > 50%) | Discuss approach BEFORE implementation |

## Automated Checks Integration

| Check | Tool | When |
| --- | --- | --- |
| Lint | ESLint / Prettier | Pre-commit hook |
| Type check | `tsc --noEmit` | CI |
| Tests | Jest / Vitest | CI required to pass |
| Security | `npm audit` | CI advisory |
| Bundle size | `bundlewatch` | CI budget check |
| Coverage diff | Codecov | CI on PR |

**Rule:** Automate everything automatable. Humans review logic, architecture, and intent — not formatting.

## Receiving Code Review

See `codex-subagent-execution/references/code-review-discipline.md` for the full discipline.

Key principles:
1. **Verify before implementing** — check reviewer's suggestion against codebase reality.
2. **Push back with evidence** — if reviewer is wrong, show working tests/code.
3. **No performative agreement** — don't say "You're absolutely right!" Just fix or discuss.
4. **One item at a time** — implement, test, verify, then move to next item.
