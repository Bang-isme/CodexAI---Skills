from __future__ import annotations

import importlib.util
import subprocess
import sys
import zipfile
from configparser import ConfigParser
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


release_zip = load_script_module("build_release_zip_script", ".system/scripts/build_release_zip.py")


def test_render_docx_help_does_not_require_site_packages() -> None:
    script = SKILLS_ROOT / "codex-doc-renderer" / "scripts" / "render_docx.py"

    result = subprocess.run(
        [sys.executable, "-S", str(script), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert "pdf2image" not in result.stderr


def test_gitignore_is_utf8_without_bom_and_ignores_runtime_artifacts() -> None:
    raw = (REPO_ROOT / ".gitignore").read_bytes()
    text = raw.decode("utf-8")

    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    for pattern in [
        "__pycache__/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        "dist/",
        "*.log",
        ".codexai-backups/",
        "cache/",
        "state/",
    ]:
        assert pattern in text


def test_release_zip_excludes_repository_and_runtime_artifacts(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".git" / "objects").mkdir(parents=True)
    (project / "skills" / ".system" / "scripts").mkdir(parents=True)
    (project / "skills" / ".analytics").mkdir(parents=True)
    (project / "skills" / "__pycache__").mkdir(parents=True)
    (project / ".pytest_cache").mkdir()
    (project / ".codexai-backups").mkdir()
    (project / "skills" / "VERSION").write_text("99.0.0\n", encoding="utf-8")
    (project / "README.md").write_text("# Release\n", encoding="utf-8")
    (project / ".coveragerc").write_text("[run]\nsource = skills\n", encoding="utf-8")
    (project / ".codex-plugin").mkdir()
    (project / ".codex-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (project / ".claude-plugin").mkdir()
    (project / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (project / "hooks").mkdir()
    (project / "hooks" / "hooks.json").write_text("{}", encoding="utf-8")
    (project / "skills" / ".analytics" / "usage-log.jsonl").write_text("{}", encoding="utf-8")
    (project / "skills" / ".system" / ".codex-system-skills.marker").write_text("", encoding="utf-8")
    (project / ".git" / "objects" / "leak").write_text("secret", encoding="utf-8")
    (project / "skills" / "__pycache__" / "x.pyc").write_bytes(b"bytecode")
    (project / ".pytest_cache" / "state").write_text("cache", encoding="utf-8")
    (project / ".codexai-backups" / "backup.txt").write_text("backup", encoding="utf-8")
    (project / "skills" / ".system" / "scripts" / "tool.py").write_text("print('ok')\n", encoding="utf-8")

    output = tmp_path / "release.zip"
    payload = release_zip.build_zip(project, output, include_tests=True, dry_run=False)

    assert payload["status"] == "generated"
    with zipfile.ZipFile(output) as archive:
        entries = archive.namelist()

    assert "README.md" in entries
    assert ".coveragerc" in entries
    assert ".codex-plugin/plugin.json" in entries
    assert ".claude-plugin/plugin.json" in entries
    assert "hooks/hooks.json" in entries
    assert "skills/.system/scripts/tool.py" in entries
    assert not any("/.git/" in f"/{entry}" for entry in entries)
    assert not any("__pycache__" in entry or entry.endswith(".pyc") for entry in entries)
    assert not any(".pytest_cache" in entry for entry in entries)
    assert not any(".codexai-backups" in entry for entry in entries)
    assert not any(".analytics" in entry for entry in entries)
    assert not any(".codex-system-skills.marker" in entry for entry in entries)


def test_release_zip_can_exclude_tests(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "skills" / "tests").mkdir(parents=True)
    (project / "skills" / "VERSION").write_text("99.0.0\n", encoding="utf-8")
    (project / "skills" / "tests" / "test_demo.py").write_text("def test_demo(): pass\n", encoding="utf-8")
    (project / "skills" / "codex-demo").mkdir()
    (project / "skills" / "codex-demo" / "SKILL.md").write_text("---\nname: codex-demo\n---\n", encoding="utf-8")

    output = tmp_path / "release-no-tests.zip"
    release_zip.build_zip(project, output, include_tests=False, dry_run=False)

    with zipfile.ZipFile(output) as archive:
        entries = archive.namelist()

    assert "skills/codex-demo/SKILL.md" in entries
    assert not any(entry.startswith("skills/tests/") for entry in entries)


def test_release_zip_missing_project_root_returns_controlled_error(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing"

    try:
        release_zip.build_zip(missing_root, tmp_path / "out.zip", include_tests=True, dry_run=False)
    except FileNotFoundError as exc:
        assert "Project root does not exist" in str(exc)
    else:  # pragma: no cover - defensive failure branch
        raise AssertionError("expected FileNotFoundError")


def test_coveragerc_measures_source_only_and_excludes_tests() -> None:
    parser = ConfigParser()
    parser.read(REPO_ROOT / ".coveragerc", encoding="utf-8")

    run_source = "\n".join(parser.get("run", "source").splitlines())
    run_omit = "\n".join(parser.get("run", "omit").splitlines())

    assert "skills/codex-execution-quality-gate/scripts" in run_source
    assert "skills/codex-runtime-hook/scripts" in run_source
    assert "*/tests/*" in run_omit
    assert "*/.codexai-backups/*" in run_omit
