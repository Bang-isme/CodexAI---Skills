# Changelog

## [15.2.0] - 2026-04-28

### Added
- Added native Codex plugin packaging with `.codex-plugin/plugin.json`.
- Added local marketplace entry at `.agents/plugins/marketplace.json`.
- Added `.system/scripts/validate_codex_plugin.py` for plugin manifest, marketplace, skill metadata, native agent TOML, and path-rule validation.
- Added `.system/scripts/install_codex_native.py` with repo/user/admin/legacy/custom install targets for Codex-native skill directories.
- Added `.system/scripts/init_agents_md.py` to create a small Codex-native `AGENTS.md` bridge instead of copying the full rule set.
- Added `install_codex_hooks.py`, `validate_codex_hooks.py`, and `templates/codex-hooks.json` for project-local Codex hook integration.
- Added `runtime_hook.py --format prompt` for compact hook output.

### Changed
- Prefer Codex-native plugin/marketplace install over legacy global skills sync for normal users.
- Treat `sync_global_skills.py` as a development compatibility path.
- Rewrote skill descriptions to front-load "Use for" / "Use when" triggers for better Codex progressive disclosure.

### Fixed
- Avoid relying on `~/.codex/skills` as the only install target.
- Ensure generated Codex hook commands use explicit project and skills paths.
- Add native plugin validation coverage so packaging drift is caught by tests.

### Infrastructure
- Bumped version: `15.1.0` -> `15.2.0`
- Verified suite target: `204` unit tests + `68` smoke checks.

## [15.1.0] - 2026-04-28

### Added
- Added **NEW SKILL**: `codex-spec-driven-development` for spec-first prototype, MVP, and fullstack workflows.
- Added `$spec` and `$prototype` aliases plus `.workflows/prototype.md`.
- Added `init_spec.py` and `check_spec.py` for `.codex/specs/<slug>/SPEC.md` creation and advisory traceability checks.
- Added `init_profile.py` for optional `.codex/profile.json` routing hints and user/project preferences.
- Added `build_knowledge_index.py` to generate `.codex/knowledge/INDEX.md` and `index.json` from genome, role docs, decisions, commits, and config.
- Added `.system/scripts/sync_global_skills.py` to sync global skills with dot directories, dry-run/apply mode, backups, and protected built-in Codex system skills.

### Changed
- Upgraded `runtime_hook.py` with profile priority, context readiness, knowledge/spec status, workflow recommendation, and monorepo advisory output.
- Added schema-versioned contracts for profile JSON, runtime hook output, spec markdown, and knowledge index.
- Hardened knowledge index output with redaction, provenance, confidence, and untrusted-content labeling.
- Updated `$create` and `$prototype` routing so fullstack/MVP work follows preflight -> profile/context -> role docs -> spec -> plan -> implementation -> full gate.
- Updated `auto_gate.py` full/deploy modes with non-blocking spec and knowledge advisory checks.
- Updated README, Vietnamese guide, registry, manifest, operation runbook, and smoke coverage for the full-cycle development workflow.

### Infrastructure
- Bumped version: `15.0.0` -> `15.1.0`
- Verified suite target: `197` unit tests + `63` smoke checks.

## [15.0.0] - 2026-04-26

### Added
- Added **NEW SKILL**: `codex-project-pulse` — autonomous project management with real-time state tracking.
  - Sprint state management: `$sprint-init`, `$sprint-close`, `$add-story`, `$done`, `$wip`.
  - Priority queue engine with automatic scoring, WIP limits, and reordering.
  - Blocker tracking with stale detection and escalation: `$block`, `$unblock`, `$blockers`.
  - Risk register with severity × probability matrix: `$risk`.
  - Milestone tracking with deadline proximity alerts: `$milestone`, `$milestones`.
  - Daily brief generation: `$today`, `$pulse`, `$daily`, `$status`, `$brief`.
  - Vietnamese daily brief support ("hôm nay thế nào?").
  - Sprint velocity tracking and capacity forecasting.
  - Kanban fallback mode when no sprint is initialized.
  - Integration with `codex-project-memory`, `codex-execution-quality-gate`, `codex-scrum-subagents`, and `codex-workflow-autopilot`.
- Added `references/state-schemas.md`: JSON schemas for sprint-state, priority-queue, blockers, risk-register, milestones.
- Added `references/daily-brief-template.md`: generation protocol, calculation rules, full example, Vietnamese version, edge cases.
- Added `references/priority-engine.md`: priority scoring formula, queue algorithm, WIP limits, reordering.
- Added `.workflows/refactor.md` alias (was missing — `workflow-refactor.md` reference existed without alias).
- Added `references/workflow-plan.md` to `codex-workflow-autopilot` (consistency fix — all other workflows had both ref + alias).
- Added **NEW SKILL**: `codex-runtime-hook` for one-command project preflight, domain detection, missing FE/BE/DevOps/QA readiness artifacts, and suggested next commands.
- Added **NEW SKILL**: `codex-logical-decision-layer` for compact option comparison, evidence, tradeoff, verification, and stop-condition contracts without leaking hidden chain-of-thought.
- Added `$hook`, `$preflight`, `$think`, and `$decide` aliases to master instructions.
- Added `runtime_hook.py` and `build_decision_matrix.py` to the central registry and smoke coverage.
- Added `.system/OPERATION_RUNBOOK.md` for exact install, preflight, role-doc, gate, hook, CI, and troubleshooting operations.
- Added `.system/scripts/check_pack_health.py` to verify manifest, registry, aliases, dot directories, global sync, and markdown encoding drift.

### Changed
- Enriched all 7 Scrum ceremony workflows (backlog-refinement, sprint-planning, daily-scrum, story-delivery, sprint-review, retrospective, release-readiness) from stubs (~500B) to production-grade with templates, checklists, anti-patterns, and examples (~3KB each).
- Updated `codex-workflow-autopilot/SKILL.md` to reference `workflow-plan.md` and `refactor.md` alias.
- Updated `manifest.json`: added `refactor` to workflows list, added `codex-project-pulse` to skills and on-demand load order.
- Updated `manifest.json`: added `codex-runtime-hook` and `codex-logical-decision-layer` to on-demand load order.
- Updated `auto_gate.py` quick/full/deploy modes to include runtime preflight as a non-blocking advisory check.
- Repaired the Vietnamese usage guide from mojibake to valid UTF-8 text.
- Verified suite target: `184` unit tests + `58` smoke checks.
- Bumped version from 14.3.0 to 15.0.0.

## [14.3.0] - 2026-04-24

### Added
- Added **NEW SKILL**: `codex-role-docs` for project-local role documentation under `.codex/project-docs/`.
- Added role-doc templates for project brief, ADR seed, and FE/BE/DevOps/Admin/QA documentation.
- Added `init_role_docs.py`, `update_role_docs.py`, `check_role_docs.py`, and `build_role_docs_index.py`.
- Added aliases `$role-docs`, `$init-docs`, and `$check-docs`.
- Added role-doc regression tests for initialization, updates, indexing, changed-file mapping, agent ownership, and advisory gate behavior.

