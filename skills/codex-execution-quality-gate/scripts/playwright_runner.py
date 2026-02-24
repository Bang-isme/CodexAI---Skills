#!/usr/bin/env python3
"""
Playwright wrapper for installation checks, test skeleton generation, and test execution.
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
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse


TEST_FILE_EXTENSIONS = {".js", ".ts", ".jsx", ".tsx"}
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Playwright check/generate/run wrapper.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python playwright_runner.py --project-root <path> --mode check\n"

            "  python playwright_runner.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--mode", required=True, choices=["run", "generate", "check"], help="Execution mode")
    parser.add_argument("--url", default="", help="URL for generate mode")
    parser.add_argument("--test-dir", default="", help="Test directory override")
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"], default="chromium", help="Browser")
    return parser.parse_args()


def emit(payload: Dict[str, object], exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


def run_command(args: Sequence[str], cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[Optional[subprocess.CompletedProcess], Optional[str]]:
    cmd_list = list(args)
    try:
        process = subprocess.run(
            cmd_list,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
            timeout=timeout,
        )
        return process, None
    except FileNotFoundError:
        if os.name == "nt":
            try:
                cmd = subprocess.list2cmdline(cmd_list)
                process = subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    shell=True,
                    check=False,
                    timeout=timeout,
                )
                return process, None
            except Exception as exc:  # pragma: no cover - defensive
                return None, str(exc)
        return None, "Command not found"
    except subprocess.TimeoutExpired:
        return None, "Command timed out"
    except OSError as exc:
        return None, str(exc)


def detect_playwright(project_root: Path) -> Tuple[bool, str]:
    process, error = run_command(["npx", "playwright", "--version"], cwd=project_root, timeout=300)
    if error is not None or process is None:
        return False, ""
    if process.returncode != 0:
        return False, ""
    version_text = (process.stdout or process.stderr).strip()
    version = version_text.split()[-1] if version_text else ""
    return True, version


def resolve_test_dir(project_root: Path, provided: str, create: bool) -> Path:
    if provided:
        candidate = Path(provided).expanduser()
        if not candidate.is_absolute():
            candidate = project_root / candidate
        candidate = candidate.resolve()
    else:
        preferred = project_root / "e2e"
        secondary = project_root / "tests" / "e2e"
        if preferred.exists():
            candidate = preferred.resolve()
        elif secondary.exists():
            candidate = secondary.resolve()
        else:
            candidate = preferred.resolve()
    if create:
        candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def count_test_files(test_dir: Path) -> int:
    if not test_dir.exists() or not test_dir.is_dir():
        return 0
    count = 0
    for path in test_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEST_FILE_EXTENSIONS:
            continue
        name = path.name.lower()
        if ".spec." in name or ".test." in name:
            count += 1
    return count


def browser_install_status(project_root: Path, browser: str) -> bool:
    process, error = run_command(["npx", "playwright", "install", "--dry-run", browser], cwd=project_root, timeout=300)
    if error is not None or process is None or process.returncode != 0:
        return False
    output = ((process.stdout or "") + "\n" + (process.stderr or "")).lower()
    if "will be downloaded" in output or "download" in output and "already" not in output:
        return False
    if "already" in output and ("installed" in output or "downloaded" in output):
        return True
    return True


def slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    raw = parsed.path.strip("/").split("/")[-1] if parsed.path else ""
    if not raw:
        raw = "home"
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", raw).strip("-").lower()
    return slug or "page"


def choose_output_file(test_dir: Path, slug: str) -> Path:
    base = test_dir / f"{slug}.spec.js"
    if not base.exists():
        return base
    counter = 2
    while True:
        candidate = test_dir / f"{slug}-{counter}.spec.js"
        if not candidate.exists():
            return candidate
        counter += 1


def make_skeleton(url: str, page_name: str) -> str:
    return (
        "// Auto-generated E2E test skeleton\n"
        "const { test, expect } = require('@playwright/test');\n\n"
        f"test.describe('{page_name}', () => {{\n"
        "  test.beforeEach(async ({ page }) => {\n"
        f"    await page.goto('{url}');\n"
        "  });\n\n"
        "  test('should load page successfully', async ({ page }) => {\n"
        "    await expect(page).toHaveTitle(/.*/);\n"
        "  });\n\n"
        "  test('should have main content visible', async ({ page }) => {\n"
        "    // TODO: Add specific content assertions\n"
        "    await expect(page.locator('main, #root, #app, body')).toBeVisible();\n"
        "  });\n\n"
        "  test('should be responsive', async ({ page }) => {\n"
        "    await page.setViewportSize({ width: 375, height: 667 });\n"
        "    // TODO: Add mobile-specific assertions\n"
        "  });\n\n"
        "  // TODO: Add more specific tests for this page\n"
        "});\n"
    )


def strip_ansi(text: str) -> str:
    return ANSI_PATTERN.sub("", text)


def extract_json_blob(text: str) -> Optional[Dict[str, object]]:
    cleaned = strip_ansi(text).strip()
    if not cleaned:
        return None
    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        fragment = cleaned[start : end + 1]
        try:
            payload = json.loads(fragment)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            return None
    return None


def collect_failures(report: Dict[str, object]) -> List[Dict[str, str]]:
    failures: List[Dict[str, str]] = []

    def walk_suite(suite: Dict[str, object]) -> None:
        for child in suite.get("suites", []) if isinstance(suite.get("suites"), list) else []:
            if isinstance(child, dict):
                walk_suite(child)

        specs = suite.get("specs", [])
        if not isinstance(specs, list):
            return
        for spec in specs:
            if not isinstance(spec, dict):
                continue
            file_path = str(spec.get("file") or suite.get("file") or "")
            spec_title = str(spec.get("title") or "Unnamed test")
            tests = spec.get("tests", [])
            if not isinstance(tests, list):
                continue
            for test in tests:
                if not isinstance(test, dict):
                    continue
                test_title = str(test.get("title") or spec_title)
                results = test.get("results", [])
                if not isinstance(results, list):
                    continue
                for result in results:
                    if not isinstance(result, dict):
                        continue
                    status = str(result.get("status") or "")
                    if status not in {"failed", "timedOut", "interrupted"}:
                        continue
                    errors = result.get("errors", [])
                    error_text = status
                    if isinstance(errors, list) and errors:
                        first = errors[0]
                        if isinstance(first, dict):
                            error_text = str(first.get("message") or first.get("value") or status)
                        else:
                            error_text = str(first)
                    failures.append(
                        {
                            "test": test_title,
                            "file": file_path,
                            "error": error_text.strip()[:300],
                        }
                    )
                    break

    for top_suite in report.get("suites", []) if isinstance(report.get("suites"), list) else []:
        if isinstance(top_suite, dict):
            walk_suite(top_suite)
    return failures


def parse_run_summary(report: Optional[Dict[str, object]], fallback_exit: int, elapsed_ms: int) -> Dict[str, object]:
    if report is None:
        failed = 1 if fallback_exit != 0 else 0
        total = max(failed, 1 if fallback_exit != 0 else 0)
        return {
            "total": total,
            "passed": max(total - failed, 0),
            "failed": failed,
            "skipped": 0,
            "duration_ms": elapsed_ms,
            "failures": [],
            "warnings": ["Unable to parse Playwright JSON reporter output."],
        }

    stats = report.get("stats", {})
    if not isinstance(stats, dict):
        stats = {}
    passed = int(stats.get("expected", 0) or 0)
    failed = int(stats.get("unexpected", 0) or 0) + int(stats.get("timedOut", 0) or 0)
    skipped = int(stats.get("skipped", 0) or 0)
    flaky = int(stats.get("flaky", 0) or 0)
    total = int(stats.get("total", 0) or 0)
    if total <= 0:
        total = passed + failed + skipped + flaky
    duration = int(stats.get("duration", 0) or 0)
    if duration <= 0:
        duration = elapsed_ms

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_ms": duration,
        "failures": collect_failures(report),
        "warnings": [],
    }


def mode_check(project_root: Path, args: argparse.Namespace) -> None:
    installed, version = detect_playwright(project_root)
    test_dir = resolve_test_dir(project_root, args.test_dir, create=False)
    test_dir_exists = test_dir.exists() and test_dir.is_dir()
    test_files = count_test_files(test_dir)

    if not installed:
        emit(
            {
                "status": "not_installed",
                "install_steps": [
                    "npm init playwright@latest",
                    "npx playwright install chromium",
                ],
                "test_dir_exists": test_dir_exists,
                "test_files": test_files,
            },
            exit_code=0,
        )

    browsers = {
        "chromium": browser_install_status(project_root, "chromium"),
        "firefox": browser_install_status(project_root, "firefox"),
        "webkit": browser_install_status(project_root, "webkit"),
    }

    emit(
        {
            "status": "installed",
            "version": version,
            "browsers": browsers,
            "test_dir_exists": test_dir_exists,
            "test_files": test_files,
        },
        exit_code=0,
    )


def mode_generate(project_root: Path, args: argparse.Namespace) -> None:
    if not args.url.strip():
        emit(
            {
                "status": "error",
                "message": "Mode generate requires --url.",
                "hint": "Use: --mode generate --url http://localhost:3000/path",
            },
            exit_code=1,
        )

    test_dir = resolve_test_dir(project_root, args.test_dir, create=True)
    slug = slug_from_url(args.url.strip())
    output_file = choose_output_file(test_dir, slug)
    page_name = slug.replace("-", " ")
    output_file.write_text(make_skeleton(args.url.strip(), page_name), encoding="utf-8", newline="\n")

    file_display = output_file.as_posix()
    try:
        file_display = output_file.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        pass

    emit(
        {
            "status": "generated",
            "file": file_display,
            "tests": 3,
            "note": "Skeleton generated Ã¢â‚¬â€ fill in TODO assertions",
        },
        exit_code=0,
    )


def mode_run(project_root: Path, args: argparse.Namespace) -> None:
    installed, _ = detect_playwright(project_root)
    if not installed:
        emit(
            {
                "status": "not_installed",
                "install_steps": [
                    "npm init playwright@latest",
                    "npx playwright install chromium",
                ],
            },
            exit_code=0,
        )

    test_dir = resolve_test_dir(project_root, args.test_dir, create=False)
    if not test_dir.exists() or not test_dir.is_dir():
        emit(
            {
                "status": "warn",
                "message": f"Test directory not found: {test_dir.as_posix()}",
                "suggestion": "Use --mode generate --url <url> to create starter tests or pass --test-dir.",
            },
            exit_code=0,
        )

    if count_test_files(test_dir) == 0:
        emit(
            {
                "status": "warn",
                "message": f"No Playwright test files found in: {test_dir.as_posix()}",
                "suggestion": "Create *.spec.js/*.spec.ts files or run --mode generate first.",
            },
            exit_code=0,
        )

    command = [
        "npx",
        "playwright",
        "test",
        test_dir.as_posix(),
        "--reporter=json",
        f"--browser={args.browser}",
    ]

    started = time.time()
    process, error = run_command(command, cwd=project_root, timeout=1800)
    elapsed_ms = int((time.time() - started) * 1000)
    if error is not None or process is None:
        emit(
            {
                "status": "error",
                "message": error or "Unable to execute Playwright tests.",
                "suggestion": "Run `npx playwright --version` and verify Node/npm environment.",
            },
            exit_code=1,
        )

    report = extract_json_blob(process.stdout or "") or extract_json_blob(process.stderr or "")
    parsed = parse_run_summary(report, process.returncode, elapsed_ms)
    summary = (
        f"{parsed['passed']}/{parsed['total']} passed, {parsed['failed']} failed, "
        f"{parsed['skipped']} skipped ({parsed['duration_ms'] / 1000:.1f}s)"
    )

    payload: Dict[str, object] = {
        "status": "completed",
        "total": parsed["total"],
        "passed": parsed["passed"],
        "failed": parsed["failed"],
        "skipped": parsed["skipped"],
        "duration_ms": parsed["duration_ms"],
        "failures": parsed["failures"],
        "summary": summary,
    }
    warnings = list(parsed.get("warnings", []))
    if process.returncode not in {0, 1}:
        warnings.append(f"Playwright exited with code {process.returncode}.")
    if warnings:
        payload["warnings"] = warnings
    emit(payload, exit_code=0)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit(
            {
                "status": "error",
                "message": f"Project root does not exist or is not a directory: {project_root.as_posix()}",
            },
            exit_code=1,
        )

    if args.mode == "check":
        mode_check(project_root, args)
    if args.mode == "generate":
        mode_generate(project_root, args)
    if args.mode == "run":
        mode_run(project_root, args)


if __name__ == "__main__":
    main()
