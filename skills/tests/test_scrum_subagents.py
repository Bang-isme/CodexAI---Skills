#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_SCRIPT = SKILLS_ROOT / "codex-scrum-subagents" / "scripts" / "install_scrum_subagents.py"
VALIDATOR_SCRIPT = SKILLS_ROOT / "codex-scrum-subagents" / "scripts" / "validate_scrum_agent_kit.py"


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_installer_cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INSTALLER_SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
        env=env,
    )


def run_validator_cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR_SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
        env=env,
    )


installer = load_script_module(
    "skills_install_scrum_subagents",
    "codex-scrum-subagents/scripts/install_scrum_subagents.py",
)
helper = load_script_module(
    "skills_scrum_agent_kit_helper",
    "codex-scrum-subagents/scripts/_scrum_agent_kit.py",
)
validator = load_script_module(
    "skills_validate_scrum_agent_kit",
    "codex-scrum-subagents/scripts/validate_scrum_agent_kit.py",
)
artifact_generator = load_script_module(
    "skills_generate_scrum_artifact",
    "codex-scrum-subagents/scripts/generate_scrum_artifact.py",
)
alias_runner = load_script_module(
    "skills_run_scrum_alias",
    "codex-scrum-subagents/scripts/run_scrum_alias.py",
)


def test_collect_bundle_stats_counts_bundle_files() -> None:
    stats = helper.collect_bundle_stats(installer.BUNDLE_ROOT)
    assert stats.agent_files == 10
    assert stats.workflow_files == 7
    assert stats.service_files == 3
    assert stats.native_agent_files == 10
    assert stats.total_files == 32


def test_missing_required_paths_ok_for_bundled_kit() -> None:
    assert helper.missing_required_paths(installer.BUNDLE_ROOT) == []


def test_validate_bundle_ok_for_bundled_kit() -> None:
    report = helper.validate_bundle(installer.BUNDLE_ROOT)
    assert report["status"] == "ok"
    assert report["errors"] == []


def test_detect_conflicts_reports_existing_files(tmp_path: Path) -> None:
    install_root = tmp_path / ".agent"
    target = install_root / "agents" / "product-owner.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("existing", encoding="utf-8")

    conflicts = helper.detect_conflicts(installer.BUNDLE_ROOT, install_root)
    assert "agents/product-owner.md" in conflicts


def test_copy_bundle_dry_run_does_not_create_files(tmp_path: Path) -> None:
    install_root = tmp_path / ".agent"
    copied = helper.copy_entire_bundle(installer.BUNDLE_ROOT, install_root, dry_run=True)
    assert copied == 22
    assert not install_root.exists()


def test_copy_bundle_and_write_stamp(tmp_path: Path) -> None:
    target_root = tmp_path / "project"
    target_root.mkdir()
    install_root = target_root / ".agent"
    copied = helper.copy_entire_bundle(installer.BUNDLE_ROOT, install_root)
    stats = helper.collect_bundle_stats(installer.BUNDLE_ROOT)
    stamp_path = helper.write_stamp(install_root, target_root, stats, force=False, operation="install")

    assert copied == 22
    assert (install_root / "agents" / "scrum-master.md").exists()
    payload = json.loads(stamp_path.read_text(encoding="utf-8"))
    assert payload["kit"] == "codex-scrum-subagents"
    assert payload["bundle"]["agent_files"] == 10
    assert payload["bundle"]["service_files"] == 3
    assert payload["bundle"]["native_agent_files"] == 10
    assert payload["target_root"] == str(target_root.resolve())
    assert payload["codex_agents_root"] == str((target_root / ".codex" / "agents").resolve())
    assert payload["project_codex_agents_rel"] == ".codex/agents"


def test_native_agent_specs_render_prefixed_toml_agents() -> None:
    specs = helper.native_agent_specs(installer.BUNDLE_ROOT)

    assert len(specs) == 10
    assert "scrum-product-owner.toml" in specs
    assert "scrum-master.toml" in specs
    assert "scrum-solution-architect.toml" in specs
    assert 'name = "scrum-product-owner"' in specs["scrum-product-owner.toml"]
    assert "description =" in specs["scrum-product-owner.toml"]
    assert "developer_instructions = '''" in specs["scrum-product-owner.toml"]
    assert "prompt =" not in specs["scrum-product-owner.toml"]