### Enhanced
- Updated agent personas so each role can edit its own `.codex/project-docs/` files without violating boundary enforcement.
- Added advisory role-doc checks to `auto_gate.py` full/deploy modes; missing or stale docs warn but never block.
- Added `codex-role-docs` to manifest, registry, public README, and technical internals.

### Infrastructure
- Bumped version: `14.2.1` -> `14.3.0`
- Fixed install/sync documentation so dot directories such as `.system`, `.agents`, and `.workflows` are copied into global skills.
- Refreshed the Vietnamese usage guide for v14.3.0 release metadata and safe sync commands.
- Verified suite target: `168` unit tests + `55` smoke checks.

## [14.2.1] - 2026-04-24

### Fixed
- Removed a user-specific default path from `track_skill_usage.py`; the script now defaults to `Path.home() / ".codex" / "skills"` for portability.
- Replaced mojibake text in `track_skill_usage.py` recommendations with ASCII-safe separators.
- Replaced mojibake text in `playwright_runner.py` generated-test notes with an ASCII-safe separator.
- Added UTF-8 stdout/stderr configuration for output-quality CLIs to prevent Windows console encoding failures on Vietnamese deliverables.
- Improved `output_guard.py` evidence detection for Vietnamese prose commands such as `Bang chung: chay python -m pytest ...`.
- Reduced false-positive security scan noise from scanner literals, local HTTP examples, and non-production TODO references.
- Hardened `tech_debt_scan.py` against UTF-8 BOM parsing failures and low-signal test/template directories.
- Tightened command evidence extraction so same-line Vietnamese section labels do not get captured as part of commands.
- Expanded command evidence support for modern toolchains such as `npx`, `uv`, `bun`, `yarn`, `ruff`, `mypy`, and `docker`, with prose guards to avoid false positives such as "Python is required".
- Hardened `benchmark_quality.py` corpus parsing with structured JSON error output and support for string-valued expectation matchers.
- Added `utf-8-sig` corpus loading so benchmark files created by Windows tools with a UTF-8 BOM still work.

### Added
- Added `.system/WORKFLOW_DISCIPLINE_MATRIX.md` to track CodexAI coverage against core coding-agent workflow disciplines without third-party branding.
- Added workflow discipline regression tests for the skill invocation rule, brainstorm/review-feedback routing, and safe parallel subagent dispatch.
- Added file-based benchmark corpus for release reports, decision memos, PR reviews, incident postmortems, technical decisions, frontend handoffs, and stakeholder status reports.
- Expanded `benchmark_quality.py` to report output score, editorial score, quality index, and expectation hit rate.
- Added regression tests for UTF-8 CLI output, Vietnamese command evidence, benchmark corpus loading, invalid corpus handling, BOM-encoded corpus JSON, scanner noise, BOM handling, modern command parsing, and prose false-positive prevention.
- Added release integrity tests that verify version strings, README badges, changelog, benchmark version, and published test-count metadata stay aligned.
- Added specialist integrity tests to lock domain/security reference coverage and anti-overengineering guardrails.

### Enhanced
- Added a P0 Skill Invocation Rule to `codex-master-instructions` so relevant skills are selected before acting, without bulk-loading unrelated context.
- Added `$brainstorm` and `$review-feedback` routing for planning and review feedback workflows.
- Updated `codex-subagent-execution` to allow safe parallel dispatch only for disjoint write scopes with explicit ownership and final integration by the coordinator.
- Strengthened `codex-domain-specialist` with a Scope Fit Gate, complexity budget, and explicit proof requirement before adding dependencies, services, queues, caches, or architecture layers.
- Strengthened `codex-security-specialist` with proportional-control rules so defense-in-depth does not become unjustified WAF/SIEM/mTLS/Vault/compliance overengineering.

### Infrastructure
- Bumped version: `14.2.0` -> `14.2.1`
- Verified suite target: `149` unit tests + `51` smoke checks.
- Added missing `codex-verification-discipline` and `codex-branch-finisher` entries to manifest on-demand load order.

## [14.1.0] - 2026-04-19

### Added - 2 New Discipline Skills (Round 2 Workflow Discipline Coverage)
- **NEW SKILL**: `codex-verification-discipline`
  - `SKILL.md`: Iron Law "evidence before claims" behavioral constraint
  - Rationalization prevention table (8 excuses countered)
  - Evidence patterns for tests, builds, requirements, agent delegation
  - Aliases: `$verify`, `$evidence`
  - Load priority: `always` (constant behavioral constraint)

- **NEW SKILL**: `codex-branch-finisher`
  - `SKILL.md`: Structured 4-option completion workflow (merge, PR, keep, discard)
  - Test verification gate - blocks completion if tests fail
  - Worktree cleanup integration with `codex-git-worktrees`
  - Bash + PowerShell command equivalents
  - Aliases: `$finish`, `$finish-branch`

### Added - New Reference Files
- `codex-test-driven-development/references/testing-anti-patterns.md`: Enhanced with Iron Laws, gate functions for anti-patterns 1-3
- `codex-subagent-execution/references/code-review-discipline.md`: How to receive code review feedback without performative agreement
- `codex-plan-writer/references/plan-document-reviewer-prompt.md`: Subagent dispatch template for automated plan quality verification

### Enhanced - Intent Context Analyzer
- Added **HARD-GATE**: Design before implementation - no code without approved design
- Added **Anti-Pattern**: "This Is Too Simple To Need A Design" counter
- Added **2-3 Approaches**: Propose approaches with trade-offs before settling
- Added **Design Self-Review**: Placeholder scan, internal consistency, scope check, ambiguity check
- Added **One question at a time** discipline + multiple choice preference
- Added **Sub-project decomposition** for multi-system requests

### Enhanced - Cross-References and Integration
- `codex-subagent-execution`: Added `codex-verification-discipline` and `codex-branch-finisher` to Related Skills
- `codex-plan-writer`: Added Reference Files and Related Skills sections
- `codex-master-instructions`: Added 4 new aliases (`$finish-branch`, `$verify`, `$evidence`), fixed `$finish` routing to `codex-branch-finisher`

### Fixed - Quality Issues (Round 1 Audit)
- Consolidated 3 duplicate reference files (condition-based-waiting, defense-in-depth, root-cause-tracing) - old versions in `codex-master-instructions/references/` now redirect to canonical versions in `codex-systematic-debugging/references/`
- Added `tdd` to workflow-autopilot Output Contract mode enum
- Synced quality gate decision tree with master-instructions v14 (added TDD, systematic debugging, worktree routes)
- Updated intent analyzer with Discipline Skill Notes table
- Translated 6 Vietnamese fragments to English across 6 skills
- Added PowerShell equivalents for all critical git-worktrees commands
- Added "Announce at start" to `codex-systematic-debugging` and `codex-subagent-execution`
- Added Related Discipline Skills section to `codex-execution-quality-gate`
- Updated `codex-master-instructions` reference pointers to canonical sources

