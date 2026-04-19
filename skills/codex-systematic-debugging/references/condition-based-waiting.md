# Condition-Based Waiting

## Overview

Flaky tests often guess at timing with arbitrary delays. This creates race conditions where tests pass on fast machines but fail under load or in CI.

**Core principle:** Wait for the actual condition you care about, not a guess about how long it takes.

## When to Use

- Tests have arbitrary delays (`time.sleep()`, `setTimeout`, `asyncio.sleep()`)
- Tests are flaky (pass sometimes, fail under load)
- Tests timeout when run in parallel
- Waiting for async operations to complete

**Don't use when:**
- Testing actual timing behavior (debounce, throttle intervals)
- Always document WHY if using arbitrary timeout

## Core Pattern

```python
# ❌ BEFORE: Guessing at timing
import time
start_operation()
time.sleep(2)  # Hope 2 seconds is enough?
result = get_result()
assert result is not None

# ✅ AFTER: Waiting for condition
start_operation()
result = wait_for(lambda: get_result(), description="operation result")
assert result is not None
```

```typescript
// ❌ BEFORE
await new Promise(r => setTimeout(r, 50));
const result = getResult();
expect(result).toBeDefined();

// ✅ AFTER
await waitFor(() => getResult() !== undefined);
const result = getResult();
expect(result).toBeDefined();
```

## Quick Patterns

| Scenario | Pattern |
|----------|---------|
| Wait for event | `wait_for(lambda: events.find(type="DONE"))` |
| Wait for state | `wait_for(lambda: machine.state == "ready")` |
| Wait for count | `wait_for(lambda: len(items) >= 5)` |
| Wait for file | `wait_for(lambda: os.path.exists(path))` |
| Complex condition | `wait_for(lambda: obj.ready and obj.value > 10)` |

## Implementation

### Python

```python
import time
from typing import TypeVar, Callable, Optional

T = TypeVar("T")

def wait_for(
    condition: Callable[[], Optional[T]],
    description: str = "condition",
    timeout_ms: int = 5000,
    poll_ms: int = 10,
) -> T:
    """Wait for condition to return truthy value."""
    start = time.monotonic()
    timeout_sec = timeout_ms / 1000

    while True:
        result = condition()
        if result:
            return result

        elapsed = time.monotonic() - start
        if elapsed > timeout_sec:
            raise TimeoutError(
                f"Timeout waiting for {description} after {timeout_ms}ms"
            )

        time.sleep(poll_ms / 1000)
```

### TypeScript

```typescript
async function waitFor<T>(
  condition: () => T | undefined | null | false,
  description: string = 'condition',
  timeoutMs = 5000,
): Promise<T> {
  const startTime = Date.now();

  while (true) {
    const result = condition();
    if (result) return result;

    if (Date.now() - startTime > timeoutMs) {
      throw new Error(`Timeout waiting for ${description} after ${timeoutMs}ms`);
    }

    await new Promise(r => setTimeout(r, 10)); // Poll every 10ms
  }
}
```

## Common Mistakes

**❌ Polling too fast:** `time.sleep(0.001)` — wastes CPU
**✅ Fix:** Poll every 10ms

**❌ No timeout:** Loop forever if condition never met
**✅ Fix:** Always include timeout with clear error

**❌ Stale data:** Cache state before loop
**✅ Fix:** Call getter inside loop for fresh data

## When Arbitrary Timeout IS Correct

```python
# Tool ticks every 100ms — need 2 ticks to verify partial output
wait_for(lambda: manager.state == "STARTED")  # First: wait for condition
time.sleep(0.2)  # Then: wait for timed behavior
# 200ms = 2 ticks at 100ms intervals — documented and justified
```

**Requirements:**
1. First wait for triggering condition
2. Based on known timing (not guessing)
3. Comment explaining WHY

## Real-World Impact

- Fixed 15 flaky tests across 3 files
- Pass rate: 60% → 100%
- Execution time: 40% faster
- No more race conditions
