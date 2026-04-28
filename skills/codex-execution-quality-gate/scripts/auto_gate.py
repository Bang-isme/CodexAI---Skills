#!/usr/bin/env python3
"""Run the CodexAI quality gate as a single entry point."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bundle_check
import pre_commit_check
import run_gate
import security_scan
import tech_debt_scan


RunnerResult = Dict[str, Any]
Runner = Callable[[Path], RunnerResult]

MODE_CHECKS: Dict[str, List[str]] = {
    "quick": ["runtime_hook", "security", "pre_commit"],
    "full": ["runtime_hook", "security", "gate", "tech_debt", "role_docs", "specs", "knowledge"],
    "deploy": ["runtime_hook", "security", "gate", "tech_debt", "role_docs", "specs", "knowledge", "bundle", "suggestions"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the CodexAI quality gate through a single orchestration entry point.",
    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument(
        "--mode",
        choices=tuple(MODE_CHECKS.keys()),
        default="quick",
        help="Gate mode: quick, full, or deploy",
    )
    parser.add_argument("--human", action="store_true", help="Print a summary table to stderr")
    return parser.parse_args()


def dedupe_strings(values: List[str]) -> List[str]:
    merged: List[str] = []
    seen = set()
    for value in values:
        normalized = str(value).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(normalized)
    return merged


def make_runner_result(
    payload: Dict[str, Any],
    *,
    blocking_issues: List[str] | None = None,
    warnings: List[str] | None = None,
) -> RunnerResult:
    return {
        "payload": payload,
        "blocking_issues": blocking_issues or [],
        "warnings": warnings or [],
    }


def summarize_result_statuses(statuses: List[str]) -> str:
    meaningful = [status for status in statuses if status not in {"", "skip"}]
    if not meaningful:
        return "skip"
    if any(status == "fail" for status in meaningful):
        return "fail"
    if any(status == "warn" for status in meaningful):
        return "warn"
    if any(status == "pass" for status in meaningful):
        return "pass"
    return "skip"


def summarize_gate_child(item: Dict[str, Any]) -> str:
    if item.get("executed"):
        return "pass" if item.get("status") == "pass" else "fail"
    if not item.get("detected"):
        return "skip"
    return "pass" if bool(item.get("passed")) else "fail"


def run_security(project_root: Path) -> RunnerResult:
    raw = security_scan.scan(project_root)
    critical_count = len(raw.get("critical", []))
    warning_count = len(raw.get("warnings", []))
    payload = {
        "status": "pass" if critical_count == 0 else "fail",
        "critical": critical_count,
        "warnings": warning_count,
        "summary": raw.get("summary", ""),
    }
    blocking_issues = [f"{critical_count} security critical issue(s) detected."] if critical_count else []
    warnings = [f"{warning_count} security warning(s)."] if warning_count else []
    return make_runner_result(payload, blocking_issues=blocking_issues, warnings=warnings)


def run_pre_commit(project_root: Path) -> RunnerResult:
    raw, exit_code = pre_commit_check.run_pre_commit(project_root, strict=False, skip_tests=False)
    results = raw.get("results", []) if isinstance(raw.get("results"), list) else []
    lint_status = summarize_result_statuses(
        [str(item.get("status", "skip")) for item in results if str(item.get("check", "")) in {"eslint", "python_lint", "type_check"}]
    )
    test_status = summarize_result_statuses(
        [str(item.get("status", "skip")) for item in results if str(item.get("check", "")) == "tests"]
    )
    warn_checks = [
        str(item.get("check", "unknown"))
        for item in results
        if str(item.get("status", "")).strip().lower() == "warn"
    ]
    payload = {
        "status": "pass" if exit_code == 0 and raw.get("status") != "error" else "fail",
        "staged_files": int(raw.get("staged_files", 0) or 0),
        "checks_run": int(raw.get("checks_run", 0) or 0),
        "checks_skipped": int(raw.get("checks_skipped", 0) or 0),
        "lint": lint_status,
        "test": test_status,
        "warnings": len(warn_checks),
        "summary": raw.get("summary", ""),
    }

    if exit_code != 0 or raw.get("status") == "error":
        blocking = [f"Pre-commit check failed: {raw.get('summary', 'unknown error')}"]
        if isinstance(raw.get("blocking"), list) and raw.get("blocking"):
            blocking = [f"Pre-commit blocking checks: {', '.join(str(item) for item in raw['blocking'])}"]
        return make_runner_result(payload, blocking_issues=blocking)

    warnings: List[str] = []
    if warn_checks:
        warnings.append(f"Pre-commit reported warnings for: {', '.join(warn_checks)}.")
    return make_runner_result(payload, warnings=warnings)


def run_gate_check(project_root: Path) -> RunnerResult:
    raw = run_gate.build_gate_report(
        project_root=project_root,
        timeout_lint=120,
        timeout_test=300,
        skip_lint=False,
        skip_test=False,
    )
    lint_status = summarize_gate_child(raw.get("lint", {})) if isinstance(raw.get("lint"), dict) else "skip"
    test_status = summarize_gate_child(raw.get("test", {})) if isinstance(raw.get("test"), dict) else "skip"
    warnings_count = len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0
    payload = {
        "status": "pass" if bool(raw.get("gate_passed", False)) else "fail",
        "lint": lint_status,
        "test": test_status,
        "blocking_issues": len(raw.get("blocking_issues", [])) if isinstance(raw.get("blocking_issues"), list) else 0,
        "warnings": warnings_count,
    }
    return make_runner_result(
        payload,
        blocking_issues=[str(item) for item in raw.get("blocking_issues", []) if str(item).strip()],
        warnings=[str(item) for item in raw.get("warnings", []) if str(item).strip()],
    )


def run_tech_debt(project_root: Path) -> RunnerResult:
    raw = tech_debt_scan.scan_project(
        project_root=project_root,
        max_function_lines=50,
        max_file_lines=500,
        todo_age_days=30,
    )
    total_issues = int(raw.get("total_issues", 0) or 0)
    warning_count = len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0
    status = "warn" if total_issues or warning_count else "pass"
    payload = {
        "status": status,
        "total_issues": total_issues,
        "warnings": warning_count,
        "summary": raw.get("summary", ""),
    }
    warnings: List[str] = []
    if total_issues:
        warnings.append(f"{total_issues} tech debt signal(s) detected.")
    if warning_count:
        warnings.append(f"Tech debt scan emitted {warning_count} warning(s).")
    return make_runner_result(payload, warnings=warnings)


def run_bundle(project_root: Path) -> RunnerResult:
    raw = bundle_check.analyze(project_root)
    status_map = {"ok": "pass", "warning": "warn", "not_applicable": "skip"}
    warning_count = len(raw.get("warnings", [])) if isinstance(raw.get("warnings"), list) else 0
    payload = {
        "status": status_map.get(str(raw.get("status", "warning")), "warn"),
        "package_manager": raw.get("package_manager", "none"),
        "total_dependencies": int(raw.get("total_dependencies", 0) or 0),
        "large_packages": len(raw.get("large_packages", [])) if isinstance(raw.get("large_packages"), list) else 0,
        "warnings": warning_count,
    }
    warnings: List[str] = []
    if payload["status"] == "warn":
        warnings.append(f"Bundle check reported {warning_count} warning(s).")
    return make_runner_result(payload, warnings=warnings)


def run_json_subprocess(script_name: str, args: List[str], project_root: Path) -> Tuple[Dict[str, Any], int]:
    script_path = SCRIPT_DIR / script_name
    command = [sys.executable, str(script_path), *args]
    completed = subprocess.run(
        command,
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=300,
    )
    payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
    return payload, completed.returncode


def git_changed_files(project_root: Path) -> List[str]:
    commands = [
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--cached", "--name-only"],
    ]
    changed: List[str] = []
    seen: set[str] = set()
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                cwd=project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if completed.returncode != 0:
            continue
        for line in completed.stdout.splitlines():
            normalized = line.strip().replace("\\", "/")
            if normalized and normalized not in seen:
                changed.append(normalized)
                seen.add(normalized)
    return changed


def run_suggestions(project_root: Path) -> RunnerResult:
    try:
        raw, exit_code = run_json_subprocess(
            "suggest_improvements.py",
            ["--project-root", str(project_root), "--source", "last-commit"],
            project_root,
        )
    except (json.JSONDecodeError, OSError, subprocess.TimeoutExpired) as exc:
        payload = {
            "status": "warn",
            "suggestions": 0,
            "changed_files_scanned": 0,
            "summary": "Suggestion engine unavailable.",
        }
        return make_runner_result(payload, warnings=[f"Suggest improvements unavailable: {exc}"])

    suggestions_count = len(raw.get("suggestions", [])) if isinstance(raw.get("suggestions"), list) else 0
    payload = {
        "status": "warn" if suggestions_count else ("pass" if exit_code == 0 else "warn"),
        "suggestions": suggestions_count,
        "changed_files_scanned": int(raw.get("changed_files_scanned", 0) or 0),
        "summary": raw.get("summary", ""),
    }
    warnings: List[str] = []
    if exit_code != 0 or raw.get("status") == "error":
        warnings.append(str(raw.get("message", "Suggest improvements exited with an error.")))
    elif suggestions_count:
        warnings.append(f"{suggestions_count} improvement suggestion(s) generated.")
    return make_runner_result(payload, warnings=warnings)


def run_role_docs(project_root: Path) -> RunnerResult:
    script_path = SCRIPT_DIR.parent.parent / "codex-role-docs" / "scripts" / "check_role_docs.py"
    if not script_path.exists():
        payload = {
            "status": "skip",
            "overall": "skip",
            "missing_docs": 0,
            "stale_docs": 0,
            "suggested_updates": 0,
            "summary": "Role docs skill is not installed.",
        }
        return make_runner_result(payload, warnings=["Role docs advisory skipped: codex-role-docs is not installed."])

    command = [
        sys.executable,
        str(script_path),
        "--project-root",
        str(project_root),
        "--format",
        "json",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
        raw = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except (json.JSONDecodeError, OSError, subprocess.TimeoutExpired) as exc:
        payload = {
            "status": "warn",
            "overall": "warn",
            "missing_docs": 0,
            "stale_docs": 0,
            "suggested_updates": 0,
            "summary": "Role docs advisory unavailable.",
        }
        return make_runner_result(payload, warnings=[f"Role docs advisory unavailable: {exc}"])

    missing_count = len(raw.get("missing_docs", [])) if isinstance(raw.get("missing_docs"), list) else 0
    stale_count = len(raw.get("stale_docs", [])) if isinstance(raw.get("stale_docs"), list) else 0
    suggested_count = len(raw.get("suggested_updates", [])) if isinstance(raw.get("suggested_updates"), list) else 0
    overall = str(raw.get("overall", "warn"))
    status = "pass" if overall == "pass" else ("skip" if overall == "skip" else "warn")
    payload = {
        "status": status,
        "overall": overall,
        "missing_docs": missing_count,
        "stale_docs": stale_count,
        "suggested_updates": suggested_count,
        "summary": "Role docs advisory check completed.",
    }

    warnings: List[str] = []
    if completed.returncode != 0 or raw.get("status") == "error":
        warnings.append(str(raw.get("message", "Role docs advisory exited with an error.")))
    elif overall == "warn":
        warnings.append(
            "Role docs advisory: "
            f"{missing_count} missing doc(s), {stale_count} stale doc(s), {suggested_count} suggested update(s)."
        )
    return make_runner_result(payload, warnings=warnings)


def run_specs(project_root: Path) -> RunnerResult:
    specs_root = project_root / ".codex" / "specs"
    if not specs_root.exists():
        payload = {
            "status": "skip",
            "overall": "skip",
            "matched_specs": 0,
            "unmapped_files": 0,
            "summary": "Spec advisory skipped because .codex/specs is absent.",
        }
        return make_runner_result(payload)

    script_path = SCRIPT_DIR.parent.parent / "codex-spec-driven-development" / "scripts" / "check_spec.py"
    if not script_path.exists():
        payload = {
            "status": "warn",
            "overall": "warn",
            "matched_specs": 0,
            "unmapped_files": 0,
            "summary": "Spec advisory unavailable.",
        }
        return make_runner_result(payload, warnings=["Spec advisory skipped: codex-spec-driven-development is not installed."])

    changed_files = git_changed_files(project_root)
    command = [
        sys.executable,
        str(script_path),
        "--project-root",
        str(project_root),
        "--changed-files",
        ",".join(changed_files),
        "--format",
        "json",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
        raw = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except (json.JSONDecodeError, OSError, subprocess.TimeoutExpired) as exc:
        payload = {"status": "warn", "overall": "warn", "matched_specs": 0, "unmapped_files": 0, "summary": "Spec advisory unavailable."}
        return make_runner_result(payload, warnings=[f"Spec advisory unavailable: {exc}"])

    unmapped = raw.get("unmapped_files", [])
    matched = raw.get("matched_specs", [])
    unmapped_count = len(unmapped) if isinstance(unmapped, list) else 0
    matched_count = len(matched) if isinstance(matched, list) else 0
    overall = str(raw.get("overall", "warn"))
    payload = {
        "status": "pass" if overall == "pass" else ("skip" if overall == "skip" else "warn"),
        "overall": overall,
        "matched_specs": matched_count,
        "unmapped_files": unmapped_count,
        "changed_files": len(changed_files),
        "summary": "Spec traceability advisory completed.",
    }
    warnings: List[str] = []
    if completed.returncode != 0 or raw.get("status") == "error":
        warnings.append(str(raw.get("message", "Spec advisory exited with an error.")))
    elif unmapped_count:
        warnings.append(f"Spec advisory: {unmapped_count} changed file(s) are not mapped to a spec.")
    return make_runner_result(payload, warnings=warnings)


def run_knowledge(project_root: Path) -> RunnerResult:
    index_path = project_root / ".codex" / "knowledge" / "index.json"
    if not index_path.exists():
        payload = {
            "status": "skip",
            "overall": "skip",
            "summary": "Knowledge index advisory skipped because .codex/knowledge/index.json is absent.",
        }
        return make_runner_result(payload)
    try:
        raw = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        payload = {"status": "warn", "overall": "warn", "summary": "Knowledge index is unreadable."}
        return make_runner_result(payload, warnings=[f"Knowledge index unreadable: {exc}"])

    stale_sources: List[str] = []
    index_mtime = index_path.stat().st_mtime
    for rel in [".codex/context/genome.md", ".codex/project-docs/index.json"]:
        source = project_root / rel
        if source.exists() and source.stat().st_mtime > index_mtime:
            stale_sources.append(rel)
    payload = {
        "status": "warn" if stale_sources else "pass",
        "overall": "warn" if stale_sources else "pass",
        "sources": raw.get("sources", {}),
        "stale_sources": stale_sources,
        "summary": "Knowledge index advisory completed.",
    }
    warnings = [f"Knowledge index is older than: {', '.join(stale_sources)}."] if stale_sources else []
    return make_runner_result(payload, warnings=warnings)


def run_runtime_hook(project_root: Path) -> RunnerResult:
    script_path = SCRIPT_DIR.parent.parent / "codex-runtime-hook" / "scripts" / "runtime_hook.py"
    if not script_path.exists():
        payload = {
            "status": "skip",
            "overall": "skip",
            "detected_domains": [],
            "suggested_agent": None,
            "missing_readiness": 0,
            "recommended_commands": [],
            "summary": "Runtime hook skill is not installed.",
        }
        return make_runner_result(payload)

    command = [
        sys.executable,
        str(script_path),
        "--project-root",
        str(project_root),
        "--format",
        "json",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
        raw = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except (json.JSONDecodeError, OSError, subprocess.TimeoutExpired) as exc:
        payload = {
            "status": "warn",
            "overall": "warn",
            "detected_domains": [],
            "suggested_agent": None,
            "missing_readiness": 0,
            "recommended_commands": [],
            "summary": "Runtime hook advisory unavailable.",
        }
        return make_runner_result(payload, warnings=[f"Runtime hook advisory unavailable: {exc}"])

    domains = raw.get("detected_domains", [])
    missing = raw.get("missing", [])
    commands = raw.get("recommended_commands", [])
    missing_count = len(missing) if isinstance(missing, list) else 0
    overall = str(raw.get("overall", "warn"))
    status = "pass" if overall == "pass" else ("skip" if overall == "skip" else "warn")
    payload = {
        "status": status,
        "overall": overall,
        "detected_domains": domains if isinstance(domains, list) else [],
        "suggested_agent": raw.get("suggested_agent"),
        "missing_readiness": missing_count,
        "recommended_commands": commands if isinstance(commands, list) else [],
        "summary": "Runtime hook advisory check completed.",
    }

    warnings: List[str] = []
    if completed.returncode != 0 or raw.get("status") == "error":
        warnings.append(str(raw.get("message", "Runtime hook advisory exited with an error.")))
    elif status == "warn" and missing_count:
        warnings.append(f"Runtime hook found {missing_count} readiness gap(s).")
    return make_runner_result(payload, warnings=warnings)


CHECK_RUNNERS: Dict[str, Runner] = {
    "runtime_hook": run_runtime_hook,
    "security": run_security,
    "pre_commit": run_pre_commit,
    "gate": run_gate_check,
    "tech_debt": run_tech_debt,
    "role_docs": run_role_docs,
    "specs": run_specs,
    "knowledge": run_knowledge,
    "bundle": run_bundle,
    "suggestions": run_suggestions,
}


def describe_check(name: str, payload: Dict[str, Any]) -> str:
    status = str(payload.get("status", "skip")).upper()
    if name == "runtime_hook":
        domains = payload.get("detected_domains", [])
        domain_text = ",".join(str(item) for item in domains) if isinstance(domains, list) and domains else "none"
        return (
            f"Runtime hook: {status} "
            f"({domain_text}; {payload.get('missing_readiness', 0)} readiness gaps)"
        )
    if name == "security":
        return f"Security: {status} ({payload.get('critical', 0)} critical, {payload.get('warnings', 0)} warnings)"
    if name == "pre_commit":
        return (
            f"Pre-commit: {status} "
            f"(lint {str(payload.get('lint', 'skip')).upper()}, test {str(payload.get('test', 'skip')).upper()})"
        )
    if name == "gate":
        return f"Run gate: {status} (lint {str(payload.get('lint', 'skip')).upper()}, test {str(payload.get('test', 'skip')).upper()})"
    if name == "tech_debt":
        return f"Tech debt: {status} ({payload.get('total_issues', 0)} issues)"
    if name == "role_docs":
        return (
            f"Role docs: {status} "
            f"({payload.get('missing_docs', 0)} missing, {payload.get('stale_docs', 0)} stale, "
            f"{payload.get('suggested_updates', 0)} updates)"
        )
    if name == "specs":
        return (
            f"Specs: {status} "
            f"({payload.get('matched_specs', 0)} matched, {payload.get('unmapped_files', 0)} unmapped)"
        )
    if name == "knowledge":
        stale = payload.get("stale_sources", [])
        stale_count = len(stale) if isinstance(stale, list) else 0
        return f"Knowledge: {status} ({stale_count} stale source(s))"
    if name == "bundle":
        return f"Bundle: {status} ({payload.get('warnings', 0)} warnings)"
    if name == "suggestions":
        return f"Suggestions: {status} ({payload.get('suggestions', 0)} suggestions)"
    return f"{name}: {status}"


def render_human_box(title: str, rows: List[str]) -> str:
    width = max(42, len(title), *(len(row) for row in rows))
    top = "+" + ("-" * (width + 2)) + "+"
    header = f"| {title.center(width)} |"
    divider = "+" + ("-" * (width + 2)) + "+"
    body = [f"| {row.ljust(width)} |" for row in rows]
    return "\n".join([top, header, divider, *body, top])


def print_human_summary(report: Dict[str, Any]) -> None:
    checks = report.get("checks", {})
    rows: List[str] = []
    if isinstance(checks, dict):
        for name in MODE_CHECKS.get(str(report.get("mode", "quick")), []):
            payload = checks.get(name, {})
            if isinstance(payload, dict):
                rows.append(describe_check(name, payload))
    rows.append(f"Overall: {str(report.get('overall', 'fail')).upper()}")
    rows.append(f"Duration: {report.get('duration_seconds', 0)}s")
    print(render_human_box("AUTO GATE RESULTS", rows), file=sys.stderr)


def run_auto_gate(project_root: Path, mode: str) -> Tuple[Dict[str, Any], int]:
    started = time.perf_counter()
    if not project_root.exists() or not project_root.is_dir():
        report = {
            "status": "error",
            "mode": mode,
            "project_root": str(project_root),
            "checks": {},
            "overall": "fail",
            "duration_seconds": 0.0,
            "blocking_issues": [f"Project root does not exist or is not a directory: {project_root}"],
            "warnings": [],
        }
        return report, 1

    checks: Dict[str, Dict[str, Any]] = {}
    blocking_issues: List[str] = []
    warnings: List[str] = []

    for check_name in MODE_CHECKS[mode]:
        runner = CHECK_RUNNERS[check_name]
        try:
            result = runner(project_root)
        except Exception as exc:  # pragma: no cover - defensive fallback
            payload = {"status": "fail", "summary": f"{check_name} runner failed unexpectedly"}
            checks[check_name] = payload
            if check_name in {"security", "pre_commit", "gate"}:
                blocking_issues.append(f"{check_name} runner crashed: {exc}")
            else:
                warnings.append(f"{check_name} runner crashed: {exc}")
            continue

        payload = result.get("payload", {})
        checks[check_name] = payload
        result_blocking = [str(item) for item in result.get("blocking_issues", []) if str(item).strip()]
        result_warnings = [str(item) for item in result.get("warnings", []) if str(item).strip()]

        if check_name in {"security", "pre_commit", "gate"}:
            blocking_issues.extend(result_blocking)
        else:
            warnings.extend(result_blocking)
        warnings.extend(result_warnings)

    duration_seconds = round(time.perf_counter() - started, 2)
    blocking_issues = dedupe_strings(blocking_issues)
    warnings = dedupe_strings(warnings)
    overall = "pass" if not blocking_issues else "fail"
    report = {
        "status": overall,
        "mode": mode,
        "project_root": str(project_root),
        "checks": checks,
        "overall": overall,
        "duration_seconds": duration_seconds,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
    }
    return report, (0 if overall == "pass" else 1)


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    report, exit_code = run_auto_gate(project_root, args.mode)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.human:
        print_human_summary(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
