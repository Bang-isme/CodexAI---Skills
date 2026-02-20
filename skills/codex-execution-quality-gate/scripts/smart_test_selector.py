#!/usr/bin/env python3
"""
Select related tests for changed files and optionally run them.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union


TEST_EXTS = {".js", ".jsx", ".ts", ".tsx", ".py"}
SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".next"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Select related tests from changed files.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python smart_test_selector.py --project-root <path> --source staged\n"

            "  python smart_test_selector.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--changed-files", default="", help="Comma-separated changed files")
    parser.add_argument("--source", choices=["staged", "unstaged", "branch"], default="staged")
    parser.add_argument("--run", action="store_true", help="Run selected tests")
    parser.add_argument("--runner", choices=["jest", "pytest", "vitest"], default="")
    parser.add_argument("--human", action="store_true", help="Print human-readable summary to stderr")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def run_git(project_root: Path, args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def git_ready(project_root: Path) -> bool:
    inside = run_git(project_root, ["rev-parse", "--is-inside-work-tree"])
    return inside.returncode == 0 and inside.stdout.strip().lower() == "true"


def detect_base_branch(project_root: Path) -> Optional[str]:
    for candidate in ("main", "master"):
        result = run_git(project_root, ["rev-parse", "--verify", candidate])
        if result.returncode == 0:
            return candidate
    return None


def get_changed_files_from_git(project_root: Path, source: str) -> List[str]:
    if source == "staged":
        cmd = ["diff", "--cached", "--name-only"]
    elif source == "unstaged":
        cmd = ["diff", "--name-only"]
    else:
        base = detect_base_branch(project_root)
        if not base:
            return []
        cmd = ["diff", "--name-only", f"{base}...HEAD"]
    result = run_git(project_root, cmd)
    if result.returncode != 0:
        return []
    files = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
    return sorted(dict.fromkeys(files))


def parse_changed_files(arg_value: str) -> List[str]:
    if not arg_value.strip():
        return []
    items = [item.strip().replace("\\", "/") for item in arg_value.split(",") if item.strip()]
    return sorted(dict.fromkeys(items))


def is_test_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix not in TEST_EXTS:
        return False
    name = path.name.lower()
    rel = path.as_posix().lower()
    return (
        ".test." in name
        or ".spec." in name
        or "/__tests__/" in rel
        or "/tests/" in rel
        or name.startswith("test_")
    )


def collect_test_files(project_root: Path) -> List[str]:
    tests: List[str] = []
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        for name in files:
            path = root_path / name
            rel = path.resolve().relative_to(project_root.resolve()).as_posix()
            rel_path = Path(rel)
            if is_test_file(rel_path):
                tests.append(rel)
    return sorted(dict.fromkeys(tests))


def add_reason(target: Dict[str, Set[str]], test_path: str, reason: str) -> None:
    target.setdefault(test_path, set()).add(reason)


def strategy_convention(
    project_root: Path,
    changed_files: List[str],
    all_tests: Set[str],
    reasons: Dict[str, Set[str]],
) -> Dict[str, bool]:
    found_by_changed: Dict[str, bool] = {}
    all_test_paths = [Path(path) for path in all_tests]

    for changed in changed_files:
        changed_path = Path(changed)
        stem = changed_path.stem
        base = stem.split(".")[0]
        tokens = {stem, base}
        file_found = False

        if is_test_file(changed_path):
            add_reason(reasons, changed, "changed test file")
            found_by_changed[changed] = True
            continue

        candidates: Set[str] = set()
        for token in tokens:
            patterns = [
                f"**/{token}.test.*",
                f"**/{token}.spec.*",
                f"**/{token}*.test.*",
                f"**/{token}*.spec.*",
                f"**/__tests__/{token}*.*",
            ]
            for pattern in patterns:
                for candidate in project_root.glob(pattern):
                    if not candidate.is_file():
                        continue
                    rel = candidate.resolve().relative_to(project_root.resolve()).as_posix()
                    if rel in all_tests:
                        candidates.add(rel)

        if "controller" in stem.lower():
            token = base
            for test_path in all_test_paths:
                rel = test_path.as_posix()
                if token.lower() in test_path.name.lower() and rel in all_tests:
                    candidates.add(rel)

        for match in sorted(candidates):
            add_reason(reasons, match, "convention match")
            file_found = True

        found_by_changed[changed] = file_found

    return found_by_changed


def strategy_import_tracing(
    project_root: Path,
    changed_files: List[str],
    all_tests: Set[str],
    reasons: Dict[str, Set[str]],
    found_by_changed: Dict[str, bool],
) -> Dict[str, bool]:
    test_contents: Dict[str, str] = {}
    for test in all_tests:
        path = project_root / test
        try:
            test_contents[test] = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            test_contents[test] = ""

    for changed in changed_files:
        changed_path = Path(changed)
        stem = changed_path.stem
        base = stem.split(".")[0]
        rel_no_ext = changed_path.with_suffix("").as_posix()
        tokens = [re.escape(rel_no_ext), re.escape(stem), re.escape(base)]
        matched = found_by_changed.get(changed, False)

        for test, content in test_contents.items():
            if not content:
                continue
            for token in tokens:
                from_pattern = re.compile(rf"from\s+['\"][^'\"]*{token}[^'\"]*['\"]")
                require_pattern = re.compile(rf"require\(['\"][^'\"]*{token}[^'\"]*['\"]\)")
                if from_pattern.search(content) or require_pattern.search(content):
                    add_reason(reasons, test, f"imports {base}")
                    matched = True
                    break

        found_by_changed[changed] = matched

    return found_by_changed


def strategy_proximity(
    changed_files: List[str],
    all_tests: Set[str],
    reasons: Dict[str, Set[str]],
    found_by_changed: Dict[str, bool],
) -> None:
    all_test_paths = [Path(path) for path in all_tests]
    for changed in changed_files:
        if found_by_changed.get(changed):
            continue
        changed_parent = Path(changed).parent
        for test_path in all_test_paths:
            if test_path.parent == changed_parent:
                add_reason(reasons, test_path.as_posix(), "directory proximity")
            elif test_path.parent.name == "__tests__" and test_path.parent.parent == changed_parent:
                add_reason(reasons, test_path.as_posix(), "directory proximity")


def detect_runner(project_root: Path, explicit_runner: str) -> Optional[str]:
    if explicit_runner:
        return explicit_runner

    if any(project_root.glob("jest.config.*")):
        return "jest"
    if any(project_root.glob("vitest.config.*")):
        return "vitest"
    if (project_root / "pytest.ini").exists():
        return "pytest"

    pyproject = (project_root / "pyproject.toml")
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore").lower()
        if "[tool.pytest" in content:
            return "pytest"

    package_json = project_root / "package.json"
    if package_json.exists():
        content = package_json.read_text(encoding="utf-8", errors="ignore").lower()
        if "jest" in content:
            return "jest"
        if "vitest" in content:
            return "vitest"

    return None


def run_command(project_root: Path, parts: List[str]) -> Dict[str, object]:
    is_windows = os.name == "nt"
    shell = is_windows and parts and parts[0] in {"npx", "npm"}
    command: Union[str, List[str]] = " ".join(parts) if shell else parts
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=shell,
            check=False,
        )
    except FileNotFoundError:
        return {"ok": False, "error": "runner not found", "duration_ms": int((time.perf_counter() - start) * 1000)}
    except OSError as exc:
        return {"ok": False, "error": str(exc), "duration_ms": int((time.perf_counter() - start) * 1000)}

    duration = int((time.perf_counter() - start) * 1000)
    return {
        "ok": True,
        "exit_code": proc.returncode,
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
        "duration_ms": duration,
    }


def parse_pass_fail(output: str, default_pass: int, exit_code: int) -> Tuple[int, int]:
    lowered = output.lower()
    pass_match = re.search(r"(\d+)\s+passed", lowered)
    fail_match = re.search(r"(\d+)\s+failed", lowered)
    passed = int(pass_match.group(1)) if pass_match else (default_pass if exit_code == 0 else 0)
    failed = int(fail_match.group(1)) if fail_match else (0 if exit_code == 0 else 1)
    return passed, failed


def maybe_run_tests(
    project_root: Path,
    selected_tests: List[str],
    explicit_runner: str,
) -> Tuple[Optional[Dict[str, object]], List[str]]:
    warnings: List[str] = []
    if not selected_tests:
        warnings.append("No related tests selected. Consider running full suite.")
        return None, warnings

    runner = detect_runner(project_root, explicit_runner)
    if not runner:
        warnings.append("No supported test runner detected. Skipped --run execution.")
        return None, warnings

    if runner == "jest":
        cmd = ["npx", "jest", *selected_tests]
    elif runner == "vitest":
        cmd = ["npx", "vitest", "run", *selected_tests]
    else:
        cmd = ["pytest", *selected_tests]

    exec_result = run_command(project_root, cmd)
    if not exec_result.get("ok"):
        warnings.append(f"Failed to start runner '{runner}': {exec_result.get('error')}")
        return None, warnings

    output = f"{exec_result.get('stdout', '')}\n{exec_result.get('stderr', '')}"
    exit_code = int(exec_result.get("exit_code", 1))
    passed, failed = parse_pass_fail(output, default_pass=len(selected_tests), exit_code=exit_code)
    run_result = {
        "runner": runner,
        "exit_code": exit_code,
        "passed": passed,
        "failed": failed,
        "duration_ms": int(exec_result.get("duration_ms", 0)),
    }
    return run_result, warnings


def coverage_estimate(selected_count: int, total_count: int) -> str:
    if total_count <= 0:
        return "0.0%"
    value = (selected_count / total_count) * 100.0
    return f"{value:.1f}%"


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


def print_human_summary(payload: Dict[str, object]) -> None:
    changed_count = len(payload.get("changed_files", [])) if isinstance(payload.get("changed_files"), list) else 0
    selected_count = int(payload.get("selected_count", 0) or 0)
    total_tests = int(payload.get("total_tests_in_project", 0) or 0)
    coverage = str(payload.get("coverage_estimate", "0.0%"))
    rows: List[str] = [
        f"Changed Files:  {changed_count}",
        f"Tests Selected: {selected_count} / {total_tests}",
        f"Coverage Est:   {coverage}",
    ]
    if str(payload.get("status", "")) == "error":
        rows.append(f"Error: {payload.get('message', '')}")

    print(render_human_box("SMART TEST SELECTOR RESULTS", rows), file=sys.stderr)


def emit_with_human(payload: Dict[str, object], human: bool) -> None:
    emit(payload)
    if human:
        print_human_summary(payload)


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit_with_human({"status": "error", "message": f"Project root does not exist or is not a directory: {project_root}"}, args.human)
        return 1

    changed_files = parse_changed_files(args.changed_files)
    if not changed_files:
        if not git_ready(project_root):
            emit_with_human({"status": "error", "message": "Git repository required when --changed-files is not provided."}, args.human)
            return 1
        changed_files = get_changed_files_from_git(project_root, args.source)

    changed_files = [path for path in changed_files if path]
    changed_files = sorted(dict.fromkeys(changed_files))

    all_tests_list = collect_test_files(project_root)
    all_tests = set(all_tests_list)
    reasons: Dict[str, Set[str]] = {}

    found_by_changed = strategy_convention(project_root, changed_files, all_tests, reasons)
    found_by_changed = strategy_import_tracing(project_root, changed_files, all_tests, reasons, found_by_changed)
    strategy_proximity(changed_files, all_tests, reasons, found_by_changed)

    selected = sorted(reasons.keys())
    selected_tests = [{"test": test, "reason": "; ".join(sorted(reasons[test]))} for test in selected]
    skipped_count = max(0, len(all_tests_list) - len(selected_tests))

    payload: Dict[str, object] = {
        "status": "selected",
        "changed_files": changed_files,
        "selected_tests": selected_tests,
        "total_tests_in_project": len(all_tests_list),
        "selected_count": len(selected_tests),
        "skipped_count": skipped_count,
        "coverage_estimate": coverage_estimate(len(selected_tests), len(all_tests_list)),
        "run_result": None,
    }

    warnings: List[str] = []
    if not selected_tests:
        warnings.append("No related tests found; run full suite for broader coverage.")

    if args.run:
        run_result, run_warnings = maybe_run_tests(project_root, [item["test"] for item in selected_tests], args.runner)
        payload["run_result"] = run_result
        warnings.extend(run_warnings)

    if warnings:
        payload["warnings"] = warnings

    emit_with_human(payload, args.human)
    return 0


if __name__ == "__main__":
    sys.exit(main())
