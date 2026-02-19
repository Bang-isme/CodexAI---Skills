# Smart Test Selector
## Purpose
Select relevant tests from changed files instead of running the full test suite.
It optimizes feedback speed while preserving practical confidence.
## When to Run
- After implementation of a feature or fix.
- During bug-fix verification cycles.
- Before creating or updating a pull request.
- On `$smart-test` or "which tests to run".
## How AI Uses It
1. Run `smart_test_selector.py` with changed file context.
2. Read selected test files and selection reasons from JSON output.
3. Execute only selected tests and summarize risk coverage.
## Integration Behavior
- Trigger on `$smart-test` or "which tests to run".
- Auto-run after pre-commit checks in fast verification loops.
- Advisory behavior; selection quality informs but does not block completion by itself.
## Output Intent
- Minimize test execution time while maintaining coverage confidence.
- Caveat: selection can miss indirect regressions, so full suite may still be required.
