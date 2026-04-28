from __future__ import annotations

import importlib.util
import json
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


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def test_pack_health_current_source_is_operationally_clean() -> None:
    payload = pack_health.summarize(pack_health.check_source(SKILLS_ROOT))

    assert payload["status"] == "pass"
    names = {item["name"] for item in payload["checks"]}
    assert "manifest_skills" in names
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