def test_copy_and_compare_native_agents(tmp_path: Path) -> None:
    install_root = tmp_path / ".codex" / "agents"
    copied = helper.copy_native_agents(
        installer.BUNDLE_ROOT,
        install_root,
        helper.native_agent_specs(installer.BUNDLE_ROOT).keys(),
    )

    assert copied == 10
    diff = helper.compare_native_agents_to_install(installer.BUNDLE_ROOT, install_root)
    assert diff["missing"] == []
    assert diff["changed"] == []
    assert diff["same"] == sorted(helper.native_agent_specs(installer.BUNDLE_ROOT).keys())


def test_compare_bundle_to_install_reports_missing_changed_and_extra(tmp_path: Path) -> None:
    install_root = tmp_path / ".agent"
    helper.copy_entire_bundle(installer.BUNDLE_ROOT, install_root)
    (install_root / "agents" / "scrum-master.md").write_text("changed", encoding="utf-8")
    extra_file = install_root / "notes.txt"
    extra_file.write_text("extra", encoding="utf-8")
    missing_file = install_root / "workflows" / "retrospective.md"
    missing_file.unlink()

    diff = helper.compare_bundle_to_install(installer.BUNDLE_ROOT, install_root)
    assert "agents/scrum-master.md" in diff["changed"]
    assert "workflows/retrospective.md" in diff["missing"]
    assert "notes.txt" in diff["extra"]


def test_backup_existing_files_copies_only_existing_targets(tmp_path: Path) -> None:
    install_root = tmp_path / ".agent"
    helper.copy_entire_bundle(installer.BUNDLE_ROOT, install_root)
    backup_root = tmp_path / "backup"

    backed_up = helper.backup_existing_files(
        install_root=install_root,
        backup_root=backup_root,
        relative_paths=["agents/product-owner.md", "missing.md"],
    )

    assert backed_up == 1
    assert (backup_root / "agents" / "product-owner.md").exists()
    assert not (backup_root / "missing.md").exists()


