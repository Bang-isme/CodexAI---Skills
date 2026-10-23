#!/usr/bin/env python3
"""Initialize role-scoped project documentation under .codex/project-docs."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_DIR / "templates"
MANIFEST_PATH = TEMPLATE_DIR / "role_docs_manifest.json"
DOCS_ROOT_REL = PurePosixPath(".codex/project-docs")

ROLE_PRESETS: Dict[str, List[str]] = {
    "fullstack": ["frontend", "backend", "devops", "qa"],
    "mvp": ["frontend", "backend", "qa"],
    "fe": ["frontend", "qa"],
    "be": ["backend", "devops", "qa"],
}

ROLE_DOMAIN_SECTIONS: Dict[str, str] = {
    "frontend": """## Surface & UX Contract Matrix (6-State & SILC-001 Alignment)

| Route / Component | Surface Mode | Default / Rest | Loading (`aria-busy`) | Empty (Guided CTA) | Error (`fieldErrors` + Retry) | Success / Permission | Linked `SILC-###` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Not recorded | `operate` | Not recorded | Skeleton | Guided empty CTA | Inline `fieldErrors` | Toast / state update | `SILC-001` |

## Layout Mathematics, Typography & OKLCH Tokens

- Composition thesis & column ratio: Not recorded
- Typography scale & `tabular-nums` usage: Not recorded
- OKLCH surface & action tokens (`DESIGN.md`): Not recorded
- WCAG AA keyboard, focus order & `prefers-reduced-motion` parity: Not recorded
""",
    "backend": """## API & Service Contract Matrix (`SILC-001` Producer)

| Endpoint / Method | Auth / Scope | Request Schema (Zod) | Response DTO Shape | Error Codes (`fieldErrors`) | Idempotency / Rate Limit | Linked `AC / SILC` |
| --- | --- | --- | --- | --- | --- | --- |
| Not recorded | Bearer / Cookie | Not recorded | `{ data, meta }` | `400, 401, 403, 409, 422` | `Idempotency-Key` | `SILC-001` |

## Persistence, Indexing & Migration Contract (`SILC-002`)

| Table / Collection | Key Columns & Types (Money in Cents) | Composite / Partial Indexes (`ESR`) | Expand-and-Contract Migration Plan | Concurrency / Outbox Strategy |
| --- | --- | --- | --- | --- |
| Not recorded | Not recorded | Not recorded | Additive first -> Backfill -> Contract | Optimistic `version` / Outbox |
""",
    "devops": """## Environment, Container & Probe Matrix (`SILC-002` Runtime)

| Environment | Runtime / Image Digest | Liveness (`/health/live`) | Readiness (`/health/ready`) | Required Env / Secret Keys |
| --- | --- | --- | --- | --- |
| `local / staging / prod` | Non-root `USER 10001` | Event-loop check only | DB/Cache ping + `isDraining` flag | `DATABASE_URL`, `JWT_SECRET` |

## Quantitative Rollout & `< 2 Minute` Rollback Runbook

- Pre-deploy verification command: `python skills/codex-execution-quality-gate/scripts/auto_gate.py --project-root . --mode deploy`
- Canary / rollout abort thresholds: `5xx > 1.0%`, `p95 latency > +30%`, `OOMKilled`, or readiness probe failure
- Immediate rollback command (`< 2 min`): Not recorded
- Post-rollback smoke verification: Not recorded
""",
    "qa": """## Testing Trophy & Boundary Coverage Matrix

| Layer | Target Surface / Seam | Real Dependency / Harness | 5-Dimension Boundary Cases Covered | Verification Command | Linked `AC / SILC` |
| --- | --- | --- | --- | --- | --- |
| Unit / Domain | Pure business logic | No mocks | Empty, min/max, negative/zero | Not recorded | `AC-001` |
| Integration / DB | Service + Repository | Real Test DB / Transaction | Conflict (`409`), tenant isolation | Not recorded | `SILC-002` |
| Contract (`SILC`) | FE ↔ BE API seam | Shared Zod / MSW v2 | `2xx` DTO + `422 fieldErrors` | Not recorded | `SILC-001` |
| E2E Journey | Critical user path | Playwright / Browser | Auth -> primary action -> persist | Not recorded | `AC-001` |
""",
    "admin": """## Role & Permission Matrix (`RBAC / ABAC`)

