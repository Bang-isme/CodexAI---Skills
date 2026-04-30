from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILLS_ROOT / "codex-execution-quality-gate" / "scripts" / "smart_test_selector.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("skills_smart_test_selector_full", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["skills_smart_test_selector_full"] = module
    spec.loader.exec_module(module)
    return module


smart_test_selector = load_script_module()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


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


def test_selector_parse_changed_files_normalizes_dedupes_and_sorts() -> None:
    assert smart_test_selector.parse_changed_files(r"src\b.ts, src/a.ts, src/b.ts, src/a.ts") == [
        "src/a.ts",
        "src/b.ts",
    ]


def test_selector_collect_test_files_skips_dependency_and_cache_dirs(tmp_path: Path) -> None:
    write(tmp_path / "src" / "user.test.ts", "test('x', () => {})")
    write(tmp_path / "src" / "__tests__" / "flow.ts", "test('x', () => {})")
    write(tmp_path / "node_modules" / "pkg" / "bad.test.ts", "test('x', () => {})")
    write(tmp_path / "__pycache__" / "bad_test.py", "def test_x(): pass")

    assert smart_test_selector.collect_test_files(tmp_path) == [
        "src/__tests__/flow.ts",
        "src/user.test.ts",
    ]


def test_selector_import_tracing_matches_es_import_and_require(tmp_path: Path) -> None:
    write(tmp_path / "src" / "user.ts", "export const user = 1")
    write(tmp_path / "tests" / "user.spec.ts", "import { user } from '../src/user'")
    write(tmp_path / "tests" / "legacy.test.js", "const user = require('../src/user')")
    reasons: dict[str, set[str]] = {}

    found = smart_test_selector.strategy_import_tracing(
        tmp_path,
        ["src/user.ts"],
        {"tests/user.spec.ts", "tests/legacy.test.js"},
        reasons,
        {"src/user.ts": False},
    )

    assert found["src/user.ts"] is True
    assert reasons["tests/user.spec.ts"] == {"imports user"}
    assert reasons["tests/legacy.test.js"] == {"imports user"}


def test_selector_proximity_matches_same_directory_and_nested_tests() -> None:
    reasons: dict[str, set[str]] = {}
    found_by_changed = {"src/order.ts": False}

    smart_test_selector.strategy_proximity(
        ["src/order.ts"],
        {"src/order.spec.ts", "src/__tests__/order.integration.ts", "tests/order.spec.ts"},
        reasons,
        found_by_changed,
    )

    assert reasons["src/order.spec.ts"] == {"directory proximity"}
    assert reasons["src/__tests__/order.integration.ts"] == {"directory proximity"}
    assert "tests/order.spec.ts" not in reasons


def test_selector_detect_runner_prefers_explicit_and_detects_configs(tmp_path: Path) -> None:
    assert smart_test_selector.detect_runner(tmp_path, "vitest") == "vitest"
    write(tmp_path / "pytest.ini", "[pytest]\n")
    assert smart_test_selector.detect_runner(tmp_path, "") == "pytest"

    js_root = tmp_path / "js"
    write(js_root / "package.json", '{"scripts":{"test":"vitest"},"devDependencies":{"vitest":"latest"}}')
    assert smart_test_selector.detect_runner(js_root, "") == "vitest"

    jest_root = tmp_path / "jest"
    write(jest_root / "jest.config.js", "module.exports = {}\n")
    assert smart_test_selector.detect_runner(jest_root, "") == "jest"


def test_selector_run_command_handles_runner_start_failures(monkeypatch, tmp_path: Path) -> None:
    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(smart_test_selector.subprocess, "run", raise_file_not_found)
    assert smart_test_selector.run_command(tmp_path, ["missing"])["error"] == "runner not found"

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=300)

    monkeypatch.setattr(smart_test_selector.subprocess, "run", raise_timeout)
    assert "timed out" in smart_test_selector.run_command(tmp_path, ["pytest"])["error"]

    def raise_os_error(*args, **kwargs):
        raise OSError("bad cwd")

    monkeypatch.setattr(smart_test_selector.subprocess, "run", raise_os_error)
    assert smart_test_selector.run_command(tmp_path, ["pytest"])["error"] == "bad cwd"


def test_selector_maybe_run_tests_handles_empty_selection_and_missing_runner(tmp_path: Path) -> None:
    run_result, warnings = smart_test_selector.maybe_run_tests(tmp_path, [], "")
    assert run_result is None
    assert warnings == ["No related tests selected. Consider running full suite."]

    run_result, warnings = smart_test_selector.maybe_run_tests(tmp_path, ["tests/test_app.py"], "")
    assert run_result is None
    assert warnings == ["No supported test runner detected. Skipped --run execution."]


def test_selector_maybe_run_tests_parses_runner_output(monkeypatch, tmp_path: Path) -> None:
    write(tmp_path / "pytest.ini", "[pytest]\n")

    def fake_run_command(project_root: Path, parts: list[str]) -> dict[str, object]:
        return {
            "ok": True,
            "exit_code": 1,
            "stdout": "2 passed, 1 failed",
            "stderr": "",
            "duration_ms": 42,
        }

    monkeypatch.setattr(smart_test_selector, "run_command", fake_run_command)

    run_result, warnings = smart_test_selector.maybe_run_tests(tmp_path, ["tests/test_app.py"], "")

    assert warnings == []
    assert run_result == {
        "runner": "pytest",
        "exit_code": 1,
        "passed": 2,
        "failed": 1,
        "duration_ms": 42,
    }


def test_selector_human_box_is_ascii_only() -> None:
    text = smart_test_selector.render_human_box("SMART TEST SELECTOR RESULTS", ["Changed Files:  1"])

    assert text.startswith("+")
    assert "|" in text
    text.encode("ascii")


def test_selector_cli_missing_project_root_returns_json_error(tmp_path: Path) -> None:
    result = run_cli("--project-root", str(tmp_path / "missing"))

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "error"
    assert "Project root does not exist" in payload["message"]


def test_selector_cli_no_git_requires_changed_files(tmp_path: Path) -> None:
    result = run_cli("--project-root", str(tmp_path))

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "error"
    assert "Git repository required" in payload["message"]


def test_selector_cli_selects_tests_and_prints_ascii_human_summary(tmp_path: Path) -> None:
    write(tmp_path / "src" / "user.ts", "export const user = 1")
    write(tmp_path / "tests" / "user.test.ts", "import { user } from '../src/user'")

    result = run_cli(
        "--project-root",
        str(tmp_path),
        "--changed-files",
        "src/user.ts",
        "--human",
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["selected_count"] == 1
    assert payload["selected_tests"][0]["test"] == "tests/user.test.ts"
    assert "SMART TEST SELECTOR RESULTS" in result.stderr
    result.stderr.encode("ascii")
