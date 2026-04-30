from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


bundle_check = load_script_module("bundle_check_tests", "codex-execution-quality-gate/scripts/bundle_check.py")
track_usage = load_script_module("track_skill_usage_tests", "codex-project-memory/scripts/track_skill_usage.py")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def test_bundle_check_npm_detects_large_packages_and_missing_lock(tmp_path: Path) -> None:
    write(
        tmp_path / "package.json",
        json.dumps({"dependencies": {"moment": "^2.29.0", "lodash": "^4.17.0"}}),
    )

    report = bundle_check.analyze(tmp_path)

    assert report["package_manager"] == "npm"
    assert report["total_dependencies"] == 2
    assert {item["name"] for item in report["large_packages"]} == {"moment", "lodash"}
    assert any("No npm lock file detected" in warning for warning in report["warnings"])
    assert report["status"] == "warning"


def test_bundle_check_npm_detects_section_conflicts_and_lock_duplicates(tmp_path: Path) -> None:
    write(
        tmp_path / "package.json",
        json.dumps(
            {
                "dependencies": {"react": "18.2.0"},
                "devDependencies": {"react": "17.0.2"},
            }
        ),
    )
    write(
        tmp_path / "package-lock.json",
        json.dumps(
            {
                "packages": {
                    "node_modules/react": {"version": "18.2.0"},
                    "node_modules/react-copy/node_modules/react": {"version": "17.0.2"},
                }
            }
        ),
    )

    report = bundle_check.analyze(tmp_path)
    warnings = "\n".join(report["warnings"])

    assert "Direct dependency version mismatch for 'react'" in warnings
    assert "Multiple lockfile versions for direct dependency 'react': 17.0.2, 18.2.0" in warnings


def test_bundle_check_pip_normalizes_requirements_and_detects_duplicates(tmp_path: Path) -> None:
    write(
        tmp_path / "requirements.txt",
        "\n".join(
            [
                "# comment",
                "-r base.txt",
                "opencv_python==4.9.0",
                "opencv-python>=4.8",
                "requests[security]>=2.0",
            ]
        ),
    )

    report = bundle_check.analyze(tmp_path)
    warnings = "\n".join(report["warnings"])

    assert report["package_manager"] == "pip"
    assert report["total_dependencies"] == 2
    assert report["large_packages"] == [{"name": "opencv-python", "size_estimate": "large native package"}]
    assert "Duplicate dependency entry detected: opencv-python" in warnings


def test_bundle_check_pyproject_without_lock_warns(tmp_path: Path) -> None:
    write(tmp_path / "pyproject.toml", "tensorflow>=2.0\nrequests>=2.0\n")

    report = bundle_check.analyze(tmp_path)

    assert report["package_manager"] == "pip"
    assert report["total_dependencies"] == 2
    assert report["large_packages"] == [{"name": "tensorflow", "size_estimate": "large ml dependency"}]
    assert "Python project has pyproject.toml but no poetry.lock or Pipfile.lock." in report["warnings"]


def test_bundle_check_cargo_detects_missing_lock(tmp_path: Path) -> None:
    write(tmp_path / "Cargo.toml", "[dependencies]\nserde = \"1\"\n[dev-dependencies]\npretty_assertions = \"1\"\n")

    report = bundle_check.analyze(tmp_path)

    assert report["package_manager"] == "cargo"
    assert report["total_dependencies"] == 2
    assert report["warnings"] == ["Cargo.lock not found."]


def test_bundle_check_missing_or_empty_project_is_controlled(tmp_path: Path) -> None:
    missing = bundle_check.analyze(tmp_path / "missing")
    empty = bundle_check.analyze(tmp_path)

    assert missing["status"] == "warning"
    assert "Project root does not exist" in missing["warnings"][0]
    assert empty["status"] == "not_applicable"
    assert empty["warnings"] == ["No supported package manager manifest detected."]


def test_bundle_check_invalid_package_json_is_safe(tmp_path: Path) -> None:
    write(tmp_path / "package.json", "{not json")

    report = bundle_check.analyze(tmp_path)

    assert report["package_manager"] == "npm"
    assert report["total_dependencies"] == 0
    assert report["status"] == "warning"


