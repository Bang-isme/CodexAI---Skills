# Knowledge Release Hardening Design

## Goal

Ship CodexAI Skills 16.0.1 with deterministic project-memory discovery, actual incremental index reuse, artifact redaction, accurate query and graph outputs, consistent workflow routing, and release evidence that works on supported Windows and Linux Python environments.

## Scope

This release completes the already-started hardening work only. It does not add a new runtime service, change the public artifact schema version, introduce network access in validators, or rewrite the router and knowledge builders.

## Architecture

The shared traversal module owns deterministic discovery, ignore handling, sorting, file caps, and byte caps. The codebase indexer consumes that listing and records full chunks for search, while the knowledge graph receives the already-built index from the knowledge-index orchestrator. This yields one source of file-set truth and prevents a second index build during a knowledge run.

Redaction remains a final artifact-boundary pass. It redacts secret-like values throughout payload values, preserves map keys so paths and module identifiers do not collide, and preserves 40- and 64-character Git/content hashes. A bare secret-like identifier such as `token` is still unsafe when used as a serialized value, including route handlers, and must be redacted.

The prompt router remains the authority for explicit user intent. Runtime-hook repository analysis may supply an agent only when the prompt route has no actionable intent. Workflow names and aliases are defined consistently in the system manifest, workflow contract, workflow documents, and router output.

## Components

### Project-memory

- `project_traversal.py` exposes a file-listing phase that performs canonical discovery without reading content, then uses the result for the content-reading traversal phase.
- `codebase_indexer.py` uses the shared listing, persists source chunks sufficient for query hits beyond a preview window, and retains unchanged file/chunk payloads when the content hash is unchanged.
- `build_knowledge_index.py` builds the codebase index once and passes it to `build_knowledge_graph.py`.
- `build_knowledge_graph.py` compares only language-relevant files under the same test inclusion policy when reporting graph/index coherence and declares shared redaction metadata.
- `redaction.py` redacts secret-like artifact values while retaining hashes and dictionary keys needed for stable references.

### Workflow and router contracts

- `prompt_router.py` adds test, Scrum, and project-pulse intents and exposes a merge function with explicit prompt-router precedence.
- `workflow-routing-contract.json`, `.system/manifest.json`, and `.workflows/{build,docs,fix}.md` express the same alias semantics.
- Router, runtime hook, loop/autopilot integration, and workflow aliases have behavior-focused tests that run the real functions with controlled repository fixtures.

### Release safety

- `trust_harness.py` treats any adapter setup error or non-zero exit as a failed harness check and records the host interpreter in generated prompt hooks.
- `validate_tool_contracts.py` inspects registered scripts and validates their documented CLI options against parser declarations, then runs safe smoke calls.
- `local_release_gate.py` is read-only by default, creates Antigravity output in an isolated temporary directory, validates that package, and performs the ZIP dry-run unless an explicit writable release build is requested.
- `build_release_zip.py` permits release documentation while excluding repository metadata and runtime artifacts.
- CI keeps the full Python 3.11–3.13 matrix and adds Windows/Linux memory smoke coverage plus Antigravity package validation.

## Data Flow

1. The orchestrator creates one traversal configuration and one deterministic file listing.
2. The indexer hashes listed source files; unchanged hashes retain prior file metadata and chunk IDs, while changed hashes create replacement chunks.
3. The graph consumes the same traversal configuration and the in-memory index result. It emits coherence diagnostics without comparing non-code files.
4. Index, graph, dashboard, and Markdown outputs pass through the same redaction boundary before disk writes.
5. A user prompt is routed first; repository analysis can fill only an absent route. The selected workflow must be listed in all workflow contracts.
6. Local and CI gates validate contracts, package health, both plugin formats, an Antigravity build/validation pair, and the release archive plan without writing release artifacts unless explicitly requested.

## Error Handling and Safety

- Traversal records deterministic structured warnings for ignored, binary, unreadable, oversize, and symlink-skipped files rather than aborting an entire artifact build.
- An unavailable opportunistic index adds a warning only when callers did not supply a pre-built index.
- Secret-like values are replaced before persisted artifacts; disabling redaction is explicit and adds a warning.
- Contract parse, schema, CLI declaration, smoke, adapter, package, and archive failures are release-blocking.
- Temporary Antigravity build output is cleaned after local-gate execution; no release ZIP is written in default read-only mode.

## Acceptance Criteria

1. Index discovery and traversal return the same sorted capped source file set under the same configuration and ignore rules.
2. A second index build with one changed file reuses all unchanged file payloads and chunk IDs; query hits include terms beyond a preview field.
3. A normal knowledge build creates the codebase index once, reports no coherence drift for a common code fixture, and applies redaction consistently to the graph and all persisted artifacts.
4. Git SHAs and SHA-256 content hashes remain searchable; emails, credentials, tokens, and secret-like serialized handler values are redacted, while dictionary keys are unchanged.
5. Test, Scrum, and pulse prompts select their intended agents/skills; prompt intent wins over runtime-hook inference; aliases are valid in every workflow contract.
6. Adapter failure fails the trust harness, tool schemas match script parsers, and new tools participate in smoke coverage.
7. The read-only release gate validates Codex, Claude, and Antigravity packages and plans the ZIP without writing a release file. Writable mode emits a valid ZIP containing documentation and no forbidden runtime/repository entries.
8. CI runs supported Python 3.11–3.13 coverage, including the required Windows and Linux memory smoke path.
9. Targeted, full, release-gate, scale, archive, Antigravity, and platform checks provide fresh passing evidence before commit and push.

## Validation Matrix

| Concern | Primary evidence |
| --- | --- |
| Traversal/index/query/graph/redaction | `test_memory_accuracy.py`, `test_full_cycle_hardening.py`, `test_memory_at_scale.py` |
| Router/workflow/autopilot | `test_routing_workflow_sync.py`, router corpus validation, relevant loop/autopilot tests |
| Harness/contracts/smoke | `test_generic_harness.py`, `validate_tool_contracts.py --smoke`, `smoke_test.py` |
| Release archive/plugins | `test_release_hygiene.py`, `local_release_gate.py --no-write`, Antigravity validator |
| Cross-version and operating system | CI matrix configuration review plus local Python environments available in this workspace |
| Scale | `run_scale_gate.py` medium/polyglot suite and generated summary |

## Release Plan

1. Set all canonical version metadata to 16.0.1 without leaving stale 16.0.0 release values.
2. Rebase onto the current remote `main` only after every local gate is green; resolve only conflicts affecting these release changes.
3. Re-run the mandatory gates after the rebase, stage the intended files, commit with a release-hardening message, and push the rebased commit to `origin/main` without force push.

## Out of Scope

- New external dependencies, cloud services, credentials, deployment promotion, or automatic tagging.
- Changing unrelated skills, existing user changes, or generated runtime state outside the requested release artifacts.
