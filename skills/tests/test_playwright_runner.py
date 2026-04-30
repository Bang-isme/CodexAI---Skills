from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILLS_ROOT / "codex-execution-quality-gate" / "scripts" / "playwright_runner.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("skills_playwright_runner_full", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["skills_playwright_runner_full"] = module
    spec.loader.exec_module(module)
    return module


playwright_runner = load_script_module()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )


def make_args(**overrides: object):
    payload = {
        "url": "",
        "test_dir": "",
        "browser": "chromium",
    }
    payload.update(overrides)
    return type("Args", (), payload)()


def test_playwright_slug_from_url_handles_home_path_and_symbols() -> None:
    assert playwright_runner.slug_from_url("http://localhost:3000/") == "home"
    assert playwright_runner.slug_from_url("https://app.test/admin/users?id=1") == "users"
    assert playwright_runner.slug_from_url("https://app.test/Café Déjà Vu") == "caf-d-j-vu"


def test_playwright_choose_output_file_increments_without_overwrite(tmp_path: Path) -> None:
    test_dir = tmp_path / "e2e"
    write(test_dir / "dashboard.spec.js", "existing\n")
    write(test_dir / "dashboard-2.spec.js", "existing\n")

    assert playwright_runner.choose_output_file(test_dir, "dashboard") == test_dir / "dashboard-3.spec.js"


def test_playwright_count_test_files_ignores_non_specs(tmp_path: Path) -> None:
    write(tmp_path / "e2e" / "home.spec.js", "test('x', () => {})")
    write(tmp_path / "e2e" / "settings.test.ts", "test('x', () => {})")
    write(tmp_path / "e2e" / "helper.ts", "export const x = 1")
    write(tmp_path / "e2e" / "notes.md", "# notes")

    assert playwright_runner.count_test_files(tmp_path / "e2e") == 2
    assert playwright_runner.count_test_files(tmp_path / "missing") == 0


def test_playwright_extract_json_blob_handles_ansi_and_wrapped_output() -> None:
    text = "\x1b[31mnoise\x1b[0m\n{\"stats\":{\"expected\":1}}\nmore noise"

    assert playwright_runner.extract_json_blob(text) == {"stats": {"expected": 1}}
    assert playwright_runner.extract_json_blob("not json") is None


def test_playwright_collect_failures_walks_nested_suites() -> None:
    report = {
        "suites": [
            {
                "suites": [
                    {
                        "file": "e2e/login.spec.ts",
                        "specs": [
                            {
                                "title": "login flow",
                                "tests": [
                                    {
                                        "title": "submits credentials",
                                        "results": [
                                            {
                                                "status": "failed",
                                                "errors": [{"message": "Expected dashboard"}],
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        ]
    }

    assert playwright_runner.collect_failures(report) == [
        {
            "test": "submits credentials",
            "file": "e2e/login.spec.ts",
            "error": "Expected dashboard",
        }
    ]


def test_playwright_parse_run_summary_uses_stats_and_fallback() -> None:
    report = {"stats": {"expected": 3, "unexpected": 1, "timedOut": 1, "skipped": 2, "total": 7, "duration": 1234}}

    summary = playwright_runner.parse_run_summary(report, fallback_exit=1, elapsed_ms=9999)
    fallback = playwright_runner.parse_run_summary(None, fallback_exit=1, elapsed_ms=42)

    assert summary["passed"] == 3
    assert summary["failed"] == 2
    assert summary["skipped"] == 2
    assert summary["total"] == 7
    assert summary["duration_ms"] == 1234
    assert fallback["warnings"] == ["Unable to parse Playwright JSON reporter output."]
    assert fallback["failed"] == 1


def test_playwright_browser_install_status_interprets_dry_run_output(monkeypatch, tmp_path: Path) -> None:
    class FakeProcess:
        returncode = 0
        stdout = "chromium is already installed"
        stderr = ""

    monkeypatch.setattr(playwright_runner, "run_command", lambda *args, **kwargs: (FakeProcess(), None))
    assert playwright_runner.browser_install_status(tmp_path, "chromium") is True

    class DownloadProcess:
        returncode = 0
        stdout = "chromium will be downloaded"
        stderr = ""

    monkeypatch.setattr(playwright_runner, "run_command", lambda *args, **kwargs: (DownloadProcess(), None))
    assert playwright_runner.browser_install_status(tmp_path, "chromium") is False


def test_playwright_mode_check_not_installed_outputs_install_steps(monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(playwright_runner, "detect_playwright", lambda root: (False, ""))

    with pytest.raises(SystemExit) as exc_info:
        playwright_runner.mode_check(tmp_path, make_args())

    payload = json.loads(capsys.readouterr().out)
    assert exc_info.value.code == 0
    assert payload["status"] == "not_installed"
    assert "npm init playwright@latest" in payload["install_steps"]


def test_playwright_mode_generate_requires_url(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        playwright_runner.mode_generate(tmp_path, make_args())

    payload = json.loads(capsys.readouterr().out)
    assert exc_info.value.code == 1
    assert payload["status"] == "error"
    assert "requires --url" in payload["message"]


def test_playwright_mode_run_warns_when_test_dir_missing(monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(playwright_runner, "detect_playwright", lambda root: (True, "1.2.3"))

    with pytest.raises(SystemExit) as exc_info:
        playwright_runner.mode_run(tmp_path, make_args(test_dir="e2e"))

    payload = json.loads(capsys.readouterr().out)
    assert exc_info.value.code == 0
    assert payload["status"] == "warn"
    assert "Test directory not found" in payload["message"]


def test_playwright_mode_run_completes_with_parsed_json(monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(tmp_path / "e2e" / "home.spec.js", "test('x', () => {})")
    monkeypatch.setattr(playwright_runner, "detect_playwright", lambda root: (True, "1.2.3"))

    class FakeProcess:
        returncode = 0
        stdout = json.dumps({"stats": {"expected": 1, "unexpected": 0, "skipped": 0, "total": 1, "duration": 25}})
        stderr = ""

    monkeypatch.setattr(playwright_runner, "run_command", lambda *args, **kwargs: (FakeProcess(), None))

    with pytest.raises(SystemExit) as exc_info:
        playwright_runner.mode_run(tmp_path, make_args(test_dir="e2e"))

    payload = json.loads(capsys.readouterr().out)
    assert exc_info.value.code == 0
    assert payload["status"] == "completed"
    assert payload["summary"] == "1/1 passed, 0 failed, 0 skipped (0.0s)"


def test_playwright_cli_missing_project_root_returns_json_error(tmp_path: Path) -> None:
    result = run_cli("--project-root", str(tmp_path / "missing"), "--mode", "check")

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "error"
    assert "Project root does not exist" in payload["message"]
