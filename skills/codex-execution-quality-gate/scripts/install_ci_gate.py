#!/usr/bin/env python3
"""Generate CodexAI quality gate CI configuration."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


START_MARKER = "# >>> CODEXAI QUALITY GATE START >>>"
END_MARKER = "# <<< CODEXAI QUALITY GATE END <<<"
SKILLS_REPO_URL = "https://github.com/Bang-isme/CodexAI---Skills.git"


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def remove_managed_block(text: str) -> str:
    normalized = normalize_text(text)
    start = normalized.find(START_MARKER)
    if start == -1:
        if normalized and not normalized.endswith("\n"):
            normalized += "\n"
        return normalized
    end = normalized.find(END_MARKER, start)
    if end == -1:
        if normalized and not normalized.endswith("\n"):
            normalized += "\n"
        return normalized
    end += len(END_MARKER)
    while end < len(normalized) and normalized[end] == "\n":
        end += 1
    cleaned = (normalized[:start] + normalized[end:]).rstrip("\n")
    if cleaned:
        cleaned += "\n"
    return cleaned


def github_workflow() -> str:
    return f"""name: CodexAI Quality Gate
on: [push, pull_request]
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Resolve CodexAI Skills
        shell: bash
        run: |
          if [ -d ".codex/skills" ]; then
            echo "CODEX_SKILLS_ROOT=$PWD/.codex/skills" >> "$GITHUB_ENV"
          else
            git clone --depth 1 {SKILLS_REPO_URL} "$RUNNER_TEMP/codexai-skills"
            echo "CODEX_SKILLS_ROOT=$RUNNER_TEMP/codexai-skills/skills" >> "$GITHUB_ENV"
          fi
      - name: Security Scan
        run: python "$CODEX_SKILLS_ROOT/codex-execution-quality-gate/scripts/security_scan.py" --project-root .
      - name: Run Gate
        run: python "$CODEX_SKILLS_ROOT/codex-execution-quality-gate/scripts/run_gate.py" --project-root .
"""


def write_github_workflow(output_path: Path, force: bool) -> None:
    if output_path.exists():
        existing_text = output_path.read_text(encoding="utf-8", errors="ignore")
        if "CodexAI Quality Gate" not in existing_text and not force:
            raise FileExistsError(
                f"Refusing to overwrite existing workflow without --force: {output_path}"
            )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(github_workflow(), encoding="utf-8", newline="\n")


def gitlab_block() -> str:
    return f"""{START_MARKER}
codex_quality_gate:
  image: python:3.11
  stage: test
  before_script:
    - |
      if [ -d ".codex/skills" ]; then
        export CODEX_SKILLS_ROOT="$PWD/.codex/skills"
      else
        git clone --depth 1 {SKILLS_REPO_URL} /tmp/codexai-skills
        export CODEX_SKILLS_ROOT="/tmp/codexai-skills/skills"
      fi
  script:
    - python "$CODEX_SKILLS_ROOT/codex-execution-quality-gate/scripts/security_scan.py" --project-root .
    - python "$CODEX_SKILLS_ROOT/codex-execution-quality-gate/scripts/run_gate.py" --project-root .
  only:
    - branches
    - merge_requests
{END_MARKER}
"""


def merge_gitlab_content(existing_text: str) -> str:
    cleaned = remove_managed_block(existing_text).rstrip("\n")
    block = gitlab_block().rstrip("\n")
    if not cleaned:
        return f"{block}\n"
    return f"{cleaned}\n\n{block}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CodexAI quality gate CI configuration.")
    parser.add_argument("--project-root", required=True, help="Project root that will receive the CI file")
    parser.add_argument("--ci", required=True, choices=("github", "gitlab"), help="CI platform to generate")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing non-CodexAI GitHub workflow file")
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists():
        print(json.dumps({"status": "error", "message": f"Project root does not exist: {project_root}"}, indent=2))
        return 1
    if not project_root.is_dir():
        print(json.dumps({"status": "error", "message": f"Project root is not a directory: {project_root}"}, indent=2))
        return 1

    try:
        if args.ci == "github":
            output_path = project_root / ".github" / "workflows" / "quality-gate.yml"
            write_github_workflow(output_path, args.force)
        else:
            output_path = project_root / ".gitlab-ci.yml"
            existing_text = output_path.read_text(encoding="utf-8", errors="ignore") if output_path.exists() else ""
            output_path.write_text(merge_gitlab_content(existing_text), encoding="utf-8", newline="\n")
    except OSError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "status": "generated",
                "path": str(output_path),
                "ci_platform": args.ci,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