### Infrastructure
- Bumped version: `14.0.0` -> `14.1.0`
- Total skills: 19 -> 21 (15 pipeline + 6 discipline)
- Total aliases: 27 -> 31

## [14.0.0] - 2026-04-19

### Added - 4 New Discipline Skills (Workflow Mastery)
- **NEW SKILL**: `codex-test-driven-development`
  - `SKILL.md`: RED-GREEN-REFACTOR Iron Law enforcement, 12-excuse rationalization table, verification checklist
  - `references/testing-anti-patterns.md`: 7 anti-patterns with Python + TypeScript examples
  - Aliases: `$tdd`, `$red-green`

- **NEW SKILL**: `codex-systematic-debugging`
  - `SKILL.md`: 4-phase root cause debugging, 3+ fix failure = question architecture (Phase 4.5)
  - `references/root-cause-tracing.md`: backward call-chain tracing technique
  - `references/defense-in-depth.md`: 4-layer validation pattern
  - `references/condition-based-waiting.md`: replace sleep() with condition polling
  - Aliases: `$root-cause`, `$trace`

- **NEW SKILL**: `codex-subagent-execution`
  - `SKILL.md`: fresh subagent per task + 2-stage review (spec compliance -> code quality)
  - `agents/implementer-prompt.md`: implementer dispatch template
  - `agents/spec-reviewer-prompt.md`: spec compliance review template
  - `agents/code-quality-reviewer-prompt.md`: code quality review template
  - Aliases: `$sdd`, `$dispatch`

- **NEW SKILL**: `codex-git-worktrees`
  - `SKILL.md`: isolated workspaces with safety verification, auto-setup, clean test baseline
  - Aliases: `$worktree`, `$isolate`, `$finish`

### Enhanced - 3 Existing Skills
- `codex-plan-writer/SKILL.md`:
  - Added File Structure section (lock decomposition decisions before tasks)
  - Added No Placeholders enforcement (TBD/TODO = plan failure)
  - Added Self-Review checklist (spec coverage, placeholder scan, type consistency)
  - Added Execution Handoff (Subagent-Driven vs Inline choice)
  - Added Scope Check for multi-subsystem specs
  - Added Plan Document Header template

- `codex-master-instructions/SKILL.md`:
  - Added 9 new aliases: `$tdd`, `$red-green`, `$root-cause`, `$trace`, `$sdd`, `$dispatch`, `$worktree`, `$isolate`, `$finish`
  - Enhanced Decision Tree: simple-code now routes through TDD, debug through systematic debugging
  - Enhanced Quality Gate Decision Tree: TDD + systematic debugging + worktree + subagent paths

- `codex-workflow-autopilot/SKILL.md`:
  - Added TDD behavioral mode
  - Enhanced debug mode -> 4-phase systematic debugging
  - Enhanced Intent to Workflow table with TDD and skill aliases
  - Enhanced BMAD Phase 4 with worktree, subagent execution, TDD integration

### Updated - Agents & Infrastructure
- `.agents/debugger.md`: linked to `codex-systematic-debugging` + `codex-test-driven-development`, added 4-phase behavioral rules
- `.agents/test-engineer.md`: linked to `codex-test-driven-development`, added TDD Iron Law + anti-patterns reference
- `.workflows/debug.md`: routes through `codex-systematic-debugging` + Phase 4.5 architecture check
- `.system/manifest.json`: version 14.0.0, added 4 new skills to skill list and on-demand load order
- `skills/README.md`: updated metrics (19 skills), runtime flow, skill inventory, workflow aliases

### Metrics
- Skills: 15 -> 19 (4 new discipline skills)
- Short aliases: 16 -> 25+ (9 new)
- References: 160 -> 165+
- Version: 13.0.0 -> 14.0.0


## [12.6.0] - 2026-03-18

### Added
- `codex-execution-quality-gate/scripts/editorial_review.py`: new editorial-quality rubric that scores decision clarity, grounding, tradeoff awareness, structure, and AI-safe tone drift for written deliverables.
- `codex-execution-quality-gate/references/editorial-review-spec.md`: documented the new human-quality deliverable rubric and its fail conditions.

### Improved
- `codex-execution-quality-gate/scripts/run_gate.py`: strict deliverables (`plan`, `review`, `handoff`) now evaluate both output specificity and editorial quality before passing.
- `codex-execution-quality-gate/scripts/quality_trend.py`: reports now include average editorial score and editorial failure rate in addition to gate pass rate and output-guard score.
- `codex-reasoning-rigor/assets/output-review-template.md`: expanded to include decision and editorial checks, not just specificity.
- `README.md`, `skills/README.md`, and `docs/huong-dan-vi.md`: refreshed and simplified with current metrics, clearer workflow guidance, and cleaner rendering-safe formatting.

### Tests
- `tests/test_output_rigor.py`: added editorial rubric coverage for AI-speak rejection and decision-ready deliverables.
- `tests/test_parsing.py`: added gate integration coverage for editorial review and trend aggregation.
- `tests/smoke_test.py`: expanded to `49` smoke checks with JSON coverage for `editorial_review.py`.
- Full suite status: `98` unit tests and `49` smoke checks passing

## [12.5.0] - 2026-03-18

### Improved
- `codex-execution-quality-gate/scripts/run_gate.py`: plan, review, and handoff deliverables now auto-enable strict output enforcement by default when an output file or text is provided, unless `--advisory-output` is used to downgrade them intentionally.
- `codex-execution-quality-gate/scripts/run_gate.py`: gate runs now append quality events under `.codex/quality/gate-events.jsonl` so output quality and gate pass rate can be tracked over time.
- `codex-execution-quality-gate/scripts/quality_trend.py`: trend reports now include gate pass rate, strict-output failure rate, average output-guard score, and deliverable-kind counts in addition to code-shape metrics.
- `codex-plan-writer/SKILL.md`, `codex-reasoning-rigor/SKILL.md`, `codex-execution-quality-gate/SKILL.md`, and `codex-execution-quality-gate/references/*.md`: updated to document default strict-output expectations for plans, reviews, and handoffs.
- `skills/tests/test_parsing.py` and pack docs: added single-snapshot gate-quality coverage and refreshed the published test totals to 83 unit + 47 smoke.

### Tests
- `tests/test_parsing.py`: expanded to 44 tests with auto-strict-output and gate-quality trend coverage.
- `tests/smoke_test.py`: expanded to 47 smoke checks with CLI coverage for gate-aware quality trend reports.
- Full suite status: `83` unit tests and `47` smoke checks passing

## [12.4.0] - 2026-03-18

