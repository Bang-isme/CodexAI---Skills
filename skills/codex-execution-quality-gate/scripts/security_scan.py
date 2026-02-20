#!/usr/bin/env python3
"""
Basic security scan for source repositories.

Output contract:
{
  "scan_type": "basic",
  "critical": [{"file": "...", "line": 1, "issue": "...", "severity": "critical"}],
  "warnings": [{"file": "...", "line": 1, "issue": "...", "severity": "warning"}],
  "passed": true,
  "summary": "0 critical, 0 warnings found"
}
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".next",
    ".venv",
    "venv",
    ".codex",
    ".idea",
    ".vscode",
    ".yarn",
}

TEXT_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".py",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".swift",
    ".php",
    ".rb",
    ".cs",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".conf",
    ".env",
    ".sh",
    ".ps1",
}

MAX_FILE_SIZE = 1_000_000

SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|secret|password|passwd|client[_-]?secret)\b\s*[:=]\s*[\"']([^\"'\n]{8,})[\"']"
)
AWS_KEY_PATTERN = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
GITHUB_TOKEN_PATTERN = re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")
EVAL_CALL_PATTERN = re.compile(r"(^|[^A-Za-z0-9_\"'])eval\s*\(")
EXEC_CALL_PATTERN = re.compile(r"(^|[^A-Za-z0-9_\"'])exec\s*\(")
HTTP_PATTERN = re.compile(r"http://[^\s\"')`]+")
TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK)\b", re.IGNORECASE)
CONSOLE_PATTERN = re.compile(r"\bconsole\.(log|debug)\s*\(")
PRINT_PATTERN = re.compile(r"(^|\s)print\s*\(")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run basic security scan and emit JSON.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--human", action="store_true", help="Print human-readable summary to stderr")
    return parser.parse_args()


def relative_path(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def is_relevant_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    return path.name.startswith(".env")


def read_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    placeholders = (
        "example",
        "changeme",
        "your_",
        "dummy",
        "sample",
        "placeholder",
        "xxxx",
        "test",
    )
    return any(token in lowered for token in placeholders)


def is_production_path(rel_path: str) -> bool:
    parts = rel_path.lower().split("/")
    non_production_tokens = {
        "test",
        "tests",
        "__tests__",
        "spec",
        "specs",
        "fixtures",
        "examples",
        "docs",
        "scripts",
    }
    return not any(part in non_production_tokens for part in parts)


def collect_source_files(project_root: Path) -> List[Path]:
    files: List[Path] = []
    for root, dirs, names in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        for name in names:
            path = root_path / name
            if not is_relevant_text_file(path):
                continue
            try:
                if path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue
            files.append(path)
    return files


def build_issue(file_path: str, line: int, issue: str, severity: str) -> Dict[str, object]:
    return {
        "file": file_path,
        "line": line,
        "issue": issue,
        "severity": severity,
    }


def read_gitignore_rules(project_root: Path) -> Set[str]:
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return set()
    rules: Set[str] = set()
    for line in read_lines(gitignore_path):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rules.add(stripped)
    return rules


def env_ignored_by_rules(rules: Set[str]) -> bool:
    accepted = {".env", ".env.*", "*.env", "**/.env", "**/.env.*", ".env.local"}
    if accepted & rules:
        return True
    for rule in rules:
        lowered = rule.lower()
        if lowered.endswith("/.env") or lowered.endswith("/.env.*"):
            return True
    return False


def scan(project_root: Path) -> Dict[str, object]:
    critical: List[Dict[str, object]] = []
    warnings: List[Dict[str, object]] = []
    seen: Set[Tuple[str, int, str, str]] = set()

    if not project_root.exists() or not project_root.is_dir():
        critical.append(
            build_issue(
                file_path=".",
                line=1,
                issue=f"Project root does not exist or is not a directory: {project_root}",
                severity="critical",
            )
        )
        return {
            "scan_type": "basic",
            "critical": critical,
            "warnings": warnings,
            "passed": False,
            "summary": "1 critical, 0 warnings found",
        }

    for file_path in collect_source_files(project_root):
        rel = relative_path(file_path, project_root)
        lines = read_lines(file_path)
        if not lines:
            continue
        prod_path = is_production_path(rel)

        for idx, line in enumerate(lines, start=1):
            secret_match = SECRET_ASSIGNMENT_PATTERN.search(line)
            if secret_match:
                secret_value = secret_match.group(2).strip()
                if not looks_like_placeholder(secret_value):
                    item = build_issue(rel, idx, "Potential hardcoded secret value", "critical")
                    key = (item["file"], item["line"], item["issue"], item["severity"])
                    if key not in seen:
                        seen.add(key)
                        critical.append(item)

            if AWS_KEY_PATTERN.search(line):
                item = build_issue(rel, idx, "Potential AWS access key exposure", "critical")
                key = (item["file"], item["line"], item["issue"], item["severity"])
                if key not in seen:
                    seen.add(key)
                    critical.append(item)

            if GITHUB_TOKEN_PATTERN.search(line):
                item = build_issue(rel, idx, "Potential GitHub token exposure", "critical")
                key = (item["file"], item["line"], item["issue"], item["severity"])
                if key not in seen:
                    seen.add(key)
                    critical.append(item)

            if EVAL_CALL_PATTERN.search(line) or EXEC_CALL_PATTERN.search(line):
                item = build_issue(rel, idx, "Dynamic code execution pattern found (eval/exec)", "critical")
                key = (item["file"], item["line"], item["issue"], item["severity"])
                if key not in seen:
                    seen.add(key)
                    critical.append(item)

            if HTTP_PATTERN.search(line):
                item = build_issue(rel, idx, "HTTP URL found; prefer HTTPS for production traffic", "warning")
                key = (item["file"], item["line"], item["issue"], item["severity"])
                if key not in seen:
                    seen.add(key)
                    warnings.append(item)

            if TODO_PATTERN.search(line):
                item = build_issue(rel, idx, "TODO/FIXME/HACK marker present", "warning")
                key = (item["file"], item["line"], item["issue"], item["severity"])
                if key not in seen:
                    seen.add(key)
                    warnings.append(item)

            if prod_path and (CONSOLE_PATTERN.search(line) or PRINT_PATTERN.search(line)):
                item = build_issue(rel, idx, "Debug logging statement in production path", "warning")
                key = (item["file"], item["line"], item["issue"], item["severity"])
                if key not in seen:
                    seen.add(key)
                    warnings.append(item)

    env_files = []
    for candidate in project_root.glob(".env*"):
        if candidate.is_file():
            env_files.append(candidate)

    if env_files:
        rules = read_gitignore_rules(project_root)
        if not env_ignored_by_rules(rules):
            for env_file in env_files:
                item = build_issue(
                    relative_path(env_file, project_root),
                    1,
                    ".env file found but .gitignore does not clearly ignore environment files",
                    "warning",
                )
                key = (item["file"], item["line"], item["issue"], item["severity"])
                if key not in seen:
                    seen.add(key)
                    warnings.append(item)

    summary = f"{len(critical)} critical, {len(warnings)} warnings found"
    return {
        "scan_type": "basic",
        "critical": critical,
        "warnings": warnings,
        "passed": len(critical) == 0,
        "summary": summary,
    }


def render_human_box(title: str, rows: List[str]) -> str:
    width = max(len(title), *(len(row) for row in rows), 32)
    border = "+" + "-" * (width + 2) + "+"
    out = [border, f"| {title.ljust(width)} |", border]
    for row in rows:
        out.append(f"| {row.ljust(width)} |")
    out.append(border)
    return "\n".join(out)


def print_human_summary(report: Dict[str, object]) -> None:
    critical = report.get("critical", [])
    warnings = report.get("warnings", [])
    rows: List[str] = [
        f"Passed: {bool(report.get('passed', False))}",
        f"Critical: {len(critical) if isinstance(critical, list) else 0}",
        f"Warnings: {len(warnings) if isinstance(warnings, list) else 0}",
    ]

    top: List[Dict[str, object]] = []
    if isinstance(critical, list):
        top.extend(critical[:3])
    if isinstance(warnings, list) and len(top) < 5:
        top.extend(warnings[: 5 - len(top)])
    if top:
        rows.append("Top Issues:")
        for idx, item in enumerate(top, start=1):
            file_path = str(item.get("file", "?"))
            line = item.get("line", "?")
            issue = str(item.get("issue", ""))
            rows.append(f"  {idx}. {file_path}:{line} {issue}")

    print(render_human_box("SECURITY SCAN RESULTS", rows), file=sys.stderr)


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    report = scan(project_root)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.human:
        print_human_summary(report)
    critical = report.get("critical", [])
    return 1 if isinstance(critical, list) and len(critical) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
