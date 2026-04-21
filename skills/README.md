# CodexAI Skill Pack - Technical Internals

> Runtime-focused reference for the `skills/` directory. For the public overview, see [../README.md](../README.md).

## Current State

| Metric | Value |
| --- | --- |
| Version | `14.1.0` |
| Core Skills | 22 |
| Entry-point Scripts | 49 |
| Shared Helpers | 2 (`_js_parser.py`, `_scrum_agent_kit.py`) |
| References | 168+ |
| Starters | 29 |
| Artifact Templates | 6 |
| Agent Personas | 8 |
| Workflow Aliases | 6 |
| Short Aliases | 25+ |
| Pytest | 116/116 |
| Smoke | 51/51 |

---

## Runtime Flow

```text
User Request
  -> Intent Context Analyzer
  -> Plan Writer (when task is medium/large, with TDD steps + No Placeholders)
  -> Workflow Autopilot (routes to mode + TDD/Debug/Subagent skills)
  -> Domain/Security Routing
  -> Git Worktrees (optional, for complex tasks needing isolation)
  -> Subagent Execution (optional, for plan with independent tasks)
  -> TDD Implementation (RED-GREEN-REFACTOR per feature/fix)
  -> Systematic Debugging (4-phase root cause, for bugs)
  -> Execution Quality Gate
  -> Docs Change Sync / Project Memory / Git Autopilot
```

### Output Quality Path

```text
Reasoning Rigor
  -> Output Guard
  -> Editorial Review
  -> Run Gate (strict by default for plan/review/handoff)
  -> Quality Trend logging
```

---

## Skill Inventory

### Core Pipeline

| Skill | Role |
| --- | --- |
| `codex-master-instructions` | Global completion rules, evidence policy, failure circuit breaker |
| `codex-intent-context-analyzer` | Parse request into structured intent JSON |
| `codex-context-engine` | Generate/load `.codex/context/genome.md` |
| `codex-plan-writer` | Create verifiable task plans |
| `codex-workflow-autopilot` | Route work into build/fix/debug/review/docs/deploy/teach flows |
| `codex-reasoning-rigor` | Force deliberate, non-generic, evidence-backed reasoning |
| `codex-scrum-subagents` | Install project Scrum kits and native `.codex/agents` |

### Knowledge Packs

| Skill | Notes |
| --- | --- |
| `codex-design-system` | Premium visual vocabulary with palettes, typography, layouts, motion, composition, trends, and anti-pattern guards |
| `codex-design-md` | DESIGN.md contract authoring, scaffold, lint/diff/export wrapper, and reusable design-system source-of-truth workflow |
| `codex-domain-specialist` | 66 references and 19 starters across frontend, backend, data, DevOps, UX, and debugging |
| `codex-security-specialist` | 30 references and 10 starters across network, infrastructure, AppSec, DevSecOps, compliance, and advanced security |

### Quality, Memory, Delivery, and Discipline

| Skill | Notes |
| --- | --- |
| `codex-execution-quality-gate` | 17 runtime scripts including gate orchestration, security scan, smart tests, output guard, editorial review, quality trends, UX/a11y, and Lighthouse |
| `codex-project-memory` | 11 scripts plus the `genome_builder.py` helper for multi-role genome generation across Architecture, API Surface, Data Layer, Security Posture, Test Coverage, and File Map |
| `codex-docs-change-sync` | Code-to-docs impact mapper |
| `codex-git-autopilot` | Commit automation with gate awareness |
| `codex-doc-renderer` | DOCX rendering and verification helpers |
| `codex-test-driven-development` | **v14 NEW** — RED-GREEN-REFACTOR enforcement, Iron Law TDD, testing anti-patterns reference. Aliases: `$tdd`, `$red-green` |
| `codex-systematic-debugging` | **v14 NEW** — 4-phase root cause debugging, defense-in-depth, condition-based waiting, root cause tracing. Aliases: `$root-cause`, `$trace` |
| `codex-subagent-execution` | **v14 NEW** — Fresh subagent per task + 2-stage review (spec compliance → code quality), prompt templates. Aliases: `$sdd`, `$dispatch` |
| `codex-git-worktrees` | **v14 NEW** — Isolated workspaces with safety verification, auto-setup, clean test baseline. Aliases: `$worktree`, `$isolate` |
| `codex-verification-discipline` | **v14.1 NEW** — Iron Law "evidence before claims" behavioral constraint. No "should work" without fresh verification. Aliases: `$verify`, `$evidence` |
| `codex-branch-finisher` | **v14.1 NEW** — Structured 4-option completion workflow (merge, PR, keep, discard) with test gate and worktree cleanup. Aliases: `$finish`, `$finish-branch` |

