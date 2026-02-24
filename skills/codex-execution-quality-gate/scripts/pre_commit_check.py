#!/usr/bin/env python3
"""
Run staged-file intelligence checks before commit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union


JS_TS_EXTS = {".js", ".jsx", ".ts", ".tsx"}
PY_EXTS = {".py"}
STYLE_EXTS = {".css", ".scss"}
DOC_EXTS = {".md"}
JSON_EXTS = {".json"}
CODE_EXTS = JS_TS_EXTS | PY_EXTS

SECRET_PATTERNS = [
    ("API_KEY=", re.compile(r"api[_-]?key\s*=", re.IGNORECASE)),
    ("SECRET=", re.compile(r"\bsecret\s*=", re.IGNORECASE)),
    ("password=", re.compile(r"\bpassword\s*=", re.IGNORECASE)),
    ("token=", re.compile(r"\btoken\s*=", re.IGNORECASE)),
    ("private_key", re.compile(r"private[_-]?key", re.IGNORECASE)),
]

TODO_PATTERN = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)
CONSOLE_LOG_PATTERN = re.compile(r"\bconsole\.log\s*\(", re.IGNORECASE)
PY_DEBUG_PATTERNS = [
    re.compile(r"\bprint\s*\("),
    re.compile(r"\bbreakpoint\s*\("),
    re.compile(r"\bimport\s+pdb\b"),
    re.compile(r"\bpdb\.(?:set_trace|post_mortem)\s*\("),
]
HUNK_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
LINT_ISSUE_PATTERN = re.compile(r"(\d+)\s+problems?", re.IGNORECASE)


@dataclass
class CommandSpec:
    name: str
    command: Union[str, List[str]]
    shell: bool
    display: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Run staged-file pre-commit intelligence checks.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python pre_commit_check.py --project-root <path>\n"

            "  python pre_commit_check.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--strict", action="store_true", help="Fail on warning-level findings")
    parser.add_argument("--skip-tests", action="store_true", help="Skip test execution")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def run_git(project_root: Path, args: List[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=["git", *args],
            returncode=1,
            stdout="",
            stderr="git timeout",
        )


def git_ready(project_root: Path) -> bool:
    inside = run_git(project_root, ["rev-parse", "--is-inside-work-tree"])
    return inside.returncode == 0 and inside.stdout.strip().lower() == "true"


def staged_files(project_root: Path) -> List[str]:
    result = run_git(project_root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    if result.returncode != 0:
        return []
    files = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
    return sorted(dict.fromkeys(files))


def classify(files: Iterable[str]) -> Dict[str, List[str]]:
    buckets = {
        "python": [],
        "js_ts": [],
        "ts_only": [],
        "style": [],
        "docs": [],
        "json": [],
    }
    for rel in files:
        ext = Path(rel).suffix.lower()
        if ext in PY_EXTS:
            buckets["python"].append(rel)
        if ext in JS_TS_EXTS:
            buckets["js_ts"].append(rel)
        if ext in {".ts", ".tsx"}:
            buckets["ts_only"].append(rel)
        if ext in STYLE_EXTS:
            buckets["style"].append(rel)
        if ext in DOC_EXTS:
            buckets["docs"].append(rel)
        if ext in JSON_EXTS:
            buckets["json"].append(rel)
    return buckets


def parse_added_lines(diff_text: str) -> Dict[str, List[Tuple[int, str]]]:
    added: Dict[str, List[Tuple[int, str]]] = {}
    current_file: Optional[str] = None
    new_line_no: Optional[int] = None

    for raw in diff_text.splitlines():
        if raw.startswith("+++ "):
            target = raw[4:].strip()
            if target == "/dev/null":
                current_file = None
            elif target.startswith("b/"):
                current_file = target[2:]
            else:
                current_file = target
            new_line_no = None
            continue

        if raw.startswith("@@ "):
            match = HUNK_PATTERN.match(raw)
            if match:
                new_line_no = int(match.group(1))
            continue

        if raw.startswith("+") and not raw.startswith("+++"):
            if current_file is not None and new_line_no is not None:
                added.setdefault(current_file, []).append((new_line_no, raw[1:]))
                new_line_no += 1
            continue

        if raw.startswith("-") and not raw.startswith("---"):
            continue

        if raw.startswith(" ") and new_line_no is not None:
            new_line_no += 1

    return added


def staged_added_lines(project_root: Path) -> Dict[str, List[Tuple[int, str]]]:
    diff_result = run_git(project_root, ["diff", "--cached", "--unified=0", "--no-color"])
    if diff_result.returncode != 0:
        return {}
    return parse_added_lines(diff_result.stdout)


def contains_pyproject_section(project_root: Path, section: str) -> bool:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return False
    content = pyproject.read_text(encoding="utf-8", errors="ignore")
    return section in content


def make_command(parts: List[str], is_windows: bool, name: str) -> CommandSpec:
    display = " ".join(parts)
    if is_windows and parts and parts[0] in {"npx", "npm"}:
        return CommandSpec(name=name, command=parts, shell=True, display=display)
    return CommandSpec(name=name, command=parts, shell=False, display=display)


def run_command(project_root: Path, spec: CommandSpec) -> Dict[str, object]:
    try:
        proc = subprocess.run(
            spec.command,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=spec.shell,
            check=False,
            timeout=120,
        )
        return {
            "ok": True,
            "exit_code": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + "\n[TIMEOUT] Command exceeded 120s limit.",
            "not_found": False,
        }
    except FileNotFoundError:
        return {"ok": False, "exit_code": None, "stdout": "", "stderr": f"Tool not found for {spec.name}"}
    except OSError as exc:
        return {"ok": False, "exit_code": None, "stdout": "", "stderr": str(exc)}


def lint_js_ts(project_root: Path, files: List[str], strict: bool) -> Tuple[Dict[str, object], bool]:
    if not files:
        return ({"check": "eslint", "status": "skip", "reason": "no js/ts staged"}, False)

    has_eslint = any(project_root.glob(".eslintrc*")) or any(project_root.glob("eslint.config.*"))
    if not has_eslint and (project_root / "package.json").exists():
        try:
            package_data = json.loads((project_root / "package.json").read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError:
            package_data = {}
        if isinstance(package_data, dict) and "eslintConfig" in package_data:
            has_eslint = True
    if not has_eslint:
        return ({"check": "eslint", "status": "skip", "reason": "eslint config not found"}, False)

    spec = make_command(["npx", "eslint", *files], os.name == "nt", "eslint")
    result = run_command(project_root, spec)
    if not result["ok"]:
        return ({"check": "eslint", "status": "skip", "reason": str(result["stderr"])}, False)

    exit_code = int(result["exit_code"] or 0)
    output = f"{result['stdout']}\n{result['stderr']}"
    issues_match = LINT_ISSUE_PATTERN.search(output)
    issues = int(issues_match.group(1)) if issues_match else (0 if exit_code == 0 else 1)
    if exit_code == 0:
        return ({"check": "eslint", "status": "pass", "files": len(files), "issues": 0}, True)

    status = "fail" if strict else "warn"
    return (
        {
            "check": "eslint",
            "status": status,
            "files": len(files),
            "issues": issues,
            "command": spec.display,
            "exit_code": exit_code,
        },
        strict,
    )


def lint_python(project_root: Path, files: List[str], strict: bool) -> Tuple[Dict[str, object], bool]:
    if not files:
        return ({"check": "python_lint", "status": "skip", "reason": "no python files staged"}, False)

    is_windows = os.name == "nt"
    use_ruff = (
        (project_root / "ruff.toml").exists()
        or (project_root / ".ruff.toml").exists()
        or contains_pyproject_section(project_root, "[tool.ruff]")
    )
    use_flake8 = (
        (project_root / ".flake8").exists()
        or contains_pyproject_section(project_root, "[tool.flake8]")
        or "[flake8]" in (project_root / "setup.cfg").read_text(encoding="utf-8", errors="ignore")
        if (project_root / "setup.cfg").exists()
        else False
    )

    if use_ruff:
        spec = make_command(["ruff", "check", *files], is_windows, "ruff")
        check_name = "ruff"
    elif use_flake8:
        spec = make_command(["flake8", *files], is_windows, "flake8")
        check_name = "flake8"
    else:
        return ({"check": "python_lint", "status": "skip", "reason": "ruff/flake8 config not found"}, False)

    result = run_command(project_root, spec)
    if not result["ok"]:
        return ({"check": "python_lint", "status": "skip", "reason": str(result["stderr"])}, False)

    exit_code = int(result["exit_code"] or 0)
    if exit_code == 0:
        return ({"check": "python_lint", "status": "pass", "tool": check_name, "files": len(files), "issues": 0}, True)

    status = "fail" if strict else "warn"
    issues = len([line for line in (result["stdout"] + "\n" + result["stderr"]).splitlines() if line.strip()])
    return (
        {
            "check": "python_lint",
            "status": status,
            "tool": check_name,
            "files": len(files),
            "issues": max(1, issues),
            "command": spec.display,
            "exit_code": exit_code,
        },
        strict,
    )


def type_check(project_root: Path, ts_files: List[str], strict: bool) -> Tuple[Dict[str, object], bool]:
    if not ts_files:
        return ({"check": "type_check", "status": "skip", "reason": "no ts/tsx files staged"}, False)
    if not (project_root / "tsconfig.json").exists():
        return ({"check": "type_check", "status": "skip", "reason": "tsconfig.json not found"}, False)

    spec = make_command(["npx", "tsc", "--noEmit"], os.name == "nt", "tsc")
    result = run_command(project_root, spec)
    if not result["ok"]:
        return ({"check": "type_check", "status": "skip", "reason": str(result["stderr"])}, False)

    exit_code = int(result["exit_code"] or 0)
    if exit_code == 0:
        return ({"check": "type_check", "status": "pass", "files": len(ts_files), "issues": 0}, True)

    status = "fail" if strict else "warn"
    return (
        {
            "check": "type_check",
            "status": status,
            "files": len(ts_files),
            "issues": 1,
            "command": spec.display,
            "exit_code": exit_code,
        },
        strict,
    )


def scan_todos(added: Dict[str, List[Tuple[int, str]]], code_files: Set[str], strict: bool) -> Tuple[Dict[str, object], bool]:
    matches = []
    for file_path, rows in added.items():
        if file_path not in code_files:
            continue
        for line_no, text in rows:
            if TODO_PATTERN.search(text):
                matches.append({"file": file_path, "line": line_no, "text": text.strip()})

    if not matches:
        return ({"check": "todo_audit", "status": "pass", "new_todos": 0}, True)
    status = "fail" if strict else "warn"
    return ({"check": "todo_audit", "status": status, "new_todos": len(matches), "issues": matches[:20]}, strict)


def scan_large_files(project_root: Path, files: Iterable[str], added: Dict[str, List[Tuple[int, str]]], strict: bool) -> Tuple[Dict[str, object], bool]:
    issues = []
    for rel in files:
        if rel not in added:
            continue
        full = project_root / rel
        if not full.exists() or not full.is_file():
            continue
        try:
            line_count = len(full.read_text(encoding="utf-8", errors="ignore").splitlines())
        except OSError:
            continue
        if line_count > 500:
            issues.append({"file": rel, "lines": line_count})

    if not issues:
        return ({"check": "large_file", "status": "pass", "issues": 0}, True)
    status = "fail" if strict else "warn"
    return ({"check": "large_file", "status": status, "issues": issues}, strict)


def secret_scan(added: Dict[str, List[Tuple[int, str]]]) -> Tuple[Dict[str, object], bool]:
    issues = []
    for file_path, rows in added.items():
        for line_no, text in rows:
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    issues.append({"file": file_path, "line": line_no, "pattern": label})
                    break

    if not issues:
        return ({"check": "secret_scan", "status": "pass", "files": 0, "issues": 0}, True)
    return (
        {
            "check": "secret_scan",
            "status": "fail",
            "files": len(sorted({item["file"] for item in issues})),
            "issues": issues,
        },
        False,
    )


def console_log_scan(added: Dict[str, List[Tuple[int, str]]], js_ts_files: Set[str], strict: bool) -> Tuple[Dict[str, object], bool]:
    if not js_ts_files:
        return ({"check": "console_log", "status": "skip", "reason": "no js/ts files staged"}, False)
    hits = []
    for file_path, rows in added.items():
        if file_path not in js_ts_files:
            continue
        for line_no, text in rows:
            if CONSOLE_LOG_PATTERN.search(text):
                hits.append({"file": file_path, "line": line_no, "text": text.strip()})

    if not hits:
        return ({"check": "console_log", "status": "pass", "new_count": 0}, True)
    status = "fail" if strict else "warn"
    return ({"check": "console_log", "status": status, "new_count": len(hits), "issues": hits[:30]}, strict)


def python_debug_scan(added: Dict[str, List[Tuple[int, str]]], py_files: Set[str], strict: bool) -> Tuple[Dict[str, object], bool]:
    if not py_files:
        return ({"check": "python_debug", "status": "skip", "reason": "no python files staged"}, False)
    hits = []
    for file_path, rows in added.items():
        if file_path not in py_files:
            continue
        for line_no, text in rows:
            if any(pattern.search(text) for pattern in PY_DEBUG_PATTERNS):
                hits.append({"file": file_path, "line": line_no, "text": text.strip()})

    if not hits:
        return ({"check": "python_debug", "status": "pass", "new_count": 0}, True)
    status = "fail" if strict else "warn"
    return ({"check": "python_debug", "status": status, "new_count": len(hits), "issues": hits[:30]}, strict)


def detect_runner_for_staged_tests(project_root: Path, buckets: Dict[str, List[str]]) -> Optional[str]:
    if buckets["js_ts"]:
        if any(project_root.glob("jest.config.*")):
            return "jest"
        if any(project_root.glob("vitest.config.*")):
            return "vitest"
        package_json = project_root / "package.json"
        if package_json.exists():
            content = package_json.read_text(encoding="utf-8", errors="ignore").lower()
            if "jest" in content:
                return "jest"
            if "vitest" in content:
                return "vitest"
    if buckets["python"]:
        if (project_root / "pytest.ini").exists() or contains_pyproject_section(project_root, "[tool.pytest]"):
            return "pytest"
    return None


def run_related_tests(
    project_root: Path,
    buckets: Dict[str, List[str]],
    strict: bool,
    skip_tests: bool,
) -> Tuple[Dict[str, object], bool]:
    if skip_tests:
        return ({"check": "tests", "status": "skip", "reason": "skipped by --skip-tests"}, False)

    runner = detect_runner_for_staged_tests(project_root, buckets)
    if not runner:
        return ({"check": "tests", "status": "skip", "reason": "no supported runner detected"}, False)

    if runner == "jest":
        files = buckets["js_ts"][:40]
        spec = make_command(["npx", "jest", "--findRelatedTests", *files, "--passWithNoTests"], os.name == "nt", "jest")
    elif runner == "vitest":
        files = buckets["js_ts"][:40]
        spec = make_command(["npx", "vitest", "related", *files], os.name == "nt", "vitest")
    else:
        test_files = [f for f in buckets["python"] if ("/tests/" in f or Path(f).name.startswith("test_"))]
        if not test_files:
            return ({"check": "tests", "status": "skip", "reason": "no staged python test files"}, False)
        spec = make_command(["pytest", *test_files], os.name == "nt", "pytest")

    result = run_command(project_root, spec)
    if not result["ok"]:
        return ({"check": "tests", "status": "skip", "reason": str(result["stderr"])}, False)

    exit_code = int(result["exit_code"] or 0)
    if exit_code == 0:
        return ({"check": "tests", "status": "pass", "runner": runner, "issues": 0}, True)

    status = "fail" if strict else "warn"
    return (
        {
            "check": "tests",
            "status": status,
            "runner": runner,
            "issues": 1,
            "command": spec.display,
            "exit_code": exit_code,
        },
        strict,
    )


def build_summary(blocking: List[str], warn_count: int) -> str:
    if not blocking and warn_count == 0:
        return "All staged checks passed."
    if blocking and warn_count:
        return f"{len(blocking)} blocking issue(s), {warn_count} warning(s)"
    if blocking:
        return f"{len(blocking)} blocking issue(s)"
    return f"{warn_count} warning(s)"


def run_pre_commit(project_root: Path, strict: bool, skip_tests: bool) -> Tuple[Dict[str, object], int]:
    if not git_ready(project_root):
        payload = {
            "status": "error",
            "staged_files": 0,
            "checks_run": 0,
            "checks_skipped": 0,
            "results": [],
            "blocking": [],
            "summary": "Not a git repository.",
            "message": f"Not a git repository: {project_root}",
        }
        return payload, 1

    staged = staged_files(project_root)
    if not staged:
        payload = {
            "status": "pass",
            "staged_files": 0,
            "checks_run": 0,
            "checks_skipped": 0,
            "results": [],
            "blocking": [],
            "summary": "no files staged",
        }
        return payload, 0

    buckets = classify(staged)
    added = staged_added_lines(project_root)
    code_files = {path for path in staged if Path(path).suffix.lower() in CODE_EXTS}
    js_ts_files = set(buckets["js_ts"])
    py_files = set(buckets["python"])

    checks: List[Tuple[Dict[str, object], bool]] = [
        lint_js_ts(project_root, buckets["js_ts"], strict),
        lint_python(project_root, buckets["python"], strict),
        type_check(project_root, buckets["ts_only"], strict),
        run_related_tests(project_root, buckets, strict, skip_tests),
        scan_todos(added, code_files, strict),
        scan_large_files(project_root, staged, added, strict),
        secret_scan(added),
        console_log_scan(added, js_ts_files, strict),
        python_debug_scan(added, py_files, strict),
    ]

    results: List[Dict[str, object]] = []
    blocking: List[str] = []
    checks_run = 0
    checks_skipped = 0
    warn_count = 0

    for item, should_block in checks:
        status = str(item.get("status", "skip"))
        if status == "skip":
            checks_skipped += 1
        else:
            checks_run += 1

        if status == "warn":
            warn_count += 1
        if status == "fail":
            if should_block or item.get("check") == "secret_scan":
                blocking.append(str(item.get("check")))
            else:
                warn_count += 1
                item["status"] = "warn"
        elif status == "warn" and strict:
            blocking.append(str(item.get("check")))

        results.append(item)

    overall_status = "fail" if blocking else ("warn" if warn_count > 0 else "pass")
    payload = {
        "status": overall_status,
        "staged_files": len(staged),
        "checks_run": checks_run,
        "checks_skipped": checks_skipped,
        "results": results,
        "blocking": sorted(dict.fromkeys(blocking)),
        "summary": build_summary(sorted(dict.fromkeys(blocking)), warn_count),
    }
    exit_code = 1 if blocking else 0
    return payload, exit_code


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit(
            {
                "status": "error",
                "staged_files": 0,
                "checks_run": 0,
                "checks_skipped": 0,
                "results": [],
                "blocking": [],
                "summary": "Invalid project root.",
                "message": f"Project root does not exist or is not a directory: {project_root}",
            }
        )
        return 1

    payload, code = run_pre_commit(project_root, args.strict, args.skip_tests)
    emit(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
