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

## Goals
- Define the user-visible outcome before implementation.
- Keep frontend, backend, data, QA, and deployment impact explicit.

## Non-Goals
- Do not add unrelated features.
- Do not change unrelated architecture without a separate ADR.

## Requirements
- R1: The implementation must satisfy the stated user workflow.
- R2: The implementation must preserve existing behavior unless explicitly changed.
- R3: The implementation must include verification evidence before completion.

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

## Validation Plan
- Run focused tests for changed modules.
- Run `python <SKILLS_ROOT>/codex-execution-quality-gate/scripts/auto_gate.py --project-root <PROJECT_ROOT> --mode full`.

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
