#!/usr/bin/env python3
"""Build .codex/project-docs/index.json from role documentation files."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from init_role_docs import docs_root, load_manifest, normalize_rel, validate_project_root


def extract_source_files(text: str) -> List[str]:
    files: List[str] = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Source Files":
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if in_section and stripped.startswith("- ") and stripped != "- Not recorded":
            files.append(stripped[2:].strip())
    return files


def extract_header_field(text: str, field: str, default: str = "") -> str:
    prefix = f"{field}:"
    for line in text.splitlines()[:20]:
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return default


def classify_doc_population(text: str, source_files: List[str]) -> str:
    explicit = extract_header_field(text, "Population", "").lower()
    unrecorded_count = text.count("- Not recorded")
    if explicit in {"locked", "production"} and unrecorded_count <= 3:
        return explicit
    if source_files or unrecorded_count < 6:
        return "populated" if explicit in {"", "stub"} else explicit
    return "stub"


def build_index(project_root: Path) -> Dict[str, Any]:
    project_root = validate_project_root(project_root)
    manifest = load_manifest()
    root = docs_root(project_root)
    documents: List[Dict[str, Any]] = []
    missing: List[str] = []

    brief_path = root / "PROJECT-BRIEF.md"
    project_stage = "Stage 0: From-Scratch Bootstrap"
    if brief_path.exists():
        brief_text = brief_path.read_text(encoding="utf-8", errors="replace")
        project_stage = extract_header_field(brief_text, "Stage", project_stage)

    for role, role_payload in manifest["roles"].items():
        for doc in role_payload["docs"]:
            path = root / role / str(doc["file"])
            rel_path = normalize_rel(path.relative_to(project_root))
            if path.exists():
                text = path.read_text(encoding="utf-8", errors="replace")
                sources = extract_source_files(text)
                population = classify_doc_population(text, sources)
                stage = extract_header_field(text, "Stage", project_stage)
                documents.append(
                    {
                        "role": role,
                        "id": doc["id"],
                        "title": doc["title"],
                        "path": rel_path,
                        "owner_agents": doc.get("owner_agents", []),
                        "stage": stage,
                        "population": population,
                        "source_files": sources,
                        "last_modified": datetime.fromtimestamp(
                            path.stat().st_mtime,
                            tz=timezone.utc,
                        ).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    }
                )
            else:
                missing.append(rel_path)

    populated_count = sum(1 for item in documents if item.get("population") != "stub")
    stub_count = sum(1 for item in documents if item.get("population") == "stub")
    payload = {
        "status": "indexed",
        "project_root": str(project_root),
        "docs_root": normalize_rel(root.relative_to(project_root)),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "project_stage": project_stage,
        "summary": {
            "total": len(documents),
            "populated": populated_count,
            "stubs": stub_count,
            "missing": len(missing),
        },
        "documents": documents,
        "docs": documents,
        "missing_documents": missing,
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the role documentation index JSON file.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--format", choices=("json",), default="json", help="Output format")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    try:
        payload = build_index(project_root)
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
