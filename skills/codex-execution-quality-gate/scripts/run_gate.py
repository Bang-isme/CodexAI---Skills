#!/usr/bin/env python3
"""
Run lint/test quality gate for a project and emit JSON report.

MVP policy:
- block only on detected lint/test failures with exit code 1
- treat timeouts and tool crashes (exit >= 2) as warnings
- allow pass when tools are not detected, but emit warnings
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class CommandSpec:
    tool: str
    display_command: str
    invocation: Union[str, List[str]]
    shell: bool


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def load_package_json(project_root: Path) -> Dict[str, Any]:
    package_json = project_root / "package.json"
    if not package_json.exists():
        return {}
    try:
        return json.loads(read_text(package_json))
    except json.JSONDecodeError:
        return {}


def has_any(project_root: Path, patterns: List[str]) -> bool:
    for pattern in patterns:
        if any(project_root.glob(pattern)):
            return True
    return False


def contains_pyproject_section(project_root: Path, section: str) -> bool:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return False
    return section in read_text(pyproject)


def make_command(command_parts: List[str], tool: str, is_windows: bool) -> CommandSpec:
    display = " ".join(command_parts)
    if is_windows and command_parts and command_parts[0] in {"npm", "npx"}:
        return CommandSpec(tool=tool, display_command=display, invocation=command_parts, shell=True)
    return CommandSpec(tool=tool, display_command=display, invocation=command_parts, shell=False)


def is_placeholder_npm_test(script: str) -> bool:
    lowered = script.lower()
    return "no test specified" in lowered and "exit 1" in lowered


def detect_lint_command(project_root: Path, is_windows: bool, package_data: Dict[str, Any]) -> Optional[CommandSpec]:
    scripts = package_data.get("scripts", {}) if isinstance(package_data, dict) else {}
    if isinstance(scripts, dict) and isinstance(scripts.get("lint"), str) and scripts["lint"].strip():
        return make_command(["npm", "run", "lint"], "npm", is_windows)

    if has_any(project_root, [".eslintrc", ".eslintrc.*", "eslint.config.*"]):
        return make_command(["npx", "eslint", "."], "eslint", is_windows)

    if (project_root / "biome.json").exists():
        return make_command(["npx", "biome", "check", "."], "biome", is_windows)

    if contains_pyproject_section(project_root, "[tool.ruff]"):
        return make_command(["ruff", "check", "."], "ruff", is_windows)

    if contains_pyproject_section(project_root, "[tool.flake8]") or (project_root / ".flake8").exists():
        return make_command(["flake8", "."], "flake8", is_windows)

    if (project_root / ".golangci.yml").exists():
        return make_command(["golangci-lint", "run"], "golangci-lint", is_windows)

    return None


def detect_test_command(project_root: Path, is_windows: bool, package_data: Dict[str, Any]) -> Optional[CommandSpec]:
    scripts = package_data.get("scripts", {}) if isinstance(package_data, dict) else {}
    test_script = scripts.get("test") if isinstance(scripts, dict) else None
    if isinstance(test_script, str) and test_script.strip() and not is_placeholder_npm_test(test_script):
        return make_command(["npm", "test"], "npm", is_windows)

    if has_any(project_root, ["jest.config.*"]):
        return make_command(["npx", "jest", "--passWithNoTests"], "jest", is_windows)

    if has_any(project_root, ["vitest.config.*"]):
        return make_command(["npx", "vitest", "run"], "vitest", is_windows)

    if (
        contains_pyproject_section(project_root, "[tool.pytest]")
        or (project_root / "pytest.ini").exists()
        or (project_root / "conftest.py").exists()
    ):
        return make_command(["pytest"], "pytest", is_windows)

    if (project_root / "Cargo.toml").exists():
        return make_command(["cargo", "test"], "cargo", is_windows)

    if (project_root / "go.mod").exists():
        return make_command(["go", "test", "./..."], "go", is_windows)

    return None


def summarize_output(stdout: str, stderr: str) -> str:
    content = (stderr.strip() + "\n" + stdout.strip()).strip() if stderr.strip() else stdout.strip()
    if not content:
        return ""
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    summary = " | ".join(lines[:3])
    return summary[:400]


def run_command(spec: CommandSpec, cwd: Path, timeout_seconds: int) -> Dict[str, Any]:
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            spec.invocation,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            shell=spec.shell,
            check=False,
        )
        duration = round(time.perf_counter() - start, 2)
        return {
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
            "not_found": False,
            "duration_seconds": duration,
        }
    except subprocess.TimeoutExpired as exc:
        duration = round(time.perf_counter() - start, 2)
        return {
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
            "not_found": False,
            "duration_seconds": duration,
        }
    except FileNotFoundError:
        duration = round(time.perf_counter() - start, 2)
        return {
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "timed_out": False,
            "not_found": True,
            "duration_seconds": duration,
        }


def empty_check_result() -> Dict[str, Any]:
    return {
        "detected": False,
        "tool": "",
        "command": "",
        "passed": False,
        "exit_code": None,
        "output_summary": "",
        "duration_seconds": 0.0,
    }


def execute_check(
    label: str,
    spec: Optional[CommandSpec],
    cwd: Path,
    timeout_seconds: int,
    warnings: List[str],
) -> Dict[str, Any]:
    result = empty_check_result()
    if spec is None:
        return result

    raw = run_command(spec, cwd, timeout_seconds)
    if raw["not_found"]:
        warnings.append(f"{label} tool '{spec.tool}' is not installed or not in PATH.")
        return result

    exit_code = raw["exit_code"]
    summary = summarize_output(raw["stdout"], raw["stderr"])

    passed = bool(exit_code == 0)
    if raw["timed_out"]:
        warnings.append(f"{label} command timed out after {timeout_seconds}s: {spec.display_command}")
    elif isinstance(exit_code, int) and exit_code >= 2:
        warnings.append(f"{label} command returned exit code {exit_code} (tool/config issue): {spec.display_command}")

    result.update(
        {
            "detected": True,
            "tool": spec.tool,
            "command": spec.display_command,
            "passed": passed,
            "exit_code": exit_code,
            "output_summary": summary,
            "duration_seconds": raw["duration_seconds"],
        }
    )
    return result


def build_gate_report(
    project_root: Path,
    timeout_lint: int,
    timeout_test: int,
    skip_lint: bool,
    skip_test: bool,
) -> Dict[str, Any]:
    warnings: List[str] = []
    blocking_issues: List[str] = []

    if not project_root.exists() or not project_root.is_dir():
        return {
            "lint": empty_check_result(),
            "test": empty_check_result(),
            "gate_passed": False,
            "blocking_issues": [f"Project root does not exist or is not a directory: {project_root}"],
            "warnings": [],
        }

    is_windows = os.name == "nt"
    package_data = load_package_json(project_root)
    lint_spec = None if skip_lint else detect_lint_command(project_root, is_windows, package_data)
    test_spec = None if skip_test else detect_test_command(project_root, is_windows, package_data)

    if skip_lint:
        warnings.append("Lint check skipped by --skip-lint.")
    if skip_test:
        warnings.append("Test check skipped by --skip-test.")

    if package_data and not (project_root / "node_modules").exists():
        needs_node_modules = (
            (lint_spec is not None and lint_spec.tool in {"npm", "eslint", "biome"})
            or (test_spec is not None and test_spec.tool in {"npm", "jest", "vitest"})
        )
        if needs_node_modules:
            warnings.append("node_modules directory is missing. Run `npm install` if commands fail.")

    lint_result = execute_check("Lint", lint_spec, project_root, timeout_lint, warnings)
    test_result = execute_check("Test", test_spec, project_root, timeout_test, warnings)

    lint_detected = bool(lint_result["detected"])
    test_detected = bool(test_result["detected"])

    if lint_detected and lint_result["exit_code"] == 1:
        blocking_issues.append("Lint check failed with exit code 1.")
    if test_detected and test_result["exit_code"] == 1:
        blocking_issues.append("Test suite failed with exit code 1.")

    if not lint_detected and not test_detected and not skip_lint and not skip_test:
        warnings.append("No lint/test tools detected. Consider adding linting and testing tools to your project.")
    else:
        if not lint_detected and not skip_lint:
            warnings.append("No linter detected.")
        if not test_detected and not skip_test:
            warnings.append("No test runner detected.")

    gate_passed = len(blocking_issues) == 0
    return {
        "lint": lint_result,
        "test": test_result,
        "gate_passed": gate_passed,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
    }


def load_gate_state(project_root: Path) -> Dict[str, Any]:
    """Load persistent gate state from .codex/state/gate_state.json."""
    state_file = project_root / ".codex" / "state" / "gate_state.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    return {"consecutive_failures": 0}


def save_gate_state(project_root: Path, state: Dict[str, Any]) -> None:
    """Persist gate state to .codex/state/gate_state.json."""
    state_file = project_root / ".codex" / "state" / "gate_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run lint/test gate and output JSON report.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--timeout-lint", type=int, default=120, help="Lint timeout seconds")
    parser.add_argument("--timeout-test", type=int, default=300, help="Test timeout seconds")
    parser.add_argument("--skip-lint", action="store_true", help="Skip lint execution")
    parser.add_argument("--skip-test", action="store_true", help="Skip test execution")
    parser.add_argument("--human", action="store_true", help="Print human-readable summary to stderr")
    return parser.parse_args()


def render_human_box(title: str, rows: List[str]) -> str:
    width = max(38, len(title), *(len(row) for row in rows))
    top = "╔" + ("═" * width) + "╗"
    mid = "╠" + ("═" * width) + "╣"
    bottom = "╚" + ("═" * width) + "╝"
    out = [top, f"║{title.center(width)}║", mid]
    for row in rows:
        out.append(f"║ {'{}'.format(row).ljust(width - 2)} ║")
    out.append(bottom)
    return "\n".join(out)


def print_human_summary(report: Dict[str, Any]) -> None:
    lint = report.get("lint", {})
    test = report.get("test", {})
    gate_passed = bool(report.get("gate_passed", False))

    def status_for(item: Dict[str, Any]) -> str:
        if not item.get("detected"):
            return "SKIP"
        return "PASS" if bool(item.get("passed")) else "FAIL"

    rows: List[str] = [
        f"Lint:     {status_for(lint)}",
        f"Tests:    {status_for(test)}",
        f"Gate:     {'PASS' if gate_passed else 'FAIL'}",
        f"Retries:  {report.get('consecutive_failures', 0)}",
    ]

    print(render_human_box("QUALITY GATE RESULTS", rows), file=sys.stderr)


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    report = build_gate_report(
        project_root=project_root,
        timeout_lint=args.timeout_lint,
        timeout_test=args.timeout_test,
        skip_lint=args.skip_lint,
        skip_test=args.skip_test,
    )
    # --- Circuit Breaker state tracking (START) ---
    state = load_gate_state(project_root)
    if report["gate_passed"]:
        state["consecutive_failures"] = 0
    else:
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
    save_gate_state(project_root, state)
    report["consecutive_failures"] = state["consecutive_failures"]
    # --- Circuit Breaker state tracking (END) ---
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.human:
        print_human_summary(report)
    return 0 if report["gate_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
