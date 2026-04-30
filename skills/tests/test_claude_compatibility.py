from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validate_claude = load_script_module("validate_claude_plugin_tests", ".system/scripts/validate_claude_plugin.py")
install_claude = load_script_module("install_claude_native_tests", ".system/scripts/install_claude_native.py")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def test_claude_plugin_manifest_and_hooks_match_current_release() -> None:
    manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    hooks = json.loads((REPO_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    version = (SKILLS_ROOT / "VERSION").read_text(encoding="utf-8").strip()

    assert manifest["name"] == "codexai-agentic-workflow"
    assert manifest["version"] == version
    command = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert "${CLAUDE_PLUGIN_ROOT}" in command
    assert "${CLAUDE_PROJECT_DIR}" in command
    assert "runtime_hook.py" in command
    assert "--format prompt" in command


def test_validate_claude_plugin_current_repo_passes() -> None:
    payload = validate_claude.validate(REPO_ROOT)

    assert payload["status"] == "pass"
    names = {item["name"] for item in payload["checks"]}
    assert "claude_manifest_exists" in names
    assert "claude_skill_metadata" in names
    assert "claude_hooks" in names


def test_validate_claude_plugin_rejects_non_object_manifest(tmp_path: Path) -> None:
    write(tmp_path / ".claude-plugin" / "plugin.json", "[]\n")
    write(tmp_path / "skills" / "VERSION", "1.0.0\n")

    payload = validate_claude.validate(tmp_path)

    assert payload["status"] == "fail"
    assert any(item["name"] == "claude_manifest_json" for item in payload["checks"])


def test_validate_claude_plugin_rejects_incomplete_hooks(tmp_path: Path) -> None:
    write(
        tmp_path / ".claude-plugin" / "plugin.json",
        json.dumps({"name": "codexai-test", "description": "Test", "version": "1.0.0"}),
    )
    write(tmp_path / "skills" / "VERSION", "1.0.0\n")
    write(tmp_path / "skills" / "codex-demo" / "SKILL.md", "---\ndescription: Use for demo.\n---\n")
    write(
        tmp_path / "hooks" / "hooks.json",
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup|resume",
                            "hooks": [{"type": "command", "command": "python runtime_hook.py", "timeout": 30}],
                        }
                    ]
                }
            }
        ),
    )

    payload = validate_claude.validate(tmp_path)
    hook_check = next(item for item in payload["checks"] if item["name"] == "claude_hooks")

    assert payload["status"] == "fail"
    assert hook_check["status"] == "fail"
    assert "${CLAUDE_PLUGIN_ROOT}" in hook_check["detail"]


def test_install_claude_native_project_scope_maps_to_claude_skills(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    target = install_claude.resolve_target("project", str(repo), "")

    assert target == repo.resolve() / ".claude" / "skills"


def test_install_claude_native_user_scope_uses_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.delenv("HOME", raising=False)

    assert install_claude.resolve_target("user", "", "") == tmp_path / "home" / ".claude" / "skills"


def test_install_claude_native_apply_copies_skills(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write(source / "codex-demo" / "SKILL.md", "---\ndescription: Use for demo.\n---\n")

    payload = install_claude.install(source, target, dry_run=False)

    assert payload["status"] == "synced"
    assert payload["claude_install"] is True
    assert (target / "codex-demo" / "SKILL.md").read_text(encoding="utf-8").startswith("---")


def test_install_claude_native_cli_invalid_source_returns_json_error(tmp_path: Path) -> None:
    script = SKILLS_ROOT / ".system" / "scripts" / "install_claude_native.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--source",
            str(tmp_path / "missing"),
            "--scope",
            "custom",
            "--target-root",
            str(tmp_path / "target"),
            "--apply",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "error"
    assert "Source skills root does not exist" in payload["message"]