---

## Execution Quality Gate

### Main Entry Points

| Script | Purpose |
| --- | --- |
| `auto_gate.py` | Single entry point for quick, full, and deploy verification modes |
| `run_gate.py` | Aggregate lint, test, and deliverable quality into a single gate decision |
| `pre_commit_check.py` | Fast staged-file checks before commit |
| `smart_test_selector.py` | Run only relevant tests for the current change surface |
| `security_scan.py` | Secret, debug, HTTP, and placeholder security checks |
| `install_hooks.py` | Install managed pre-commit enforcement hooks |
| `install_ci_gate.py` | Generate GitHub Actions or GitLab CI quality gate files |
| `output_guard.py` | Detect generic filler and weak evidence |
| `editorial_review.py` | Score decision clarity, grounding, tradeoffs, structure, and tone |
| `quality_trend.py` | Track code-shape, gate pass rate, output score, and editorial score over time |

### Strict Deliverables

These deliverable types auto-enable strict output behavior unless intentionally downgraded with `--advisory-output`:

- `plan`
- `review`
- `handoff`

For those artifacts, the pack now expects both:

1. grounded, reproducible evidence
2. writing that reads like an accountable human engineering artifact

---

## Scrum Subagents

The Scrum kit is no longer just documentation. It is executable infrastructure:

- 10 role briefs in the `.agent` bundle
- 10 native Codex custom agents rendered into `.codex/agents`
- 7 workflows
- 12 shorthand aliases
- 6 artifact templates
- installer, validator, diff, and update flows

Supported native-agent scopes:

- `project`
- `personal`
- `both`

---

## Agent Personas

The agent layer adds scoped personas on top of the normal skill pipeline. Current personas:

- `frontend-specialist`
- `backend-specialist`
- `security-auditor`
- `debugger`
- `test-engineer`
- `devops-engineer`
- `planner`
- `scrum-master`

These files live under `skills/.agents/` and are loaded when intent analysis suggests a matching persona.

---

## Workflow Aliases

Workflow aliases are shorthand entry points that load `skills/.workflows/*.md` before running the richer underlying flow.

| Alias | Workflow File | Equivalent |
| --- | --- | --- |
| `$plan` | `.workflows/plan.md` | `$codex-plan-writer` + BMAD Phase 1-2 |
| `$debug` | `.workflows/debug.md` | `$codex-systematic-debugging` + 4-phase root cause |
| `$create` | `.workflows/create.md` | `workflow-create.md` + TDD |
| `$review` | `.workflows/review.md` | `workflow-review.md` + output-guard + editorial |
| `$deploy` | `.workflows/deploy.md` | `workflow-deploy.md` + full gate |
| `$handoff` | `.workflows/handoff.md` | `workflow-handoff.md` + session summary |

---

## Testing Strategy

### Unit tests

Current suite coverage includes:

- parsing and routing behavior
- output rigor and editorial rubric
- strict-output gate logic
- quality-trend aggregation
- Scrum installer, validator, diff, update, and native agent rendering
- docs encoding and mojibake regression guards
- skill validation and pre-commit hardening

### Smoke tests

Smoke checks verify:

- all codex skill directories expose `SKILL.md`
- critical scripts respond to `--help`
- selected JSON-returning CLIs run real happy paths
- the DESIGN.md wrapper reports runtime health through `design_contract.py doctor`
- workflow routing contract exists and is valid

---

## Maintenance Notes

### When updating docs

Refresh these together:

- `README.md`
- `skills/README.md`
- `docs/huong-dan-vi.md`
- `skills/CHANGELOG.md`
- `skills/VERSION`

### When updating deliverable quality logic

Review these together:

- `codex-reasoning-rigor/SKILL.md`
- `codex-execution-quality-gate/SKILL.md`
- `scripts/output_guard.py`
- `scripts/editorial_review.py`
- `scripts/run_gate.py`
- `scripts/quality_trend.py`
- `tests/test_output_rigor.py`
- `tests/test_parsing.py`
- `tests/smoke_test.py`

---

## Commands Worth Remembering

```bash
python skills/tests/smoke_test.py
python -m pytest skills/tests -q
python skills/codex-execution-quality-gate/scripts/run_gate.py --project-root <repo>
python skills/codex-execution-quality-gate/scripts/output_guard.py --file <deliverable.md>
python skills/codex-execution-quality-gate/scripts/editorial_review.py --file <deliverable.md>
python skills/codex-execution-quality-gate/scripts/quality_trend.py --project-root <repo> --report
python skills/codex-design-md/scripts/design_contract.py scaffold --name <brand-or-product>
python skills/codex-design-md/scripts/design_contract.py lint DESIGN.md
```
