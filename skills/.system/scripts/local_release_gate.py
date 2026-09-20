#!/usr/bin/env python3
"""Local pre-release gate: validators + optional ZIP build before tagging v*."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPT_DIR.parents[1]
PLUGIN_ROOT = SKILLS_ROOT.parent


def run_step(label: str, args: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    cmd = [sys.executable, *args]
    result = subprocess.run(
        cmd,
        cwd=str(cwd or PLUGIN_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"status": "unknown", "stdout_tail": result.stdout[-1500:], "stderr_tail": result.stderr[-1500:]}
    ok = result.returncode == 0 and payload.get("status") in {"pass", "dry_run", "generated", "warn"}
    return {
        "name": label,
        "ok": ok,
        "exit_code": result.returncode,
        "command": cmd,
        "payload": payload,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local release gate before tagging.")
    parser.add_argument("--project-root", default="", help="Plugin repo root (default: parent of skills/)")
    parser.add_argument("--skills-root", default="", help="Skills root (default: skills/ under project root)")
    parser.add_argument("--apply", action="store_true", help="Build release ZIP (default: dry-run only)")
    parser.add_argument("--no-write", action="store_true", help="Keep validators read-only (implied when --apply is omitted)")
    parser.add_argument("--target", choices=("none", "s3", "ssh"), default="none", help="Optional deploy target preview")
    parser.add_argument("--dry-run", action="store_true", help="For s3/ssh: print promotion commands only")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve() if args.project_root else PLUGIN_ROOT
    skills_root = Path(args.skills_root).expanduser().resolve() if args.skills_root else project_root / "skills"
    rel_skills = skills_root.relative_to(project_root).as_posix() if skills_root.is_relative_to(project_root) else str(skills_root)

    write_allowed = bool(args.apply) and not args.no_write
    audit_args = [
        str(SCRIPT_DIR / "audit_skill_pack.py"),
        "--skills-root",
        rel_skills,
        "--strict",
        "--format",
        "json",
    ]
    if not write_allowed:
        audit_args.append("--no-write")

    antigravity_tmp = tempfile.TemporaryDirectory()
    antigravity_out = Path(antigravity_tmp.name) / "antigravity-plugin"

    steps = [
        run_step(
            "pack_health",
            [
                str(SCRIPT_DIR / "check_pack_health.py"),
                "--skills-root",
                rel_skills,
                "--strict",
                "--format",
                "json",
            ],
            cwd=project_root,
        ),
        run_step(
            "tool_contracts",
            [
                str(SCRIPT_DIR / "validate_tool_contracts.py"),
                "--skills-root",
                rel_skills,
                "--strict",
                "--format",
                "json",
            ],
            cwd=project_root,
        ),
        run_step(
            "skill_capabilities",
            audit_args,
            cwd=project_root,
        ),
        run_step(
            "prompt_router_corpus",
            [
                str(SCRIPT_DIR / "prompt_router.py"),
                "--corpus",
                str((skills_root / ".system" / "references" / "prompt-router.corpus.json")),
                "--format",
                "json",
            ],
            cwd=project_root,
        ),
        run_step(
            "codex_plugin",
            [
                str(SCRIPT_DIR / "validate_codex_plugin.py"),
                "--plugin-root",
                str(project_root),
                "--strict",
                "--format",
                "json",
            ],
            cwd=project_root,
        ),
        run_step(
            "claude_plugin",
            [
                str(SCRIPT_DIR / "validate_claude_plugin.py"),
                "--plugin-root",
                str(project_root),
                "--format",
                "json",
            ],
            cwd=project_root,
        ),
        run_step(
            "antigravity_build",
            [
                str(SCRIPT_DIR / "build_antigravity_plugin.py"),
                "--plugin-root",
                str(project_root),
                "--output",
                str(antigravity_out),
                "--apply",
                "--format",
                "json",
            ],
            cwd=project_root,
        ),
        run_step(
            "antigravity_validate",
            [
                str(SCRIPT_DIR / "validate_antigravity_plugin.py"),
                "--package-dir",
                str(antigravity_out),
                "--format",
                "json",
            ],
            cwd=project_root,
        ),
        run_step(
            "release_zip",
            [
                str(SCRIPT_DIR / "build_release_zip.py"),
                "--project-root",
                str(project_root),
                "--exclude-tests",
                *(["--apply"] if write_allowed else ["--dry-run"]),
                "--format",
                "json",
            ],
            cwd=project_root,
        ),
    ]

    antigravity_tmp.cleanup()

    failures = [s for s in steps if not s["ok"]]
    zip_path = ""
    release_payload = steps[-1]["payload"]
    if isinstance(release_payload, dict):
        zip_path = str(release_payload.get("output", ""))

    deploy_preview: dict[str, Any] | None = None
    if args.target != "none" and zip_path:
        deploy_preview = run_step(
            "deploy_preview",
            [
                str(SCRIPT_DIR / "promote_deploy.py"),
                "--zip",
                zip_path,
                "--target",
                args.target,
                "--environment",
                "staging",
                *(["--dry-run"] if args.dry_run or not args.apply else []),
                "--format",
                "json",
            ],
            cwd=project_root,
        )
        if not deploy_preview["ok"] and not args.dry_run:
            failures.append(deploy_preview)

    report = {
        "status": "pass" if not failures else "fail",
        "project_root": str(project_root),
        "skills_root": str(skills_root),
        "steps": steps,
        "deploy_preview": deploy_preview,
        "ready_for_tag": not failures,
        "read_only": not write_allowed,
        "next": "git tag vX.Y.Z && git push origin vX.Y.Z" if not failures else "fix failing steps before tagging",
    }

    if args.format == "text":
        print(f"status={report['status']} ready_for_tag={report['ready_for_tag']}")
        for step in steps:
            print(f"- {step['name']}: {'ok' if step['ok'] else 'FAIL'}")
        if deploy_preview:
            print(f"- deploy_preview: {'ok' if deploy_preview['ok'] else 'FAIL'}")
        print(report["next"])
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