### Added
- `codex-scrum-subagents/scripts/install_scrum_subagents.py`: native-agent scope support via `--native-scope project|personal|both`, so personal `~/.codex/agents` installs no longer require manual copying.
- `codex-workflow-autopilot/references/workflow-routing-contract.json`: machine-checkable routing contract for workflow modes, Scrum overlay triggers, and required output fields.

### Improved
- `codex-scrum-subagents/scripts/validate_scrum_agent_kit.py`: validator now supports `--target-root` + `--install-dir`, reads the install stamp to resolve custom install directories correctly, and can validate project and personal native-agent scopes.
- `codex-scrum-subagents/scripts/_scrum_agent_kit.py`: native agent validation now parses generated TOML with `tomllib` instead of relying on string-shape checks only.
- `codex-scrum-subagents/scripts/run_scrum_alias.py`: installer aliases can now forward native-agent scope to install and validate flows.
- `codex-workflow-autopilot/SKILL.md`: routing guidance now explicitly references the machine-checkable contract and no longer implies that subagent-aware execution is impossible.
- `README.md`, `skills/README.md`, and `docs/huong-dan-vi.md`: refreshed metrics, install guidance, and subagent/runtime notes.

### Tests
- `tests/test_scrum_subagents.py`: expanded to 28 tests with coverage for custom install directories, personal native-agent scope, and TOML validation.
- `tests/smoke_test.py`: expanded to 46 smoke checks and now validates the workflow routing contract plus custom install-dir/native-scope installer paths.
- Full suite status: `79` unit tests and `46` smoke checks passing

## [12.3.0] - 2026-03-18

### Added
- `codex-scrum-subagents`: the installer now materializes native Codex custom agents into `<project-root>/.codex/agents` alongside the existing `.agent` workflow kit, so Scrum roles can align with the official Codex subagent discovery path.
- `codex-scrum-subagents/scripts/_scrum_agent_kit.py`: added native custom-agent rendering, comparison, and copy helpers generated from the existing Scrum role briefs and manifests.

### Improved
- `codex-scrum-subagents/scripts/install_scrum_subagents.py`: install, diff, and update flows now track both the `.agent` bundle and the generated `.codex/agents` native custom-agent layer in one report.
- `codex-scrum-subagents/scripts/validate_scrum_agent_kit.py`: validator now detects drift in project-local native Codex agents as well as the `.agent` tree.
- `codex-scrum-subagents/SKILL.md`, `README.md`, `skills/README.md`, `docs/huong-dan-vi.md`, `references/command-aliases.md`, and the bundled Scrum kit docs: refreshed to document the new native custom-agent install path.

### Tests
- `tests/test_scrum_subagents.py`: expanded to 24 tests covering native custom-agent rendering, installer creation, drift repair, and validator drift detection for `.codex/agents`.
- `tests/smoke_test.py`: expanded to 45 smoke checks with JSON execution coverage for Scrum install and validate flows.
- Full suite status: `75` unit tests and `45` smoke checks passing

## [12.2.2] - 2026-03-18

### Fixed
- `codex-scrum-subagents/scripts/install_scrum_subagents.py`: `--diff` and `--update` now render table output without crashing when the report comes from the operation path.
- `codex-scrum-subagents/scripts/install_scrum_subagents.py`: `--update` now recomputes the returned diff after repairing the installed `.agent` tree, so the report reflects the post-update state instead of stale pre-copy drift.
- `codex-scrum-subagents/scripts/install_scrum_subagents.py`: provenance stamps now preserve the real `--force` flag during update operations instead of hardcoding `true`.

### Tests
- `tests/test_scrum_subagents.py`: expanded to 20 tests with CLI regression coverage for `--diff`, `--update`, post-update diff reporting, and update stamp metadata.
- Full suite status: `71` unit tests and `43` smoke checks passing

## [12.2.1] - 2026-03-18

### Changed
- Source pack cleanup: removed the repo/global drift doctor from the repository so `<SOURCE_REPO>` stays focused on the clean distributable pack, while that helper can remain global-only in `<CODEX_HOME>/skills` if desired.
- `codex-execution-quality-gate/SKILL.md`, `README.md`, `skills/README.md`, and `docs/huong-dan-vi.md`: removed source-pack references to the repo/global drift helper and refreshed metrics for the clean source pack.

### Tests
- `tests/smoke_test.py`: reduced to `43` checks after removing the source-pack-only drift audit entry points.
- Full suite status: `68` unit tests and `43` smoke checks passing

## [12.2.0] - 2026-03-18

### Improved
- `codex-execution-quality-gate/scripts/output_guard.py`: added optional `--repo-root` grounding checks so file references and path-like command arguments can be verified against the real repo tree.
- `codex-execution-quality-gate/scripts/run_gate.py`: added `--strict-output`, `--output-file`, and `--output-text` so weak deliverables can fail the gate instead of being advisory-only.
- `codex-execution-quality-gate/references/output-guard-spec.md`: documented repo-aware grounding validation.
- `codex-execution-quality-gate/references/run-gate-spec.md`: documented strict-output behavior.
- `codex-execution-quality-gate/SKILL.md`: added strict-output usage and pack-maintenance routing guidance for deliverable quality checks.
- `README.md`, `skills/README.md`, and `docs/huong-dan-vi.md`: refreshed metrics, command surface, and quality-gate guidance.

### Tests
- `tests/test_output_rigor.py`: added repo-aware grounding coverage for valid vs stale artifact references.
- `tests/test_parsing.py`: added strict-output gate coverage for pass/fail deliverables.
- `tests/smoke_test.py`: expanded to cover `run_gate.py --strict-output` and repo-aware deliverable validation paths.
- Full suite status: `68` unit tests and `43` smoke checks passing

## [12.1.0] - 2026-03-18

### Fixed
- `codex-execution-quality-gate/scripts/output_guard.py`: command evidence now requires runnable command snippets instead of counting prose mentions like "git" or "python", and overlapping filler phrases are deduplicated so one phrase is not penalized twice.
- `codex-reasoning-rigor/scripts/build_reasoning_brief.py`: strict mode now blocks placeholder-only briefs, adds the missing `quality_bar` field from the skill contract, and reserves `_TODO_` scaffolds for explicit `--allow-placeholders` mode.
- `codex-scrum-subagents/scripts/generate_scrum_artifact.py`: artifact generation now validates all template fields before returning success, with explicit scaffold mode for intentional placeholders.
- `codex-scrum-subagents/scripts/run_scrum_alias.py`: alias-driven artifact generation now rejects incomplete story/release artifacts by default and reports required or missing fields clearly.

### Improved
- `codex-execution-quality-gate/references/output-guard-spec.md`: clarified that only runnable command snippets count as verification evidence.
- `codex-reasoning-rigor/SKILL.md`: documented strict brief generation and the explicit scaffold escape hatch.
- `codex-scrum-subagents/SKILL.md` and `references/artifact-templates.md`: updated examples and guardrails so ceremony artifacts no longer imply success when they are still placeholders.
- `README.md`, `skills/README.md`, and `docs/huong-dan-vi.md`: refreshed metrics, examples, and validation guidance for the stricter anti-generic workflow.

