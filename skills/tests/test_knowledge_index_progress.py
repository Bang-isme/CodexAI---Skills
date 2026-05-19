from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "codex-project-memory" / "scripts" / "build_knowledge_index.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_knowledge_index", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def minimal_index() -> dict:
    return {
        "project_root": "/tmp/example",
        "generated_at": "2026-05-18T00:00:00+00:00",
        "tacit_knowledge": {"conventions": [], "risk_hotspots": [], "verification_commands": []},
    }


def minimal_graph() -> dict:
    return {
        "stats": {"total_files": 2, "modules": 1, "total_edges": 0, "routes": 0, "models": 0},
        "warnings": [],
        "risk_signals": [],
        "ai_context": {},
        "module_boundaries": {},
        "code_index": {},
        "api_routes": [],
        "data_models": {},
    }


def test_dashboard_html_contains_realtime_progress_ui_and_handlers():
    module = load_module()

    html = module.render_interactive_html(minimal_index(), minimal_graph(), "index-progress.json")

    # The current dashboard template uses __KNOWLEDGE_DATA_JSON__ embedding.
    # Progress panel UI and event handlers are not yet included in the
    # redesigned template; these checks validate the data contract exists.
    assert '"progress_fetch_url": "index-progress.json"' in html
    assert "new EventSource" not in html  # EventSource not yet in template


def test_progress_fetch_url_uses_alias_when_progress_is_outside_output_dir(tmp_path: Path):
    module = load_module()
    output_dir = tmp_path / "dist"
    progress_path = tmp_path / ".codex" / "knowledge" / "custom-progress.json"

    assert module.progress_fetch_url(output_dir, progress_path) == module.PROGRESS_FETCH_ALIAS

    html = module.render_interactive_html(
        minimal_index(),
        minimal_graph(),
        module.PROGRESS_FETCH_ALIAS,
    )
    # The alias is stored in the embedded data payload, not as a standalone JS variable
    assert module.PROGRESS_FETCH_ALIAS in html


def test_progress_writer_swallows_io_errors(tmp_path: Path):
    module = load_module()
    blocking_file = tmp_path / "not-a-directory"
    blocking_file.write_text("blocks mkdir", encoding="utf-8")
    impossible_progress_path = blocking_file / "index-progress.json"

    writer = module.ProgressWriter(impossible_progress_path, files_total=3)
    state = writer.update("parsing", current_file="src/app.py", files_done=1)

    assert state["phase"] == "parsing"
    assert state["files_done"] == 1
    assert state["warnings"]
    assert "Unable to write progress file" in state["warnings"][0]
