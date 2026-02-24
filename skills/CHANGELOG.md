# Changelog

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
