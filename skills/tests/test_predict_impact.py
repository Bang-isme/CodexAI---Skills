from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILLS_ROOT / "codex-execution-quality-gate" / "scripts" / "predict_impact.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("skills_predict_impact_full", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["skills_predict_impact_full"] = module
    spec.loader.exec_module(module)
    return module


predict_impact = load_script_module()


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


def test_predict_parse_files_arg_normalizes_dedupes_and_sorts() -> None:
    assert predict_impact.parse_files_arg(r"src\b.ts, src/a.ts, src/b.ts, src/a.ts") == [
        "src/a.ts",
        "src/b.ts",
    ]


def test_predict_resolve_target_handles_extensionless_and_absolute_paths(tmp_path: Path) -> None:
    target = tmp_path / "src" / "service.ts"
    write(target, "export const service = 1\n")
    existing = {"src/service.ts"}

    resolved_extless, warning_extless = predict_impact.resolve_target("src/service", tmp_path, existing)
    resolved_abs, warning_abs = predict_impact.resolve_target(str(target), tmp_path, existing)
    missing, warning_missing = predict_impact.resolve_target("src/missing.ts", tmp_path, existing)

    assert (resolved_extless, warning_extless) == ("src/service.ts", None)
    assert (resolved_abs, warning_abs) == ("src/service.ts", None)
    assert missing == "src/missing.ts"
    assert warning_missing == "Target file not found in project: src/missing.ts"


def test_predict_dependent_levels_respects_depth() -> None:
    reverse = {
        "src/core.ts": {"src/service.ts"},
        "src/service.ts": {"src/page.ts"},
        "src/page.ts": {"src/app.ts"},
    }

    direct, indirect = predict_impact.dependent_levels("src/core.ts", reverse, depth=2)

    assert direct == {"src/service.ts"}
    assert indirect == {"src/page.ts"}
    assert "src/app.ts" not in indirect


def test_predict_collect_tests_and_find_affected_tests(tmp_path: Path) -> None:
    write(tmp_path / "src" / "user.ts", "export const user = 1\n")
    write(tmp_path / "tests" / "user.test.ts", "import { user } from '../src/user'\n")
    write(tmp_path / "src" / "__tests__" / "order.spec.ts", "test('order', () => {})\n")
    write(tmp_path / "node_modules" / "bad.test.ts", "test('bad', () => {})\n")

    tests = predict_impact.collect_tests(tmp_path)
    affected = predict_impact.find_affected_tests(tmp_path, ["src/user.ts", "src/order.ts"], tests)

    assert tests == ["src/__tests__/order.spec.ts", "tests/user.test.ts"]
    assert affected == ["src/__tests__/order.spec.ts", "tests/user.test.ts"]


def test_predict_classifies_entrypoints_and_configs_as_critical() -> None:
    assert predict_impact.is_entry_or_config("src/index.ts")
    assert predict_impact.is_entry_or_config("vite.config.ts")
    assert predict_impact.is_entry_or_config("config/app.ts")
    assert predict_impact.classify_level(0, critical_signal=True) == "critical"
    assert predict_impact.classify_level(11, critical_signal=False) == "critical"
    assert predict_impact.classify_level(5, critical_signal=False) == "high"
    assert predict_impact.classify_level(2, critical_signal=False) == "medium"
    assert predict_impact.classify_level(1, critical_signal=False) == "low"


def test_predict_build_recommendations_include_tests_contracts_and_high_risk() -> None:
    recommendations = predict_impact.build_recommendations(
        targets=["src/models/user.ts"],
        dependency_tree={"src/models/user.ts": {"direct": ["src/api/user.ts"], "indirect": []}},
        affected_tests=["tests/user.test.ts"],
        impact_level="high",
    )

    joined = "\n".join(recommendations)
    assert "1 direct dependents" in joined
    assert "Run affected tests: 1 test files identified." in joined
    assert "API response shape" in joined
    assert "High blast radius detected" in joined


def test_predict_cli_missing_project_root_returns_json_error(tmp_path: Path) -> None:
    result = run_cli("--project-root", str(tmp_path / "missing"), "--files", "src/app.ts")

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "error"
    assert "Project root does not exist" in payload["message"]


def test_predict_cli_empty_files_returns_json_error(tmp_path: Path) -> None:
    result = run_cli("--project-root", str(tmp_path), "--files", "  ")

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["status"] == "error"
    assert "No target files provided" in payload["message"]


def test_predict_cli_marks_config_change_critical(tmp_path: Path) -> None:
    write(tmp_path / "package.json", "{}\n")
    write(tmp_path / "src" / "app.ts", "export const app = 1\n")
    write(tmp_path / "tests" / "app.test.ts", "test('app', () => {})\n")

    result = run_cli("--project-root", str(tmp_path), "--files", "package.json")

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["status"] == "predicted"
    assert payload["impact_summary"]["level"] == "critical"
    assert payload["targets"] == ["package.json"]


def test_predict_cli_escalates_large_blast_radius(tmp_path: Path) -> None:
    write(tmp_path / "src" / "core.ts", "export const core = 1\n")
    for index in range(21):
        write(tmp_path / "src" / f"consumer-{index}.ts", "import { core } from './core';\n")

    result = run_cli("--project-root", str(tmp_path), "--files", "src/core.ts", "--depth", "1")

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["blast_radius_size"] == 22
    assert payload["escalate_to_epic"] is True
    assert any("BLAST RADIUS EXCEEDS COGNITIVE LIMIT" in item for item in payload["warnings"])
