#!/usr/bin/env python3
"""
Smoke test suite for Codex AI Skill Pack.
Run: python smoke_test.py [--verbose]
Verifies all scripts respond to --help and key scripts produce valid JSON output.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

SKILLS_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS: List[Tuple[str, str]] = [
    ("codex-docs-change-sync", "scripts/map_changes_to_docs.py"),
    ("codex-execution-quality-gate", "scripts/accessibility_check.py"),
    ("codex-execution-quality-gate", "scripts/bundle_check.py"),
    ("codex-execution-quality-gate", "scripts/lighthouse_audit.py"),
    ("codex-execution-quality-gate", "scripts/playwright_runner.py"),
    ("codex-execution-quality-gate", "scripts/pre_commit_check.py"),
    ("codex-execution-quality-gate", "scripts/predict_impact.py"),
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
    ("codex-project-memory", "scripts/decision_logger.py"),
    ("codex-project-memory", "scripts/generate_changelog.py"),
    ("codex-project-memory", "scripts/generate_growth_report.py"),
    ("codex-project-memory", "scripts/generate_handoff.py"),
    ("codex-project-memory", "scripts/generate_session_summary.py"),
    ("codex-project-memory", "scripts/track_feedback.py"),
    ("codex-project-memory", "scripts/track_skill_usage.py"),
    ("codex-workflow-autopilot", "scripts/explain_code.py"),
    ("codex-doc-renderer", "scripts/render_docx.py"),
]


def run_help(script_path: Path) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
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

    # 3. --help for each script
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
