#!/usr/bin/env python3
"""Initialize a project-local spec document."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = "1.0"


def validate_project_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Project root does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {resolved}")
    return resolved


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (cleaned or "spec")[:48].strip("-") or "spec"


def dated_slug(title: str) -> str:
    return f"{datetime.now(timezone.utc).date().isoformat()}-{slugify(title)}"


def parse_csv(value: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in value.split(","):
        normalized = item.strip()
        if normalized and normalized.lower() not in seen:
            result.append(normalized)
            seen.add(normalized.lower())
    return result


def render_spec(title: str, prompt: str, domains: list[str]) -> str:
    generated = datetime.now(timezone.utc).isoformat()
    domains_text = ", ".join(domains) if domains else "Not classified yet"
    prompt_text = prompt.strip() or "Not provided"
    return f"""# Spec: {title}

Schema-Version: {SCHEMA_VERSION}
Spec-ID: {dated_slug(title)}
Generated: {generated}
Status: draft
Domains: {domains_text}

## Problem
{prompt_text}

## Context Summary
- Business or user context: Capture what the user is trying to accomplish and why the change matters.
- Current repo context: Record the files, docs, scripts, and existing patterns inspected before implementation.
- Decision context: Note the chosen approach and the alternatives rejected, including the evidence used.

## Evidence and Source Log
| Source | Tool or Method | Key Finding | Confidence |
| --- | --- | --- | --- |
| Original request | Conversation | {prompt_text} | High |
| Repository scan | `rg --files` and targeted reads | Record project-specific files or docs before coding | To verify |
| Helper scripts | Run `--help` before use | Record CLI contract, inputs, outputs, and limits | To verify |

## Assumptions
- The implementation should preserve existing behavior unless an acceptance criterion explicitly changes it.
- The smallest project-specific change is preferred over new architecture, dependencies, services, or long-lived abstractions.
- Tool evidence should be recorded when requirements depend on repository structure, generated artifacts, external commands, or security posture.

## Constraints
- Keep changes within the domains listed above unless evidence shows a cross-domain dependency.
- Do not bulk-load unrelated references or starter templates.
- Do not claim completion without fresh validation evidence from tests, builds, lint, or a documented manual check.

## User Workflow
1. Trigger or request: Describe the user action, command, workflow alias, or development scenario.
2. Expected system behavior: Describe what the agent, tool, plugin, or application should do.
3. Evidence captured: Describe what files, scripts, outputs, screenshots, logs, or security checks support the result.
4. Handoff: Describe what another agent or developer can verify without re-discovering context.

## Goals
- Define the user-visible outcome before implementation.
- Keep frontend, backend, data, QA, and deployment impact explicit.
- Make domain routing, tool usage, security reasoning, and validation evidence visible.
- Produce enough context that another agent can implement or review the work without guessing.

## Non-Goals
- Do not add unrelated features.
- Do not change unrelated architecture without a separate ADR.
- Do not require a full compliance audit when the task only needs proportional security reasoning.
- Do not create separate tickets, agents, or workflows unless the spec spans multiple acceptance criteria, files, domains, or delivery roles.

## Requirements
- R1: The implementation must satisfy the stated user workflow.
- R2: The implementation must preserve existing behavior unless explicitly changed.
- R3: The implementation must include verification evidence before completion.
- R4: Domain routing must explain primary domain, secondary signals, loaded references, skipped references, and tool usage when applicable.
- R5: Specs must include implementation tickets when the work spans multiple files, acceptance criteria, domains, or delivery roles.
- R6: Specs must document security assets, trust boundaries, attacker-controlled inputs, abuse cases, and validation when the work changes a security-relevant surface.

## Acceptance Criteria
- [ ] AC-001: Primary user flow works end to end.
  - Files: To be filled from implementation scope.
  - Validation: Record the exact command or manual check.
- [ ] AC-002: Error, empty, loading, and success states are handled where applicable.
  - Files: To be filled from implementation scope.
  - Validation: Record focused tests or walkthrough evidence.
- [ ] AC-003: Relevant tests or manual verification commands are recorded before handoff.
  - Files: To be filled from implementation scope.
  - Validation: `python <SKILLS_ROOT>/codex-execution-quality-gate/scripts/auto_gate.py --project-root <PROJECT_ROOT> --mode full`
- [ ] SEC-001: Security-relevant surfaces are identified and either tested or explicitly marked as not applicable with rationale.
  - Files: Spec, routes, auth, secrets, CI, deployment, file handling, or data-access files that apply to the work.
  - Validation: Record focused security checks, threat-model notes, or a justified no-security-surface statement.

## Implementation Tickets
- [ ] TICKET-001: Establish requirements and evidence baseline.
  - Domain: planning, QA
  - Linked AC: AC-001, AC-003
  - Intent: Inspect the repository, identify relevant files, record tool evidence, and confirm the smallest viable implementation path.
  - Likely Files: `.codex/specs/<slug>/SPEC.md`, project docs, tests, and files discovered by repo search.
  - Dependencies: None.
  - Security Notes: Capture assets, trust boundaries, and attacker-controlled inputs before implementation when applicable.
  - Validation: Run the focused tests or manual checks named in the Validation Matrix.
- [ ] TICKET-002: Implement domain-specific behavior.
  - Domain: {domains_text}
  - Linked AC: AC-001, AC-002
  - Intent: Make the smallest code or document change that satisfies the accepted workflow and preserves existing behavior.
  - Likely Files: To be narrowed after evidence collection.
  - Dependencies: TICKET-001.
  - Security Notes: Apply proportional controls only when the changed surface affects auth, secrets, user input, deployment, CI, or sensitive data.
  - Validation: Run focused tests for changed modules and record the exact command.
