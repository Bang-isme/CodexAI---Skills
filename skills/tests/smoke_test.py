#!/usr/bin/env python3
"""
Smoke test suite for Codex AI Skill Pack.
Run: python smoke_test.py [--verbose]
Verifies all entry-point scripts respond to --help and key scripts produce valid JSON output.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

SKILLS_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS: List[Tuple[str, str]] = [
    ("codex-docs-change-sync", "scripts/map_changes_to_docs.py"),
    ("codex-git-autopilot", "scripts/auto_commit.py"),
    ("codex-execution-quality-gate", "scripts/accessibility_check.py"),
    ("codex-execution-quality-gate", "scripts/bundle_check.py"),
    ("codex-execution-quality-gate", "scripts/doctor.py"),
    ("codex-execution-quality-gate", "scripts/editorial_review.py"),
    ("codex-execution-quality-gate", "scripts/lighthouse_audit.py"),
    ("codex-execution-quality-gate", "scripts/playwright_runner.py"),
    ("codex-execution-quality-gate", "scripts/pre_commit_check.py"),
    ("codex-execution-quality-gate", "scripts/predict_impact.py"),
    ("codex-execution-quality-gate", "scripts/output_guard.py"),
    ("codex-execution-quality-gate", "scripts/quality_trend.py"),
    ("codex-execution-quality-gate", "scripts/run_gate.py"),
    ("codex-execution-quality-gate", "scripts/security_scan.py"),
    ("codex-execution-quality-gate", "scripts/smart_test_selector.py"),
    ("codex-execution-quality-gate", "scripts/suggest_improvements.py"),
    ("codex-execution-quality-gate", "scripts/tech_debt_scan.py"),
    ("codex-execution-quality-gate", "scripts/ux_audit.py"),
    ("codex-execution-quality-gate", "scripts/with_server.py"),
    ("codex-project-memory", "scripts/analyze_patterns.py"),
    ("codex-project-memory", "scripts/build_knowledge_graph.py"),
    ("codex-project-memory", "scripts/compact_context.py"),
    ("codex-project-memory", "scripts/decision_logger.py"),
    ("codex-project-memory", "scripts/generate_changelog.py"),
    ("codex-project-memory", "scripts/generate_growth_report.py"),
    ("codex-project-memory", "scripts/generate_genome.py"),
    ("codex-project-memory", "scripts/generate_handoff.py"),
    ("codex-project-memory", "scripts/generate_session_summary.py"),
    ("codex-project-memory", "scripts/track_feedback.py"),
    ("codex-project-memory", "scripts/track_skill_usage.py"),
    ("codex-reasoning-rigor", "scripts/build_reasoning_brief.py"),
    ("codex-scrum-subagents", "scripts/generate_scrum_artifact.py"),
    ("codex-scrum-subagents", "scripts/install_scrum_subagents.py"),
    ("codex-scrum-subagents", "scripts/run_scrum_alias.py"),
    ("codex-scrum-subagents", "scripts/validate_scrum_agent_kit.py"),
    ("codex-workflow-autopilot", "scripts/explain_code.py"),
    ("codex-doc-renderer", "scripts/render_docx.py"),
]
JSON_CHECKS: List[Tuple[str, List[str]]] = [
    (
        "editorial_review",
        [
            "codex-execution-quality-gate/scripts/editorial_review.py",
            "--text",
            "# Review\nDecision: keep `skills/tests/test_output_rigor.py` in the suite.\nEvidence:\n- python skills/tests/smoke_test.py\nRisk: stale heuristics can drift from release quality.\nNext step: assign an owner to review failures after each gate change.",
            "--format",
            "json",
        ],
    ),
    (
        "output_guard",
        [
            "codex-execution-quality-gate/scripts/output_guard.py",
            "--text",
            "Decision: keep `skills/tests/test_output_rigor.py` in the suite.\nEvidence: run `python skills/tests/smoke_test.py`.\nRisk: false positives still need tuning.\nNext step: review failing heuristics.",
            "--format",
            "json",
        ],
    ),
    (
        "reasoning_brief",
        [
            "codex-reasoning-rigor/scripts/build_reasoning_brief.py",
            "--title",
            "Smoke test reasoning brief",
            "--goal",
            "Verify strict brief generation",
            "--constraints",
            "Keep output deterministic",
            "--non-goals",
            "Rewrite the skill pack",
            "--evidence",
            "pytest passes",
            "--signals",
            "smoke test exits zero",
            "--risks",
            "CLI drift",
            "--quality-bar",
            "Names exact files and runnable commands",
            "--format",
            "json",
        ],
    ),
    (
        "generate_scrum_artifact",
        [
            "codex-scrum-subagents/scripts/generate_scrum_artifact.py",
            "--template",
            "user-story",
            "--field",
            "title=Checkout validation",
            "--field",
            "persona=Store admin",
            "--field",
            "need=Validate checkout input",
            "--field",
            "outcome=Prevent invalid orders",
            "--field",
            "acceptance_criteria=- invalid addresses are rejected",
            "--field",
            "notes=- QA pairs on edge cases",
            "--format",
            "json",
        ],
    ),
    (
        "run_scrum_alias",
        [
            "codex-scrum-subagents/scripts/run_scrum_alias.py",
        ],
    ),
    (
        "install_scrum_subagents",
        [
            "codex-scrum-subagents/scripts/install_scrum_subagents.py",
        ],
    ),
    (
        "validate_scrum_agent_kit",
        [
            "codex-scrum-subagents/scripts/validate_scrum_agent_kit.py",
        ],
    ),
    (
        "run_gate",
        [
            "codex-execution-quality-gate/scripts/run_gate.py",
        ],
    ),
    (
        "quality_trend",
        [
            "codex-execution-quality-gate/scripts/quality_trend.py",
        ],
    ),
]


def run_help(script_path: Path) -> Tuple[bool, str]:
    command = [sys.executable, str(script_path), "--help"]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode == 0, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as exc:
        return False, str(exc)


def run_json_check(script_path: Path, args: List[str], cwd: Path, env: Dict[str, str] | None = None) -> Tuple[bool, str]:
    command = [sys.executable, str(script_path), *args]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=20,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd),
            env=env,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as exc:
        return False, str(exc)

    if result.returncode != 0:
        return False, result.stderr.strip() or result.stdout.strip() or "non-zero exit"

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return False, f"invalid json: {exc}"

    if payload.get("status") not in {"ok", "pass", "scaffold", "installed", "updated", "up_to_date", "diff", "report_ready", "recorded"}:
        return False, f"unexpected status: {payload.get('status')}"
    return True, ""


def check_skill_md() -> List[str]:
    failures = []
    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if skill_dir.is_dir() and skill_dir.name.startswith("codex-"):
            if not skill_md.exists():
                failures.append(f"Missing SKILL.md: {skill_dir.name}")
    return failures


def check_version() -> Tuple[bool, str]:
    version_file = SKILLS_ROOT / "VERSION"
    if not version_file.exists():
        return False, "VERSION file missing"
    content = version_file.read_text(encoding="utf-8").strip()
    if not content:
        return False, "VERSION file empty"
    return True, content


def check_workflow_routing_contract() -> Tuple[bool, str]:
    contract_path = (
        SKILLS_ROOT
        / "codex-workflow-autopilot"
        / "references"
        / "workflow-routing-contract.json"
    )
    if not contract_path.exists():
        return False, "workflow-routing-contract.json missing"
    try:
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"invalid json: {exc}"
    required_top_level = {"version", "modes", "workflow_types", "overlays", "output_contract"}
    if not required_top_level.issubset(payload):
        return False, "missing required top-level keys"
    output_contract = payload.get("output_contract", {})
    if not isinstance(output_contract, dict):
        return False, "output_contract must be an object"
    required_fields = output_contract.get("required_fields")
    if not isinstance(required_fields, list) or "coordination_overlay" not in required_fields or "ceremony" not in required_fields:
        return False, "output contract missing scrum-aware fields"
    overlays = payload.get("overlays", {})
    if not isinstance(overlays, dict) or "scrum" not in overlays or "reasoning_rigor" not in overlays:
        return False, "missing scrum/reasoning overlays"
    return True, "workflow routing contract ok"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test for Codex AI Skill Pack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run from any directory. Tests all scripts and SKILL.md presence.",
    )
    parser.add_argument("--verbose", action="store_true", help="Show details for passing tests")
    args = parser.parse_args()

    total = 0
    passed = 0
    failed = 0
    results: List[Dict[str, object]] = []

    # 1. VERSION check
    total += 1
    ver_ok, ver_msg = check_version()
    if ver_ok:
        passed += 1
        if args.verbose:
            print(f"  PASS  VERSION = {ver_msg}")
    else:
        failed += 1
        print(f"  FAIL  VERSION: {ver_msg}")

    # 2. SKILL.md presence
    skill_failures = check_skill_md()
    total += 1
    if not skill_failures:
        passed += 1
        if args.verbose:
            print("  PASS  All codex-* skills have SKILL.md")
    else:
        failed += 1
        for failure in skill_failures:
            print(f"  FAIL  {failure}")

    # 3. workflow routing contract
    total += 1
    contract_ok, contract_msg = check_workflow_routing_contract()
    if contract_ok:
        passed += 1
        if args.verbose:
            print(f"  PASS  {contract_msg}")
    else:
        failed += 1
        print(f"  FAIL  workflow routing contract: {contract_msg}")

    # 4. --help for each script
    for skill_name, script_rel in SCRIPTS:
        script_path = SKILLS_ROOT / skill_name / script_rel
        total += 1
        if not script_path.exists():
            failed += 1
            print(f"  FAIL  {skill_name}/{script_rel} - file not found")
            continue

        ok, err = run_help(script_path)
        if ok:
            passed += 1
            if args.verbose:
                print(f"  PASS  {skill_name}/{script_rel} --help")
        else:
            failed += 1
            print(f"  FAIL  {skill_name}/{script_rel} --help - {err}")

    # 5. JSON output for critical CLI paths
    for label, command_spec in JSON_CHECKS:
        total += 1
        rel_script, *args_list = command_spec
        script_path = SKILLS_ROOT / rel_script
        if not script_path.exists():
            failed += 1
            print(f"  FAIL  {label} json - file not found")
            continue

        if label == "run_scrum_alias":
            with tempfile.TemporaryDirectory() as temp_dir:
                artifact_path = Path(temp_dir) / "story.md"
                dynamic_args = [
                    "--alias",
                    "$story-ready-check",
                    "--artifact-output",
                    str(artifact_path),
                    "--field",
                    "title=Checkout validation",
                    "--field",
                    "persona=Store admin",
                    "--field",
                    "need=Validate checkout input",
                    "--field",
                    "outcome=Prevent invalid orders",
                    "--field",
                    "acceptance_criteria=- invalid addresses are rejected",
                    "--field",
                    "notes=- QA pairs on edge cases",
                    "--format",
                    "json",
                ]
                ok, err = run_json_check(script_path, dynamic_args, SKILLS_ROOT)
        elif label == "install_scrum_subagents":
            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir) / "project"
                project_root.mkdir(parents=True, exist_ok=True)
                fake_home = Path(temp_dir) / "fake-home"
                fake_home.mkdir(parents=True, exist_ok=True)
                env = os.environ.copy()
                env["USERPROFILE"] = str(fake_home)
                env["HOME"] = str(fake_home)
                dynamic_args = [
                    "--target-root",
                    str(project_root),
                    "--install-dir",
                    ".meta/.agent",
                    "--native-scope",
                    "both",
                    "--format",
                    "json",
                ]
                ok, err = run_json_check(script_path, dynamic_args, SKILLS_ROOT, env=env)
        elif label == "validate_scrum_agent_kit":
            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir) / "project"
                project_root.mkdir(parents=True, exist_ok=True)
                fake_home = Path(temp_dir) / "fake-home"
                fake_home.mkdir(parents=True, exist_ok=True)
                env = os.environ.copy()
                env["USERPROFILE"] = str(fake_home)
                env["HOME"] = str(fake_home)
                install_script = SKILLS_ROOT / "codex-scrum-subagents" / "scripts" / "install_scrum_subagents.py"
                install_result = subprocess.run(
                    [
                        sys.executable,
                        str(install_script),
                        "--target-root",
                        str(project_root),
                        "--install-dir",
                        ".meta/.agent",
                        "--native-scope",
                        "both",
                        "--format",
                        "json",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    encoding="utf-8",
                    errors="replace",
                    cwd=str(SKILLS_ROOT),
                    env=env,
                    check=False,
                )
                if install_result.returncode != 0:
                    ok, err = False, install_result.stderr.strip() or install_result.stdout.strip() or "install failed"
                else:
                    dynamic_args = [
                        "--install-root",
                        str(project_root / ".meta" / ".agent"),
                        "--native-scope",
                        "both",
                        "--format",
                        "json",
                    ]
                    ok, err = run_json_check(script_path, dynamic_args, SKILLS_ROOT, env=env)
        elif label == "run_gate":
            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                output_file = project_root / "handoff.md"
                (project_root / "skills" / "tests").mkdir(parents=True, exist_ok=True)
                (project_root / "skills" / "tests" / "smoke_test.py").write_text("print('ok')\n", encoding="utf-8")
                output_file.write_text(
                    "\n".join(
                        [
                            "Decision: keep `skills/tests/smoke_test.py` in the gate.",
                            "Evidence: run `python skills/tests/smoke_test.py` before handoff.",
                            "Risk: stale paths can drift from the repo.",
                            "Next step: keep the smoke entry current.",
                        ]
                    ),
                    encoding="utf-8",
                )
                dynamic_args = [
                    "--project-root",
                    str(project_root),
                    "--skip-lint",
                    "--skip-test",
                    "--strict-output",
                    "--output-file",
                    str(output_file),
                ]
                ok, err = run_json_check(script_path, dynamic_args, project_root)
        elif label == "quality_trend":
            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                quality_dir = project_root / ".codex" / "quality"
                snapshots_dir = quality_dir / "snapshots"
                snapshots_dir.mkdir(parents=True, exist_ok=True)
                (snapshots_dir / "2026-03-17.json").write_text(
                    json.dumps(
                        {
                            "date": "2026-03-17",
                            "metrics": {
                                "total_code_files": 5,
                                "total_lines": 50,
                                "avg_file_lines": 10.0,
                                "avg_functions_per_file": 1.0,
                                "todo_count": 2,
                                "long_functions": 0,
                                "long_files": 0,
                                "test_files": 1,
                                "test_to_source_ratio": 0.25,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                (snapshots_dir / "2026-03-18.json").write_text(
                    json.dumps(
                        {
                            "date": "2026-03-18",
                            "metrics": {
                                "total_code_files": 5,
                                "total_lines": 50,
                                "avg_file_lines": 10.0,
                                "avg_functions_per_file": 1.0,
                                "todo_count": 1,
                                "long_functions": 0,
                                "long_files": 0,
                                "test_files": 2,
                                "test_to_source_ratio": 0.5,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                (quality_dir / "gate-events.jsonl").write_text(
                    "\n".join(
                        [
                            json.dumps(
                                {
                                    "timestamp": "2026-03-17T10:00:00+00:00",
                                    "gate_passed": True,
                                    "strict_output_effective": True,
                                    "deliverable_kind": "plan",
                                    "output_guard_status": "pass",
                                    "output_guard_score": 78,
                                }
                            ),
                            json.dumps(
                                {
                                    "timestamp": "2026-03-18T10:00:00+00:00",
                                    "gate_passed": True,
                                    "strict_output_effective": True,
                                    "deliverable_kind": "handoff",
                                    "output_guard_status": "pass",
                                    "output_guard_score": 82,
                                }
                            ),
                        ]
                    )
                    + "\n",
                    encoding="utf-8",
                )
                dynamic_args = [
                    "--project-root",
                    str(project_root),
                    "--report",
                    "--days",
                    "30",
                ]
                ok, err = run_json_check(script_path, dynamic_args, project_root)
        else:
            ok, err = run_json_check(script_path, args_list, SKILLS_ROOT)

        if ok:
            passed += 1
            if args.verbose:
                print(f"  PASS  {label} json")
        else:
            failed += 1
            print(f"  FAIL  {label} json - {err}")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Smoke Test Results: {passed}/{total} passed, {failed} failed")
    print(f"{'=' * 50}")

    payload = {
        "status": "pass" if failed == 0 else "fail",
        "total": total,
        "passed": passed,
        "failed": failed,
    }
    print(json.dumps(payload, indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
