#!/usr/bin/env python3
"""Unified local pipeline: one command that runs every plugin gate in a fixed order.

Stages (run in this order when selected):
  lint      pack health (strict) + core-rules drift check
  contracts tool contracts, capability audit, prompt-router corpus, Codex/Claude validators
  test      pytest suite + smoke_test.py
  build     Antigravity build/validate + release ZIP dry-run
  doctor    install.py doctor --host all

The same stages back the GitHub Actions `pipeline-selfcheck` job so local and CI stay aligned.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPT_DIR.parents[1]
PLUGIN_ROOT = SKILLS_ROOT.parent

STAGE_ORDER = ("lint", "contracts", "test", "build", "doctor")
PASS_STATUSES = {"pass", "dry_run", "generated", "warn", "ok", "built"}
SYMLINK_TEST = "test_project_traversal_does_not_follow_symlinks_outside_root"


def force_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def child_env() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return env


def symlinks_available() -> bool:
    """Windows without developer mode cannot create symlinks; mirror the CI exclusion."""
    if platform.system() != "Windows":
        return True
    try:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.write_text("x", encoding="utf-8")
            link = Path(tmp) / "link"
            os.symlink(target, link)
            return link.exists()
    except (OSError, NotImplementedError):
        return False


def run_step(
    name: str,
    args: list[str],
    *,
    cwd: Path,
    expect_json: bool = True,
    timeout: int = 900,
) -> dict[str, Any]:
    cmd = [sys.executable, *args]
    started = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env=child_env(),
        )
        exit_code = result.returncode
        stdout, stderr = result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = f"timeout after {timeout}s"
    duration = round(time.perf_counter() - started, 2)

    payload: dict[str, Any]
    if expect_json:
        try:
            parsed = json.loads(stdout)
            payload = parsed if isinstance(parsed, dict) else {"status": "unknown", "value": parsed}
        except json.JSONDecodeError:
            payload = {"status": "unknown", "stdout_tail": stdout[-1500:], "stderr_tail": stderr[-1500:]}
        ok = exit_code == 0 and str(payload.get("status", "")).lower() in PASS_STATUSES
    else:
        payload = {"status": "pass" if exit_code == 0 else "fail", "stdout_tail": stdout[-2000:], "stderr_tail": stderr[-1500:]}
        ok = exit_code == 0
    return {
        "name": name,
        "ok": ok,
        "exit_code": exit_code,
        "duration_s": duration,
        "command": cmd,
        "payload": payload,
    }


def script(name: str) -> str:
    return str(SCRIPT_DIR / name)


def stage_lint(project_root: Path, rel_skills: str) -> list[dict[str, Any]]:
    return [
        run_step(
            "pack_health",
            [script("check_pack_health.py"), "--skills-root", rel_skills, "--strict", "--format", "json"],
            cwd=project_root,
        ),
        run_step(
            "core_rules_drift",
            [script("init_agents_md.py"), "--repo-root", str(project_root), "--target", "all", "--check", "--format", "json"],
            cwd=project_root,
        ),
    ]


def stage_contracts(project_root: Path, rel_skills: str, skills_root: Path) -> list[dict[str, Any]]:
    corpus = skills_root / ".system" / "references" / "prompt-router.corpus.json"
    return [
        run_step(
            "tool_contracts",
            [script("validate_tool_contracts.py"), "--skills-root", rel_skills, "--strict", "--format", "json"],
            cwd=project_root,
        ),
        run_step(
            "skill_capabilities",
            [script("audit_skill_pack.py"), "--skills-root", rel_skills, "--strict", "--no-write", "--format", "json"],
            cwd=project_root,
        ),
        run_step(
            "prompt_router_corpus",
            [script("prompt_router.py"), "--corpus", str(corpus), "--format", "json"],
            cwd=project_root,
        ),
        run_step(
            "codex_plugin",
            [script("validate_codex_plugin.py"), "--plugin-root", str(project_root), "--strict", "--format", "json"],
            cwd=project_root,
        ),
        run_step(
            "claude_plugin",
            [script("validate_claude_plugin.py"), "--plugin-root", str(project_root), "--format", "json"],
            cwd=project_root,
        ),
    ]


def stage_test(project_root: Path, rel_skills: str, skills_root: Path) -> list[dict[str, Any]]:
    pytest_args = ["-m", "pytest", f"{rel_skills}/tests", "-q"]
    if not symlinks_available():
        pytest_args.extend(["-k", f"not {SYMLINK_TEST}"])
    return [
        run_step("pytest", pytest_args, cwd=project_root, expect_json=False, timeout=1800),
        run_step("smoke_test", [str(skills_root / "tests" / "smoke_test.py")], cwd=project_root, expect_json=False),
    ]


def stage_build(project_root: Path) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp:
        antigravity_out = Path(tmp) / "antigravity-plugin"
        steps.append(
            run_step(
                "antigravity_build",
                [
                    script("build_antigravity_plugin.py"),
                    "--plugin-root",
                    str(project_root),
                    "--output",
                    str(antigravity_out),
                    "--apply",
                    "--format",
                    "json",
                ],
                cwd=project_root,
            )
        )
        steps.append(
            run_step(
                "antigravity_validate",
                [script("validate_antigravity_plugin.py"), "--package-dir", str(antigravity_out), "--format", "json"],
                cwd=project_root,
            )
        )
    steps.append(
        run_step(
            "release_zip_dry_run",
            [script("build_release_zip.py"), "--project-root", str(project_root), "--exclude-tests", "--dry-run", "--format", "json"],
            cwd=project_root,
        )
    )
    return steps


def stage_doctor(project_root: Path) -> list[dict[str, Any]]:
    return [
        run_step(
            "install_doctor",
            [script("install.py"), "doctor", "--host", "all", "--repo-root", str(project_root), "--format", "json"],
            cwd=project_root,
        )
    ]


def parse_stages(raw: str, skip_tests: bool) -> list[str]:
    tokens = [token.strip() for token in raw.split(",") if token.strip()]
    if not tokens or "all" in tokens:
        selected = list(STAGE_ORDER)
    else:
        unknown = [token for token in tokens if token not in STAGE_ORDER]
        if unknown:
            raise ValueError(f"unknown stage(s): {', '.join(unknown)}; choose from {', '.join(STAGE_ORDER)} or all")
        selected = [stage for stage in STAGE_ORDER if stage in tokens]
    if skip_tests:
        selected = [stage for stage in selected if stage != "test"]
    return selected


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run_pipeline(project_root: Path, skills_root: Path, stages: list[str], fail_fast: bool = False) -> dict[str, Any]:
    rel_skills = skills_root.relative_to(project_root).as_posix() if skills_root.is_relative_to(project_root) else str(skills_root)
    runners: dict[str, Callable[[], list[dict[str, Any]]]] = {
        "lint": lambda: stage_lint(project_root, rel_skills),
        "contracts": lambda: stage_contracts(project_root, rel_skills, skills_root),
        "test": lambda: stage_test(project_root, rel_skills, skills_root),
        "build": lambda: stage_build(project_root),
        "doctor": lambda: stage_doctor(project_root),
    }
    started = time.perf_counter()
    stage_reports: list[dict[str, Any]] = []
    all_steps: list[dict[str, Any]] = []
    for stage in stages:
        steps = runners[stage]()
        stage_ok = all(step["ok"] for step in steps)
        stage_reports.append(
            {
                "name": stage,
                "ok": stage_ok,
                "duration_s": round(sum(step["duration_s"] for step in steps), 2),
                "steps": [step["name"] for step in steps],
            }
        )
        all_steps.extend(steps)
        if fail_fast and not stage_ok:
            break
    failures = [step["name"] for step in all_steps if not step["ok"]]
    skipped = [stage for stage in stages if stage not in {item["name"] for item in stage_reports}]
    return {
        "status": "pass" if not failures else "fail",
        "artifact_type": "codexai.pipeline.report",
        "schema_version": "1.0",
        "project_root": str(project_root),
        "skills_root": str(skills_root),
        "python": platform.python_version(),
        "platform": platform.system(),
        "stages": stage_reports,
        "stages_skipped": skipped,
        "steps": all_steps,
        "failures": failures,
        "duration_s": round(time.perf_counter() - started, 2),
        "next": "ready: run local_release_gate.py --apply then git tag vX.Y.Z" if not failures else f"fix failing step(s): {', '.join(failures)}",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the CodexAI plugin pipeline (lint, contracts, test, build, doctor).")
    parser.add_argument("--project-root", default="", help="Plugin repo root (default: parent of skills/)")
    parser.add_argument("--skills-root", default="", help="Skills root (default: skills/ under project root)")
    parser.add_argument("--stage", default="all", help="Comma-separated stages: lint,contracts,test,build,doctor or all")
    parser.add_argument("--skip-tests", action="store_true", help="Drop the test stage even when selected")
    parser.add_argument("--fail-fast", action="store_true", help="Stop after the first failing stage")
    parser.add_argument("--report-path", default="", help="Write the JSON report to this path (atomic)")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    force_utf8_stdio()
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve() if args.project_root else PLUGIN_ROOT
    skills_root = Path(args.skills_root).expanduser().resolve() if args.skills_root else project_root / "skills"
    try:
        stages = parse_stages(args.stage, args.skip_tests)
    except ValueError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    report = run_pipeline(project_root, skills_root, stages, fail_fast=args.fail_fast)
    if args.report_path:
        report_path = Path(args.report_path).expanduser().resolve()
        write_report(report_path, report)
        report["report_path"] = str(report_path)

    if args.format == "text":
        print(f"status={report['status']} duration={report['duration_s']}s stages={','.join(stages)}")
        for stage in report["stages"]:
            print(f"[{'ok' if stage['ok'] else 'FAIL'}] {stage['name']} ({stage['duration_s']}s)")
        for step in report["steps"]:
            marker = "ok" if step["ok"] else "FAIL"
            print(f"  - {step['name']}: {marker} exit={step['exit_code']} {step['duration_s']}s")
            if not step["ok"]:
                payload = step["payload"]
                detail = payload.get("stderr_tail") or payload.get("stdout_tail") or json.dumps(payload, ensure_ascii=False)[:800]
                print(f"    {str(detail).strip()[-800:]}")
        print(report["next"])
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
