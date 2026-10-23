#!/usr/bin/env python3
"""Scaffold and validate project-local product/surface design context."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PRODUCT_REL = Path(".codex") / "design" / "PRODUCT.md"
SURFACES_REL = Path(".codex") / "design" / "surfaces"
PRODUCT_HEADINGS = ("Audience", "Offer", "Proof", "Constraints", "Surface mode")
SURFACE_HEADINGS = ("Job", "Flow", "States", "Responsive", "Accessibility")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read or scaffold .codex/design product and surface context. Dry-run by default."
    )
    parser.add_argument("--project-root", required=True, help="Project root to confine all reads and writes")
    parser.add_argument("--command", choices=("doctor", "dump", "scaffold", "validate"), default="dump")
    parser.add_argument("--slug", default="", help="Surface slug for scaffold/validate")
    parser.add_argument("--title", default="", help="Optional product or surface title")
    parser.add_argument("--apply", action="store_true", help="Write files. Default is dry-run.")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def confined(project_root: Path, relative: Path) -> Path:
    root = project_root.expanduser().resolve()
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"path escapes project root: {relative}")
    return target


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def heading_present(text: str, heading: str) -> bool:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\b", re.IGNORECASE | re.MULTILINE)
    return bool(pattern.search(text))


def product_template(title: str) -> str:
    name = title.strip() or "Product"
    return (
        f"# {name}\n\n"
        "Stage: Stage 1: Architecture & SILC Contract Lock\n"
        "Linked-Spec: .codex/specs/<slug>/SPEC.md\n"
        "Linked-Design-Contract: DESIGN.md\n\n"
        "## Audience\n\nWho the product is for and the job they hire it to do.\n\n"
        "## Offer\n\nProduct claims that visuals must not invent.\n\n"
        "## Proof\n\nEvidence that can sit near the primary action.\n\n"
        "## Constraints\n\nBrand, legal, incumbent system, and technical limits.\n\n"
        "## Surface mode\n\nDefault `persuade|operate|read|experience` and why.\n\n"
        "## Typography & OKLCH Tokens\n\nDisplay/Body/Mono stack, `tabular-nums`, and perceptual OKLCH surface/action tokens.\n"
    )


def surface_template(slug: str, title: str) -> str:
    name = title.strip() or slug
    return (
        f"# Surface: {name}\n\n"
        "Surface-Mode: operate\n"
        "Change-Mode: new\n"
        "Linked-Spec: .codex/specs/<slug>/SPEC.md\n"
        "Linked-SILC: SILC-001\n\n"
        "## Job\n\nPrimary user task, audience moment, and measurable success signal.\n\n"
        "## Flow\n\nHappy path, failure recovery path, IA grouping, and Composition Thesis + Asymmetric Layout Ratio (e.g., 7:5, 8:4, 260px + minmax(0, 1fr)).\n\n"
        "## Signature Move & Anti-Slop Guardrails\n\n- 10% Signature Move & user benefit: Record one purposeful signature detail.\n- Rejected AI Slop / Gimmicks: No 3-equal-card soup, no AI neon dark-mode cliché, no custom cursor hijacking, no forced 100vh clipping.\n\n"
        "## States\n\n"
        "Empty, loading, error, success, permission denied (6-State Interactive Matrix aligned to `SILC-001`):\n\n"
        "| State | Visual / ARIA Treatment | Microcopy / Action | Linked `SILC-001` Status / Error Code | Recovery Action |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| Default / Rest | Primary hierarchy & >=44px hit target | Action verb CTA | `200 OK` | Ready |\n"
        "| Hover / Focus-Visible | 2px focus ring (`outline-offset: 2px`) | Accessible label | N/A | Keyboard Tab order |\n"
        "| Loading / Pending | `aria-busy=\"true\"` layout-matched skeleton | Progress label | In-flight request | Lock double-submit |\n"
        "| Empty / Zero-Data | Structured empty card with preview | Guided activation CTA | `200 OK` (`data: []`) | Create / reset filter |\n"
        "| Error / Degraded | Preserve form input + `aria-invalid` | Diagnostic + retry CTA | `400 / 409 / 422 fieldErrors / 503` | Retry / fix field |\n"
        "| Success / Permission | Confirmation toast / locked state | Undo or request access | `201 / 204 / 401 / 403` | Undo / re-authenticate |\n\n"
        "## Responsive\n\nDesktop, tablet, and mobile (`320px–2560px`) reflow notes (`minmax(0, 1fr)` and `min-width: 0`).\n\n"
        "## Accessibility\n\nFocus order, semantic landmarks, WCAG AA contrast (`|ΔL| >= 0.65`), `tabular-nums`, and `prefers-reduced-motion` designed still frame.\n"
    )


def validate_product(text: str) -> list[str]:
    if not text.strip():
        return ["PRODUCT.md is missing"]
    return [f"missing heading: {heading}" for heading in PRODUCT_HEADINGS if not heading_present(text, heading)]


def validate_surface(text: str, slug: str) -> list[str]:
    issues = []
    if not SLUG_RE.match(slug):
        issues.append(f"invalid slug: {slug}")
    if not text.strip():
        issues.append(f"surface file missing: {slug}")
        return issues
    issues.extend(f"{slug} missing heading: {heading}" for heading in SURFACE_HEADINGS if not heading_present(text, heading))
    return issues


def list_surface_slugs(surfaces_dir: Path) -> list[str]:
    if not surfaces_dir.is_dir():
        return []
    return sorted(path.stem for path in surfaces_dir.glob("*.md") if path.is_file())


def build_report(project_root: Path, command: str, slug: str, title: str, apply: bool) -> dict[str, Any]:
    product_path = confined(project_root, PRODUCT_REL)
    surfaces_dir = confined(project_root, SURFACES_REL)
    dry_run = not apply
    product_text = read_text(product_path)
    slugs = [slug] if slug else list_surface_slugs(surfaces_dir)
    surface_issues: list[str] = []
    surfaces: dict[str, str] = {}
    for item in slugs:
        rel = SURFACES_REL / f"{item}.md"
        path = confined(project_root, rel)
        text = read_text(path)
        surfaces[item] = text
        surface_issues.extend(validate_surface(text, item))

    written: list[str] = []
    planned: list[str] = []
    if command == "scaffold":
        planned.append(PRODUCT_REL.as_posix())
        if not product_path.exists() or apply:
            if apply:
                product_path.parent.mkdir(parents=True, exist_ok=True)
                if not product_path.exists():
                    product_path.write_text(product_template(title), encoding="utf-8", newline="\n")
                    written.append(PRODUCT_REL.as_posix())
        if slug:
            if not SLUG_RE.match(slug):
                raise ValueError(f"invalid slug: {slug}")
            rel = SURFACES_REL / f"{slug}.md"
            planned.append(rel.as_posix())
            surface_path = confined(project_root, rel)
            if apply:
                surface_path.parent.mkdir(parents=True, exist_ok=True)
                if not surface_path.exists():
                    surface_path.write_text(surface_template(slug, title), encoding="utf-8", newline="\n")
                    written.append(rel.as_posix())

    product_issues = validate_product(read_text(product_path) if command != "doctor" else product_text)
    if command == "scaffold" and dry_run:
        product_issues = []
        surface_issues = []

    status = "dry_run" if dry_run and command == "scaffold" else "pass"
    if command in {"validate", "dump"} and (product_issues or surface_issues):
        status = "fail" if product_issues or (slug and surface_issues) else "warn"

    return {
        "status": status,
        "command": command,
        "project_root": str(project_root.resolve()),
        "dry_run": dry_run,
        "product_path": PRODUCT_REL.as_posix(),
        "product_exists": product_path.exists(),
        "surfaces": sorted(surfaces.keys()) if command != "scaffold" else slugs,
        "planned_writes": planned,
        "written": written,
        "issues": product_issues + surface_issues,
        "product_headings": PRODUCT_HEADINGS,
        "surface_headings": SURFACE_HEADINGS,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        project_root = Path(args.project_root).expanduser().resolve()
        if not project_root.is_dir():
            raise NotADirectoryError(f"Project root does not exist or is not a directory: {project_root}")
        payload = build_report(project_root, args.command, args.slug.strip(), args.title, args.apply)
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    if args.format == "text":
        print(f"{payload['status']}: issues={len(payload.get('issues') or [])} dry_run={payload.get('dry_run')}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] in {"fail", "error"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
