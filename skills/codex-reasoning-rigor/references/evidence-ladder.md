# Evidence Ladder

Use stronger evidence whenever the task has meaningful cost, risk, or ambiguity. Before making a claim, check which rung your evidence sits on — then decide if the claim deserves better proof.

## The Ladder

### Tier 1 — Weak (Intuition)

Evidence that comes from training data, habit, or assumption. Never sufficient for completion claims.

| Pattern | Example | When Acceptable |
|---|---|---|
| "This usually works" | "React apps typically use useEffect for data fetching" | Brainstorming only |
| Generic framework knowledge | "PostgreSQL handles concurrent writes well" | Initial exploration |
| Analogy from other projects | "We did it this way in Project X" | Suggesting options, never deciding |
| "Best practice" citation | "The docs recommend X" | Only with repo-specific validation |

**Red flag:** If your evidence could apply to any project without modification, it's Tier 1.

### Tier 2 — Medium (Repo Inspection)

Evidence gathered from reading the actual codebase. Sufficient for low-risk changes.

| Pattern | Example | When Acceptable |
|---|---|---|
| File inspection | "Found 3 uses of `useQuery` in `src/hooks/`" | Understanding patterns |
| Command output (read-only) | "`grep -r 'TODO' src/ | wc -l` → 14 TODOs" | Counting, measuring |
| Version comparison | "`package.json` shows React 18.2, compatible with React Router 6" | Dependency decisions |
| Existing patterns in nearby files | "All controllers in `src/controllers/` use the same error wrapper" | Following conventions |
| Config file reading | "`.env.example` defines `DATABASE_URL` and `REDIS_URL`" | Environment setup |

**Upgrade trigger:** If the change affects runtime behavior, you need Tier 3.

### Tier 3 — Strong (Verified Execution)

Evidence from running commands that prove the claim. Required for completion claims.

| Pattern | Example | When Required |
|---|---|---|
| Tests passing now | "`npm test` → 47/47 pass, 0 failures" | Any "tests pass" claim |
| Build succeeding now | "`npm run build` → exit 0, no warnings" | Any "build works" claim |
| Linter clean now | "`npx eslint src/` → 0 errors, 0 warnings" | Any "lint clean" claim |
| Diff confirming change | "`git diff` shows exact lines changed" | Any "fixed" claim |
| Runtime verification | "Started server → `curl /health` → 200 OK" | Any "works" claim |
| Red-green test cycle | "Test failed → fix applied → test passes" | Regression test claims |

**No shortcuts:** Tier 3 evidence from a previous session or previous message does not count. Re-run.

### Tier 4 — Conclusive (Multi-Signal)

Multiple independent verification signals converging. Required for "ship it" or "production-ready" claims.

| Pattern | Example |
|---|---|
| Tests + build + lint | All three pass in the same run |
| Tests + manual smoke test | Automated tests pass AND manual verification confirms expected behavior |
| Review + tests + deploy | Code reviewed, tests green, staging deploy successful |
| Before/after metrics | Response time: 800ms → 200ms, measured with same methodology |

## Decision Rules

```
claim_risk = low    → Tier 2 sufficient (file inspection)
claim_risk = medium → Tier 3 required (run the command)
claim_risk = high   → Tier 4 required (multiple signals)

"done" / "fixed" / "safe to ship" → always Tier 3+
"I think" / "probably" → you're at Tier 1, upgrade or state uncertainty
```

## Evidence Escalation Examples

### Example: "The bug is fixed"

| Tier | Evidence | Verdict |
|---|---|---|
| 1 | "I changed the code, should be fixed now" | ❌ Insufficient |
| 2 | "I can see the fix in the diff — the null check is added" | ⚠️ Better, not enough |
| 3 | "Regression test reproduces the bug → FAIL. Apply fix → PASS." | ✅ Sufficient |
| 4 | "Regression test passes + full suite passes + manual repro confirms fix" | ✅ Conclusive |

### Example: "The API is working"

| Tier | Evidence | Verdict |
|---|---|---|
| 1 | "The code looks correct" | ❌ |
| 2 | "Route is registered in `routes/index.js`, handler exists" | ⚠️ |
| 3 | "`curl -X POST /api/users -d '...' → 201 Created`" | ✅ |
| 4 | "Curl returns 201 + test passes + invalid input returns 422" | ✅ Conclusive |

### Example: "Dependencies are compatible"

| Tier | Evidence | Verdict |
|---|---|---|
| 1 | "React 18 works with React Router 6" | ❌ |
| 2 | "`package.json` shows compatible version ranges" | ⚠️ |
| 3 | "`npm install` → 0 peer dependency warnings + `npm run build` → exit 0" | ✅ |

## Integration with Other Skills

- **codex-verification-discipline**: Uses this ladder to determine if evidence is sufficient before making claims
- **codex-reasoning-rigor**: Uses this ladder during the "Repo Grounding" step
- **codex-execution-quality-gate**: Gate scripts produce Tier 3/4 evidence automatically
