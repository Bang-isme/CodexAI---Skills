# Condition-Based Waiting

Replace arbitrary `time.sleep()` / `setTimeout()` with condition polling.

## Anti-Pattern

```python
subprocess.run(["npm", "run", "dev"])
time.sleep(5)  # Hope server is ready
requests.get("http://localhost:3000")  # Might fail
```

## Correct Pattern

```python
import time


def wait_for_condition(check_fn, timeout=30, interval=0.5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if check_fn():
            return True
        time.sleep(interval)
    raise TimeoutError(f"Condition not met within {timeout}s")


# Usage
wait_for_condition(lambda: port_is_open("localhost", 3000))
```

## When to Use

- Waiting for servers to start
- Waiting for files to appear
- Waiting for processes to complete
- Any test with sleep() -> replace with condition poll