### Tests
- `tests/test_output_rigor.py`: expanded to cover prose-only evidence rejection, overlapping filler dedupe, strict reasoning brief validation, and scaffold mode.
- `tests/test_scrum_subagents.py`: added coverage for required-field enforcement and explicit scaffold mode in both artifact generation and alias dispatch.
- `tests/smoke_test.py`: upgraded from help-only coverage to `42` checks including real JSON CLI execution for `output_guard.py`, `build_reasoning_brief.py`, `generate_scrum_artifact.py`, and `run_scrum_alias.py`.
- Full suite status: `64` unit tests and `42` smoke checks passing

## [12.0.0] - 2026-03-18

### Added
- **NEW SKILL**: `codex-reasoning-rigor`
  - `SKILL.md`: anti-generic reasoning protocol focused on task contracts, evidence ladders, monitoring loops, and output contracts
  - `scripts/build_reasoning_brief.py`: deterministic brief generator for complex, high-signal work
  - `references/anti-generic-patterns.md`, `evidence-ladder.md`, `monitoring-loops.md`, `output-contracts.md`
  - `assets/`: reasoning brief, output review, and monitoring checklist templates
- `codex-execution-quality-gate/scripts/output_guard.py`: heuristic scorer for generic filler, weak evidence, and low-specificity deliverables
- `codex-execution-quality-gate/references/output-guard-spec.md`: scoring expectations and use cases for output guard
- `codex-scrum-subagents/scripts/run_scrum_alias.py`: runnable dispatcher for `$scrum-*`, `$story-*`, `$retro`, and `$release-readiness`
- `codex-scrum-subagents/scripts/generate_scrum_artifact.py`: Scrum markdown artifact generator
- `codex-scrum-subagents/references/artifact-templates.md` plus 6 bundled artifact templates for user story, sprint goal, daily scrum, retrospective, story delivery, and release readiness

### Improved
- `codex-master-instructions/SKILL.md`: added reasoning-rigor activation when users ask for deeper, less generic output
- `codex-plan-writer/SKILL.md`: plans now explicitly call out required evidence and monitoring signals for medium/high-risk work
- `codex-workflow-autopilot/SKILL.md`: added reasoning-rigor trigger and guidance to pair high-stakes outputs with `$output-guard`
- `codex-execution-quality-gate/SKILL.md`: documented `$output-guard` and the new deliverable-quality route
- `codex-scrum-subagents/SKILL.md`: documented runnable alias workflow and artifact templates
- `README.md`, `skills/README.md`, and `docs/huong-dan-vi.md`: refreshed skill inventory, command surface, metrics, and anti-generic capabilities

### Tests
- `tests/test_output_rigor.py`: added 4 tests for output guard and reasoning brief generation
- `tests/test_scrum_subagents.py`: expanded to 14 tests with artifact generation and alias workflow coverage
- `tests/smoke_test.py`: expanded to 38 checks including output guard, reasoning brief, and Scrum artifact scripts
- Full suite status: `57` unit tests and `38` smoke checks passing

## [11.2.0] - 2026-03-18

### Added
- `codex-scrum-subagents/assets/scrum-agent-kit/services/commands.json`: machine-readable alias registry for installer actions and Scrum ceremony shortcuts.
- `codex-scrum-subagents/references/command-aliases.md`: shorthand command reference for `$scrum-*`, `$story-*`, `$retro`, and `$release-readiness`.

### Improved
- `codex-scrum-subagents/SKILL.md`: documented the new shorthand command layer and when to load it.
- `codex-workflow-autopilot/SKILL.md`: added explicit routing for Scrum shorthand aliases so ceremony-style requests can trigger the Scrum overlay faster.
- `README.md`, `skills/README.md`, and `docs/huong-dan-vi.md`: refreshed counts, command tables, and Scrum alias examples.

### Tests
- `tests/test_scrum_subagents.py`: expanded to 12 tests, including coverage for `commands.json` and updated bundle file counts.
- Full suite status: `51` unit tests and `34` smoke checks passing

## [11.1.0] - 2026-03-18

### Added
- `codex-scrum-subagents/scripts/validate_scrum_agent_kit.py`: validates the bundled Scrum kit and can compare an installed `.agent` tree against the source bundle.
- `codex-scrum-subagents/scripts/_scrum_agent_kit.py`: shared helper module for diffing, validation, backups, and bundle metadata.
- `codex-workflow-autopilot/references/workflow-scrum.md`: Scrum ceremony overlay for backlog refinement, sprint planning, daily scrum, review, retrospective, and release readiness.

### Improved
- `codex-scrum-subagents/scripts/install_scrum_subagents.py`: added `--diff`, `--update`, and `--backup-dir`; update mode now copies only missing or changed files and writes fresh bundle provenance.
- `codex-scrum-subagents/SKILL.md`: expanded quick-start instructions with validate, diff, and update commands.
- `codex-workflow-autopilot/SKILL.md`: added Scrum-aware activation, ceremony routing, and optional coordination overlay fields.
- `README.md`, `skills/README.md`, and `docs/huong-dan-vi.md`: refreshed counts and documented the validator plus update workflow.

### Tests
- `tests/test_scrum_subagents.py`: expanded from 5 to 11 tests covering validation, diffing, backups, and drift detection.
- `tests/smoke_test.py`: added `codex-scrum-subagents/scripts/validate_scrum_agent_kit.py`
- Full suite status: `50` unit tests and `34` smoke checks passing

## [11.0.0] - 2026-03-18

### Added
- **NEW SKILL**: `codex-scrum-subagents`
  - `SKILL.md`: Scrum-oriented routing rules for Product Owner, Scrum Master, architect, developer, QA, security, DevOps, and UX collaboration
  - `references/scrum-role-routing.md`: role selection matrix and escalation guidance
  - `references/scrum-ceremonies.md`: ceremony playbooks for refinement, planning, daily scrum, review, retrospective, and release readiness
  - `references/delivery-contracts.md`: Definition of Ready/Done and role-to-role handoff contracts
  - `references/subagent-boundaries.md`: ownership boundaries and escalation rules
  - `scripts/install_scrum_subagents.py`: installer for a project-local `.agent` Scrum kit
  - `assets/scrum-agent-kit/`: 10 role briefs, 7 workflows, 2 manifest files, and onboarding docs

### Improved
- `README.md`, `skills/README.md`, and `docs/huong-dan-vi.md`: updated public and technical docs for the new Scrum delivery kit, refreshed counts, and installation guidance.

### Tests
- `tests/test_scrum_subagents.py`: added 5 installer bundle tests
- `tests/smoke_test.py`: added `codex-scrum-subagents/scripts/install_scrum_subagents.py`
- Full suite status: `44` unit tests and `33` smoke checks passing

