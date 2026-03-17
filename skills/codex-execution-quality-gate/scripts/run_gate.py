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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import output_guard as output_guard_script
import editorial_review as editorial_review_script


@dataclass
class CommandSpec:
    tool: str
    display_command: str
    invocation: Union[str, List[str]]
    shell: bool


DEFAULT_STRICT_DELIVERABLE_SCORES: Dict[str, int] = {
    "plan": 70,
    "review": 70,
    "handoff": 65,
}
DEFAULT_EDITORIAL_DELIVERABLE_SCORES: Dict[str, int] = {
    "plan": 68,
    "review": 72,
    "handoff": 62,
}


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


def empty_output_guard_result() -> Dict[str, Any]:
    return {
        "executed": False,
        "status": "skipped",
        "score": 0,
        "min_score": 0,
        "issues": [],
        "suggestions": [],
        "counts": {
            "generic_phrases": 0,
            "artifact_refs": 0,
            "commands": 0,
            "numbers": 0,
            "sections": 0,
            "resolved_artifact_refs": 0,
            "missing_artifact_refs": 0,
            "resolved_command_paths": 0,
            "missing_command_paths": 0,
        },
    }


def empty_editorial_review_result() -> Dict[str, Any]:
    return {
        "executed": False,
        "status": "skipped",
        "score": 0,
        "min_score": 0,
        "deliverable_kind": "generic",
        "rubric": {
            "decision_clarity": 0,
            "grounding": 0,
            "tradeoff_awareness": 0,
            "structure": 0,
            "editorial_tone": 0,
        },
        "issues": [],
        "suggestions": [],
    }


def infer_deliverable_kind(output_file: Optional[str], text: str) -> str:
    source = (output_file or "").lower()
    lowered = text.lower()

    if any(token in source for token in ("handoff", "session-summary")):
        return "handoff"
    if any(token in source for token in ("review", "audit")):
        return "review"
    if "plan" in source:
        return "plan"

    plan_signals = (
        "success criteria",
        "task breakdown",
        "phase x verification",
        "rollback strategy",
    )
    review_signals = (
        "findings",
        "residual risk",
        "open questions",
        "severity",
    )
    handoff_signals = (
        "next steps",
        "current state",
        "blockers",
        "handoff",
    )

    if sum(signal in lowered for signal in plan_signals) >= 2:
        return "plan"
    if sum(signal in lowered for signal in review_signals) >= 2:
        return "review"
    if sum(signal in lowered for signal in handoff_signals) >= 2:
        return "handoff"
    return "generic"


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


def resolve_optional_path(project_root: Path, value: Optional[str]) -> Optional[Path]:
    if not value:
        return None
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (project_root / candidate).resolve()


def execute_output_guard(
    project_root: Path,
    output_file: Optional[str],
    output_text: Optional[str],
    min_score: int,
) -> Tuple[Dict[str, Any], str]:
    if output_file is None and output_text is None:
        return empty_output_guard_result(), "none"

    try:
        if output_text is not None:
            text = output_text
        else:
            assert output_file is not None
            text = resolve_optional_path(project_root, output_file).read_text(encoding="utf-8")
    except (AssertionError, OSError, ValueError) as exc:
        payload = empty_output_guard_result()
        payload.update(
            {
                "executed": True,
                "status": "error",
                "message": str(exc),
            }
        )
        return payload, "generic"

    deliverable_kind = infer_deliverable_kind(output_file, text)

    report = output_guard_script.analyze_text(text, min_score=min_score, repo_root=project_root)
    report["executed"] = True
    if output_file:
        resolved = resolve_optional_path(project_root, output_file)
        report["source_file"] = resolved.as_posix() if resolved is not None else output_file
    return report, deliverable_kind


def execute_editorial_review(
    project_root: Path,
    output_file: Optional[str],
    output_text: Optional[str],
    deliverable_kind: str,
    min_score: int,
) -> Dict[str, Any]:
    if output_file is None and output_text is None:
        return empty_editorial_review_result()

    try:
        if output_text is not None:
            text = output_text
        else:
            assert output_file is not None
            text = resolve_optional_path(project_root, output_file).read_text(encoding="utf-8")
    except (AssertionError, OSError, ValueError) as exc:
        payload = empty_editorial_review_result()
        payload.update(
            {
                "executed": True,
                "status": "error",
                "message": str(exc),
            }
        )
        return payload

    report = editorial_review_script.analyze_text(
        text,
        min_score=min_score,
        deliverable_kind=deliverable_kind,
        repo_root=project_root,
    )
    report["executed"] = True
    if output_file:
        resolved = resolve_optional_path(project_root, output_file)
        report["source_file"] = resolved.as_posix() if resolved is not None else output_file
    return report


