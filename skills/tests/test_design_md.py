from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


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


def test_cli_scaffold_writes_output(tmp_path: Path) -> None:
    output_path = tmp_path / "DESIGN.md"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "scaffold",
            "--name",
            "Atlas Console",
            "--description",
            "Design contract for Atlas Console.",
            "--output",
            str(output_path),
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
    assert payload["status"] == "scaffold"
    assert output_path.exists()
    text = output_path.read_text(encoding="utf-8")
    assert "Atlas Console" in text
    assert "## Components" in text