def test_validator_detects_manifest_mismatch(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    (bundle_root / "agents").mkdir(parents=True)
    (bundle_root / "workflows").mkdir()
    (bundle_root / "services").mkdir()
    (bundle_root / "README.md").write_text("# Readme", encoding="utf-8")
    (bundle_root / "ARCHITECTURE.md").write_text("# Architecture", encoding="utf-8")
    (bundle_root / "agents" / "product-owner.md").write_text(
        "---\nname: product-owner\ndescription: role\n---\n\n# Product Owner\n",
        encoding="utf-8",
    )
    (bundle_root / "workflows" / "sprint-planning.md").write_text(
        "---\nname: sprint-planning\ndescription: workflow\n---\n\n# Sprint Planning\n",
        encoding="utf-8",
    )
    (bundle_root / "services" / "agents.json").write_text(
        json.dumps([{"name": "wrong-agent", "description": "bad", "skills": []}], indent=2),
        encoding="utf-8",
    )
    (bundle_root / "services" / "workflows.json").write_text(
        json.dumps([{"command": "/sprint-planning", "description": "ok"}], indent=2),
        encoding="utf-8",
    )
    (bundle_root / "services" / "commands.json").write_text(
        json.dumps(
            [
                {
                    "command": "$sprint-plan",
                    "alias_for": "sprint-planning",
                    "description": "ok",
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    report = helper.validate_bundle(bundle_root)
    assert report["status"] == "error"
    assert "services/agents.json: manifest names do not match agents/*.md" in report["errors"]


def test_commands_manifest_exposes_scrum_aliases() -> None:
    commands = helper.read_json(installer.BUNDLE_ROOT / "services" / "commands.json")
    assert isinstance(commands, list)

    alias_map = {item["command"]: item["alias_for"] for item in commands}
    assert alias_map["$scrum-install"] == "codex-scrum-subagents.install"
    assert alias_map["$story-ready-check"] == "backlog-refinement"
    assert alias_map["$release-readiness"] == "release-readiness"


def test_generate_scrum_artifact_requires_complete_fields_by_default() -> None:
    try:
        artifact_generator.build_artifact_payload("user-story", {"title": "Checkout validation"}, allow_placeholders=False)
    except ValueError as exc:
        assert "Missing required fields for template 'user-story'" in str(exc)
    else:
        raise AssertionError("Expected missing field validation to fail")


def test_generate_scrum_artifact_scaffold_mode_uses_todo_for_missing_fields() -> None:
    payload = artifact_generator.build_artifact_payload(
        "user-story",
        {"title": "Checkout validation"},
        allow_placeholders=True,
    )
    assert payload["status"] == "scaffold"
    assert "persona" in payload["missing_fields"]
    assert "_TODO_" in payload["markdown"]


def test_run_scrum_alias_generates_workflow_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "retro.md"
    payload = alias_runner.build_workflow_payload(
        alias="$retro",
        artifact_output=str(output_path),
        fields={
            "title": "Sprint 8 retrospective",
            "sprint_name": "Sprint 8",
            "wins": "- Release stabilized",
            "pain_points": "- Late QA handoff",
            "actions": "- Pull QA into story delivery sooner",
            "owners": "- scrum-master",
        },
    )
    assert payload["workflow"] == "retrospective"
    assert payload["artifact_path"] == output_path.as_posix()
    assert output_path.exists()
    assert "Sprint 8 retrospective" in output_path.read_text(encoding="utf-8")


def test_run_scrum_alias_requires_complete_fields_for_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "story.md"
    try:
        alias_runner.build_workflow_payload(
            alias="$story-ready-check",
            artifact_output=str(output_path),
            fields={"title": "Checkout validation"},
        )
    except ValueError as exc:
        assert "Missing required fields for template 'user-story'" in str(exc)
    else:
        raise AssertionError("Expected workflow artifact generation to reject placeholder-only output")


def test_run_scrum_alias_scaffold_mode_is_explicit(tmp_path: Path) -> None:
    output_path = tmp_path / "story.md"
    payload = alias_runner.build_workflow_payload(
        alias="$story-ready-check",
        artifact_output=str(output_path),
        fields={"title": "Checkout validation"},
        allow_placeholders=True,
    )
    assert payload["status"] == "scaffold"
    assert "persona" in payload["missing_fields"]
    assert output_path.exists()


def test_validator_script_format_table_includes_diff_counts(tmp_path: Path) -> None:
    install_root = tmp_path / ".agent"
    helper.copy_entire_bundle(installer.BUNDLE_ROOT, install_root)
    (install_root / "services" / "agents.json").write_text("[]", encoding="utf-8")
    report = helper.validate_bundle(installer.BUNDLE_ROOT)
    report["diff"] = helper.compare_bundle_to_install(installer.BUNDLE_ROOT, install_root)
    table = validator.format_table(report)
    assert "missing" in table
    assert "changed" in table


def test_validator_marks_drift_when_install_root_is_out_of_sync(tmp_path: Path) -> None:
    install_root = tmp_path / ".agent"
    helper.copy_entire_bundle(installer.BUNDLE_ROOT, install_root)
    (install_root / "README.md").unlink()

    report = helper.validate_bundle(installer.BUNDLE_ROOT)
    diff = helper.compare_bundle_to_install(installer.BUNDLE_ROOT, install_root)
    if report["status"] == "ok" and (diff["missing"] or diff["changed"] or diff["extra"]):
        report["status"] = "drift"

    assert report["status"] == "drift"


def test_installer_diff_table_mode_does_not_crash(tmp_path: Path) -> None:
    target_root = tmp_path / "project"
    target_root.mkdir()

    result = run_installer_cli("--target-root", str(target_root), "--diff")

    assert result.returncode == 0
    assert "status       : diff" in result.stdout
    assert "force        : False" in result.stdout
    assert "native_miss  : 10" in result.stdout


def test_installer_update_table_mode_reports_clean_diff_after_repair(tmp_path: Path) -> None:
    target_root = tmp_path / "project"
    target_root.mkdir()
    install_root = target_root / ".agent"
    helper.copy_entire_bundle(installer.BUNDLE_ROOT, install_root)
    codex_agents_root = target_root / ".codex" / "agents"
    helper.copy_native_agents(
        installer.BUNDLE_ROOT,
        codex_agents_root,
        helper.native_agent_specs(installer.BUNDLE_ROOT).keys(),
    )
    (install_root / "agents" / "scrum-master.md").write_text("drifted", encoding="utf-8")
    (install_root / "workflows" / "retrospective.md").unlink()
    (codex_agents_root / "scrum-product-owner.toml").write_text("drifted", encoding="utf-8")

    result = run_installer_cli("--target-root", str(target_root), "--update")

    assert result.returncode == 0
    assert "status       : updated" in result.stdout
    assert "changed      : 0" in result.stdout
    assert "missing      : 0" in result.stdout
    assert "native_chg   : 0" in result.stdout


def test_installer_update_json_uses_post_update_diff_and_preserves_force_flag(tmp_path: Path) -> None:
    target_root = tmp_path / "project"
    target_root.mkdir()
    install_root = target_root / ".agent"
    helper.copy_entire_bundle(installer.BUNDLE_ROOT, install_root)
    codex_agents_root = target_root / ".codex" / "agents"
    helper.copy_native_agents(
        installer.BUNDLE_ROOT,
        codex_agents_root,
        helper.native_agent_specs(installer.BUNDLE_ROOT).keys(),
    )
    (install_root / "agents" / "scrum-master.md").write_text("drifted", encoding="utf-8")
    (install_root / "workflows" / "retrospective.md").unlink()
    (codex_agents_root / "scrum-product-owner.toml").write_text("drifted", encoding="utf-8")

    result = run_installer_cli("--target-root", str(target_root), "--update", "--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "updated"
    assert payload["diff"]["changed"] == []
    assert payload["diff"]["missing"] == []
    assert payload["native_agents_diff"]["changed"] == []
    assert payload["native_agents_diff"]["missing"] == []

    stamp = json.loads((install_root / ".codexai-scrum-kit.json").read_text(encoding="utf-8"))
    assert stamp["operation"] == "update"
    assert stamp["force"] is False


def test_installer_install_creates_native_codex_agents(tmp_path: Path) -> None:
    target_root = tmp_path / "project"
    target_root.mkdir()

    result = run_installer_cli("--target-root", str(target_root), "--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "installed"
    assert payload["copied_files"] == 32
    assert (target_root / ".codex" / "agents" / "scrum-product-owner.toml").exists()
    assert payload["native_agents_diff"]["missing"] == []


def test_validator_marks_drift_when_native_agent_is_out_of_sync(tmp_path: Path) -> None:
    install_root = tmp_path / ".agent"
    helper.copy_entire_bundle(installer.BUNDLE_ROOT, install_root)
    codex_agents_root = tmp_path / ".codex" / "agents"
    helper.copy_native_agents(
        installer.BUNDLE_ROOT,
        codex_agents_root,
        helper.native_agent_specs(installer.BUNDLE_ROOT).keys(),
    )
    (codex_agents_root / "scrum-product-owner.toml").write_text("changed", encoding="utf-8")

    report = helper.validate_bundle(installer.BUNDLE_ROOT)
    report["diff"] = helper.compare_bundle_to_install(installer.BUNDLE_ROOT, install_root)
    report["native_agents_diff"] = helper.compare_native_agents_to_install(installer.BUNDLE_ROOT, codex_agents_root)
    if report["status"] == "ok":
        diff = report["diff"]
        native_diff = report["native_agents_diff"]
        assert isinstance(diff, dict)
        assert isinstance(native_diff, dict)
        if diff["missing"] or diff["changed"] or diff["extra"] or native_diff["missing"] or native_diff["changed"] or native_diff["extra"]:
            report["status"] = "drift"

    assert report["status"] == "drift"


def test_validate_native_agent_specs_parses_all_generated_toml() -> None:
    assert helper.validate_native_agent_specs(installer.BUNDLE_ROOT) == []


def test_validator_uses_stamp_for_custom_install_dir(tmp_path: Path) -> None:
    target_root = tmp_path / "project"
    target_root.mkdir()

    install_result = run_installer_cli("--target-root", str(target_root), "--install-dir", ".meta/.agent", "--format", "json")

    assert install_result.returncode == 0
    validate_result = run_validator_cli("--install-root", str(target_root / ".meta" / ".agent"), "--format", "json")
    assert validate_result.returncode == 0
    payload = json.loads(validate_result.stdout)
    assert payload["status"] == "ok"
    assert payload["native_agents_diff"]["missing"] == []


def test_installer_supports_personal_native_scope(tmp_path: Path) -> None:
    target_root = tmp_path / "project"
    target_root.mkdir()
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    env = os.environ.copy()
    env["USERPROFILE"] = str(fake_home)
    env["HOME"] = str(fake_home)

    result = run_installer_cli(
        "--target-root",
        str(target_root),
        "--native-scope",
        "both",
        "--format",
        "json",
        env=env,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    personal_root = fake_home / ".codex" / "agents"
    assert payload["status"] == "installed"
    assert payload["personal_native_agents_diff"]["missing"] == []
    assert (personal_root / "scrum-product-owner.toml").exists()


def test_validator_supports_personal_native_scope(tmp_path: Path) -> None:
    target_root = tmp_path / "project"
    target_root.mkdir()
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    env = os.environ.copy()
    env["USERPROFILE"] = str(fake_home)
    env["HOME"] = str(fake_home)

    install_result = run_installer_cli(
        "--target-root",
        str(target_root),
        "--native-scope",
        "both",
        "--format",
        "json",
        env=env,
    )
    assert install_result.returncode == 0

    validate_result = run_validator_cli(
        "--target-root",
        str(target_root),
        "--native-scope",
        "both",
        "--format",
        "json",
        env=env,
    )

    assert validate_result.returncode == 0
    payload = json.loads(validate_result.stdout)
    assert payload["status"] == "ok"
    assert payload["personal_native_agents_diff"]["missing"] == []