| Role / Persona | Allowed Operations | Restricted / Denied Operations | Tenant Isolation Boundary | Audit Log Event Emitted |
| --- | --- | --- | --- | --- |
| `user` | Own workspace resources | Admin mutations, cross-tenant read | `WHERE tenant_id = $1` | Standard access log |
| `admin` | Tenant management, exports | Unaudited destructive deletes | Explicit confirmation + reason | `admin.action.recorded` |
""",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_timestamp() -> str:
    return utc_now().isoformat(timespec="seconds").replace("+00:00", "Z")


def today() -> str:
    return utc_now().date().isoformat()


def load_manifest() -> Dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def docs_root(project_root: Path) -> Path:
    return project_root / ".codex" / "project-docs"


def validate_project_root(project_root: Path) -> Path:
    if not project_root.exists() or not project_root.is_dir():
        raise NotADirectoryError(f"Project root does not exist or is not a directory: {project_root}")
    return project_root


def normalize_rel(path: str | Path) -> str:
    return PurePosixPath(str(path).replace("\\", "/")).as_posix()


def rel_to_project(path: Path, project_root: Path) -> str:
    try:
        return normalize_rel(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return normalize_rel(path)


def render_template(template_name: str, values: Dict[str, str]) -> str:
    text = (TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text if text.endswith("\n") else text + "\n"


def parse_roles(raw: str, manifest: Dict[str, Any]) -> List[str]:
    available = list(manifest["roles"].keys())
    cleaned = raw.strip().lower()
    if cleaned == "all":
        return available
    if not cleaned:
        return []
    expanded: List[str] = []
    for part in cleaned.split(","):
        token = part.strip()
        if not token:
            continue
        if token in ROLE_PRESETS:
            for preset_role in ROLE_PRESETS[token]:
                if preset_role not in expanded:
                    expanded.append(preset_role)
        elif token not in expanded:
            expanded.append(token)
    invalid = [role for role in expanded if role not in manifest["roles"]]
    if invalid:
        raise ValueError(
            f"Unsupported role(s): {', '.join(invalid)}. Available: {', '.join(available)} (or presets: {', '.join(ROLE_PRESETS)})"
        )
    return expanded


def iter_role_docs(manifest: Dict[str, Any], roles: Iterable[str]) -> Iterable[tuple[str, Dict[str, Any]]]:
    for role in roles:
        for doc in manifest["roles"][role]["docs"]:
            yield role, doc


def write_if_needed(path: Path, content: str, force: bool, project_root: Path) -> tuple[str, str]:
    if path.exists() and not force:
        return "skipped", rel_to_project(path, project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return "created", rel_to_project(path, project_root)


def initialize_role_docs(project_root: Path, roles: List[str], force: bool = False) -> Dict[str, Any]:
    project_root = validate_project_root(project_root)
    manifest = load_manifest()
    root = docs_root(project_root)
    created: List[str] = []
    skipped: List[str] = []

    project_values = {
        "project_name": project_root.name,
        "generated_at": iso_timestamp(),
        "date": today(),
    }
    for target, template in (
        (root / "PROJECT-BRIEF.md", "project-brief-template.md"),
        (root / "decisions" / "ADR-0001-template.md", "adr-template.md"),
    ):
        status, rel_path = write_if_needed(target, render_template(template, project_values), force, project_root)
        (created if status == "created" else skipped).append(rel_path)

    for role, doc in iter_role_docs(manifest, roles):
        values = {
            "doc_id": str(doc["id"]),
            "title": str(doc["title"]),
            "role": role,
            "owner_agents": ", ".join(doc.get("owner_agents", [])),
            "purpose": str(doc["purpose"]),
            "domain_blueprint": ROLE_DOMAIN_SECTIONS.get(role, "").rstrip(),
            "date": today(),
        }
        target = root / role / str(doc["file"])
        status, rel_path = write_if_needed(target, render_template("role-doc-template.md", values), force, project_root)
        (created if status == "created" else skipped).append(rel_path)

    return {
        "status": "created" if created else "up_to_date",
        "project_root": str(project_root),
        "docs_root": normalize_rel(DOCS_ROOT_REL),
        "roles_created": roles,
        "files_created": created,
        "files_skipped": skipped,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize .codex/project-docs role documentation for a project.",
    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument(
        "--roles",
        default="",
        help="Comma-separated roles (frontend,backend,devops,admin,qa), preset (fullstack,mvp,fe,be), or 'all'. Default: project brief and ADR template only",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing docs")
    parser.add_argument("--format", choices=("json",), default="json", help="Output format")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    try:
        manifest = load_manifest()
        roles = parse_roles(args.roles, manifest)
        payload = initialize_role_docs(project_root, roles, force=args.force)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        payload = {
            "status": "error",
            "project_root": str(project_root),
            "message": str(exc),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
