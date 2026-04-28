from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml


SKILLS_ROOT = Path(__file__).resolve().parents[1]
AGENTS_ROOT = SKILLS_ROOT / ".agents"
WORKFLOWS_ROOT = SKILLS_ROOT / ".workflows"
MANIFEST_PATH = SKILLS_ROOT / ".system" / "manifest.json"
VERSION_PATH = SKILLS_ROOT / "VERSION"
BOUNDARY_SCRIPT = SKILLS_ROOT / ".system" / "scripts" / "check_boundaries.py"


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


boundary_checker = load_script_module(
    "skills_check_boundaries",
    ".system/scripts/check_boundaries.py",
)


def parse_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path} is missing frontmatter")
    frontmatter_text = text.split("---\n", 2)[1]
    payload = yaml.safe_load(frontmatter_text)
    assert isinstance(payload, dict)
    return payload


def test_agent_files_have_valid_frontmatter() -> None:
    expected_keys = {"name", "description", "skills", "file_ownership"}
    for path in sorted(AGENTS_ROOT.glob("*.md")):
        payload = parse_frontmatter(path)
        assert set(payload.keys()) == expected_keys
        assert isinstance(payload["name"], str) and payload["name"]
        assert isinstance(payload["description"], str) and payload["description"]
        assert isinstance(payload["skills"], list) and payload["skills"]
        assert all(isinstance(item, str) and item for item in payload["skills"])
        assert isinstance(payload["file_ownership"], list) and payload["file_ownership"]
        assert all(isinstance(item, str) and item for item in payload["file_ownership"])


def test_workflow_files_have_required_contract_sections() -> None:
    for path in sorted(WORKFLOWS_ROOT.glob("*.md")):
        payload = parse_frontmatter(path)
        body = path.read_text(encoding="utf-8")
        assert isinstance(payload.get("trigger"), str) and payload["trigger"].startswith("$")
        assert isinstance(payload.get("loads"), list) and payload["loads"]
        assert "## Trigger" in body
        assert "## Step Outline" in body
        assert "## Exit Criteria" in body


def test_manifest_lists_all_agents_and_workflows() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert sorted(manifest["agents"]) == sorted(path.stem for path in AGENTS_ROOT.glob("*.md"))
    assert sorted(manifest["workflows"]) == sorted(path.stem for path in WORKFLOWS_ROOT.glob("*.md"))
    assert manifest["version"] == VERSION_PATH.read_text(encoding="utf-8").strip()


def test_check_boundaries_blocks_and_suggests_handoff() -> None:
    report = boundary_checker.build_report(
        "frontend-specialist",
        ["src/components/Header.vue", "src/server/api.js"],
    )
    assert report["agent"] == "frontend-specialist"
    assert report["files_allowed"] == ["src/components/Header.vue"]
    assert report["files_blocked"] == ["src/server/api.js"]
    assert report["suggested_handoff"] == {"src/server/api.js": "backend-specialist"}

    result = subprocess.run(
        [
            sys.executable,
            str(BOUNDARY_SCRIPT),
            "--agent",
            "frontend-specialist",
            "--files",
            "src/components/Header.vue,src/server/api.js",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == report


def test_check_boundaries_has_no_external_yaml_dependency() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            str(BOUNDARY_SCRIPT),
            "--agent",
            "frontend-specialist",
            "--files",
            "src/components/Header.vue",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["files_allowed"] == ["src/components/Header.vue"]
