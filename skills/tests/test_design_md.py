from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILLS_ROOT / "codex-design-md" / "scripts" / "design_contract.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("skills_design_contract", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["skills_design_contract"] = module
    spec.loader.exec_module(module)
    return module


design_contract = load_script_module()


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )


def valid_design_markdown(name: str = "Atlas Console") -> str:
    return design_contract.render_scaffold(
        name,
        "A durable design contract for the dashboard.",
        "Editorial precision with technical clarity.",
    )


def test_render_scaffold_contains_canonical_sections() -> None:
    markdown = design_contract.render_scaffold(
        "Atlas Console",
        "A durable design contract for the dashboard.",
        "Editorial precision with technical clarity.",
    )
    assert 'name: Atlas Console' in markdown
    assert "## Overview" in markdown
    assert "## Colors" in markdown
    assert "## Typography" in markdown
    assert "## Layout" in markdown
    assert "## Elevation & Depth" in markdown
    assert "## Shapes" in markdown
    assert "## Components" in markdown
    assert "## Do's and Don'ts" in markdown


def test_build_doctor_payload_reads_runtime_state(tmp_path: Path) -> None:
    source_repo = tmp_path / "design.md-main"
    (source_repo / "docs").mkdir(parents=True)
    (source_repo / "packages" / "cli" / "src").mkdir(parents=True)
    (source_repo / "docs" / "spec.md").write_text("# DESIGN.md Format\n", encoding="utf-8")
    (source_repo / "packages" / "cli" / "src" / "index.ts").write_text("console.log('noop')\n", encoding="utf-8")

    payload = design_contract.build_doctor_payload(source_repo, "auto")

    assert payload["status"] == "checked"
    assert payload["source_repo"]["exists"] is True
    assert payload["local_repo"]["spec_available"] is True
    assert "selected_runner" in payload


def test_build_doctor_payload_without_source_repo_stays_portable() -> None:
    payload = design_contract.build_doctor_payload(None, "auto")

    assert payload["status"] == "checked"
    assert payload["bundled_engine"] is True
    assert payload["source_repo"]["exists"] is False
    assert payload["selected_runner"] == "bundled-python"


