#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


auto_gate = load_script_module(
    "skills_auto_gate",
    "codex-execution-quality-gate/scripts/auto_gate.py",
)


def make_result(payload, blocking=None, warnings=None):
    return {
        "payload": payload,
        "blocking_issues": blocking or [],
        "warnings": warnings or [],
    }


def test_auto_gate_quick_mode_passes_and_collects_warnings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "security",
        lambda project_root: make_result(
            {"status": "pass", "critical": 0, "warnings": 2, "summary": "0 critical, 2 warnings found"},
            warnings=["2 security warning(s)."],
        ),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "pre_commit",
        lambda project_root: make_result(
            {
                "status": "pass",
                "staged_files": 1,
                "checks_run": 3,
                "checks_skipped": 1,
                "lint": "pass",
                "test": "pass",
                "warnings": 0,
                "summary": "All staged checks passed.",
            }
        ),
    )

    report, exit_code = auto_gate.run_auto_gate(tmp_path, "quick")
    assert exit_code == 0
    assert report["overall"] == "pass"
    assert report["checks"]["security"]["warnings"] == 2
    assert report["checks"]["pre_commit"]["lint"] == "pass"
    assert report["warnings"] == ["2 security warning(s)."]


def test_auto_gate_surfaces_runtime_hook_readiness_warnings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "runtime_hook",
        lambda project_root: make_result(
            {
                "status": "warn",
                "overall": "warn",
                "detected_domains": ["frontend"],
                "suggested_agent": "frontend-specialist",
                "missing_readiness": 2,
                "recommended_commands": ["$init-docs"],
                "summary": "Runtime hook advisory check completed.",
            },
            warnings=["Runtime hook found 2 readiness gap(s)."],
        ),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "security",
        lambda project_root: make_result({"status": "pass", "critical": 0, "warnings": 0, "summary": "ok"}),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "pre_commit",
        lambda project_root: make_result(
            {
                "status": "pass",
                "staged_files": 0,
                "checks_run": 0,
                "checks_skipped": 0,
                "lint": "skip",
                "test": "skip",
                "warnings": 0,
                "summary": "no files staged",
            }
        ),
    )

    report, exit_code = auto_gate.run_auto_gate(tmp_path, "quick")

    assert exit_code == 0
    assert report["overall"] == "pass"
    assert "Runtime hook found 2 readiness gap(s)." in report["warnings"]


def test_auto_gate_full_mode_blocks_on_gate_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "security",
        lambda project_root: make_result({"status": "pass", "critical": 0, "warnings": 0, "summary": "ok"}),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "gate",
        lambda project_root: make_result(
            {"status": "fail", "lint": "fail", "test": "pass", "blocking_issues": 1, "warnings": 0},
            blocking=["Lint check failed with exit code 1."],
        ),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "tech_debt",
        lambda project_root: make_result(
            {"status": "warn", "total_issues": 4, "warnings": 0, "summary": "4 issues found"},
            warnings=["4 tech debt signal(s) detected."],
        ),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "role_docs",
        lambda project_root: make_result(
            {"status": "pass", "overall": "pass", "missing_docs": 0, "stale_docs": 0, "suggested_updates": 0}
        ),
    )

    report, exit_code = auto_gate.run_auto_gate(tmp_path, "full")
    assert exit_code == 1
    assert report["overall"] == "fail"
    assert report["blocking_issues"] == ["Lint check failed with exit code 1."]
    assert "4 tech debt signal(s) detected." in report["warnings"]


def test_auto_gate_deploy_mode_keeps_advisory_checks_non_blocking(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "security",
        lambda project_root: make_result({"status": "pass", "critical": 0, "warnings": 0, "summary": "ok"}),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "gate",
        lambda project_root: make_result({"status": "pass", "lint": "pass", "test": "pass", "blocking_issues": 0, "warnings": 0}),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "tech_debt",
        lambda project_root: make_result({"status": "pass", "total_issues": 0, "warnings": 0, "summary": "clean"}),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "role_docs",
        lambda project_root: make_result(
            {"status": "pass", "overall": "pass", "missing_docs": 0, "stale_docs": 0, "suggested_updates": 0}
        ),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "bundle",
        lambda project_root: make_result(
            {"status": "warn", "package_manager": "npm", "total_dependencies": 12, "large_packages": 1, "warnings": 1},
            warnings=["Bundle check reported 1 warning(s)."],
        ),
    )
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "suggestions",
        lambda project_root: make_result(
            {"status": "warn", "suggestions": 2, "changed_files_scanned": 3, "summary": "2 suggestions"},
            warnings=["2 improvement suggestion(s) generated."],
        ),
    )

    report, exit_code = auto_gate.run_auto_gate(tmp_path, "deploy")
    assert exit_code == 0
    assert report["overall"] == "pass"
    assert report["checks"]["bundle"]["status"] == "warn"
    assert report["checks"]["suggestions"]["suggestions"] == 2
    assert "Bundle check reported 1 warning(s)." in report["warnings"]
    assert "2 improvement suggestion(s) generated." in report["warnings"]
