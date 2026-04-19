---
name: codex-plan-writer
description: Create structured task plan files for complex coding requests. Use during planning phases to write verifiable, dependency-aware task breakdowns and checkpoint criteria before implementation.
load_priority: on-demand
---

## TL;DR
Create `{task-slug}.md` plan file for complex requests. Map file structure first. Required sections: Overview, Success Criteria, Tech Stack, File Structure, Task Breakdown (TDD steps, dependencies, verify), Phase X Checklist. No placeholders. Self-review before presenting. Offer execution handoff. Wait for user approval.

# Plan Writer

## Activation

1. Activate during workflow planning phases.
2. Activate on explicit `$codex-plan-writer` or `$plan`.
3. Mandatory for complex requests with scope `medium` or `large`.

**Announce at start:** "I'm using codex-plan-writer to create the implementation plan."

## Output File Naming

- Derive a short kebab-case slug from the task intent (2-3 keywords).
- Maximum 30 characters.
- Examples: `ecommerce-cart.md`, `login-fix.md`, `dark-mode.md`.

## Output Location

Write plan file to project root: `./{task-slug}.md`

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during the design phase. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Use `$sdd` (codex-subagent-execution) or execute inline.
> Follow `$tdd` (RED-GREEN-REFACTOR) for each implementation step.
> to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## Required Plan Structure

### 1. Overview

- what is being built or changed
- why it matters

### 2. Success Criteria

- measurable "done" conditions

### 3. Tech Stack (if relevant)

- selected technologies and rationale

### 4. File Structure

**Before defining tasks, map out which files will be created or modified and what each one is responsible for.** This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces
- Each file should have one clear responsibility
- Prefer smaller, focused files over large ones
- Files that change together should live together
- Split by responsibility, not by technical layer
- In existing codebases, follow established patterns

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

### 5. Task Breakdown

For each task include:

- task name and id
- domain (`frontend | backend | mobile | debug`)
- priority (`P0 | P1 | P2 | P3`)
- dependencies
- input
- output
- verify method
- rollback strategy

### 5.5 Evidence & Monitoring

For medium or high-risk tasks, also include:

- what evidence is required before claiming success
- what signal should be monitored after the change
- what drift or failure would look like
- what fallback path exists if the signal goes red

### 6. Phase X Verification Checklist

- lint passes
- tests pass
- security scan reviewed
- all tasks completed
- `$gate` passes

## Plan Granularity: Bite-Sized Tasks

Each task in an implementation plan should be **completable in 2-5 minutes**. Break down as follows:
1. "Write the failing test" - one step
2. "Run it to verify it fails" - one step
3. "Implement minimal code to pass" - one step
4. "Run tests to verify they pass" - one step
5. "Commit" - one step

### Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

Each task MUST include:
- **Files:** Exact paths to create/modify/test
- **Code:** Complete code (not "add validation here")
- **Commands:** Exact commands with expected output
- **Verification:** How to confirm this task is done
- **Evidence:** What makes the step specific and believable

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Rules

- Do not use vague placeholders in implementation tasks.
- Keep tasks small and verifiable.
- Explain why each task exists, not only what to do.
- Exact file paths always.
- Complete code in every step — if a step changes code, show the code.
- Exact commands with expected output.
- DRY, YAGNI, TDD, frequent commits.

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

If you find issues, fix them inline. If you find a spec requirement with no task, add the task.

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `./{task-slug}.md`. Two execution options:**

**1. Subagent-Driven (`$sdd`)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- Use `codex-subagent-execution` skill
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- Execute tasks sequentially in current session
- Run `$gate` after each batch of 3 tasks

## Script Invocation Discipline

1. When plan execution calls scripts from other skills, run `--help` first.
2. Treat scripts as black-box helpers and execute by contract.
3. Read script source only when customization or bug fixing is required.

## Exit Gate

Plan writing is complete only when:

1. plan file exists at `./{task-slug}.md`
2. all required sections exist (including File Structure and No Placeholders)
3. self-review completed (spec coverage, placeholder scan, type consistency)
4. the plan can survive strict deliverable validation via `run_gate.py --output-file <plan.md>` without falling back to generic filler
5. user has reviewed and approved the plan

## Reference Files

- `references/plan-document-reviewer-prompt.md`: subagent dispatch template for automated plan quality verification.

## Related Skills

| Skill | Integration |
| --- | --- |
| `codex-subagent-execution` | Executes the plan this skill produces |
| `codex-test-driven-development` | Each task follows TDD cycle |
| `codex-verification-discipline` | Verify before claiming plan is complete |
| `codex-branch-finisher` | After all plan tasks complete, use `$finish` |

