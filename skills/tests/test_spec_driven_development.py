from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = SKILLS_ROOT / "codex-spec-driven-development" / "scripts" / "init_spec.py"
CHECK_SCRIPT = SKILLS_ROOT / "codex-spec-driven-development" / "scripts" / "check_spec.py"


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


init_spec = load_script_module("skills_init_spec_full", "codex-spec-driven-development/scripts/init_spec.py")
check_spec = load_script_module("skills_check_spec_full", "codex-spec-driven-development/scripts/check_spec.py")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_init_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INIT_SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )


def run_check_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )


def test_init_spec_slugify_and_parse_csv_are_stable() -> None:
    assert init_spec.slugify("  Build Admin/Auth Flow!!!  ") == "build-admin-auth-flow"
    assert init_spec.slugify("!!!") == "spec"
    assert init_spec.parse_csv("Frontend, backend,frontend, QA ") == ["Frontend", "backend", "QA"]


def test_init_spec_cli_creates_and_skips_without_force(tmp_path: Path) -> None:
    first = run_init_cli(
        "--project-root",
        str(tmp_path),
        "--title",
        "Admin Dashboard",
        "--prompt",
        "Build admin dashboard",
        "--domains",
        "frontend,backend",
        "--slug",
        "admin-dashboard",
    )
    second = run_init_cli(
        "--project-root",
        str(tmp_path),
        "--title",
        "Admin Dashboard",
        "--slug",
        "admin-dashboard",
    )

    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    spec_path = Path(first_payload["spec_path"])
    assert first.returncode == 0
    assert first_payload["status"] == "created"
    assert spec_path.exists()
    assert "Domains: frontend, backend" in spec_path.read_text(encoding="utf-8")
    assert second.returncode == 0
    assert second_payload["status"] == "skipped"


def test_init_spec_cli_force_overwrites_existing_spec(tmp_path: Path) -> None:
    spec_path = tmp_path / ".codex" / "specs" / "demo" / "SPEC.md"
    write(spec_path, "old\n")

    result = run_init_cli("--project-root", str(tmp_path), "--title", "New Title", "--slug", "demo", "--force")

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["status"] == "created"
    assert "# Spec: New Title" in spec_path.read_text(encoding="utf-8")


def test_init_spec_cli_missing_project_root_returns_json_error(tmp_path: Path) -> None:
    result = run_init_cli("--project-root", str(tmp_path / "missing"), "--title", "Demo")

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "error"
    assert "Project root does not exist" in payload["message"]


def test_check_spec_classifies_test_files_as_qa_before_backend() -> None:
    assert check_spec.classify_file("tests/test_api.py") == "qa"
    assert check_spec.classify_file("server/tests/test_auth.py") == "qa"
    assert check_spec.classify_file("server/routes/auth.py") == "backend"
    assert check_spec.classify_file(".github/workflows/ci.yml") == "devops"


def test_check_spec_parse_metadata_legacy_and_without_ac() -> None:
    metadata = check_spec.parse_spec_metadata(
        """Status: Active
Domains: Frontend, QA

## Acceptance Criteria
- [ ] AC-002: Works
- [ ] AC-001: Also works
"""
    )

    assert metadata["schema_version"] == ""
    assert metadata["status"] == "active"
    assert metadata["domains"] == ["frontend", "qa"]
    assert metadata["acceptance_criteria"] == ["AC-001", "AC-002"]


def test_check_spec_report_warns_for_legacy_draft_and_missing_ac(tmp_path: Path) -> None:
    write(
        tmp_path / ".codex" / "specs" / "legacy" / "SPEC.md",
        """# Legacy Spec
Status: draft
Domains: frontend

No acceptance criteria yet.
""",
    )

    report = check_spec.build_report(tmp_path, ["src/App.tsx"])

    assert report["overall"] == "warn"
    assert report["matched_specs"] == ["legacy"]
    assert report["legacy_specs"] == ["legacy"]
    assert report["draft_specs"] == ["legacy"]
    assert report["specs_without_acceptance_criteria"] == ["legacy"]
    assert any("Schema-Version" in action for action in report["suggested_actions"])


def test_check_spec_report_warns_for_unmapped_domain_file(tmp_path: Path) -> None:
    write(tmp_path / ".codex" / "specs" / "frontend-only" / "SPEC.md", init_spec.render_spec("UI", "Build UI", ["frontend"]))

    report = check_spec.build_report(tmp_path, ["server/routes/auth.py"])

    assert report["overall"] == "warn"
    assert report["unmapped_files"] == ["server/routes/auth.py"]
    assert report["matched_specs"] == []
    assert "Traceability table" in report["suggested_actions"][0]


def test_check_spec_cli_text_output(tmp_path: Path) -> None:
    write(tmp_path / ".codex" / "specs" / "frontend" / "SPEC.md", init_spec.render_spec("UI", "Build UI", ["frontend"]))

    result = run_check_cli("--project-root", str(tmp_path), "--changed-files", "src/App.tsx", "--format", "text")

    assert result.returncode == 0
    assert "Overall: pass" in result.stdout
    assert "Matched specs: frontend" in result.stdout
    assert "Unmapped files: none" in result.stdout


def test_check_spec_cli_missing_project_root_returns_json_error(tmp_path: Path) -> None:
    result = run_check_cli("--project-root", str(tmp_path / "missing"), "--changed-files", "src/App.tsx")

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["schema_version"] == "1.0"
    assert payload["status"] == "error"
    assert payload["overall"] == "warn"
