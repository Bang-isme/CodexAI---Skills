from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
HOOK_INSTALLER = SKILLS_ROOT / "codex-execution-quality-gate" / "scripts" / "install_hooks.py"
CI_INSTALLER = SKILLS_ROOT / "codex-execution-quality-gate" / "scripts" / "install_ci_gate.py"
REGISTRY = SKILLS_ROOT / ".system" / "REGISTRY.md"


def run_python(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )


def init_git_repo(project_root: Path) -> None:
    subprocess.run(
        ["git", "init"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=True,
    )


def test_install_hooks_dry_run_rejects_non_git_directory(tmp_path: Path) -> None:
    result = run_python([str(HOOK_INSTALLER), "--project-root", str(tmp_path), "--dry-run"])

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "error"
    assert "Unable to locate .git directory" in payload["message"]


def test_install_hooks_dry_run_uses_resolved_git_hook_path(tmp_path: Path) -> None:
    init_git_repo(tmp_path)

    result = run_python([str(HOOK_INSTALLER), "--project-root", str(tmp_path), "--dry-run"])

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["status"] == "dry_run"
    assert Path(payload["hook_path"]).name == "pre-commit"
    assert Path(payload["hook_path"]).parent.name == "hooks"


def test_install_hooks_generates_ascii_failure_messages(tmp_path: Path) -> None:
    init_git_repo(tmp_path)

    result = run_python([str(HOOK_INSTALLER), "--project-root", str(tmp_path)])
    payload = json.loads(result.stdout)
    hook_text = Path(payload["hook_path"]).read_text(encoding="utf-8")

    assert result.returncode == 0
    assert "Security scan failed. Fix critical issues before committing." in hook_text
    assert "Pre-commit check failed." in hook_text
    assert "❌" not in hook_text
    assert "â" not in hook_text
    hook_text.encode("ascii")


def test_install_ci_gate_resolves_skills_root_without_vendored_codex_skills(tmp_path: Path) -> None:
    github_root = tmp_path / "github"
    gitlab_root = tmp_path / "gitlab"
    github_root.mkdir()
    gitlab_root.mkdir()

    result = run_python([str(CI_INSTALLER), "--project-root", str(github_root), "--ci", "github"])
    payload = json.loads(result.stdout)
    workflow_text = Path(payload["path"]).read_text(encoding="utf-8")

    assert result.returncode == 0
    assert payload["status"] == "generated"
    assert "Resolve CodexAI Skills" in workflow_text
    assert "CODEX_SKILLS_ROOT" in workflow_text
    assert "git clone --depth 1 https://github.com/Bang-isme/CodexAI---Skills.git" in workflow_text
    assert "python .codex/skills/" not in workflow_text

    result = run_python([str(CI_INSTALLER), "--project-root", str(gitlab_root), "--ci", "gitlab"])
    payload = json.loads(result.stdout)
    gitlab_text = Path(payload["path"]).read_text(encoding="utf-8")

    assert result.returncode == 0
    assert payload["status"] == "generated"
    assert "CODEX_SKILLS_ROOT" in gitlab_text
    assert "git clone --depth 1 https://github.com/Bang-isme/CodexAI---Skills.git" in gitlab_text
    assert "python .codex/skills/" not in gitlab_text


def test_registry_lists_output_quality_scripts() -> None:
    registry_text = REGISTRY.read_text(encoding="utf-8")

    assert "`output_guard.py`" in registry_text
    assert "`editorial_review.py`" in registry_text