def test_bundle_check_npm_ok_when_lock_exists_and_dependencies_are_small(tmp_path: Path) -> None:
    write(tmp_path / "package.json", json.dumps({"dependencies": {"react": "18.2.0"}}))
    write(tmp_path / "package-lock.json", json.dumps({"packages": {"node_modules/react": {"version": "18.2.0"}}}))

    report = bundle_check.analyze(tmp_path)

    assert report == {
        "package_manager": "npm",
        "total_dependencies": 1,
        "large_packages": [],
        "warnings": [],
        "status": "ok",
    }


def test_bundle_check_npm_high_dependency_count_warns(tmp_path: Path) -> None:
    deps = {f"pkg-{index}": "1.0.0" for index in range(201)}
    write(tmp_path / "package.json", json.dumps({"dependencies": deps}))
    write(tmp_path / "pnpm-lock.yaml", "lockfileVersion: 9\n")

    report = bundle_check.analyze(tmp_path)

    assert report["total_dependencies"] == 201
    assert "High dependency count for npm project: 201 (>200)." in report["warnings"]
    assert report["status"] == "warning"


def test_bundle_check_lock_key_to_package_name_handles_scoped_packages() -> None:
    assert bundle_check.lock_key_to_package_name("node_modules/@scope/pkg") == "@scope/pkg"
    assert bundle_check.lock_key_to_package_name("node_modules/react") == "react"
    assert bundle_check.lock_key_to_package_name("") == ""


def test_bundle_check_npm_lock_duplicate_handles_scoped_direct_dependency(tmp_path: Path) -> None:
    write(tmp_path / "package.json", json.dumps({"dependencies": {"@scope/pkg": "1.0.0"}}))
    write(
        tmp_path / "package-lock.json",
        json.dumps(
            {
                "packages": {
                    "node_modules/@scope/pkg": {"version": "1.0.0"},
                    "node_modules/other/node_modules/@scope/pkg": {"version": "2.0.0"},
                }
            }
        ),
    )

    report = bundle_check.analyze(tmp_path)

    assert "Multiple lockfile versions for direct dependency '@scope/pkg': 1.0.0, 2.0.0" in report["warnings"]


def test_bundle_check_pip_pyproject_with_poetry_lock_is_ok(tmp_path: Path) -> None:
    write(tmp_path / "pyproject.toml", "requests>=2.0\n")
    write(tmp_path / "poetry.lock", "# lock\n")

    report = bundle_check.analyze(tmp_path)

    assert report["package_manager"] == "pip"
    assert report["warnings"] == []
    assert report["status"] == "ok"


def test_bundle_check_cargo_with_lock_is_ok_and_skips_non_dependency_sections(tmp_path: Path) -> None:
    write(
        tmp_path / "Cargo.toml",
        "\n".join(
            [
                "[package]",
                'name = "demo"',
                "[dependencies]",
                'serde = "1"',
                "[features]",
                'default = ["serde"]',
            ]
        ),
    )
    write(tmp_path / "Cargo.lock", "# lock\n")

    report = bundle_check.analyze(tmp_path)

    assert report["package_manager"] == "cargo"
    assert report["total_dependencies"] == 1
    assert report["warnings"] == []
    assert report["status"] == "ok"


def test_bundle_check_detect_package_manager_precedence(tmp_path: Path) -> None:
    write(tmp_path / "Cargo.toml", "[dependencies]\nserde = \"1\"\n")
    assert bundle_check.detect_package_manager(tmp_path) == "cargo"
    write(tmp_path / "requirements.txt", "requests==2.0\n")
    assert bundle_check.detect_package_manager(tmp_path) == "cargo"
    write(tmp_path / "package.json", "{}\n")
    assert bundle_check.detect_package_manager(tmp_path) == "npm"