## [10.5.2] - 2026-02-27

### Fixed
- `tests/test_parsing.py`: updated `test_explain_parse_js_file_unclosed_block_warns` to match resilient parser behavior (partial function extraction + warning).
- `codex-domain-specialist/SKILL.md`: added explicit Debugging primary domain detection and routing to `debugging-rules.md`.
- `codex-domain-specialist/SKILL.md`: completed `Reference Files` section by adding all previously missing core references for maintainability and discoverability.

## [10.5.1] - 2026-02-27

### Fixed
- `codex-domain-specialist`: standardized `starters/.env.example` starter template to ensure starter inventory completeness.
- `codex-security-specialist/SKILL.md`: added 8 missing Routing Decision Table rows:
  - Vulnerability Scanning
  - SIEM & Log Analysis
  - Threat Modeling
  - PKI & Certificates
  - DDoS Mitigation
  - IDS/IPS
  - Supply Chain Security
  - API Security
- `codex-security-specialist/SKILL.md`: expanded Reference Files section with all previously missing security references (network, offensive/defensive, DevSecOps, compliance, cryptography, PKI).

## [10.5.0] - 2026-02-27

### Added (codex-security-specialist - COMPLETE)
- 4 advanced references:
  - `zero-trust-architecture.md`: pillars (identity/device/network), risk scoring, microsegmentation, and rollout roadmap
  - `ddos-mitigation.md`: L3-L7 attack model, layered defenses, edge/network/app/data controls, response playbook
  - `ids-ips-patterns.md`: detection patterns for login anomalies, API abuse, file integrity, and severity-based triage
  - `security-audit-framework.md`: audit domains, evidence model, access review workflow, and report template
- 1 starter:
  - `rate-limiter-advanced.js`: Redis-backed sliding window and token-bucket limiters with endpoint presets

### Security Specialist Complete
- 30 references + 10 starters = 40 security knowledge files.

## [10.4.0] - 2026-02-27

### Added (codex-security-specialist)
- 5 compliance + cryptography references:
  - `iso27001-checklist.md`: Annex A controls mapped to developer actions and evidence requirements
  - `gdpr-compliance.md`: principles, lawful bases, user rights implementation patterns (export/delete/consent), breach timeline
  - `soc2-checklist.md`: Trust Services Criteria coverage, control checklist, evidence and audit-ready quick wins
  - `cryptography-guide.md`: algorithm decision table, AES-256-GCM and signature examples, key management rules
  - `pki-certificates.md`: X.509 fields, certificate lifecycle, mTLS example, internal CA workflow
- 1 starter:
  - `csp-policy.js`: environment-aware CSP builder with report-only mode and trusted source toggles

## [10.3.0] - 2026-02-27

### Added (codex-security-specialist)
- 4 DevSecOps references:
  - `devsecops-pipeline.md`: shift-left pipeline architecture, pre-commit hooks, CI/CD security stages, gate policy, metrics
  - `sast-dast-sca.md`: Semgrep/SonarQube/CodeQL setup, ZAP DAST in CI, Snyk/npm audit SCA, custom rules, suppression policy
  - `iac-security.md`: tfsec/Checkov/Terrascan, common misconfigs, secure Terraform patterns (S3, RDS), IaC CI pipeline
  - `supply-chain-security.md`: attack vectors (typosquatting, dependency confusion), 6 defense layers, SBOM, Sigstore, emergency response
- 2 starters:
  - `security-ci-pipeline.yml`: full DevSecOps GitHub Actions (secrets + SAST + SCA + container + IaC + license + DAST)
  - `security-headers.js`: comprehensive Express security headers with helmet + custom policies

## [10.2.0] - 2026-02-27

### Added (codex-security-specialist)
- 6 offensive + defensive references:
  - `owasp-top10-deep.md`: A01-A10 with vulnerable/fixed code examples for each
  - `pentest-methodology.md`: 6-phase methodology, recon tools, exploitation tests, report template
  - `vulnerability-scanning.md`: scanner types, ZAP/Nmap/Snyk commands, scanning schedule, severity table
  - `incident-response.md`: NIST 6-phase IR, severity levels, containment scripts, post-mortem template
  - `siem-log-analysis.md`: ELK stack setup, security events to monitor, alert rules, retention policy
  - `threat-modeling.md`: STRIDE framework, DREAD scoring, trust boundaries, threat model document template
- 1 starter:
  - `pentest-checklist.md`: 40+ pre-deployment security test items (auth, input, API, infra, data, monitoring)

## [10.1.0] - 2026-02-27

### Added (codex-security-specialist)
- 5 infrastructure hardening references:
  - `linux-hardening.md`: user control, sudo, sysctl kernel params, auditd, file permissions, auto-updates
  - `secret-management.md`: Vault setup, AWS Secrets Manager, Docker secrets, git-secrets, rotation
  - `container-security.md`: secure Dockerfile, Trivy/Scout scanning, runtime hardening, K8s Pod Security
  - `cloud-security-aws.md`: IAM policies, VPC architecture, S3 encryption, CloudTrail/GuardDuty
  - `api-security-advanced.md`: 7-layer API security, request signing, rate limit tiers, output filtering
- 2 starters:
  - `docker-security-scan.yml`: CI pipeline with Trivy + Hadolint + Dockle
  - `vault-setup.hcl`: HashiCorp Vault configuration with policies and AppRole

## [10.0.0] - 2026-02-27

### Added
- **NEW SKILL**: `codex-security-specialist` - dedicated security and network knowledge
  - `SKILL.md`: routing table for 24 security domains with context boundaries
  - 6 references (network fundamentals):
    - `network-fundamentals.md`: OSI security, TCP/IP, ports, subnetting, attack vectors, tools
    - `firewall-rules.md`: iptables, UFW, AWS Security Groups, Docker port binding
    - `vpn-tunneling.md`: WireGuard setup (server+client), SSH tunnels, key management
    - `dns-security.md`: DNSSEC, DoH/DoT, SPF/DKIM/DMARC, CAA records
    - `ssl-tls-certificates.md`: TLS versions, Let's Encrypt, OCSP stapling, SSL testing
    - `network-segmentation.md`: zone architecture, AWS VPC, Docker networks, K8s NetworkPolicy
  - 3 starters:
    - `iptables-rules.sh`: complete firewall script with anti-spoofing and rate limiting
    - `nginx-ssl-hardened.conf`: grade A+ SSL config with security headers and CSP
    - `ssh-hardening.sh`: automated SSH hardening with key-only auth and strong crypto

## [9.7.0] - 2026-02-27

### Fixed
- Expanded Routing Decision Table from 10 to 12 primary domains (added Auth/Identity and Data/Analytics)
- Added newer references to `Load On Signal` columns (for example: `form-patterns.md`, `css-architecture.md`, `state-management.md`)
- Resolved signal conflicts by making each keyword route to one primary specialized target
- Reorganized Specialized Signal Routing by category (Frontend, Backend, Database, Auth/Security, Architecture/DevOps, Cross-Cutting)

