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


install_cursor = load_script_module("install_cursor_native_test", ".system/scripts/install_cursor_native.py")
pack_install = load_script_module("pack_install_test", ".system/scripts/install.py")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def test_install_cursor_native_repo_scope_writes_rule(tmp_path: Path) -> None:
    source = tmp_path / "source"
    repo = tmp_path / "repo"
    write(source / "codex-master-instructions" / "SKILL.md", "demo\n")
    write(source / ".system" / "manifest.json", "{}\n")
    target = install_cursor.resolve_target("repo", str(repo), "")
    payload = install_cursor.install(source, target, dry_run=False, repo_root=repo)

    assert target == repo / ".cursor" / "skills"
    assert payload["cursor_install"] is True
    assert (repo / ".cursor" / "rules" / "codexai-core.mdc").exists()
    rule = (repo / ".cursor" / "rules" / "codexai-core.mdc").read_text(encoding="utf-8")
    assert "alwaysApply: true" in rule
    assert "codex-master-instructions" in rule


def test_install_doctor_reports_missing_cursor_wiring(tmp_path: Path) -> None:
    report = pack_install.doctor_host("cursor", "repo", tmp_path)
    assert report["host"] == "cursor"
    assert report["status"] == "fail"
    names = {item["name"]: item["status"] for item in report["checks"]}
    assert names["cursor_rule"] == "fail"
    assert names["skills_root"] == "fail"


def test_install_doctor_plugin_source_cursor_is_pass(tmp_path: Path) -> None:
    write(tmp_path / "skills" / "codex-master-instructions" / "SKILL.md", "demo\n")
    write(
        tmp_path / ".cursor" / "rules" / "codexai-core.mdc",
        "<!-- codexai-agentic-workflow:start -->\n# CodexAI Core\n<!-- codexai-agentic-workflow:end -->\n",
    )
    report = pack_install.doctor_host("cursor", "repo", tmp_path)
    assert report["status"] == "pass"
    names = {item["name"]: item["status"] for item in report["checks"]}
    assert names["skills_root"] == "pass"
    assert names["cursor_rule"] == "pass"
    assert names["master_skill"] == "pass"
