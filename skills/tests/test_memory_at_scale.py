from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"
SCALE_GATE = SKILLS_ROOT / "codex-project-memory" / "scripts" / "run_scale_gate.py"
FIXTURE_GEN = SKILLS_ROOT / "codex-project-memory" / "scripts" / "generate_scale_fixture.py"


def test_generate_scale_fixture_creates_expected_file_count(tmp_path: Path) -> None:
    root = tmp_path / "fixture"
    result = subprocess.run(
        [
            sys.executable,
            str(FIXTURE_GEN),
            "--output-dir",
            str(root),
            "--file-count",
            "25",
            "--seed",
            "7",
            "--include-package-json",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "generated"
    assert payload.get("polyglot") is True
    extension_counts = payload.get("extension_counts", {})
    assert len(extension_counts) >= 4
    assert ".py" in extension_counts and ".js" in extension_counts
    source_files = [p for p in root.rglob("*") if p.is_file() and p.name != "package.json"]
    assert len(source_files) >= 25
    assert (root / "package.json").exists()
    assert (root / "tsconfig.json").exists()


def test_polyglot_fixture_indexes_multiple_language_parsers(tmp_path: Path) -> None:
    root = tmp_path / "polyglot"
    subprocess.run(
        [
            sys.executable,
            str(FIXTURE_GEN),
            "--output-dir",
            str(root),
            "--file-count",
            "40",
            "--seed",
            "99",
            "--include-package-json",
            "--format",
            "json",
        ],
        check=True,
        timeout=60,
    )
    index_cli = subprocess.run(
        [
            sys.executable,
            str(SKILLS_ROOT / "codex-project-memory/scripts/build_knowledge_index.py"),
            "--project-root",
            str(root),
            "--incremental",
            "--max-files",
            "200",
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    assert index_cli.returncode == 0, index_cli.stderr
    index_path = root / ".codex" / "knowledge" / "codebase-index.json"
    index_doc = json.loads(index_path.read_text(encoding="utf-8"))
    parsers = {meta.get("parser") for meta in index_doc.get("files", {}).values() if isinstance(meta, dict)}
    assert "regex-python-symbols" in parsers
    assert "regex-js-ts-symbols" in parsers


def load_scale_gate_module():
    spec = importlib.util.spec_from_file_location("run_scale_gate_test", SCALE_GATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scale_gate_refuses_unsafe_project_root_deletion(tmp_path: Path) -> None:
    gate = load_scale_gate_module()
    victim = tmp_path / "real-project"
    victim.mkdir()
    (victim / "important.txt").write_text("keep me\n", encoding="utf-8")

    report = gate.run_gate(
        project_root=victim,
        file_count=5,
        max_files=50,
        budget_seconds=60,
        tier="medium",
        seed=1,
        require_graph=False,
        keep_fixture=False,
    )

    assert report["status"] == "fail"
    assert victim.exists()
    assert (victim / "important.txt").read_text(encoding="utf-8") == "keep me\n"
    assert any("refusing to delete" in item for item in report.get("failures", []))


def test_scale_gate_allows_named_fixture_root(tmp_path: Path) -> None:
    gate = load_scale_gate_module()
    fixture = tmp_path / ".scale-gate-test"
    fixture.mkdir()
    (fixture / "old.txt").write_text("stale\n", encoding="utf-8")

    report = gate.run_gate(
        project_root=fixture,
        file_count=5,
        max_files=50,
        budget_seconds=120,
        tier="medium",
        seed=2,
        require_graph=False,
        keep_fixture=False,
    )

    assert (fixture / ".scale-gate-fixture").is_file()
    assert not any("refusing to delete" in item for item in report.get("failures", []))
    assert not (fixture / "old.txt").exists()


def test_run_scale_gate_small_fixture(tmp_path: Path) -> None:
    if os.environ.get("RUN_SCALE_GATE") != "1":
        import pytest

        pytest.skip("Set RUN_SCALE_GATE=1 to run full scale gate locally")
    project = tmp_path / ".scale-gate-local-smoke"
    report_path = tmp_path / "scale-gate-report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCALE_GATE),
            "--project-root",
            str(project),
            "--tier",
            "medium",
            "--file-count",
            "150",
            "--max-files",
            "500",
            "--budget-seconds",
            "300",
            "--report-path",
            str(report_path),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["incremental_reused"] > 0
    assert report["within_budget"] is True
