#!/usr/bin/env python3
"""Append factual update entries and update lifecycle metadata on a role-scoped project doc."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from init_role_docs import docs_root, load_manifest, normalize_rel, today, validate_project_root


def parse_files(raw: str | None) -> List[str]:
    if not raw:
        return []
    return [normalize_rel(part.strip()) for part in raw.split(",") if part.strip()]


def find_doc(manifest: Dict[str, Any], role: str, doc_id: str) -> Dict[str, Any]:
    role_docs = manifest["roles"].get(role, {}).get("docs", [])
    normalized = doc_id.strip().lower()
    for doc in role_docs:
        candidates = {
            str(doc["id"]).lower(),
            str(doc["file"]).lower(),
            Path(str(doc["file"])).stem.lower(),
        }
        if normalized in candidates:
            return doc
    raise ValueError(f"Unknown doc '{doc_id}' for role '{role}'")


def section_bounds(lines: List[str], heading: str) -> tuple[int, int] | None:
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return start, end


def set_header_metadata(lines: List[str], key: str, value: str) -> List[str]:
    if not value:
        return lines
    prefix = f"{key}:"
    for index, line in enumerate(lines[:20]):
        if line.startswith(prefix):
            lines[index] = f"{key}: {value}"
            return lines
    insert_idx = 1
    for index, line in enumerate(lines[:15]):
        if line.startswith("Last updated:"):
            insert_idx = index
            break
    lines.insert(insert_idx, f"{key}: {value}")
    return lines


def append_section_bullet(lines: List[str], heading: str, entry: str) -> List[str]:
    if not entry.strip():
        return lines
    bounds = section_bounds(lines, heading)
    if bounds is None:
        lines.extend(["", heading, ""])
        bounds = section_bounds(lines, heading)
    assert bounds is not None
    start, end = bounds
    body = [line for line in lines[start + 1 : end] if line.strip() != "- Not recorded"]
    if not body or body[-1].strip():
        body.append("")
    bullet = f"- {entry.strip()}"
    if bullet not in {item.strip() for item in body}:
        body.append(bullet)
    return lines[: start + 1] + body + lines[end:]


def update_source_files(lines: List[str], files: List[str]) -> List[str]:
    if not files:
        return lines
    bounds = section_bounds(lines, "## Source Files")
    if bounds is None:
        lines.extend(["", "## Source Files", ""])
        bounds = section_bounds(lines, "## Source Files")
    assert bounds is not None
    start, end = bounds
    existing = {
        line.strip()[2:].strip()
        for line in lines[start + 1 : end]
        if line.strip().startswith("- ") and line.strip() != "- Not recorded"
    }
    insert_at = end
    new_lines = lines[: start + 1]
    body = [line for line in lines[start + 1 : end] if line.strip() != "- Not recorded"]
    if not body or body[-1].strip():
        body.append("")
    for file_path in files:
        bullet = f"- {file_path}"
        if file_path not in existing:
            body.append(bullet)
    return new_lines + body + lines[insert_at:]


def append_update_log(lines: List[str], summary: str, files: List[str]) -> List[str]:
    bounds = section_bounds(lines, "## Update Log")
    if bounds is None:
        lines.extend(["", "## Update Log", ""])
        bounds = section_bounds(lines, "## Update Log")
    assert bounds is not None
    start, end = bounds
    entry = f"- {today()}: {summary.strip()}"
    if files:
        entry = f"{entry} Source files: {', '.join(files)}."
    body = lines[start + 1 : end]
    if body and body[-1].strip():
        body.append("")
    body.append(entry)
    return lines[: start + 1] + body + lines[end:]


def update_role_doc(
    project_root: Path,
    role: str,
    doc_id: str,
    summary: str,
    files: List[str],
    *,
    decision: str = "",
    contract: str = "",
    verification: str = "",
    stage: str = "",
    population: str = "",
) -> Dict[str, Any]:
    project_root = validate_project_root(project_root)
    manifest = load_manifest()
    if role not in manifest["roles"]:
        raise ValueError(f"Unknown role '{role}'")
    doc = find_doc(manifest, role, doc_id)
    path = docs_root(project_root) / role / str(doc["file"])
    if not path.exists():
        raise FileNotFoundError(f"Role doc does not exist: {path}")

    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()
    lines = set_header_metadata(lines, "Last updated", today())
    if stage:
        lines = set_header_metadata(lines, "Stage", stage)
    if population:
        lines = set_header_metadata(lines, "Population", population)
    elif decision or contract or verification or files:
        lines = set_header_metadata(lines, "Population", "populated")

    if decision:
        lines = append_section_bullet(lines, "## Current Decisions", decision)
    else:
        lines = append_section_bullet(lines, "## Current Decisions", summary)
    if contract:
        lines = append_section_bullet(lines, "## Contracts and Interfaces", contract)
    if verification:
        lines = append_section_bullet(lines, "## Verification", verification)

    lines = update_source_files(lines, files)
    lines = append_update_log(lines, summary, files)
    updated = "\n".join(lines).rstrip() + "\n"
    path.write_text(updated, encoding="utf-8", newline="\n")

    return {
        "status": "updated",
        "project_root": str(project_root),
        "doc_path": normalize_rel(path.relative_to(project_root)),
        "role": role,
        "doc": str(doc["id"]),
        "source_files": files,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a factual update to one role documentation file.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--role", required=True, help="Role key such as frontend, backend, devops, admin, qa")
    parser.add_argument("--doc", required=True, help="Doc id or filename, for example FE-04 or FE-04-component-inventory.md")
    parser.add_argument("--summary", required=True, help="One-sentence factual update summary")
    parser.add_argument("--files", default="", help="Comma-separated source files connected to this update")
    parser.add_argument("--decision", default="", help="Optional decision bullet to record under Current Decisions")
    parser.add_argument("--contract", default="", help="Optional contract/SILC entry to record under Contracts and Interfaces")
    parser.add_argument("--verification", default="", help="Optional verification command/evidence to record under Verification")
    parser.add_argument("--stage", default="", help="Optional lifecycle stage (Stage 0..Stage 4)")
    parser.add_argument("--population", choices=("", "stub", "populated", "locked", "production"), default="")
    parser.add_argument("--format", choices=("json",), default="json", help="Output format")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    try:
        payload = update_role_doc(
            project_root=project_root,
            role=args.role.strip().lower(),
            doc_id=args.doc,
            summary=args.summary,
            files=parse_files(args.files),
            decision=args.decision,
            contract=args.contract,
            verification=args.verification,
            stage=args.stage,
            population=args.population,
        )
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
