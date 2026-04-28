#!/usr/bin/env python3
"""Check changed files against project-local specs."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
DOMAIN_PATTERNS = {
    "frontend": ("src/", "app/", "components/", "pages/", "styles/", ".tsx", ".jsx", ".vue", ".css", ".scss"),
    "backend": ("api/", "server/", "routes/", "controllers/", "services/", "middleware/", ".py", ".go", ".rs", ".java", ".cs"),
    "data": ("db/", "prisma/", "migrations/", "schema.", "models/"),
    "qa": ("tests/", "__tests__/", "cypress/", "playwright/", ".test.", ".spec."),
    "devops": (".github/", "Dockerfile", "docker-compose", "infra/", "deploy/", "k8s/", "terraform/"),
}
AC_PATTERN = re.compile(r"\bAC-\d{3}\b")


def parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for item in value.split(","):
        normalized = item.strip().replace("\\", "/")
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result


def validate_project_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Project root does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {resolved}")
    return resolved


def classify_file(path: str) -> str:
    lowered = path.lower()
    for domain, patterns in DOMAIN_PATTERNS.items():
        if any(lowered.startswith(pattern.lower()) or pattern.lower() in lowered for pattern in patterns):
            return domain
    return "unknown"


def parse_spec_metadata(text: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {"schema_version": "", "status": "", "domains": [], "acceptance_criteria": []}
    for line in text.splitlines():
        lowered = line.lower()
        if lowered.startswith("schema-version:"):
            metadata["schema_version"] = line.split(":", 1)[1].strip()
        elif lowered.startswith("status:"):
            metadata["status"] = line.split(":", 1)[1].strip().lower()
        elif lowered.startswith("domains:"):
            domains_line = line.split(":", 1)[1].strip()
            metadata["domains"] = [item.strip().lower() for item in domains_line.split(",") if item.strip()]
    metadata["acceptance_criteria"] = sorted(set(AC_PATTERN.findall(text)))
    return metadata


def read_specs(project_root: Path) -> list[dict[str, Any]]:
    specs_root = project_root / ".codex" / "specs"
    specs: list[dict[str, Any]] = []
    if not specs_root.exists():
        return specs
    for path in sorted(specs_root.glob("*/SPEC.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        metadata = parse_spec_metadata(text)
        specs.append(
            {
                "slug": path.parent.name,
                "path": path,
                "domains": metadata["domains"],
                "status": metadata["status"] or "unknown",
                "schema_version": metadata["schema_version"] or "legacy",
                "acceptance_criteria": metadata["acceptance_criteria"],
                "text": text.lower(),
            }
        )
    return specs


def match_specs(file_path: str, domain: str, specs: list[dict[str, Any]]) -> list[str]:
    lowered = file_path.lower()
    matches: list[str] = []
    for spec in specs:
        domains = spec["domains"]
        text = spec["text"]
        if domain != "unknown" and (domain in domains or "not classified yet" in domains):
            matches.append(spec["slug"])
            continue
        if lowered in text or Path(lowered).name in text:
            matches.append(spec["slug"])
    return matches


def git_changed_files(project_root: Path, base: str) -> list[str]:
    commands = [
        ["git", "diff", "--name-only", base],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    changed: list[str] = []
    seen: set[str] = set()
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                cwd=project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if completed.returncode != 0:
            continue
        for line in completed.stdout.splitlines():
            normalized = line.strip().replace("\\", "/")
            if normalized and normalized not in seen:
                changed.append(normalized)
                seen.add(normalized)
    return changed


def build_report(project_root: Path, changed_files: list[str]) -> dict[str, Any]:
    specs = read_specs(project_root)
    if not specs:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "checked",
            "overall": "skip",
            "matched_specs": [],
            "unmapped_files": [],
            "suggested_actions": ["Run $spec before prototype/fullstack implementation if this is multi-domain work."],
            "specs_found": 0,
        }
    file_reports: list[dict[str, Any]] = []
    unmapped: list[str] = []
    matched_slugs: set[str] = set()
    matched_ac_ids: set[str] = set()
    legacy_specs: list[str] = []
    draft_specs: list[str] = []
    specs_without_ac: list[str] = []
    for spec in specs:
        if spec["schema_version"] != SCHEMA_VERSION:
            legacy_specs.append(spec["slug"])
        if spec["status"] == "draft":
            draft_specs.append(spec["slug"])
        if not spec["acceptance_criteria"]:
            specs_without_ac.append(spec["slug"])
    for file_path in changed_files:
        domain = classify_file(file_path)
        matches = match_specs(file_path, domain, specs)
        matched_slugs.update(matches)
        ac_ids: list[str] = []
        for spec in specs:
            if spec["slug"] in matches:
                ac_ids.extend(spec["acceptance_criteria"])
        matched_ac_ids.update(ac_ids)
        file_reports.append({"file": file_path, "domain": domain, "matched_specs": matches, "candidate_ac_ids": sorted(set(ac_ids))})
        if domain != "unknown" and not matches:
            unmapped.append(file_path)
    overall = "warn" if unmapped or legacy_specs or specs_without_ac else "pass"
    actions = []
    if unmapped:
        actions.append("Update the relevant SPEC.md Traceability table with Changed File, AC ID, and Validation Command.")
    if legacy_specs:
        actions.append("Update legacy specs so they include Schema-Version: 1.0.")
    if specs_without_ac:
        actions.append("Add AC-001 style acceptance criteria IDs to specs without traceable criteria.")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "checked",
        "overall": overall,
        "matched_specs": sorted(matched_slugs),
        "matched_acceptance_criteria": sorted(matched_ac_ids),
        "unmapped_files": unmapped,
        "files": file_reports,
        "suggested_actions": actions,
        "specs_found": len(specs),
        "legacy_specs": legacy_specs,
        "draft_specs": draft_specs,
        "specs_without_acceptance_criteria": specs_without_ac,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check changed files against .codex/specs.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--changed-files", default="", help="Comma-separated changed files")
    parser.add_argument("--base", default="HEAD", help="Git base for changed-file discovery when --changed-files is omitted")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_root = validate_project_root(Path(args.project_root))
        changed_files = parse_csv(args.changed_files) or git_changed_files(project_root, args.base)
        report = build_report(project_root, changed_files)
    except Exception as exc:
        payload = {"schema_version": SCHEMA_VERSION, "status": "error", "overall": "warn", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "text":
        print(f"Overall: {report['overall']}")
        print(f"Matched specs: {', '.join(report['matched_specs']) or 'none'}")
        print(f"Unmapped files: {', '.join(report['unmapped_files']) or 'none'}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
