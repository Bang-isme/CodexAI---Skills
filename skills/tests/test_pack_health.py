from __future__ import annotations

import importlib.util
import json
import subprocess
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


pack_health = load_script_module("skills_pack_health", ".system/scripts/check_pack_health.py")
SCRIPT_PATH = SKILLS_ROOT / ".system" / "scripts" / "check_pack_health.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )


def write_minimal_healthy_source(skills_root: Path) -> None:
    version = "15.2.0"
    write(skills_root / "VERSION", f"{version}\n")
    write(
        skills_root / ".system" / "manifest.json",
        json.dumps({"version": version, "skills": [], "agents": [], "workflows": []}),
    )
    write(
        skills_root / ".system" / "REGISTRY.md",
        """# Registry

| Script | Skill | Purpose |
|---|---|---|
| `benchmark_quality.py` | `tests` | benchmark |
""",
    )
    write(skills_root / "tests" / "benchmark_quality.py", "print('ok')\n")
    write(skills_root / ".system" / "OPERATION_RUNBOOK.md", "# Runbook\n")
    (skills_root / ".agents").mkdir(parents=True, exist_ok=True)
    (skills_root / ".workflows").mkdir(parents=True, exist_ok=True)
    write(skills_root.parent / ".codex-plugin" / "plugin.json", json.dumps({"version": version}))
    write(skills_root.parent / ".claude-plugin" / "plugin.json", json.dumps({"version": version}))
    write(skills_root.parent / ".agents" / "plugins" / "marketplace.json", "{}\n")
    write(skills_root.parent / "hooks" / "hooks.json", json.dumps({"hooks": {}}))
    for schema in [
        "codex-runtime-hook/references/profile.schema.json",
        "codex-runtime-hook/references/runtime-hook-output.schema.json",
        "codex-spec-driven-development/references/spec.schema.json",
        "codex-project-memory/references/knowledge-index.schema.json",
    ]:
        write(skills_root / schema, json.dumps({"schema_version": "1.0"}))
    aliases = "\n".join(pack_health.REQUIRED_ALIASES)
    write(skills_root / "codex-master-instructions" / "SKILL.md", aliases)


def test_pack_health_current_source_is_operationally_clean() -> None:
    payload = pack_health.summarize(pack_health.check_source(SKILLS_ROOT))

    assert payload["status"] == "pass"
    names = {item["name"] for item in payload["checks"]}
    assert "manifest_skills" in names
    assert "native_plugin_paths" in names
    assert "claude_plugin_version" in names
    assert "registry_scripts" in names
    assert "critical_aliases" in names
    assert "markdown_mojibake" in names


def test_pack_health_reports_missing_manifest_skill(tmp_path: Path) -> None:
    write(tmp_path / "VERSION", "1.0.0\n")
    write(
        tmp_path / ".system" / "manifest.json",
        json.dumps({"version": "1.0.0", "skills": ["missing-skill"], "agents": [], "workflows": []}),
    )
    write(tmp_path / ".system" / "REGISTRY.md", "# Registry\n")
    (tmp_path / ".agents").mkdir()
    (tmp_path / ".workflows").mkdir()

    checks = pack_health.check_source(tmp_path)
    manifest_skills = next(item for item in checks if item["name"] == "manifest_skills")

    assert manifest_skills["status"] == "fail"
    assert manifest_skills["missing"] == ["missing-skill"]


def test_pack_health_reports_incomplete_global_sync(tmp_path: Path) -> None:
    source = tmp_path / "source"
    global_root = tmp_path / "global"
    write(source / "VERSION", "15.0.0\n")
    write(global_root / "VERSION", "14.0.0\n")

    checks = pack_health.check_global_sync(source, global_root)
    version_check = next(item for item in checks if item["name"] == "global_version_sync")
    required_paths = next(item for item in checks if item["name"] == "global_required_paths")

    assert version_check["status"] == "fail"
    assert required_paths["status"] == "fail"
    assert ".system/OPERATION_RUNBOOK.md" in required_paths["missing"]
    assert "codex-runtime-hook/SKILL.md" in required_paths["missing"]


