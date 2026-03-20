#!/usr/bin/env python3
"""Install or remove CodexAI quality gate git hooks."""
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


START_MARKER = "# >>> CODEXAI QUALITY GATE START >>>"
END_MARKER = "# <<< CODEXAI QUALITY GATE END <<<"


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_frontmatter(text: str) -> List[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    return normalized.split("\n")


def find_block(lines: List[str]) -> tuple[int, int] | None:
    try:
        start = lines.index(START_MARKER)
        end = lines.index(END_MARKER, start + 1)
    except ValueError:
        return None
    return start, end


def strip_managed_block(text: str) -> tuple[str, bool]:
    lines = split_frontmatter(text)
    block = find_block(lines)
    if block is None:
        normalized = normalize_text(text)
        if normalized and not normalized.endswith("\n"):
            normalized += "\n"
        return normalized, False

    start, end = block
    kept_lines = lines[:start] + lines[end + 1 :]
    while kept_lines and kept_lines[-1] == "":
        kept_lines.pop()

    cleaned = "\n".join(kept_lines)
    if cleaned:
        cleaned += "\n"
    return cleaned, True


def build_commands(skills_root: Path, with_lint_test: bool) -> List[Dict[str, str]]:
    scripts_dir = skills_root / "codex-execution-quality-gate" / "scripts"
    commands: List[Dict[str, str]] = [
        {
            "name": "security_scan",
            "script_path": scripts_dir.joinpath("security_scan.py").as_posix(),
            "failure_message": "❌ Security scan failed. Fix critical issues before committing.",
        },
        {
            "name": "pre_commit_check",
            "script_path": scripts_dir.joinpath("pre_commit_check.py").as_posix(),
            "failure_message": "❌ Pre-commit check failed.",
        },
    ]
    if with_lint_test:
        commands.append(
            {
                "name": "run_gate",
                "script_path": scripts_dir.joinpath("run_gate.py").as_posix(),
                "failure_message": "❌ Run gate failed.",
            }
        )
    return commands


def detect_checks_from_text(text: str) -> List[str]:
    checks: List[str] = []
    normalized = normalize_text(text)
    if "security_scan.py" in normalized:
        checks.append("security_scan")
    if "pre_commit_check.py" in normalized:
        checks.append("pre_commit_check")
    if "run_gate.py" in normalized:
        checks.append("run_gate")
    return checks


def build_managed_block(skills_root: Path, with_lint_test: bool) -> str:
    lines = [
        START_MARKER,
        'PYTHON_BIN="${PYTHON:-python}"',
        'if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then',
        '  PYTHON_BIN="python3"',
        "fi",
        'REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"',
        'cd "$REPO_ROOT" || exit 1',
        "",
    ]
    for command in build_commands(skills_root, with_lint_test):
        script_path = command["script_path"]
        lines.extend(
            [
                f'if ! "$PYTHON_BIN" "{script_path}" --project-root .; then',
                f"  printf '%s\\n' '{command['failure_message']}'",
                "  exit 1",
                "fi",
                "",
            ]
        )
    lines.append(END_MARKER)
    return "\n".join(lines)


def render_hook_content(existing_text: str, managed_block: str) -> str:
    base_text, _ = strip_managed_block(existing_text)
    body = base_text.rstrip("\n")
    if not body:
        return f"#!/bin/sh\n\n{managed_block}\n"
    return f"{body}\n\n{managed_block}\n"


def resolve_git_dir(project_root: Path) -> Path:
    if not project_root.exists():
        raise FileNotFoundError(f"Project root does not exist: {project_root}")

    command = ["git", "-C", str(project_root), "rev-parse", "--git-dir"]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError("Git is required to install hooks.") from exc

    if result.returncode == 0:
        git_dir = Path(result.stdout.strip())
        if not git_dir.is_absolute():
            git_dir = project_root / git_dir
        return git_dir.resolve()

    fallback = project_root / ".git"
    if fallback.is_dir():
        return fallback.resolve()

    raise RuntimeError(f"Unable to locate .git directory for: {project_root}")


def ensure_executable(path: Path) -> None:
    if os.name == "nt":
        return
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def build_report(status: str, hook_path: Path, checks: List[str], project_root: Path) -> Dict[str, object]:
    return {
        "status": status,
        "project_root": str(project_root),
        "hook_path": str(hook_path),
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Install CodexAI quality gate pre-commit hooks.")
    parser.add_argument("--project-root", required=True, help="Git project root that will receive the hook")
    parser.add_argument(
        "--with-lint-test",
        action="store_true",
        help="Also run run_gate.py for a heavier lint and test gate",
    )
    parser.add_argument("--uninstall", action="store_true", help="Remove the managed CodexAI hook block")
    parser.add_argument("--dry-run", action="store_true", help="Preview the hook changes without writing files")
    args = parser.parse_args()

    skills_root = Path(__file__).resolve().parent.parent.parent
    project_root = Path(args.project_root).expanduser().resolve()
    checks = [item["name"] for item in build_commands(skills_root, args.with_lint_test)]

    if args.dry_run:
        hook_path = project_root / ".git" / "hooks" / "pre-commit"
    else:
        try:
            git_dir = resolve_git_dir(project_root)
        except (FileNotFoundError, RuntimeError) as exc:
            print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
            return 1
        hook_path = git_dir / "hooks" / "pre-commit"

    if args.uninstall:
        existing_text = hook_path.read_text(encoding="utf-8", errors="ignore") if hook_path.exists() else ""
        existing_checks = detect_checks_from_text(existing_text)
        updated_text, removed = strip_managed_block(existing_text)
        status = "uninstalled" if removed else "not_installed"
        report = build_report(status, hook_path, existing_checks or checks, project_root)
        if args.dry_run:
            report["status"] = "dry_run"
            report["action"] = "uninstall"
            report["managed_block_present"] = removed
            print(json.dumps(report, indent=2))
            return 0

        if not hook_path.exists() or not removed:
            print(json.dumps(report, indent=2))
            return 0

        remaining = updated_text.strip()
        if remaining in {"", "#!/bin/sh", "#!/usr/bin/env sh"}:
            hook_path.unlink()
        else:
            hook_path.write_text(updated_text, encoding="utf-8", newline="\n")
            ensure_executable(hook_path)
        print(json.dumps(report, indent=2))
        return 0

    managed_block = build_managed_block(skills_root, args.with_lint_test)
    existing_text = hook_path.read_text(encoding="utf-8", errors="ignore") if hook_path.exists() else ""
    new_content = render_hook_content(existing_text, managed_block)
    report = build_report("installed", hook_path, checks, project_root)
    report["action"] = "install"
    report["managed_block_present"] = find_block(split_frontmatter(existing_text)) is not None

    if args.dry_run:
        report["status"] = "dry_run"
        report["preview"] = new_content
        print(json.dumps(report, indent=2))
        return 0

    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(new_content, encoding="utf-8", newline="\n")
    ensure_executable(hook_path)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
