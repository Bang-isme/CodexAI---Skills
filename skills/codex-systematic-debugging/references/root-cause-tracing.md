# Root Cause Tracing

## Overview

Bugs often manifest deep in the call stack. Your instinct is to fix where the error appears, but that's treating a symptom.

**Core principle:** Trace backward through the call chain until you find the original trigger, then fix at the source.

## When to Use

- Bug appears deep in execution (not at entry point)
- Stack trace shows long call chain
- Unclear where invalid data originated
- Need to find which test/code triggers the problem

## The Tracing Process

### 1. Observe the Symptom
```
Error: database connection failed at /app/services/user.js:42
```

### 2. Find Immediate Cause
**What code directly causes this?**
```javascript
const db = await connect(config.database.url);
```

### 3. Ask: What Called This?
```
UserService.connect(config)
  → called by UserService.init()
  → called by App.bootstrap()
  → called by test at setupTestApp()
```

### 4. Keep Tracing Up
**What value was passed?**
- `config.database.url = undefined`
- undefined because `process.env.DATABASE_URL` not set
- Not set because `.env.test` not loaded in this test file

### 5. Find Original Trigger
**Where did undefined come from?**
```javascript
// setupTestApp() does NOT call loadEnv()
// But prod bootstrap() DOES call loadEnv()
// Root cause: test setup missing env loading
```

## Adding Stack Traces

When you can't trace manually, add instrumentation:

```python
# Python
import traceback

def connect_database(url):
    print(f"DEBUG connect_database: url={url!r}")
    traceback.print_stack()
    # ... proceed
```

```typescript
// TypeScript
function connectDatabase(url: string) {
  console.error('DEBUG connect_database:', {
    url,
    cwd: process.cwd(),
    stack: new Error().stack,
  });
  // ... proceed
}
```

**Critical:** Use `console.error()` or `print(..., file=sys.stderr)` in tests — logger may be suppressed.

**Run and capture:**
```bash
# Python
python -m pytest tests/ -s 2>&1 | grep "DEBUG connect"

# Node.js
npm test 2>&1 | grep "DEBUG connect"
```

**Analyze stack traces:**
- Look for test file names
- Find the line number triggering the call
- Identify the pattern (same test? same parameter?)

## Finding Which Test Causes Pollution

If something appears during tests but you don't know which test:

**Bisection approach:**
```bash
# Run tests one-by-one, stop at first polluter
for test_file in tests/test_*.py; do
  echo "=== Running $test_file ==="
  python -m pytest "$test_file" -x
  # Check for pollution artifact
  if [ -f ".git/index.lock" ]; then
    echo "POLLUTER FOUND: $test_file"
    break
  fi
done
```

## Real Example: Empty projectDir

**Symptom:** `.git` created in source directory instead of temp dir

**Trace chain:**
1. `git init` runs in `process.cwd()` ← empty cwd parameter
2. WorktreeManager called with empty projectDir
3. Session.create() passed empty string
4. Test accessed `context.tempDir` before beforeEach
5. setupCoreTest() returns `{ tempDir: '' }` initially

**Root cause:** Top-level variable initialization accessing empty value

**Fix:** Made tempDir a getter that throws if accessed before beforeEach

**Also added defense-in-depth** (see `defense-in-depth.md`):
- Layer 1: Project.create() validates directory
- Layer 2: WorkspaceManager validates not empty
- Layer 3: NODE_ENV guard refuses git init outside tmpdir
- Layer 4: Stack trace logging before git init

## Key Principle

```
Found immediate cause → Can trace one level up?
  |- Yes → Trace backwards → Is this the source?
  |   |- No → Keep tracing
  |   `- Yes → Fix at source → Add validation at each layer → Bug impossible
  |
  `- No → NEVER fix just the symptom
```

**NEVER fix just where the error appears.** Trace back to find the original trigger.

## Tips

- **In tests:** Use `print()` / `console.error()` not logger — logger may be suppressed
- **Before operation:** Log before the dangerous operation, not after it fails
- **Include context:** Directory, cwd, environment variables, timestamps
- **Capture stack:** `traceback.print_stack()` or `new Error().stack` shows complete call chain