def test_cli_scaffold_writes_output(tmp_path: Path) -> None:
    output_path = tmp_path / "DESIGN.md"
    result = run_cli(
        "scaffold",
        "--name",
        "Atlas Console",
        "--description",
        "Design contract for Atlas Console.",
        "--output",
        str(output_path),
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "scaffold"
    assert output_path.exists()
    text = output_path.read_text(encoding="utf-8")
    assert "Atlas Console" in text
    assert "## Components" in text


def test_cli_help_works_without_external_site_packages() -> None:
    result = subprocess.run(
        [sys.executable, "-S", str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )

    assert result.returncode == 0
    assert "DESIGN.md" in result.stdout


def test_cli_spec_does_not_read_unrelated_cwd_docs_spec(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "spec.md").write_text("# Wrong Project Spec\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "spec", "--format", "markdown"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )

    assert result.returncode == 0
    assert "Wrong Project Spec" not in result.stdout
    assert result.stdout.strip()
    assert any(marker in result.stdout for marker in ("Generated from spec.mdx", "DESIGN.md Format", "DESIGN.md"))


def test_lint_valid_scaffold_has_no_findings() -> None:
    report = design_contract.lint_content(valid_design_markdown())

    assert report["summary"] == {"errors": 0, "warnings": 0, "info": 0}
    assert report["design_system"]["colors"]["primary"] == "#111827"
    assert [section["canonical"] for section in report["sections"]] == design_contract.SECTION_SEQUENCE


def test_lint_reports_broken_reference_duplicate_section_and_bad_color() -> None:
    markdown = """---
colors:
  accent: "blue"
components:
  button:
    backgroundColor: "{colors.missing}"
---

## Colors

## Overview

## Colors
"""

    report = design_contract.lint_content(markdown)
    messages = [finding["message"] for finding in report["findings"]]

    assert report["summary"]["errors"] == 2
    assert report["summary"]["warnings"] >= 2
    assert any("Broken token reference" in message for message in messages)
    assert any("Duplicate section" in message for message in messages)
    assert any("6-digit hex" in message for message in messages)
    assert any("out of canonical order" in message for message in messages)


def test_lint_falls_back_to_simple_yaml_without_pyyaml(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(design_contract, "yaml", None)
    markdown = """---
colors:
  primary: "#102030"
rounded:
  md: 12px
components:
  button:
    rounded: "{rounded.md}"
---

## Overview
"""

    report = design_contract.lint_content(markdown)

    assert report["summary"]["errors"] == 0
    assert report["design_system"]["colors"]["primary"] == "#102030"
    assert report["design_system"]["components"]["button"]["rounded"] == "{rounded.md}"


def test_lint_reports_frontmatter_shape_errors() -> None:
    bad_yaml = design_contract.lint_content("---\n- nope\n---\n\n## Overview\n")
    unterminated = design_contract.lint_content("---\nname: Missing Close\n\n## Overview\n")

    assert bad_yaml["summary"]["errors"] == 1
    assert "Frontmatter must decode to an object" in bad_yaml["findings"][0]["message"]
    assert unterminated["summary"]["errors"] == 1
    assert "Unterminated YAML frontmatter" in unterminated["findings"][0]["message"]


def test_export_tailwind_maps_tokens_to_theme_extension() -> None:
    report = design_contract.lint_content(valid_design_markdown())
    payload = design_contract.export_tailwind(report["design_system"])

    theme = payload["theme"]["extend"]
    assert theme["colors"]["primary"] == "#111827"
    assert theme["fontFamily"]["body-md"] == ["Inter"]
    assert theme["fontSize"]["display-xl"][0] == "3.5rem"
    assert theme["spacing"]["xl"] == "40px"


def test_export_dtcg_wraps_token_groups_with_types() -> None:
    report = design_contract.lint_content(valid_design_markdown())
    payload = design_contract.export_dtcg(report["design_system"])

    assert payload["colors"]["primary"]["$type"] == "color"
    assert payload["rounded"]["md"]["$type"] == "dimension"
    assert payload["spacing"]["lg"]["$type"] == "dimension"
    assert payload["typography"]["body-md"]["$type"] == "typography"


def test_diff_maps_reports_added_removed_and_modified_keys() -> None:
    before = {"primary": "#111111", "accent": "#222222", "old": "#333333"}
    after = {"primary": "#111111", "accent": "#999999", "new": "#444444"}

    diff = design_contract.diff_maps(before, after)

    assert diff == {"added": ["new"], "removed": ["old"], "modified": ["accent"]}


def test_cli_scaffold_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    output_path = tmp_path / "DESIGN.md"
    output_path.write_text("existing\n", encoding="utf-8")

    result = run_cli("scaffold", "--name", "Atlas", "--output", str(output_path))

    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "error"
    assert output_path.read_text(encoding="utf-8") == "existing\n"


def test_cli_lint_text_returns_nonzero_for_broken_contract(tmp_path: Path) -> None:
    design_path = tmp_path / "DESIGN.md"
    design_path.write_text(
        """---
colors:
  primary: "#111827"
components:
  button:
    backgroundColor: "{colors.missing}"
---

## Overview
""",
        encoding="utf-8",
    )

    result = run_cli("lint", str(design_path), "--format", "text")

    assert result.returncode == 1
    assert "DESIGN.md lint report" in result.stdout
    assert "Broken token reference" in result.stdout


def test_cli_diff_reports_regression_when_after_adds_errors(tmp_path: Path) -> None:
    before = tmp_path / "before.md"
    after = tmp_path / "after.md"
    before.write_text(valid_design_markdown(), encoding="utf-8")
    after.write_text(valid_design_markdown().replace("{colors.tertiary}", "{colors.missing}"), encoding="utf-8")

    result = run_cli("diff", str(before), str(after), "--format", "json")

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["regression"] is True
    assert payload["findings"]["delta"]["errors"] == 1


def test_cli_export_tailwind_outputs_json_theme(tmp_path: Path) -> None:
    design_path = tmp_path / "DESIGN.md"
    design_path.write_text(valid_design_markdown(), encoding="utf-8")

    result = run_cli("export", str(design_path), "--format", "tailwind")

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["theme"]["extend"]["colors"]["tertiary"] == "#0F766E"


def test_cli_spec_rules_only_json_is_stable() -> None:
    result = run_cli("spec", "--rules-only", "--format", "json")

    payload = json.loads(result.stdout)
    rule_names = {rule["name"] for rule in payload["rules"]}
    assert result.returncode == 0
    assert payload["status"] == "ok"
    assert {"broken-ref", "duplicate-section", "section-order", "missing-primary"} <= rule_names


def test_resolve_source_repo_uses_environment_variable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source_repo = tmp_path / "design.md-main"
    (source_repo / "docs").mkdir(parents=True)
    (source_repo / "packages" / "cli" / "dist").mkdir(parents=True)
    (source_repo / "docs" / "spec.md").write_text("# DESIGN.md Format\n", encoding="utf-8")
    (source_repo / "packages" / "cli" / "dist" / "index.js").write_text("console.log('noop')\n", encoding="utf-8")
    monkeypatch.setenv(design_contract.SOURCE_REPO_ENV_VAR, str(source_repo))

    assert design_contract.resolve_source_repo("") == source_repo.resolve()


def test_resolve_upstream_runner_handles_missing_requested_runtime() -> None:
    runner, runner_kind = design_contract.resolve_upstream_runner(None, "local")

    assert runner is None
    assert runner_kind == "local-unavailable"