### Added
- Starter Template Auto-Routing: 19 starters now have explicit trigger patterns
- Common Combo Detection: 10 multi-domain task combos with pre-defined load sets
- Signal Conflict Resolution rules (specificity, combo priority, deep-vs-general, starter+reference handling)
- Expanded Feedback Category Mapping from 14 to 30 categories

### Changed
- Max specialized signal references per task set to 2 to prevent overload

## [9.6.0] - 2026-02-27

### Added
- 8 niche references completing domain specialist knowledge:
  - `data-visualization.md`: Recharts setup, chart type decision, dashboard layout, and chart color palettes
  - `form-patterns.md`: React Hook Form + Zod, dynamic field arrays, multi-step forms, and UX rules
  - `date-timezone.md`: Day.js patterns, UTC storage, timezone-aware queries, and birthday alert queries
  - `data-export.md`: CSV streaming, Excel export (ExcelJS), client-side download, and escaping rules
  - `oauth-social-login.md`: Google/GitHub Passport.js flows, account linking, Authorization Code flow
  - `monorepo-patterns.md`: Turborepo setup, shared package patterns, workspace conventions
  - `message-queue-comparison.md`: Redis Streams vs RabbitMQ vs Kafka decision table and usage patterns
  - `database-aggregation.md`: MongoDB pipeline stages, dashboard summary, trend aggregation, pagination with totals
- Skill pack completed: 59 references + 19 starters (100% full-stack coverage)

## [9.5.0] - 2026-02-27

### Added
- 5 advanced enterprise references:
  - `observability.md`: Prometheus metrics, custom counters/histograms, SLO/SLI, alerting rules, distributed tracing
  - `api-gateway.md`: gateway architecture, proxy routing, gateway vs service mesh comparison
  - `event-sourcing.md`: event store, CQRS, projections, optimistic concurrency, snapshots
  - `container-orchestration.md`: multi-stage Dockerfile, K8s Deployment/Service/HPA, scaling decisions
  - `payment-integration.md`: Stripe integration, webhook handler, refund pattern, PCI compliance
- Updated `SKILL.md` routing for all advanced signal patterns
- Skill pack reached 51 references + 19 starters (~99% full-stack coverage)

## [9.4.0] - 2026-02-27

### Added
- 6 starters: `jest-setup.js`, `react-test.jsx` (RTL+MSW), `websocket-server.js` (Socket.IO), `health-check.js` (K8s), `graceful-shutdown.js`, `swagger-setup.js`
- 10 references: `design-patterns.md` (JS), `web-security-deep.md` (CORS/CSP/XSS/injection), `i18n-patterns.md`, `testing-strategy.md` (pyramid+mocking), `api-documentation.md`, `git-workflow.md`, `pwa-patterns.md`, `performance-profiling.md` (Core Web Vitals), `deployment-strategy.md` (blue-green/canary), `code-review.md`
- Updated `SKILL.md` routing for all new signal patterns

## [9.3.0] - 2026-02-26

### Added
- `starters/nginx.conf`: reverse proxy, SSL, rate limiting, compression, security headers, WebSocket
- `starters/.env.example`: complete environment variable template with security rules
- 8 deep-dive references:
  - `background-jobs.md`: Bull queue, scheduled jobs, priority, error handling
  - `search-filter.md`: URL-driven filters, debounce, faceted search, regex safety
  - `file-upload.md`: Multer setup, presigned URLs, image processing, security checklist
  - `email-notification.md`: Nodemailer, template pattern, in-app notifications
  - `data-migration.md`: seed scripts, ETL backfill, chunked operations, safety rules
  - `multi-tenancy.md`: shared DB + tenant column, isolation rules, query safety
  - `feature-flags.md`: simple implementation, rollout strategy, cleanup rules
  - `graphql-patterns.md`: schema design, DataLoader, security, when to use vs REST
- Updated `SKILL.md` routing for all new signal patterns

## [9.2.0] - 2026-02-26

### Added
- `starters/sequelize-migration.js`: safe migration patterns (additive, phased, chunked backfill, create table)
- `starters/env-config.js`: fail-fast env validation with typed helpers (required, optional, int, bool)
- `references/caching-patterns.md`: cache-aside, TTL strategy, invalidation, in-memory vs Redis
- `references/pagination-patterns.md`: offset vs cursor, SQL keyset, frontend URL-driven
- `references/validation-patterns.md`: Joi/Zod setup, middleware factory, sanitization rules
- `references/logging-patterns.md`: structured logging, correlation IDs, Winston setup, log levels
- Updated `codex-domain-specialist/SKILL.md` routing for caching, pagination, validation, logging signals

## [9.1.0] - 2026-02-26

### Added
- 8 starter templates: `design-system.css`, `dashboard-layout.css`, `express-api.js`, `mongoose-model.js`, `auth-flow.js`, `api-client.js`, `react-crud-page.jsx`, `docker-compose.yml`, `ci-pipeline.yml`
- 6 deep-dive references: `auth-patterns.md`, `state-management.md`, `css-architecture.md`, `realtime-patterns.md`, `error-handling-patterns.md`, `file-structure.md`
- Updated `codex-domain-specialist/SKILL.md` with starter template routing

## [9.0.0] - 2026-02-26

### Added
- `architecture-rules.md`: monolith/microservice, clean architecture, SOLID, DDD, event-driven
- `integration-rules.md`: API clients, circuit breaker, webhooks, multi-DB, caching
- `frontend-rules.md`: visual design system (tokens, layout, animation, component specs)
- `backend-rules.md`: clean architecture layers, middleware pipeline, error handling patterns
- `database-rules.md`: MongoDB vs SQL schema design, embedding vs referencing, migration safety
- Updated domain specialist routing for Architecture and Integration domains

## [8.5.0] - 2026-02-26

### Fixed
- JS function parser: improved brace matching with scan cap and fallback heuristics for JSX/class components
- Fixes parse failures for `ErrorBoundary.jsx`, `Skeletons.jsx`, `dashboard.controller.js`

### Refactored
- Extracted shared JS parser module (`_js_parser.py`) from 4 duplicated copies
- DRY refactor: `quality_trend.py`, `suggest_improvements.py`, `tech_debt_scan.py`, `explain_code.py` now share one parser

## [8.4.0] - 2026-02-26

### Fixed
- `predict_impact.py`: blast_radius_size now counts only target-reachable files instead of all project files - fixes false `escalate_to_epic` for every file

## [8.3.0] - 2026-02-25

### Security
- `security_scan.py`: added detection for private keys, JWT tokens, database URLs with credentials, Slack/Discord webhooks
- `security_scan.py`: improved placeholder detection (template patterns, env vars)
- `pre_commit_check.py`: CRITICAL FIX - `secret_scan()` now blocks commit when secrets are detected (was informational-only)
- `auto_commit.py`: integrated full `security_scan.py` as an additional gate before commit

