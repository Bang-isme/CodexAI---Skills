# Changelog

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
