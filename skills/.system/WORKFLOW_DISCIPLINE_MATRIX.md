# Workflow Discipline Matrix

Purpose: keep CodexAI Skill Pack coverage explicit for core coding-agent workflow disciplines, while avoiding vendor-specific or third-party branding in the public pack.

## Coverage Map

| Workflow Discipline | CodexAI Equivalent | Status | Notes |
|---|---|---|---|
| skill invocation discipline | `codex-master-instructions` Skill Invocation Rule | Covered | Enforces checking aliases, agents, and discipline skills before acting. |
| brainstorming | `codex-workflow-autopilot` brainstorm mode + `$brainstorm` | Covered | Explores approaches without coding. |
| plan writing | `codex-plan-writer` + `.workflows/plan.md` | Covered | Adds TDD steps, file structure, dependencies, and verification criteria. |
| plan execution | `codex-workflow-autopilot` + `codex-subagent-execution` | Covered | Executes approved plans with checkpoints and review loops. |
| test-driven development | `codex-test-driven-development` + `$tdd` | Covered | RED-GREEN-REFACTOR is mandatory for code changes. |
| systematic debugging | `codex-systematic-debugging` + `$root-cause` | Covered | Root cause before fix, regression test before completion. |
| verification before completion | `codex-verification-discipline` + quality gate scripts | Covered | Evidence before claims. |
| requesting code review | `.workflows/review.md` + quality gate review mode | Covered | Findings by severity plus output/editorial guard when applicable. |
| receiving code review | `codex-subagent-execution` review-feedback path + `code-review-discipline.md` | Covered | Verify suggestions technically before applying them. |
| parallel agent dispatch | `codex-subagent-execution` Safe Parallel Dispatch | Covered with guardrails | Parallel only for disjoint write scopes and explicit ownership. |
| subagent-driven development | `codex-subagent-execution` + agents templates | Covered | Fresh subagent per task with spec and quality review. |
| git worktree isolation | `codex-git-worktrees` + `$worktree` | Covered | Isolated workspaces for complex work. |
| branch finishing | `codex-branch-finisher` + `$finish` | Covered | Structured finish/merge/PR/cleanup options. |
| skill authoring | `.system/skill-creator` | Covered | Skill authoring and validation exists in system skills. |
| project status tracking | `codex-project-pulse` + `$today` + `$pulse` | Covered | Sprint state, priority queue, blockers, risks, milestones, daily brief. |
| refactoring | `.workflows/refactor.md` + `codex-workflow-autopilot` | Covered | Tech debt baseline, blast radius prediction, incremental refactor with verification. |

## CodexAI Extensions

- Domain and security specialist routing with reference boundaries.
- Agent personas and workflow alias files.
- Runtime quality scripts: `auto_gate.py`, `output_guard.py`, `editorial_review.py`, `security_scan.py`, and benchmark tooling.
- Vietnamese document clarity and mojibake guards.
- Project memory and multi-role project genome generation.
- Design system and DESIGN.md visual identity support.
- Real-time project state with autonomous daily brief generation (`codex-project-pulse`).

## Guardrail

Coverage does not mean copying another pack's branding or behavior. CodexAI keeps stricter evidence, portability, output-quality, and anti-overengineering rules because this pack targets repeatable, verifiable output across coding and document workflows.
