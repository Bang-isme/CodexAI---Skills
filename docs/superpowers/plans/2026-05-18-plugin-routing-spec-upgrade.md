# Plugin Routing and Spec Framework Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve CodexAI domain routing, tool usage guidance, security-aware spec writing, and multi-ticket spec generation.

**Architecture:** Keep the existing skill-pack layout. Update the routing and spec contracts in markdown, then extend the spec generator/checker scripts and tests. Avoid new dependencies or a new runtime service.

**Tech Stack:** Python standard library, pytest, Markdown skill contracts, JSON schema documentation.

---

### Task 1: Add Failing Tests For Stronger Spec Output

**Files:**
- Modify: `skills/tests/test_spec_driven_development.py`

- [ ] **Step 1: Add tests for rich spec sections and tickets**

Add tests that call `init_spec.render_spec(...)` and assert the output contains `## Context Summary`, `## Evidence and Source Log`, `## Security Model`, `## Tool Research Plan`, `## Implementation Tickets`, `TICKET-001`, and `SEC-001`.

- [ ] **Step 2: Add tests for ticket parsing**

Add a test that calls `check_spec.parse_spec_metadata(...)` with a spec containing `TICKET-002` and asserts the metadata includes sorted ticket IDs.

- [ ] **Step 3: Run red test**

Run:

```powershell
python -m pytest skills/tests/test_spec_driven_development.py -q
```

Expected: tests fail because the current template, schema, and checker do not support the new sections and ticket IDs.

### Task 2: Add Failing Tests For Routing Contract

**Files:**
- Modify: `skills/tests/test_domain_specialist_integrity.py`

- [ ] **Step 1: Add domain routing contract test**

Assert `codex-domain-specialist/SKILL.md` contains `Tool-Aware Routing Overlay`, `Tool selection matrix`, `Security overlay`, and `Implementation ticket trigger`.

- [ ] **Step 2: Add security proportionality test**

Assert the domain specialist links tool evidence to security routing without requiring full compliance for every task.

- [ ] **Step 3: Run red test**

Run:

```powershell
python -m pytest skills/tests/test_domain_specialist_integrity.py -q
```

Expected: tests fail because the routing contract has not been upgraded yet.

### Task 3: Extend Spec Generator And Checker

**Files:**
- Modify: `skills/codex-spec-driven-development/scripts/init_spec.py`
- Modify: `skills/codex-spec-driven-development/scripts/check_spec.py`
- Modify: `skills/codex-spec-driven-development/references/spec.schema.json`

- [ ] **Step 1: Update `render_spec`**

Replace the short template with the richer sections from the design. Keep function signature stable.

- [ ] **Step 2: Add ticket parsing**

Add `TICKET_PATTERN = re.compile(r"\bTICKET-\d{3}\b")` and include `implementation_tickets` in `parse_spec_metadata`.

- [ ] **Step 3: Include tickets in reports**

Return `matched_implementation_tickets` and per-file `candidate_ticket_ids` in `build_report`.

- [ ] **Step 4: Update schema documentation**

Add required fields for `Implementation Tickets`, `Security Model`, `Tool Research Plan`, and ticket ID format.

- [ ] **Step 5: Run green spec tests**

Run:

```powershell
python -m pytest skills/tests/test_spec_driven_development.py -q
```

Expected: spec tests pass.

### Task 4: Extend Domain Specialist Routing Contract

**Files:**
- Modify: `skills/codex-domain-specialist/SKILL.md`

- [ ] **Step 1: Add Tool-Aware Routing Overlay**

Document when to use repo search, helper scripts, spec scripts, security references, and ticket generation.

- [ ] **Step 2: Add security overlay rules**

Document proportional security triggers: trust boundaries, attacker-controlled input, auth, secrets, deployment exposure, CI/package integrity.

- [ ] **Step 3: Add implementation ticket trigger**

Document when a spec should produce multiple tickets and what each ticket must contain.

- [ ] **Step 4: Run green routing tests**

Run:

```powershell
python -m pytest skills/tests/test_domain_specialist_integrity.py -q
```

Expected: routing tests pass.

### Task 5: Final Verification

**Files:**
- No new production files expected beyond modified skill, scripts, schema, tests, and docs.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
python -m pytest skills/tests/test_spec_driven_development.py skills/tests/test_domain_specialist_integrity.py -q
```

Expected: all focused tests pass.

- [ ] **Step 2: Inspect diff**

Run:

```powershell
git diff -- docs/superpowers skills/codex-domain-specialist/SKILL.md skills/codex-spec-driven-development skills/tests/test_spec_driven_development.py skills/tests/test_domain_specialist_integrity.py
```

Expected: diff only includes planned changes.
