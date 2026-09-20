from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"
PIPELINE = SKILLS_ROOT / ".system" / "scripts" / "pipeline.py"


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pipeline = load_script_module("codexai_pipeline_under_test", ".system/scripts/pipeline.py")


def test_stage_registry_is_ordered_and_parses_selections() -> None:
    assert pipeline.STAGE_ORDER == ("lint", "contracts", "test", "build", "doctor")
    assert pipeline.parse_stages("all", skip_tests=False) == list(pipeline.STAGE_ORDER)
    assert pipeline.parse_stages("doctor,lint", skip_tests=False) == ["lint", "doctor"]
    assert pipeline.parse_stages("all", skip_tests=True) == ["lint", "contracts", "build", "doctor"]
    assert pipeline.parse_stages("test", skip_tests=True) == []
    with pytest.raises(ValueError):
        pipeline.parse_stages("lint,nope", skip_tests=False)


def test_run_step_reports_json_status_and_exit_code(tmp_path: Path) -> None:
    ok_script = tmp_path / "ok.py"
    ok_script.write_text("import json; print(json.dumps({'status': 'pass'}))\n", encoding="utf-8")
    fail_script = tmp_path / "fail.py"
    fail_script.write_text("import json, sys; print(json.dumps({'status': 'fail', 'why': 'x'})); sys.exit(1)\n", encoding="utf-8")
    text_script = tmp_path / "text.py"
    text_script.write_text("print('plain output'); raise SystemExit(0)\n", encoding="utf-8")

    ok = pipeline.run_step("ok", [str(ok_script)], cwd=tmp_path)
    assert ok["ok"] is True and ok["exit_code"] == 0 and ok["payload"]["status"] == "pass"
    failed = pipeline.run_step("fail", [str(fail_script)], cwd=tmp_path)
    assert failed["ok"] is False and failed["exit_code"] == 1 and failed["payload"]["why"] == "x"
    plain = pipeline.run_step("text", [str(text_script)], cwd=tmp_path, expect_json=False)
    assert plain["ok"] is True and "plain output" in plain["payload"]["stdout_tail"]
    exit_zero_but_fail = tmp_path / "soft.py"
    exit_zero_but_fail.write_text("import json; print(json.dumps({'status': 'fail'}))\n", encoding="utf-8")
    soft = pipeline.run_step("soft", [str(exit_zero_but_fail)], cwd=tmp_path)
    assert soft["ok"] is False, "a JSON status of fail must fail the step even when exit code is 0"


def test_run_pipeline_fail_fast_and_report_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_stage(name: str, ok: bool):
        def runner(*_args, **_kwargs):
            calls.append(name)
            return [{"name": f"{name}_step", "ok": ok, "exit_code": 0 if ok else 1, "duration_s": 0.01, "command": [], "payload": {}}]

        return runner

    monkeypatch.setattr(pipeline, "stage_lint", fake_stage("lint", True))
    monkeypatch.setattr(pipeline, "stage_contracts", fake_stage("contracts", False))
    monkeypatch.setattr(pipeline, "stage_test", fake_stage("test", True))
    monkeypatch.setattr(pipeline, "stage_build", fake_stage("build", True))
    monkeypatch.setattr(pipeline, "stage_doctor", fake_stage("doctor", True))

    report = pipeline.run_pipeline(tmp_path, tmp_path / "skills", list(pipeline.STAGE_ORDER), fail_fast=True)
    assert report["status"] == "fail"
    assert report["failures"] == ["contracts_step"]
    assert calls == ["lint", "contracts"]
    assert report["stages_skipped"] == ["test", "build", "doctor"]
    assert report["artifact_type"] == "codexai.pipeline.report"
    assert report["schema_version"] == "1.0"
    for key in ("status", "project_root", "stages", "steps", "duration_s", "next", "python", "platform"):
        assert key in report
    assert "contracts_step" in report["next"]

    calls.clear()
    full = pipeline.run_pipeline(tmp_path, tmp_path / "skills", list(pipeline.STAGE_ORDER), fail_fast=False)
    assert calls == list(pipeline.STAGE_ORDER)
    assert full["stages_skipped"] == []
    assert [stage["ok"] for stage in full["stages"]] == [True, False, True, True, True]

    out = tmp_path / "reports" / "pipeline.json"
    pipeline.write_report(out, full)
    assert json.loads(out.read_text(encoding="utf-8"))["status"] == "fail"
    assert [path.name for path in out.parent.iterdir()] == ["pipeline.json"]


def test_cli_rejects_unknown_stage_with_exit_2() -> None:
    result = subprocess.run(
        [sys.executable, str(PIPELINE), "--stage", "bogus", "--format", "json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert "bogus" in payload["message"]


def test_pipeline_registered_in_tools_registry_and_aliases() -> None:
    tools = json.loads((SKILLS_ROOT / ".system" / "references" / "plugin-tools.json").read_text(encoding="utf-8"))["tools"]
    entry = next(tool for tool in tools if tool["name"] == "pipeline_run")
    assert entry["script"] == ".system/scripts/pipeline.py"
    assert entry["kind"] == "release"
    props = entry["args_schema"]["properties"]
    for field in ("stage", "skip_tests", "fail_fast", "report_path", "format"):
        assert field in props
    assert entry["safety_policy"]["reads_secrets"] is False

    aliases = json.loads((SKILLS_ROOT / ".system" / "references" / "aliases.json").read_text(encoding="utf-8"))
    short = {row["alias"]: row for row in aliases["short"]}
    assert short["$pipeline"]["command"].startswith("pipeline.py")
    assert "$pipeline" in (SKILLS_ROOT / "codex-master-instructions" / "SKILL.md").read_text(encoding="utf-8")


def test_registry_lists_every_system_script() -> None:
    registry = (SKILLS_ROOT / ".system" / "REGISTRY.md").read_text(encoding="utf-8")
    scripts_dir = SKILLS_ROOT / ".system" / "scripts"
    missing = sorted(
        path.name
        for path in scripts_dir.glob("*.py")
        if not path.name.startswith("_") and f"`{path.name}`" not in registry
    )
    assert missing == [], f"REGISTRY.md is missing .system scripts: {missing}"


def test_runbook_and_docs_describe_pipeline() -> None:
    runbook = (SKILLS_ROOT / ".system" / "OPERATION_RUNBOOK.md").read_text(encoding="utf-8")
    deploy_doc = (SKILLS_ROOT / ".system" / "references" / "deploy-promotion.md").read_text(encoding="utf-8")
    assert "pipeline.py" in runbook
    assert "release.yml" in runbook and "tag" in runbook
    assert "pipeline_run" in deploy_doc
