#!/usr/bin/env python3
"""Check role documentation coverage and suggest updates for changed files."""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List

from init_role_docs import docs_root, load_manifest, normalize_rel, validate_project_root


def parse_changed_files(raw: str | None) -> List[str]:
    if not raw:
        return []
    files: List[str] = []
    seen = set()
    for part in raw.split(","):
        normalized = normalize_rel(part.strip())
        if normalized and normalized not in seen:
            files.append(normalized)
            seen.add(normalized)
    return files


def run_git_changed(project_root: Path) -> List[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    return [normalize_rel(line.strip()) for line in result.stdout.splitlines() if line.strip()]


def doc_ref(role: str, filename: str) -> str:
    return normalize_rel(Path(".codex") / "project-docs" / role / filename)


def find_doc(manifest: Dict[str, Any], role: str, doc_id: str) -> Dict[str, Any]:
    for doc in manifest["roles"][role]["docs"]:
        if str(doc["id"]) == doc_id:
            return doc
    raise KeyError(f"{role}:{doc_id}")


def add_suggestion(suggestions: List[Dict[str, str]], changed_file: str, role: str, doc: Dict[str, Any], reason: str) -> None:
    candidate = {
        "changed_file": changed_file,
        "role": role,
        "doc": doc_ref(role, str(doc["file"])),
        "doc_id": str(doc["id"]),
        "reason": reason,
    }
    key = (candidate["changed_file"], candidate["doc"])
    if key not in {(item["changed_file"], item["doc"]) for item in suggestions}:
        suggestions.append(candidate)


def path_matches(path: str, patterns: Iterable[str]) -> bool:
    lowered = path.lower()
    return any(fnmatch.fnmatch(lowered, pattern.lower()) for pattern in patterns)


def map_changed_file(path: str, manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    normalized = normalize_rel(path)
    lowered = normalized.lower()
    suggestions: List[Dict[str, str]] = []

    def add(role: str, doc_id: str, reason: str) -> None:
        add_suggestion(suggestions, normalized, role, find_doc(manifest, role, doc_id), reason)

    if lowered.startswith(".codex/project-docs/"):
        return []

    if path_matches(lowered, ["tests/**", "test/**", "__tests__/**", "e2e/**", "playwright/**", "cypress/**", "**/*test.*", "**/*spec.*"]):
        add("qa", "QA-01", "test or regression surface changed")
        if any(token in lowered for token in ("e2e/", "playwright/", "cypress/")):
            add("qa", "QA-02", "end-to-end flow changed")
        else:
            add("qa", "QA-00", "test strategy may need coverage notes")

    if path_matches(lowered, [".github/workflows/**", "infra/**", "deploy/**", "k8s/**", "helm/**", "terraform/**", "**/*.tf", "dockerfile*", "docker-compose*.yml", "**/dockerfile*"]):
        add("devops", "DO-02", "CI/CD or infrastructure file changed")
        add("devops", "DO-03", "deployment runbook may need refresh")
        if any(token in lowered for token in ("secret", ".env", "config", "vault")):
            add("devops", "DO-06", "secrets or runtime config changed")

    if "admin" in lowered:
        if any(token in lowered for token in ("role", "permission", "auth", "policy")):
            add("admin", "AD-01", "admin permissions or authorization changed")
        elif any(token in lowered for token in ("audit", "log", "event")):
            add("admin", "AD-03", "admin audit logging changed")
        elif any(token in lowered for token in ("dashboard", "report", "metric", "chart")):
            add("admin", "AD-05", "admin dashboard or reporting changed")
        elif any(token in lowered for token in ("data", "export", "import", "delete", "user")):
            add("admin", "AD-04", "admin data management changed")
        else:
            add("admin", "AD-02", "admin flow changed")

    frontend_patterns = [
        "app/**/*.tsx",
        "app/**/*.jsx",
        "app/**/*.vue",
        "src/**/*.tsx",
        "src/**/*.jsx",
        "src/**/*.vue",
        "components/**",
        "pages/**",
        "styles/**",
        "**/*.css",
        "**/*.scss",
    ]
    if path_matches(lowered, frontend_patterns):
        add("frontend", "FE-00", "frontend surface changed")
        if any(token in lowered for token in ("component", "components/", "ui/", "widget")):
            add("frontend", "FE-04", "reusable component changed")
        if any(token in lowered for token in ("style", "theme", "token", "css", "scss", "tailwind", "design")):
            add("frontend", "FE-02", "design-system surface changed")
            add("frontend", "FE-03", "design token or theme changed")
        if any(token in lowered for token in ("route", "router", "page", "screen", "layout")):
            add("frontend", "FE-05", "frontend route or state surface changed")

    backend_patterns = [
        "api/**",
        "server/**",
        "src/server/**",
        "services/**",
        "controllers/**",
        "routes/**",
        "middleware/**",
        "db/**",
        "migrations/**",
        "prisma/**",
        "**/schema.*",
        "**/models/**",
    ]
    if path_matches(lowered, backend_patterns):
        add("backend", "BE-00", "backend surface changed")
        if any(token in lowered for token in ("route", "routes/", "controller", "controllers/", "api/")):
            add("backend", "BE-01", "API contract changed")
        if any(token in lowered for token in ("db/", "database", "migration", "migrations/", "schema", "model", "prisma")):
            add("backend", "BE-02", "database design changed")
            add("backend", "BE-03", "domain model may need refresh")
        if any(token in lowered for token in ("auth", "jwt", "session", "permission", "security", "middleware")):
            add("backend", "BE-04", "auth or security behavior changed")
            add("admin", "AD-01", "permission boundary may need refresh")
        if any(token in lowered for token in ("webhook", "queue", "event", "integration")):
            add("backend", "BE-05", "integration or event flow changed")
        if any(token in lowered for token in ("error", "logger", "logging", "exception")):
            add("backend", "BE-06", "error or logging behavior changed")

    return suggestions


def expected_doc_paths(manifest: Dict[str, Any]) -> List[str]:
    paths: List[str] = [
        normalize_rel(Path(".codex") / "project-docs" / "PROJECT-BRIEF.md"),
        normalize_rel(Path(".codex") / "project-docs" / "decisions" / "ADR-0001-template.md"),
    ]
    for role, payload in manifest["roles"].items():
        for doc in payload["docs"]:
            paths.append(doc_ref(role, str(doc["file"])))
    return paths


def collect_missing_docs(project_root: Path, manifest: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    root = docs_root(project_root)
    for rel_path in expected_doc_paths(manifest):
        absolute = project_root / rel_path
        if not absolute.exists():
            missing.append(normalize_rel(absolute.relative_to(project_root)))
    if not root.exists() and not missing:
        missing.append(normalize_rel(root.relative_to(project_root)))
    return missing


def collect_stale_docs(project_root: Path, suggestions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    stale: List[Dict[str, str]] = []
    for suggestion in suggestions:
        changed_path = project_root / suggestion["changed_file"]
        doc_path = project_root / suggestion["doc"]
        if not changed_path.exists() or not doc_path.exists():
            continue
        doc_text = doc_path.read_text(encoding="utf-8", errors="replace")
        if suggestion["changed_file"] not in doc_text:
            stale.append(
                {
                    "changed_file": suggestion["changed_file"],
                    "doc": suggestion["doc"],
                    "reason": "changed file is not recorded in doc Source Files",
                }
            )
            continue
        if changed_path.stat().st_mtime > doc_path.stat().st_mtime:
            stale.append(
                {
                    "changed_file": suggestion["changed_file"],
                    "doc": suggestion["doc"],
                    "reason": "source file is newer than role doc",
                }
            )
    return stale


def check_role_docs(project_root: Path, changed_files: List[str] | None = None) -> Dict[str, Any]:
    project_root = validate_project_root(project_root)
    manifest = load_manifest()
    explicit_changed_files = changed_files is not None
    root = docs_root(project_root)
    if not root.exists() and not explicit_changed_files:
        return {
            "status": "checked",
            "project_root": str(project_root),
            "docs_root": normalize_rel(root.relative_to(project_root)),
            "overall": "skip",
            "changed_files": [],
            "missing_docs": [],
            "stale_docs": [],
            "suggested_updates": [],
            "summary": "Role docs are not initialized for this project; advisory check skipped.",
        }
    files = changed_files if changed_files is not None else run_git_changed(project_root)
    suggestions: List[Dict[str, str]] = []
    for changed_file in files:
        suggestions.extend(map_changed_file(changed_file, manifest))
    missing = collect_missing_docs(project_root, manifest)
    stale = collect_stale_docs(project_root, suggestions)
    overall = "warn" if missing or stale or suggestions else "pass"
    return {
        "status": "checked",
        "project_root": str(project_root),
        "docs_root": normalize_rel(docs_root(project_root).relative_to(project_root)),
        "overall": overall,
        "changed_files": files,
        "missing_docs": missing,
        "stale_docs": stale,
        "suggested_updates": suggestions,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check role documentation coverage and update suggestions.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--changed-files", default=None, help="Comma-separated changed files; defaults to git diff --name-only")
    parser.add_argument("--format", choices=("json",), default="json", help="Output format")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    try:
        explicit_files = parse_changed_files(args.changed_files) if args.changed_files is not None else None
        payload = check_role_docs(project_root, explicit_files)
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
