# Changelog

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
