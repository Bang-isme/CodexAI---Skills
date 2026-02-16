#!/usr/bin/env python3
"""
Map changed files to documentation candidates.

MVP behavior:
- report-only
- convention-first mapping
- markdown reference search
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Set, Tuple


CONFIDENCE_RANK = {"low": 1, "medium": 2, "high": 3}
COMMON_PATH_SEGMENTS = {
    "src",
    "lib",
    "app",
    "server",
    "client",
    "api",
    "routes",
    "controllers",
    "services",
    "utils",
    "tests",
    "test",
    "docs",
}
LOW_VALUE_TOKENS = {
    "api",
    "test",
    "tests",
    "main",
    "index",
    "route",
    "routes",
    "controller",
    "controllers",
    "service",
    "services",
    "setup",
}


def run_git(project_root: Path, args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )


def is_git_repo(project_root: Path) -> bool:
    result = run_git(project_root, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def detect_default_branch(project_root: Path) -> str:
    symbolic = run_git(project_root, ["symbolic-ref", "refs/remotes/origin/HEAD"])
    if symbolic.returncode == 0:
        ref = symbolic.stdout.strip()
        if ref:
            return ref.rsplit("/", 1)[-1]

    for candidate in ("main", "master"):
        check = run_git(project_root, ["rev-parse", "--verify", candidate])
        if check.returncode == 0:
            return candidate

    return "main"


def parse_changed_output(raw_output: str) -> List[str]:
    files: List[str] = []
    seen: Set[str] = set()
    for raw in raw_output.splitlines():
        path = raw.strip()
        if not path:
            continue
        normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
        if normalized not in seen:
            files.append(normalized)
            seen.add(normalized)
    return files


def has_head_commit(project_root: Path) -> bool:
    result = run_git(project_root, ["rev-parse", "--verify", "HEAD"])
    return result.returncode == 0


def get_changed_files(project_root: Path, scope: str) -> Tuple[List[str], List[str]]:
    notes: List[str] = []

    if scope == "auto":
        for candidate in ("staged", "unstaged", "last-commit"):
            try:
                files, candidate_notes = get_changed_files(project_root, candidate)
            except RuntimeError as exc:
                notes.append(f"Auto scope candidate '{candidate}' failed: {exc}")
                continue
            notes.extend(candidate_notes)
            if files:
                notes.append(f"Auto diff scope selected: {candidate}")
                return files, notes
        notes.append("Auto diff scope selected: none (no staged, unstaged, or last-commit changes).")
        return [], notes

    if scope == "unstaged":
        cmd = ["diff", "--name-only"]
    elif scope == "staged":
        cmd = ["diff", "--name-only", "--cached"]
    elif scope == "last-commit":
        if not has_head_commit(project_root):
            notes.append("No commits found. last-commit scope has no changes.")
            return [], notes
        cmd = ["diff", "--name-only", "HEAD~1..HEAD"]
    elif scope == "branch":
        base = detect_default_branch(project_root)
        cmd = ["diff", "--name-only", f"{base}...HEAD"]
        notes.append(f"Using branch comparison base: {base}")
    else:
        raise ValueError(f"Unsupported diff scope: {scope}")

    result = run_git(project_root, cmd)
    if result.returncode != 0:
        if scope == "last-commit":
            fallback_result = run_git(project_root, ["diff-tree", "--no-commit-id", "--name-only", "-r", "--root", "HEAD"])
            if fallback_result.returncode == 0:
                notes.append("last-commit fallback used: git diff-tree --root HEAD")
                return parse_changed_output(fallback_result.stdout), notes
            fallback_message = (
                fallback_result.stderr.strip() or fallback_result.stdout.strip() or "git diff-tree fallback failed"
            )
            raise RuntimeError(fallback_message)

        if scope == "branch":
            notes.append(
                "Branch comparison failed (missing remote/default branch). "
                "Falling back to last-commit scope."
            )
            fallback_files, fallback_notes = get_changed_files(project_root, "last-commit")
            notes.extend(fallback_notes)
            notes.append("Fallback scope used: last-commit")
            return fallback_files, notes

        message = result.stderr.strip() or result.stdout.strip() or "git diff failed"
        raise RuntimeError(message)

    return parse_changed_output(result.stdout), notes


def is_public_api_path(rel_path: str) -> bool:
    parts = [part.lower() for part in PurePosixPath(rel_path).parts]
    if any(part in {"api", "route", "routes", "controller", "controllers", "public"} for part in parts):
        return True
    if len(parts) >= 2 and parts[0] == "src" and re.match(r"^(index|main)\.", parts[1]):
        return True
    return False


def relative(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def add_candidate(
    candidates: Dict[str, Dict[str, str]],
    doc_path: str,
    reason: str,
    confidence: str,
) -> None:
    current = candidates.get(doc_path)
    if not current:
        candidates[doc_path] = {
            "doc_path": doc_path,
            "reason": reason,
            "confidence": confidence,
        }
        return

    if CONFIDENCE_RANK[confidence] > CONFIDENCE_RANK[current["confidence"]]:
        candidates[doc_path] = {
            "doc_path": doc_path,
            "reason": reason,
            "confidence": confidence,
        }


def convention_mapping(
    changed_files: Iterable[str],
    project_root: Path,
    candidates: Dict[str, Dict[str, str]],
) -> None:
    for rel in changed_files:
        p = PurePosixPath(rel)
        parts = list(p.parts)
        if not parts:
            continue

        lowered = [part.lower() for part in parts]

        if len(parts) >= 3 and lowered[0] == "src":
            module = parts[1]
            docs_file = f"docs/{module}.md"
            docs_dir = project_root / "docs" / module
            docs_md = project_root / docs_file
            if docs_md.exists():
                add_candidate(
                    candidates,
                    docs_file,
                    f"Convention match: src/{module}/* -> docs/{module}.md",
                    "high",
                )
            elif docs_dir.exists():
                add_candidate(
                    candidates,
                    f"docs/{module}/",
                    f"Convention match: src/{module}/* -> docs/{module}/",
                    "high",
                )
            else:
                add_candidate(
                    candidates,
                    docs_file,
                    f"Convention suggestion: src/{module}/* -> docs/{module}.md",
                    "medium",
                )

        if len(parts) >= 3 and lowered[0] == "lib":
            module = parts[1]
            add_candidate(
                candidates,
                f"docs/api/{module}.md",
                f"Convention match: lib/{module}/* -> docs/api/{module}.md",
                "high",
            )

        if len(parts) >= 2 and lowered[0] == "src" and re.match(r"^(index|main)\.", lowered[1]):
            add_candidate(
                candidates,
                "README.md",
                "Entry point changed: src/index.* or src/main.*",
                "high",
            )

        if any("schema" in segment or "model" in segment for segment in lowered):
            if (project_root / "docs/database.md").exists():
                add_candidate(
                    candidates,
                    "docs/database.md",
                    "Schema/model change detected",
                    "high",
                )
            if (project_root / "docs/schema.md").exists():
                add_candidate(
                    candidates,
                    "docs/schema.md",
                    "Schema/model change detected",
                    "high",
                )


def build_reference_tokens(changed_files: Iterable[str]) -> Set[str]:
    tokens: Set[str] = set()
    for rel in changed_files:
        p = PurePosixPath(rel)
        parts = [segment.lower() for segment in p.parts]
        if not parts:
            continue

        stem = p.stem.lower()
        if len(stem) >= 4 and stem not in LOW_VALUE_TOKENS:
            tokens.add(stem)

        tail = "/".join(parts[-2:]).strip("/")
        if len(tail) >= 5:
            tokens.add(tail)

        for segment in parts:
            if (
                len(segment) >= 5
                and segment not in COMMON_PATH_SEGMENTS
                and segment not in LOW_VALUE_TOKENS
                and "." not in segment
            ):
                tokens.add(segment)

    return tokens


def collect_markdown_files(project_root: Path) -> List[Path]:
    files: List[Path] = []
    docs_dir = project_root / "docs"
    if docs_dir.exists():
        files.extend(path for path in docs_dir.rglob("*.md") if path.is_file())
    for root_file in ("README.md", "CHANGELOG.md"):
        path = project_root / root_file
        if path.exists():
            files.append(path)
    return files


def reference_search_mapping(
    changed_files: Iterable[str],
    project_root: Path,
    candidates: Dict[str, Dict[str, str]],
) -> None:
    tokens = build_reference_tokens(changed_files)
    if not tokens:
        return

    markdown_files = collect_markdown_files(project_root)
    if not markdown_files:
        return

    for md_file in markdown_files:
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if not content:
            continue

        matched: Optional[str] = None
        for token in tokens:
            if token in content:
                matched = token
                break

        if matched:
            add_candidate(
                candidates,
                relative(md_file, project_root),
                f"Reference search match for token '{matched}'",
                "medium",
            )


def always_include_mapping(
    changed_files: Iterable[str],
    project_root: Path,
    candidates: Dict[str, Dict[str, str]],
) -> None:
    if any(is_public_api_path(path) for path in changed_files):
        add_candidate(
            candidates,
            "README.md",
            "Public API related changes detected",
            "high",
        )

    changelog = project_root / "CHANGELOG.md"
    if changelog.exists():
        add_candidate(
            candidates,
            "CHANGELOG.md",
            "Code changes detected and CHANGELOG.md exists",
            "medium",
        )


def monorepo_note(project_root: Path) -> Optional[str]:
    package_files = [path for path in project_root.rglob("package.json") if path.is_file()]
    deep_packages = [path for path in package_files if path.parent != project_root]
    if len(deep_packages) > 1:
        return "Multiple package.json files detected. MVP mapping still runs from project root."
    return None


def build_report(project_root: Path, diff_scope: str) -> Dict[str, object]:
    if not project_root.exists() or not project_root.is_dir():
        return {
            "changed_files": [],
            "docs_candidates": [],
            "status": "error",
            "notes": [f"Project root does not exist or is not a directory: {project_root}"],
        }

    if not is_git_repo(project_root):
        return {
            "changed_files": [],
            "docs_candidates": [],
            "status": "no_git",
            "notes": ["Target path is not a git repository."],
        }

    try:
        changed_files, notes = get_changed_files(project_root, diff_scope)
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "changed_files": [],
            "docs_candidates": [],
            "status": "error",
            "notes": [f"Failed to read git diff: {exc}"],
        }

    if not changed_files:
        return {
            "changed_files": [],
            "docs_candidates": [],
            "status": "no_changes",
            "notes": notes,
        }

    monorepo = monorepo_note(project_root)
    if monorepo:
        notes.append(monorepo)

    candidates: Dict[str, Dict[str, str]] = {}
    convention_mapping(changed_files, project_root, candidates)
    reference_search_mapping(changed_files, project_root, candidates)
    always_include_mapping(changed_files, project_root, candidates)

    ordered_candidates = sorted(candidates.values(), key=lambda item: item["doc_path"])
    return {
        "changed_files": changed_files,
        "docs_candidates": ordered_candidates,
        "status": "ok",
        "notes": notes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Map changed files to documentation candidates.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument(
        "--diff-scope",
        default="auto",
        choices=["auto", "unstaged", "staged", "last-commit", "branch"],
        help="Diff scope to analyze",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    report = build_report(project_root, args.diff_scope)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
