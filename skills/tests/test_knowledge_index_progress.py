from __future__ import annotations

import importlib.util
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

    html = module.render_interactive_html(minimal_index(), minimal_graph())

    assert 'id="progress-panel"' in html
    assert 'role="progressbar"' in html
    assert 'id="progress-phase"' in html
    assert 'id="progress-speed"' in html
    assert 'id="progress-errors"' in html
    assert 'fetch("index-progress.json", {cache:"no-store"})' in html
    assert 'new EventSource("/events")' in html
    assert 'events.onmessage' in html


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
