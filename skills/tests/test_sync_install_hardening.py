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


sync_global = load_script_module("sync_global_skills_hardening", ".system/scripts/sync_global_skills.py")
install_native = load_script_module("install_codex_native_hardening", ".system/scripts/install_codex_native.py")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def test_sync_skips_runtime_cache_and_protected_builtin_system_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write(source / "codex-demo" / "SKILL.md", "demo\n")
    write(source / "codex-demo" / "__pycache__" / "demo.pyc", "bytecode\n")
    write(source / ".pytest_cache" / "state", "cache\n")
    write(source / ".ruff_cache" / "state", "cache\n")
    write(source / "htmlcov" / "index.html", "coverage\n")
    write(source / "dist" / "CodexAI.zip", "zip\n")
    write(source / ".git" / "HEAD", "ref: refs/heads/main\n")
    write(source / "node_modules" / "left-pad" / "index.js", "module.exports = ''\n")
    write(source / "cache" / "runtime.json", "{}\n")
    write(source / "state" / "runtime.json", "{}\n")
    write(source / "codex-demo" / "debug.log", "log\n")
    write(source / "codex-demo" / "patch.tmp", "tmp\n")
    write(source / "codex-demo" / "old.bak", "backup\n")
    write(source / ".system" / "skill-creator" / "SKILL.md", "protected\n")

    payload = sync_global.sync(source, target, dry_run=True)

    assert "codex-demo/SKILL.md" in payload["planned_files"]
    assert not any("__pycache__" in path for path in payload["planned_files"])
    assert not any(".pytest_cache" in path for path in payload["planned_files"])
    assert not any(".ruff_cache" in path for path in payload["planned_files"])
    assert not any("htmlcov" in path for path in payload["planned_files"])
    assert not any(path.startswith("dist/") for path in payload["planned_files"])
    assert not any(path.startswith(".git/") for path in payload["planned_files"])
    assert not any(path.startswith("node_modules/") for path in payload["planned_files"])
    assert not any(path.startswith("cache/") for path in payload["planned_files"])
    assert not any(path.startswith("state/") for path in payload["planned_files"])
    assert not any(path.endswith((".log", ".tmp", ".bak")) for path in payload["planned_files"])
    assert ".system/skill-creator/SKILL.md" in payload["protected_skipped"]
    assert ".system/skill-creator/SKILL.md" not in payload["planned_files"]


def test_sync_apply_backs_up_existing_changed_file(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    backup = tmp_path / "backup"
    write(source / "codex-demo" / "SKILL.md", "new\n")
    write(target / "codex-demo" / "SKILL.md", "old\n")

    payload = sync_global.sync(source, target, dry_run=False, backup_dir=backup)

    assert payload["status"] == "synced"
    assert payload["copied_files"] == ["codex-demo/SKILL.md"]
    assert payload["backed_up_files"] == ["codex-demo/SKILL.md"]
    assert (target / "codex-demo" / "SKILL.md").read_text(encoding="utf-8") == "new\n"
    assert (backup / "codex-demo" / "SKILL.md").read_text(encoding="utf-8") == "old\n"


def test_restore_backup_round_trip(tmp_path: Path) -> None:
    backup = tmp_path / "backup"
    target = tmp_path / "target"
    write(backup / "codex-demo" / "SKILL.md", "restored\n")
    write(target / "codex-demo" / "SKILL.md", "current\n")

    dry_run = sync_global.restore_backup(backup, target, dry_run=True)
    applied = sync_global.restore_backup(backup, target, dry_run=False)

    assert dry_run["status"] == "dry_run"
    assert dry_run["planned_files"] == ["codex-demo/SKILL.md"]
    assert applied["status"] == "restored"
    assert applied["restored_files"] == ["codex-demo/SKILL.md"]
    assert (target / "codex-demo" / "SKILL.md").read_text(encoding="utf-8") == "restored\n"


def test_sync_rejects_missing_source_root(tmp_path: Path) -> None:
    try:
        sync_global.sync(tmp_path / "missing", tmp_path / "target", dry_run=True)
    except FileNotFoundError as exc:
        assert "Source skills root does not exist" in str(exc)
    else:  # pragma: no cover - defensive failure branch
        raise AssertionError("expected FileNotFoundError")


def test_default_global_root_requires_home_environment(monkeypatch) -> None:
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.delenv("HOME", raising=False)

    try:
        sync_global.default_global_root()
    except RuntimeError as exc:
        assert "USERPROFILE/HOME is not set" in str(exc)
    else:  # pragma: no cover - defensive failure branch
        raise AssertionError("expected RuntimeError")


def test_install_codex_native_target_validation(tmp_path: Path) -> None:
    try:
        install_native.resolve_target("repo", "", "")
    except ValueError as exc:
        assert "--repo-root is required" in str(exc)
    else:  # pragma: no cover - defensive failure branch
        raise AssertionError("expected ValueError")

    try:
        install_native.resolve_target("custom", "", "")
    except ValueError as exc:
        assert "--target-root is required" in str(exc)
    else:  # pragma: no cover - defensive failure branch
        raise AssertionError("expected ValueError")

    assert install_native.resolve_target("repo", str(tmp_path), "") == tmp_path.resolve() / ".agents" / "skills"


def test_install_codex_native_user_scope_uses_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.delenv("HOME", raising=False)

    assert install_native.resolve_target("user", "", "") == tmp_path / "home" / ".agents" / "skills"
    assert install_native.resolve_target("legacy", "", "") == tmp_path / "home" / ".codex" / "skills"


def test_install_codex_native_cli_invalid_source_returns_json_error(tmp_path: Path) -> None:
    script = SKILLS_ROOT / ".system" / "scripts" / "install_codex_native.py"
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


def test_install_codex_native_install_apply_copies_into_target(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write(source / "codex-demo" / "SKILL.md", "demo\n")

    payload = install_native.install(source, target, dry_run=False)

    assert payload["status"] == "synced"
    assert payload["native_install"] is True
    assert (target / "codex-demo" / "SKILL.md").read_text(encoding="utf-8") == "demo\n"