## [8.2.0] - 2026-02-25

### Fixed
- `auto_commit.py`: GPG executable detection now checks known Windows install paths as fallback when not in PATH

## [8.1.0] - 2026-02-25

### Improved
- `auto_commit.py --setup-gpg`: fully automated GPG setup (install -> generate key -> configure git -> copy to clipboard -> open GitHub)
- User only needs 1 manual step: paste public key into GitHub Settings

## [8.0.0] - 2026-02-25

### Added
- New skill: `codex-git-autopilot` with `auto_commit.py`
- Task-scoped file staging (commit only related files)
- Pre-commit CI gate integration (lint, secret scan, tests)
- Conventional Commits auto-generation (type + scope detection)
- GPG signing for GitHub Verified badge (auto-detect, fallback)
- Auto-push after successful commit
- Interactive GPG setup wizard (`--setup-gpg`)
- Dry-run mode for commit preview
- Safety: never force push, unstage on failure, timeout on all ops

## [7.7.0] - 2026-02-25

### Fixed
- `pre_commit_check.py`: added `timeout=60` to `run_git()` helper (missed in v5.4.4)
- `playwright_runner.py`: added `timeout=300` to subprocess calls
- `render_docx.py`: added `timeout=120` to document rendering subprocess
- `install-skill-from-github.py`: added `timeout=120` to git clone operations

## [7.6.0] - 2026-02-24

### Fixed
- Added `timeout` to all `subprocess.run` calls across 8 scripts to prevent indefinite hangs
- Scripts: `suggest_improvements.py`, `tech_debt_scan.py`, `smart_test_selector.py`, `with_server.py`, `map_changes_to_docs.py`, `generate_session_summary.py`, `generate_handoff.py`, `generate_changelog.py`
- Same class of critical bug as v5.4.4 fix, now applied consistently across the skill pack

## [7.5.0] - 2026-02-24

### Fixed
- `generate_genome.py`: module map slot allocation filters non-code directories (`docs/`, `Memory/` with markdown-only files), prioritizing code-heavy directories for higher information density

## [7.4.0] - 2026-02-24

### Fixed
- `generate_genome.py`: module map route surface now shows full mounted API paths (for example: `/api/alerts`)
- `generate_genome.py`: CSS/style files are filtered from module map key files list to reduce noise

## [7.3.0] - 2026-02-24

### Fixed
- `generate_genome.py`: model display cap raised 10 -> 20, barrel/index files filtered
- `build_knowledge_graph.py`: barrel files (`index.js`, `init.js`) excluded from `data_models`
- `generate_genome.py`: model section shows count header (for example: `Key Data Models (20)`)
- `generate_genome.py`: API routes now show full mounted paths (for example: `/api/employee`) by extracting `app.use()` prefixes

## [7.2.0] - 2026-02-24

### Fixed
- `analyze_patterns.py`: removed generic Django keywords (`path(`, `include(`) that caused false positives in Node.js projects
- `analyze_patterns.py`: filters frontend-only state patterns (`useState`, `Redux`, etc.) from backend project analysis
- `generate_genome.py`: distinguishes direct circular dependencies (<=3 modules) from indirect chains (>3 modules)

## [7.1.0] - 2026-02-24

### Fixed
- `analyze_patterns.py`: multi-stack detection (ORM, auth, routing now return all matches, not just winner)
- `analyze_patterns.py`: improved AUTH_PATTERNS with jwt/bcrypt/bearer/authorization keywords
- `analyze_patterns.py`: improved ROUTING_PATTERNS with Express-specific method keywords + FastAPI/Django
- `build_knowledge_graph.py`: `module_name()` groups top-level files into "root" instead of individual modules
- `build_knowledge_graph.py`: `extract_keys_from_block` expanded meta-key filter for Mongoose + Sequelize
- `generate_genome.py`: renders multi-value stacks and groups API routes by file

## [7.0.0] - 2026-02-24

### Added
- Project Genome: multi-layer context memory architecture to reduce AI hallucination
- `generate_genome.py`: generates `.codex/context/genome.md` + module maps from existing analysis scripts
- `codex-context-engine/SKILL.md`: context loading and generation rules
- Context Loading Rule in master instructions: auto-load `genome.md` if it exists
- Master script inventory: 28 -> 29 scripts

## [6.0.0] - 2026-02-20

### Added
- HARD-GATE: Design-before-code blocking for complex tasks
- Verification-Before-Completion: Evidence-based completion claims
- Systematic Debugging Protocol: 4-phase root cause analysis
- Anti-Rationalization Defense: Table of common process-skip excuses
- Two-Stage Code Review: Spec compliance -> Code quality
- Plan Granularity Standard: 2-5 minute bite-sized tasks

## [5.4.4] - 2026-02-20

### Fixed
- `make_command` space-in-path: pass list to `shell=True` instead of joined string
- `pre_commit_check.py`: added `timeout=120` to prevent infinite subprocess hangs

## [5.4.2] - 2026-02-20

### Fixed
- Master SKILL.md inventory: 25 -> 28 scripts (added doctor, compact_context, render_docx)
- README.md: project-memory scripts count 9 -> 10
- Added `$codex-doctor` and `$compact-context` quick commands

## [5.4.1] - 2026-02-20

### Fixed
- `SKIP_DIRS` in 12 scripts: added `.venv`, `venv`, `.codex`, `.idea`, `.vscode`, `.yarn`
- `render_docx.py`: bare `except Exception` -> `except (OSError, ValueError, TypeError)`

## [5.4.0] - 2026-02-20

### Added
- Circuit Breaker: `run_gate.py` tracks consecutive failures, halts at 3
- Cognitive Load Guard: `predict_impact.py` calculates true blast radius, escalates to Epic Mode at >20 files
- 5 new unit tests for circuit breaker and blast radius

### Fixed
- `build_gate_report` kept pure; state tracking moved to `main()`
- Blast radius calculation: union of all affected files (not just forward map keys)
- Bare `except:` -> specific exception types in `load_gate_state`

## [5.3.1] - 2026-02-20

### Fixed
- Exit code: `run_gate.py main()` returns 1 on failure (was always 0)
- `--human` flag for human-readable gate summary

## [5.3.0] - 2026-02-19

### Added
- `compact_context.py`: archive old session/feedback files
- `generate_growth_report.py`: aggregate feedback/usage/session metrics

## [5.2.0] - 2026-02-19

### Fixed
- Missing `encoding="utf-8"` in file operations
- `.resolve()` without `.expanduser()` on tilde paths

## [5.0.0] - 2026-02-19

### Added
- Full 28-script skill pack across 9 skills
- Master instructions with request classifier, dependency awareness, quality gate
- Cross-reference table mapping task types to workflows and scripts
- CI template for GitHub Actions
- Smoke test (30 checks) and unit test suite (39 tests)
