from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"
REGISTRY_PATH = SKILLS_ROOT / ".system" / "references" / "plugin-tools.json"
SCHEMA_PATH = SKILLS_ROOT / ".system" / "references" / "plugin-tools.schema.json"
VALIDATOR_PATH = SKILLS_ROOT / ".system" / "scripts" / "validate_tool_contracts.py"
MANIFEST_PATH = SKILLS_ROOT / ".system" / "manifest.json"


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


tool_contracts = load_script_module("validate_tool_contracts", ".system/scripts/validate_tool_contracts.py")


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )


def test_plugin_tool_registry_schema_version_and_tools() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert registry["schema_version"] == "1.0"
    assert schema["schema_version"] == "1.0"
    names = {tool["name"] for tool in registry["tools"]}
    assert names == {
        "pack_health",
        "codex_plugin_validate",
        "claude_plugin_validate",
        "release_zip_dry_run",
        "prompt_route",
        "trust_harness",
        "memory_status",
        "memory_build_index",
        "memory_scale_gate",
        "local_release_gate",
    }
    for tool in registry["tools"]:
        for field in (
            "kind",
            "script",
            "purpose",
            "args_schema",
            "exit_codes",
            "warning_policy",
            "artifact_policy",
            "safety_policy",
        ):
            assert field in tool, f"{tool['name']} missing {field}"
        assert tool["safety_policy"]["reads_secrets"] is False


def test_manifest_references_plugin_tool_contract() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    contract = manifest["plugin_tool_contract"]

    assert contract["registry"].endswith("plugin-tools.json")
    assert contract["validator"].endswith("validate_tool_contracts.py")
    assert (SKILLS_ROOT / contract["registry"]).exists()
    assert (SKILLS_ROOT / contract["validator"]).exists()


def test_validate_tool_contracts_strict_passes_on_repo() -> None:
    result = run_validator("--skills-root", str(SKILLS_ROOT), "--strict", "--format", "json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    check_names = {item["name"] for item in payload["checks"]}
    assert "registry_shape" in check_names
    assert "script_paths" in check_names
    assert "safe_smoke" in check_names


def test_validate_tool_contracts_no_smoke_skips_execution() -> None:
    payload = tool_contracts.validate(SKILLS_ROOT, strict=False, run_smokes=False)
    assert payload["status"] == "pass"
    assert not any(item["name"] == "safe_smoke" for item in payload["checks"])


def test_validate_tool_contracts_reports_missing_script(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    refs = skills_root / ".system" / "references"
    refs.mkdir(parents=True)
    (refs / "plugin-tools.schema.json").write_text(
        json.dumps({"schema_version": "1.0"}),
        encoding="utf-8",
    )
    (refs / "plugin-tools.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "broken_tool",
                        "kind": "health",
                        "script": ".system/scripts/missing.py",
                        "purpose": "Intentionally missing script for contract tests.",
                        "args_schema": {"type": "object", "required": ["skills_root"], "properties": {"skills_root": {"type": "string"}}},
                        "exit_codes": {"success": [0], "failure": [1]},
                        "warning_policy": {"mode": "none", "description": "No warnings for this negative test."},
                        "artifact_policy": {"mode": "none", "description": "No artifacts for this negative test."},
                        "safety_policy": {
                            "network": "none",
                            "writes_artifacts": False,
                            "reads_secrets": False,
                            "smoke_allowed": False,
                            "description": "Not smoke tested.",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    payload = tool_contracts.validate(skills_root, run_smokes=False)
    assert payload["status"] == "fail"
    script_check = next(item for item in payload["checks"] if item["name"] == "script_paths")
    assert script_check["status"] == "fail"


def test_validate_tool_contracts_rejects_invalid_smoke_cwd(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    scripts = skills_root / ".system" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "stub.py").write_text("print('ok')\n", encoding="utf-8")
    refs = skills_root / ".system" / "references"
    refs.mkdir(parents=True)
    (refs / "plugin-tools.schema.json").write_text(
        json.dumps({"schema_version": "1.0"}),
        encoding="utf-8",
    )
    (refs / "plugin-tools.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "bad_cwd_tool",
                        "kind": "health",
                        "script": ".system/scripts/stub.py",
                        "purpose": "Negative test for invalid smoke.cwd enum.",
                        "args_schema": {"type": "object", "required": ["skills_root"], "properties": {"skills_root": {"type": "string"}}},
                        "exit_codes": {"success": [0], "failure": [1]},
                        "warning_policy": {"mode": "none", "description": "No warnings for this negative test."},
                        "artifact_policy": {"mode": "none", "description": "No artifacts for this negative test."},
                        "safety_policy": {
                            "network": "none",
                            "writes_artifacts": False,
                            "reads_secrets": False,
                            "smoke_allowed": True,
                            "description": "Smoke declared with invalid cwd.",
                        },
                        "smoke": {
                            "argv": ["--help"],
                            "expect_exit_codes": [0],
                            "cwd": "typo_root",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    payload = tool_contracts.validate(skills_root, run_smokes=True)
    assert payload["status"] == "fail"
    shape = next(item for item in payload["checks"] if item["name"] == "registry_shape")
    assert shape["status"] == "fail"
    assert any("invalid smoke.cwd" in str(entry) for entry in shape.get("failures", []))


def test_pack_health_includes_plugin_tool_contract_check() -> None:
    pack_health = load_script_module("pack_health_for_contracts", ".system/scripts/check_pack_health.py")
    payload = pack_health.summarize(pack_health.check_source(SKILLS_ROOT))
    names = {item["name"] for item in payload["checks"]}
    assert "plugin_tool_contracts" in names
    plugin_check = next(item for item in payload["checks"] if item["name"] == "plugin_tool_contracts")
    assert plugin_check["status"] == "pass"
