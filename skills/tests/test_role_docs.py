from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


SKILLS_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = SKILLS_ROOT / ".system" / "manifest.json"
AGENTS_ROOT = SKILLS_ROOT / ".agents"


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    script_dir = str(path.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


init_role_docs = load_script_module(
    "skills_init_role_docs",
    "codex-role-docs/scripts/init_role_docs.py",
)
update_role_docs = load_script_module(
    "skills_update_role_docs",
    "codex-role-docs/scripts/update_role_docs.py",
)
build_role_docs_index = load_script_module(
    "skills_build_role_docs_index",
    "codex-role-docs/scripts/build_role_docs_index.py",
)
check_role_docs = load_script_module(
    "skills_check_role_docs_script",
    "codex-role-docs/scripts/check_role_docs.py",
)
auto_gate = load_script_module(
    "skills_auto_gate_for_role_docs",
    "codex-execution-quality-gate/scripts/auto_gate.py",
)


def parse_agent_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    return yaml.safe_load(text.split("---\n", 2)[1])


def test_role_docs_skill_registered_in_manifest() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert "codex-role-docs" in manifest["skills"]
    assert "codex-role-docs" in manifest["load_order"]["on-demand"]


def test_init_role_docs_creates_required_docs_and_is_idempotent(tmp_path: Path) -> None:
    payload = init_role_docs.initialize_role_docs(tmp_path, ["frontend", "backend"], force=False)
    assert payload["status"] == "created"
    assert (tmp_path / ".codex/project-docs/PROJECT-BRIEF.md").exists()
    assert (tmp_path / ".codex/project-docs/decisions/ADR-0001-template.md").exists()
    assert (tmp_path / ".codex/project-docs/frontend/FE-04-component-inventory.md").exists()
    assert (tmp_path / ".codex/project-docs/backend/BE-01-api-contracts.md").exists()

    second = init_role_docs.initialize_role_docs(tmp_path, ["frontend", "backend"], force=False)
    assert second["status"] == "up_to_date"
    assert second["files_created"] == []
    assert "frontend/FE-04-component-inventory.md" in "\n".join(second["files_skipped"])


def test_init_role_docs_rejects_missing_project_root(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing"
    with pytest.raises(NotADirectoryError):
        init_role_docs.initialize_role_docs(missing_root, ["frontend"], force=False)


def test_update_role_docs_appends_update_and_source_files(tmp_path: Path) -> None:
    init_role_docs.initialize_role_docs(tmp_path, ["frontend"], force=False)
    payload = update_role_docs.update_role_doc(
        project_root=tmp_path,
        role="frontend",
        doc_id="FE-04",
        summary="Added reusable Header component props and variants.",
        files=["src/components/Header.tsx"],
    )
    assert payload["status"] == "updated"
    doc_text = (tmp_path / ".codex/project-docs/frontend/FE-04-component-inventory.md").read_text(encoding="utf-8")
    assert "- src/components/Header.tsx" in doc_text
    assert "Added reusable Header component props and variants." in doc_text


def test_build_role_docs_index_emits_valid_json(tmp_path: Path) -> None:
    init_role_docs.initialize_role_docs(tmp_path, ["qa"], force=False)
    payload = build_role_docs_index.build_index(tmp_path)
    index_path = tmp_path / ".codex/project-docs/index.json"
    assert payload["status"] == "indexed"
    assert index_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert any(item["path"].endswith("qa/QA-01-regression-map.md") for item in index["documents"])


def test_check_role_docs_maps_representative_files(tmp_path: Path) -> None:
    init_role_docs.initialize_role_docs(tmp_path, ["frontend", "backend", "devops", "admin", "qa"], force=False)
    payload = check_role_docs.check_role_docs(
        tmp_path,
        [
            "src/components/Header.tsx",
            "routes/auth.js",
            "migrations/001_create_users.sql",
            ".github/workflows/ci.yml",
            "tests/test_auth.py",
            "src/admin/permissions.ts",
            "src/admin/dashboard.tsx",
        ],
    )
    docs = {item["doc"] for item in payload["suggested_updates"]}
    assert ".codex/project-docs/frontend/FE-04-component-inventory.md" in docs
    assert ".codex/project-docs/backend/BE-01-api-contracts.md" in docs
    assert ".codex/project-docs/backend/BE-02-database-design.md" in docs
    assert ".codex/project-docs/devops/DO-02-ci-cd.md" in docs
    assert ".codex/project-docs/qa/QA-01-regression-map.md" in docs
    assert ".codex/project-docs/admin/AD-01-roles-permissions.md" in docs
    assert ".codex/project-docs/admin/AD-05-dashboard-reports.md" in docs


def test_check_role_docs_skips_when_docs_root_is_not_initialized(tmp_path: Path) -> None:
    payload = check_role_docs.check_role_docs(tmp_path)
    assert payload["overall"] == "skip"
    assert payload["missing_docs"] == []
    assert payload["suggested_updates"] == []


def test_check_role_docs_explicit_changed_files_still_suggests_docs_without_docs_root(tmp_path: Path) -> None:
    payload = check_role_docs.check_role_docs(tmp_path, ["src/components/Header.tsx"])
    docs = {item["doc"] for item in payload["suggested_updates"]}
    assert payload["overall"] == "warn"
    assert ".codex/project-docs/frontend/FE-04-component-inventory.md" in docs
    assert ".codex/project-docs/frontend/FE-04-component-inventory.md" in payload["missing_docs"]


def test_check_role_docs_cli_errors_for_missing_project_root(tmp_path: Path) -> None:
    script_path = SKILLS_ROOT / "codex-role-docs" / "scripts" / "check_role_docs.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--project-root",
            str(tmp_path / "missing"),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert "Project root does not exist or is not a directory" in payload["message"]


def test_agent_ownership_includes_role_docs() -> None:
    expected = {
        "frontend-specialist.md": ".codex/project-docs/frontend/**/*",
        "backend-specialist.md": ".codex/project-docs/backend/**/*",
        "devops-engineer.md": ".codex/project-docs/devops/**/*",
        "test-engineer.md": ".codex/project-docs/qa/**/*",
        "planner.md": ".codex/project-docs/PROJECT-BRIEF.md",
        "security-auditor.md": ".codex/project-docs/admin/AD-03-audit-logs.md",
        "debugger.md": ".codex/project-docs/qa/QA-01-regression-map.md",
    }
    for filename, pattern in expected.items():
        payload = parse_agent_frontmatter(AGENTS_ROOT / filename)
        assert pattern in payload["file_ownership"]


def test_auto_gate_role_docs_warning_is_non_blocking(tmp_path: Path, monkeypatch) -> None:
    def result(payload, warnings=None):
        return {"payload": payload, "blocking_issues": [], "warnings": warnings or []}

    monkeypatch.setitem(auto_gate.CHECK_RUNNERS, "security", lambda project_root: result({"status": "pass", "critical": 0, "warnings": 0}))
    monkeypatch.setitem(auto_gate.CHECK_RUNNERS, "gate", lambda project_root: result({"status": "pass", "lint": "pass", "test": "pass"}))
    monkeypatch.setitem(auto_gate.CHECK_RUNNERS, "tech_debt", lambda project_root: result({"status": "pass", "total_issues": 0, "warnings": 0}))
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "role_docs",
        lambda project_root: result(
            {"status": "warn", "overall": "warn", "missing_docs": 1, "stale_docs": 0, "suggested_updates": 0},
            warnings=["Role docs advisory: 1 missing doc(s), 0 stale doc(s), 0 suggested update(s)."],
        ),
    )

    report, exit_code = auto_gate.run_auto_gate(tmp_path, "full")
    assert exit_code == 0
    assert report["overall"] == "pass"
    assert report["checks"]["role_docs"]["status"] == "warn"
    assert report["warnings"] == ["Role docs advisory: 1 missing doc(s), 0 stale doc(s), 0 suggested update(s)."]


def test_auto_gate_role_docs_skip_has_no_warning(tmp_path: Path, monkeypatch) -> None:
    def result(payload, warnings=None):
        return {"payload": payload, "blocking_issues": [], "warnings": warnings or []}

    monkeypatch.setitem(auto_gate.CHECK_RUNNERS, "security", lambda project_root: result({"status": "pass", "critical": 0, "warnings": 0}))
    monkeypatch.setitem(auto_gate.CHECK_RUNNERS, "gate", lambda project_root: result({"status": "pass", "lint": "pass", "test": "pass"}))
    monkeypatch.setitem(auto_gate.CHECK_RUNNERS, "tech_debt", lambda project_root: result({"status": "pass", "total_issues": 0, "warnings": 0}))
    monkeypatch.setitem(
        auto_gate.CHECK_RUNNERS,
        "role_docs",
        lambda project_root: result(
            {"status": "skip", "overall": "skip", "missing_docs": 0, "stale_docs": 0, "suggested_updates": 0}
        ),
    )

    report, exit_code = auto_gate.run_auto_gate(tmp_path, "full")
    assert exit_code == 0
    assert report["overall"] == "pass"
    assert report["checks"]["role_docs"]["status"] == "skip"
    assert report["warnings"] == []