- [ ] TICKET-003: Verify, trace, and hand off.
  - Domain: QA, documentation
  - Linked AC: AC-003, SEC-001
  - Intent: Update traceability, run final verification, and record residual risks or follow-up work.
  - Likely Files: `.codex/specs/<slug>/SPEC.md`, test files, role docs, handoff notes if used.
  - Dependencies: TICKET-002.
  - Security Notes: Include security validation evidence or a clear explanation of why no security surface changed.
  - Validation: Run `python <SKILLS_ROOT>/codex-spec-driven-development/scripts/check_spec.py --project-root <PROJECT_ROOT> --changed-files <CSV>`.

## Frontend Impact
- Screens/components affected: To be filled from repo context.
- UX states required: loading, error, empty, success, accessibility.

## Backend Impact
- API/services affected: To be filled from repo context.
- Contracts required: request, response, validation, error behavior.

## Data Impact
- Models/migrations affected: To be filled from repo context.
- Data integrity concerns: indexes, relations, rollback, seed data.

## QA Impact
- Unit tests:
- Integration tests:
- E2E/manual checks:

## Security Model
- Assets and sensitive data: Identify secrets, tokens, credentials, PII, tenant data, financial data, protected files, CI credentials, or deployment privileges touched by this work.
- Trust boundaries: Identify browser/server, public/private API, user/admin, tenant/tenant, CI/runtime, local/remote, or third-party boundaries.
- Attacker-controlled inputs: List request fields, URL/query params, uploaded files, webhook payloads, package inputs, environment variables, generated files, or model/tool outputs that can cross a boundary.
- Abuse cases: Describe realistic misuse, privilege escalation, data exposure, injection, SSRF, path traversal, XSS, CSRF, supply-chain, or confused-deputy risks when relevant.
- Controls: Name validation, authorization, output encoding, rate limits, secret handling, dependency checks, logging, rollback, and fail-secure behavior that apply.
- Security validation: Record tests, scans, manual checks, or threat-model notes. If no security surface changed, state the evidence for that conclusion.

## Tool Research Plan
- Repository discovery: Use `rg --files` and targeted reads to find existing patterns before editing.
- Script usage: Run helper scripts with `--help` before relying on them; record command shape and output expectations.
- External or generated evidence: Record tool output, docs consulted, screenshots, logs, or security scan summaries that influence requirements.
- Tool evidence standard: Keep enough command names, file paths, and findings that another agent can verify the same conclusion.

## Validation Matrix
| Check | Command or Method | Expected Evidence | Linked AC |
| --- | --- | --- | --- |
| Focused tests | Project-specific test command | Passing output with zero unexpected warnings | AC-001, AC-002 |
| Spec traceability | `python <SKILLS_ROOT>/codex-spec-driven-development/scripts/check_spec.py --project-root <PROJECT_ROOT> --changed-files <CSV>` | Changed files map to AC IDs and ticket IDs | AC-003 |
| Security review | Threat-model note, focused test, or security scan where applicable | Security surface covered or explicitly not applicable | SEC-001 |
| Full gate | `python <SKILLS_ROOT>/codex-execution-quality-gate/scripts/auto_gate.py --project-root <PROJECT_ROOT> --mode full` | Gate pass or documented advisory warnings | AC-003 |

## Risk Matrix
| Risk | Impact | Likelihood | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| Requirements remain vague | Medium | Medium | Resolve open questions and link each ticket to AC IDs | Product/Agent |
| Tool output is trusted without inspection | High | Medium | Record command, key output, and confidence in Evidence and Source Log | Implementer |
| Security surface is missed | High | Low to Medium | Complete Security Model and SEC-001 before handoff | Security/Implementer |

## Open Questions
- Which acceptance criteria are mandatory for the first implementation slice?
- Which files or runtime surfaces are authoritative for existing behavior?
- Which validation commands are available locally and which require manual evidence?

## Validation Plan
- Run focused tests for changed modules.
- Run `python <SKILLS_ROOT>/codex-execution-quality-gate/scripts/auto_gate.py --project-root <PROJECT_ROOT> --mode full`.
- Run spec traceability check when `.codex/specs/` exists.
- Record any security validation or justified non-applicability in the Security Model.

## Traceability
| Changed File | AC ID | Validation Command | Notes |
| --- | --- | --- | --- |
| To be filled during implementation | AC-001 | To be filled | Keep this table updated before handoff |
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create .codex/specs/<slug>/SPEC.md.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--title", required=True, help="Spec title")
    parser.add_argument("--prompt", default="", help="Original user prompt or problem statement")
    parser.add_argument("--domains", default="", help="Comma-separated domains")
    parser.add_argument("--slug", default="", help="Optional slug override")
    parser.add_argument("--force", action="store_true", help="Overwrite existing SPEC.md")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_root = validate_project_root(Path(args.project_root))
        slug = slugify(args.slug) if args.slug else dated_slug(args.title)
        spec_dir = project_root / ".codex" / "specs" / slug
        spec_path = spec_dir / "SPEC.md"
        if spec_path.exists() and not args.force:
            payload = {"status": "skipped", "slug": slug, "spec_path": str(spec_path), "reason": "spec already exists"}
        else:
            spec_dir.mkdir(parents=True, exist_ok=True)
            spec_path.write_text(render_spec(args.title.strip(), args.prompt, parse_csv(args.domains)), encoding="utf-8")
            payload = {"status": "created", "slug": slug, "spec_path": str(spec_path)}
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    if args.format == "text":
        print(f"{payload['status']}: {payload.get('spec_path', '')}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