def test_pack_health_missing_skills_root_is_controlled_failure(tmp_path: Path) -> None:
    checks = pack_health.check_source(tmp_path / "missing")

    assert checks == [{"name": "skills_root", "status": "fail", "detail": str(tmp_path / "missing")}]


def test_pack_health_parses_registry_rows_and_validates_script_paths(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    write(skills_root / "tests" / "benchmark_quality.py", "print('ok')\n")
    write(skills_root / "codex-demo" / "scripts" / "demo.py", "print('ok')\n")
    registry = skills_root / ".system" / "REGISTRY.md"
    write(
        registry,
        """| Script | Skill | Purpose |
|---|---|---|
| `demo.py` | `codex-demo` | demo |
| `benchmark_quality.py` | `tests` | benchmark |
| bad row |
""",
    )

    rows = pack_health.parse_registry_rows(registry)

    assert rows == [
        {"script": "demo.py", "skill": "codex-demo", "purpose": "demo"},
        {"script": "benchmark_quality.py", "skill": "tests", "purpose": "benchmark"},
    ]
    assert pack_health.registry_script_exists(skills_root, "codex-demo", "demo.py")
    assert pack_health.registry_script_exists(skills_root, "tests", "benchmark_quality.py")
    assert not pack_health.registry_script_exists(skills_root, "codex-demo", "missing.py")


def test_pack_health_reports_invalid_contract_schema(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    write_minimal_healthy_source(skills_root)
    write(skills_root / "codex-spec-driven-development" / "references" / "spec.schema.json", "{not json")

    checks = pack_health.check_source(skills_root)
    schemas = next(item for item in checks if item["name"] == "contract_schemas")

    assert schemas["status"] == "fail"
    assert any("spec.schema.json: invalid JSON" in failure for failure in schemas["failures"])


def test_pack_health_reports_missing_critical_aliases(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    write_minimal_healthy_source(skills_root)
    write(skills_root / "codex-master-instructions" / "SKILL.md", "$spec\n$prototype\n")

    checks = pack_health.check_source(skills_root)
    aliases = next(item for item in checks if item["name"] == "critical_aliases")

    assert aliases["status"] == "fail"
    assert "$hook" in aliases["missing"]
    assert "$check-full" in aliases["missing"]


def test_pack_health_warns_on_markdown_mojibake(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    write_minimal_healthy_source(skills_root)
    write(skills_root / "codex-demo" / "SKILL.md", f"Broken sequence {pack_health.MOJIBAKE_PATTERNS[0]}\n")

    checks = pack_health.check_source(skills_root)
    mojibake = next(item for item in checks if item["name"] == "markdown_mojibake")

    assert mojibake["status"] == "warn"
    assert mojibake["files"] == ["codex-demo/SKILL.md"]


def test_pack_health_strict_cli_fails_on_warning(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    write_minimal_healthy_source(skills_root)
    write(skills_root / "codex-demo" / "SKILL.md", f"Broken sequence {pack_health.MOJIBAKE_PATTERNS[0]}\n")

    result = run_cli("--skills-root", str(skills_root), "--strict")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["status"] == "warn"
    assert payload["warnings"] == 1


def test_pack_health_validates_native_scrum_agent_role_files(tmp_path: Path) -> None:
    agents_root = tmp_path / "agents"
    write(
        agents_root / "scrum-frontend-developer.toml",
        """name = "scrum-frontend-developer"
description = "Frontend delivery"
developer_instructions = "Stay in frontend files."
prompt = "unsupported"
""",
    )

    checks = pack_health.check_native_agent_role_files(agents_root)
    roles = next(item for item in checks if item["name"] == "native_agent_roles")

    assert roles["status"] == "fail"
    assert "unsupported field(s): prompt" in roles["failures"][0]
