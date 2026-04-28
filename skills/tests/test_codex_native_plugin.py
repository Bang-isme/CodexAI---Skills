from __future__ import annotations

import importlib.util
import json
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


validate_plugin = load_script_module("codex_native_validate_plugin", ".system/scripts/validate_codex_plugin.py")
install_native = load_script_module("codex_native_install", ".system/scripts/install_codex_native.py")
init_agents_md = load_script_module("codex_native_agents_md", ".system/scripts/init_agents_md.py")
runtime_hook = load_script_module("codex_native_runtime_hook", "codex-runtime-hook/scripts/runtime_hook.py")
install_hooks = load_script_module("codex_native_install_hooks", "codex-runtime-hook/scripts/install_codex_hooks.py")
validate_hooks = load_script_module("codex_native_validate_hooks", "codex-runtime-hook/scripts/validate_codex_hooks.py")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def test_plugin_manifest_and_marketplace_are_codex_native() -> None:
    plugin = json.loads((REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))

    assert plugin["name"] == "codexai-agentic-workflow"
    assert plugin["skills"] == "./skills/"
    assert plugin["version"] == (SKILLS_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    entry = marketplace["plugins"][0]
    assert entry["name"] == plugin["name"]
    assert entry["source"]["path"].startswith("./")
    assert entry["policy"]["installation"] == "AVAILABLE"
    assert entry["policy"]["authentication"] == "ON_INSTALL"


def test_validate_codex_plugin_current_repo_has_no_blocking_failures() -> None:
    payload = validate_plugin.validate(REPO_ROOT)

    assert payload["status"] in {"pass", "warn"}
    assert payload["failed"] == 0
    names = {item["name"] for item in payload["checks"]}
    assert "plugin_manifest_exists" in names
    assert "marketplace_entry" in names
    assert "skill_metadata" in names


def test_install_codex_native_repo_scope_maps_to_agents_skills(tmp_path: Path) -> None:
    source = tmp_path / "source"
    repo = tmp_path / "repo"
    write(source / "codex-demo" / "SKILL.md", "---\nname: codex-demo\ndescription: Use for demo.\n---\n")
    write(source / ".system" / "REGISTRY.md", "# Registry\n")
    repo.mkdir()

    target = install_native.resolve_target("repo", str(repo), "")
    payload = install_native.install(source, target, dry_run=True)

    assert target == repo / ".agents" / "skills"
    assert payload["status"] == "dry_run"
    assert ".system" in payload["items"]
    assert "codex-demo" in payload["items"]


def test_init_agents_md_merge_is_idempotent(tmp_path: Path) -> None:
    first = init_agents_md.build_payload(tmp_path, mode="merge", dry_run=False)
    second = init_agents_md.build_payload(tmp_path, mode="merge", dry_run=False)
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")

    assert first["status"] == "created"
    assert second["status"] == "unchanged"
    assert text.count(init_agents_md.START_MARKER) == 1
    assert "spec-first workflow" in text


def test_runtime_hook_prompt_format_is_compact(tmp_path: Path) -> None:
    write(tmp_path / "package.json", json.dumps({"dependencies": {"react": "^18.0.0"}}))
    report = runtime_hook.build_report(tmp_path)
    prompt = runtime_hook.render_prompt(report)

    assert "Project readiness:" in prompt
    assert "Recommended workflow:" in prompt
    assert "untrusted evidence" in prompt


def test_codex_hooks_installer_and_validator(tmp_path: Path) -> None:
    payload = install_hooks.install(tmp_path, SKILLS_ROOT, dry_run=False, force=False)
    validation = validate_hooks.validate_hooks(tmp_path)

    assert payload["status"] == "updated"
    assert Path(payload["hooks_path"]).exists()
    assert validation["status"] == "pass"


def test_codex_hooks_installer_is_idempotent(tmp_path: Path) -> None:
    first = install_hooks.install(tmp_path, SKILLS_ROOT, dry_run=False, force=False)
    second = install_hooks.install(tmp_path, SKILLS_ROOT, dry_run=False, force=False)

    assert first["changed"] is True
    assert second["changed"] is False
