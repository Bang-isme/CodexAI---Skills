# Debugging Rules

## 4-Phase Process (Mandatory)

### 1. Reproduce

- capture exact steps and frequency
- document expected vs actual behavior

### 2. Isolate

- identify changed code and suspect boundaries
- reduce to minimal reproduction
- narrow code path by elimination

### 3. Root Cause

- apply 5-whys reasoning
- identify true cause, not symptom

### 4. Fix and Verify

- fix root cause
- verify with evidence
- add regression test
- check nearby code for similar risk

## Anti-Patterns

- random edits without evidence
- symptom-only fixes
- changing multiple unknown variables at once
- ignoring stack traces or logs