def test_bundle_check_cli_outputs_json(tmp_path: Path) -> None:
    script = SKILLS_ROOT / "codex-execution-quality-gate" / "scripts" / "bundle_check.py"
    write(tmp_path / "requirements.txt", "requests==2.0\n")
    result = subprocess.run(
        [sys.executable, str(script), "--project-root", str(tmp_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["package_manager"] == "pip"
    assert payload["status"] == "ok"


def test_track_skill_usage_records_entry_and_estimates_duration(tmp_path: Path) -> None:
    data_dir = tmp_path / "analytics"

    payload = track_usage.record_usage(
        skills_root=tmp_path,
        data_dir=data_dir,
        skill="codex-runtime-hook",
        task="x" * 141,
        outcome="success",
        notes="verified",
    )

    entry = json.loads((data_dir / "usage-log.jsonl").read_text(encoding="utf-8"))
    assert payload["status"] == "recorded"
    assert entry["skill"] == "codex-runtime-hook"
    assert entry["duration_estimate"] == "deep"


def test_track_skill_usage_load_skips_bad_lines_with_warnings(tmp_path: Path) -> None:
    log = tmp_path / "usage-log.jsonl"
    write(
        log,
        "\n".join(
            [
                "{bad json",
                "[]",
                json.dumps({"date": "bad-date", "skill": "codex-a", "task": "task", "outcome": "success"}),
                json.dumps({"date": "2026-04-28", "skill": "", "task": "task", "outcome": "success"}),
                json.dumps({"date": "2026-04-28", "skill": "codex-a", "task": "task", "outcome": "success"}),
            ]
        ),
    )

    entries, warnings = track_usage.load_usage_entries(log)

    assert len(entries) == 1
    assert entries[0]["skill"] == "codex-a"
    assert len(warnings) == 4
    assert any("Malformed JSON line skipped" in warning for warning in warnings)
    assert any("Non-object JSON line skipped" in warning for warning in warnings)
    assert any("Invalid date skipped" in warning for warning in warnings)
    assert any("Incomplete entry skipped" in warning for warning in warnings)


def test_track_skill_usage_empty_report_lists_unused_skills(tmp_path: Path) -> None:
    write(tmp_path / "codex-a" / "SKILL.md", "---\nname: codex-a\n---\n")
    data_dir = tmp_path / ".analytics"

    report = track_usage.report_usage(tmp_path, data_dir)

    assert report["status"] == "report_ready"
    assert report["total_usages"] == 0
    assert report["unused_skills"] == ["codex-a"]
    assert "No usage data yet" in report["recommendations"][0]


def test_track_skill_usage_report_computes_rates_trends_and_recommendations(tmp_path: Path) -> None:
    write(tmp_path / "codex-a" / "SKILL.md", "---\nname: codex-a\n---\n")
    write(tmp_path / "codex-unused" / "SKILL.md", "---\nname: codex-unused\n---\n")
    data_dir = tmp_path / ".analytics"
    rows = [
        {"date": "2026-04-01", "skill": "codex-a", "task": "one", "outcome": "failed"},
        {"date": "2026-04-02", "skill": "codex-a", "task": "two", "outcome": "partial"},
        {"date": "2026-04-03", "skill": "codex-a", "task": "three", "outcome": "success"},
        {"date": "2026-04-04", "skill": "codex-a", "task": "four", "outcome": "success"},
    ]
    write(data_dir / "usage-log.jsonl", "\n".join(json.dumps(row) for row in rows))

    report = track_usage.report_usage(tmp_path, data_dir)

    assert report["total_usages"] == 4
    assert report["by_skill"]["codex-a"]["uses"] == 4
    assert report["by_skill"]["codex-a"]["success_rate"] == 0.5
    assert report["least_effective"] == "codex-a"
    assert report["most_effective"] == "codex-a"
    assert report["trends"]["direction"] == "improving"
    assert "codex-unused" in report["unused_skills"]
    assert any("failure rate" in item for item in report["recommendations"])


def test_track_skill_usage_cli_no_mode_returns_json_error() -> None:
    script = SKILLS_ROOT / "codex-project-memory" / "scripts" / "track_skill_usage.py"
    result = subprocess.run(
        [sys.executable, str(script), "--skills-root", str(SKILLS_ROOT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "error"
    assert "Choose at least one mode" in payload["message"]


def test_track_skill_usage_cli_record_missing_args_returns_json_error(tmp_path: Path) -> None:
    script = SKILLS_ROOT / "codex-project-memory" / "scripts" / "track_skill_usage.py"
    result = subprocess.run(
        [sys.executable, str(script), "--skills-root", str(tmp_path), "--record", "--skill", "codex-a"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "error"
    assert "Missing required arguments" in payload["message"]


def test_track_skill_usage_parse_date_supports_iso_datetime_and_invalid() -> None:
    assert track_usage.parse_date("2026-04-28T12:30:00").isoformat() == "2026-04-28"
    assert track_usage.parse_date("not-a-date") is None
