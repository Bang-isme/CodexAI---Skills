# Condition-Based Waiting

> **Canonical reference:** See `codex-systematic-debugging/references/condition-based-waiting.md` for the full version with Python, TypeScript, implementation code, and real-world impact data.

Replace arbitrary `time.sleep()` / `setTimeout()` with condition polling.

## Quick Summary

```python
# ❌ BEFORE: Guessing at timing
start_operation()
time.sleep(2)  # Hope 2 seconds is enough?
result = get_result()

# ✅ AFTER: Waiting for condition
start_operation()
result = wait_for(lambda: get_result(), timeout_ms=5000)
```

## Full Reference

For complete documentation including:
- Python and TypeScript `wait_for()` implementations
- Common mistakes (polling too fast, no timeout, stale data)
- When arbitrary timeout IS correct
- Quick pattern table for events, state, counts, files

→ See `codex-systematic-debugging/references/condition-based-waiting.md`