def build_gate_report(
    project_root: Path,
    timeout_lint: int,
    timeout_test: int,
    skip_lint: bool,
    skip_test: bool,
    output_file: Optional[str] = None,
    output_text: Optional[str] = None,
    strict_output: bool = False,
    output_min_score: int = 60,
    editorial_min_score: int = 60,
    deliverable_kind: str = "auto",
    advisory_output: bool = False,
) -> Dict[str, Any]:
    warnings: List[str] = []
    blocking_issues: List[str] = []

    if not project_root.exists() or not project_root.is_dir():
        return {
            "status": "fail",
            "lint": empty_check_result(),
            "test": empty_check_result(),
            "output_guard": empty_output_guard_result(),
            "editorial_review": empty_editorial_review_result(),
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
    inferred_kind = "none"
    effective_deliverable_kind = deliverable_kind
    effective_output_min_score = output_min_score
    effective_editorial_min_score = editorial_min_score
    if output_file is not None or output_text is not None:
        preview_text = output_text
        if preview_text is None and output_file is not None:
            resolved_output_path = resolve_optional_path(project_root, output_file)
            preview_text = read_text(resolved_output_path) if resolved_output_path is not None else ""
        inferred_kind = infer_deliverable_kind(output_file, preview_text or "")
        if effective_deliverable_kind == "auto":
            effective_deliverable_kind = inferred_kind
        if effective_deliverable_kind in DEFAULT_STRICT_DELIVERABLE_SCORES:
            effective_output_min_score = max(
                output_min_score,
                DEFAULT_STRICT_DELIVERABLE_SCORES[effective_deliverable_kind],
            )
        if effective_deliverable_kind in DEFAULT_EDITORIAL_DELIVERABLE_SCORES:
            effective_editorial_min_score = max(
                editorial_min_score,
                DEFAULT_EDITORIAL_DELIVERABLE_SCORES[effective_deliverable_kind],
            )
    effective_strict_output = strict_output or (
        (output_file is not None or output_text is not None)
        and not advisory_output
        and effective_deliverable_kind in DEFAULT_STRICT_DELIVERABLE_SCORES
    )

    output_result, inferred_from_execution = execute_output_guard(
        project_root,
        output_file,
        output_text,
        effective_output_min_score,
    )
    if effective_deliverable_kind == "auto":
        effective_deliverable_kind = inferred_from_execution
    output_result["deliverable_kind"] = effective_deliverable_kind
    editorial_result = execute_editorial_review(
        project_root,
        output_file,
        output_text,
        effective_deliverable_kind,
        effective_editorial_min_score,
    )

    lint_detected = bool(lint_result["detected"])
    test_detected = bool(test_result["detected"])

    if lint_detected and lint_result["exit_code"] == 1:
        blocking_issues.append("Lint check failed with exit code 1.")
    if test_detected and test_result["exit_code"] == 1:
        blocking_issues.append("Test suite failed with exit code 1.")
    if output_result.get("executed"):
        if output_result.get("status") == "error":
            blocking_issues.append("Output guard could not evaluate the deliverable.")
        elif effective_strict_output and output_result.get("status") != "pass":
            blocking_issues.append("Written deliverable failed strict output quality checks.")
        elif output_result.get("status") != "pass":
            warnings.append("Written deliverable failed advisory output quality checks.")
    if editorial_result.get("executed"):
        if editorial_result.get("status") == "error":
            blocking_issues.append("Editorial review could not evaluate the deliverable.")
        elif effective_strict_output and editorial_result.get("status") != "pass":
            blocking_issues.append("Written deliverable failed editorial quality checks.")
        elif editorial_result.get("status") != "pass":
            warnings.append("Written deliverable failed advisory editorial quality checks.")

    if not lint_detected and not test_detected and not skip_lint and not skip_test:
        warnings.append("No lint/test tools detected. Consider adding linting and testing tools to your project.")
    else:
        if not lint_detected and not skip_lint:
            warnings.append("No linter detected.")
        if not test_detected and not skip_test:
            warnings.append("No test runner detected.")

    gate_passed = len(blocking_issues) == 0
    return {
        "status": "pass" if gate_passed else "fail",
        "lint": lint_result,
        "test": test_result,
        "output_guard": output_result,
        "editorial_review": editorial_result,
        "strict_output_requested": strict_output,
        "strict_output_effective": effective_strict_output,
        "strict_output": effective_strict_output,
        "deliverable_kind": effective_deliverable_kind,
        "deliverable_kind_inferred": inferred_kind,
        "output_min_score_effective": effective_output_min_score,
        "editorial_min_score_effective": effective_editorial_min_score,
        "advisory_output": advisory_output,
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


def append_gate_event(project_root: Path, report: Dict[str, Any]) -> None:
    quality_dir = project_root / ".codex" / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    event_path = quality_dir / "gate-events.jsonl"
    output_guard = report.get("output_guard", {})
    editorial_review = report.get("editorial_review", {})
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": report.get("status"),
        "gate_passed": bool(report.get("gate_passed", False)),
        "strict_output_effective": bool(report.get("strict_output_effective", False)),
        "strict_output_requested": bool(report.get("strict_output_requested", False)),
        "deliverable_kind": report.get("deliverable_kind", "none"),
        "output_guard_status": output_guard.get("status") if isinstance(output_guard, dict) else "skipped",
        "output_guard_score": output_guard.get("score") if isinstance(output_guard, dict) else None,
        "output_guard_min_score": report.get("output_min_score_effective"),
        "editorial_status": editorial_review.get("status") if isinstance(editorial_review, dict) else "skipped",
        "editorial_score": editorial_review.get("score") if isinstance(editorial_review, dict) else None,
        "editorial_min_score": report.get("editorial_min_score_effective"),
        "lint_detected": bool(report.get("lint", {}).get("detected", False)) if isinstance(report.get("lint"), dict) else False,
        "test_detected": bool(report.get("test", {}).get("detected", False)) if isinstance(report.get("test"), dict) else False,
        "blocking_issues": len(report.get("blocking_issues", [])) if isinstance(report.get("blocking_issues"), list) else 0,
        "warnings": len(report.get("warnings", [])) if isinstance(report.get("warnings"), list) else 0,
    }
    with event_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False))
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run lint/test gate and output JSON report.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--timeout-lint", type=int, default=120, help="Lint timeout seconds")
    parser.add_argument("--timeout-test", type=int, default=300, help="Test timeout seconds")
    parser.add_argument("--skip-lint", action="store_true", help="Skip lint execution")
    parser.add_argument("--skip-test", action="store_true", help="Skip test execution")
    parser.add_argument("--strict-output", action="store_true", help="Block gate completion when output guard fails")
    parser.add_argument(
        "--deliverable-kind",
        choices=("auto", "generic", "plan", "review", "handoff"),
        default="auto",
        help="Deliverable type used for output-quality enforcement (default: auto)",
    )
    parser.add_argument(
        "--advisory-output",
        action="store_true",
        help="Keep output guard advisory even when the deliverable looks like a plan, review, or handoff",
    )
    output_source = parser.add_mutually_exclusive_group()
    output_source.add_argument("--output-file", help="Deliverable file to evaluate with output_guard")
    output_source.add_argument("--output-text", help="Inline deliverable text to evaluate with output_guard")
    parser.add_argument("--output-min-score", type=int, default=60, help="Minimum passing score for output_guard")
    parser.add_argument("--editorial-min-score", type=int, default=60, help="Minimum passing score for editorial review")
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
    output_result = report.get("output_guard", {})
    editorial_result = report.get("editorial_review", {})
    gate_passed = bool(report.get("gate_passed", False))

    def status_for(item: Dict[str, Any]) -> str:
        if item.get("executed"):
            return "PASS" if item.get("status") == "pass" else "FAIL"
        if not item.get("detected"):
            return "SKIP"
        return "PASS" if bool(item.get("passed")) else "FAIL"

    rows: List[str] = [
        f"Lint:     {status_for(lint)}",
        f"Tests:    {status_for(test)}",
        f"Output:   {status_for(output_result) if output_result.get('executed') else 'SKIP'}",
        f"Editorial:{status_for(editorial_result) if editorial_result.get('executed') else 'SKIP'}",
        f"Gate:     {'PASS' if gate_passed else 'FAIL'}",
        f"Retries:  {report.get('consecutive_failures', 0)}",
    ]

    print(render_human_box("QUALITY GATE RESULTS", rows), file=sys.stderr)


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if args.strict_output and args.output_file is None and args.output_text is None:
        payload = {
            "status": "error",
            "message": "--strict-output requires --output-file or --output-text",
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1
    report = build_gate_report(
        project_root=project_root,
        timeout_lint=args.timeout_lint,
        timeout_test=args.timeout_test,
        skip_lint=args.skip_lint,
        skip_test=args.skip_test,
        output_file=args.output_file,
        output_text=args.output_text,
        strict_output=args.strict_output,
        output_min_score=args.output_min_score,
        editorial_min_score=args.editorial_min_score,
        deliverable_kind=args.deliverable_kind,
        advisory_output=args.advisory_output,
    )
    # --- Circuit Breaker state tracking (START) ---
    state = load_gate_state(project_root)
    if report["gate_passed"]:
        state["consecutive_failures"] = 0
    else:
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
    save_gate_state(project_root, state)
    report["consecutive_failures"] = state["consecutive_failures"]
    append_gate_event(project_root, report)
    # --- Circuit Breaker state tracking (END) ---
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.human:
        print_human_summary(report)
    return 0 if report["gate_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
