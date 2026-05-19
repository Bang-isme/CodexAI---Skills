#!/usr/bin/env python3
"""Run project-memory scale gate with synthetic fixture and JSON report."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
TIER_DEFAULTS = {
    "medium": {"file_count": 2500, "max_files": 5000, "budget_seconds": 420, "require_graph": False},
    "large": {"file_count": 8000, "max_files": 10000, "budget_seconds": 900, "require_graph": True},
}


def run_script(script: str, args: list[str], timeout: int = 600) -> tuple[int, dict[str, Any], str]:
    cmd = [sys.executable, str(SCRIPT_DIR / script), *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    stderr = result.stderr.strip()
    try:
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {"status": "error", "message": "invalid JSON stdout", "stdout": result.stdout[-2000:]}
    if not isinstance(payload, dict):
        payload = {"status": "error", "message": "stdout root must be object"}
    if result.returncode != 0 and payload.get("status") not in {"built", "generated", "pass", "warn"}:
        payload.setdefault("status", "error")
        if stderr:
            payload.setdefault("stderr", stderr[-2000:])
    return result.returncode, payload, stderr


def read_codebase_index_summary(project_root: Path) -> dict[str, Any]:
    path = project_root / ".codex" / "knowledge" / "codebase-index.json"
    if not path.exists():
        return {"parsers": {}, "languages": {}, "files_indexed": 0}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"parsers": {}, "languages": {}, "files_indexed": 0}
    files = payload.get("files", {}) if isinstance(payload, dict) else {}
    if not isinstance(files, dict):
        return {"parsers": {}, "languages": {}, "files_indexed": 0}
    parsers: dict[str, int] = {}
    languages: dict[str, int] = {}
    for meta in files.values():
        if not isinstance(meta, dict):
            continue
        parser = str(meta.get("parser", "unknown"))
        language = str(meta.get("language", "unknown"))
        parsers[parser] = parsers.get(parser, 0) + 1
        languages[language] = languages.get(language, 0) + 1
    return {
        "parsers": parsers,
        "languages": languages,
        "files_indexed": len(files),
    }


def read_codebase_incremental(project_root: Path) -> int:
    path = project_root / ".codex" / "knowledge" / "codebase-index.json"
    if not path.exists():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    incremental = payload.get("incremental", {})
    if isinstance(incremental, dict):
        return int(incremental.get("reused_files", 0) or 0)
    return 0


def run_gate(
    *,
    project_root: Path,
    file_count: int,
    max_files: int,
    budget_seconds: int,
    tier: str,
    seed: int,
    require_graph: bool,
    keep_fixture: bool,
) -> dict[str, Any]:
    failures: list[str] = []
    started = time.monotonic()
    project_root = project_root.expanduser().resolve()
    if project_root.exists() and not keep_fixture:
        import shutil

        shutil.rmtree(project_root, ignore_errors=True)
    project_root.mkdir(parents=True, exist_ok=True)

    gen_code, gen_payload, _ = run_script(
        "generate_scale_fixture.py",
        [
            "--output-dir",
            str(project_root),
            "--file-count",
            str(file_count),
            "--seed",
            str(seed),
            "--include-package-json",
        ],
    )
    if gen_code != 0 or gen_payload.get("status") != "generated":
        failures.append(f"fixture generation failed: {gen_payload}")
    extension_counts = gen_payload.get("extension_counts", {}) if isinstance(gen_payload, dict) else {}

    index_code, index_payload, _ = run_script(
        "build_knowledge_index.py",
        [
            "--project-root",
            str(project_root),
            "--incremental",
            "--max-files",
            str(max_files),
            "--format",
            "json",
        ],
        timeout=max(budget_seconds, 120),
    )
    index_status = index_payload.get("status", "error")
    if index_code != 0 or index_status != "built":
        failures.append(f"initial build_knowledge_index failed: status={index_status} code={index_code}")

    index_summary = read_codebase_index_summary(project_root)
    parsers = index_summary.get("parsers", {})
    if isinstance(parsers, dict) and file_count >= 10:
        if len(parsers) < 2:
            failures.append(f"polyglot index expected >=2 parser kinds, got {parsers}")
        if "regex-python-symbols" not in parsers or "regex-js-ts-symbols" not in parsers:
            failures.append(f"polyglot index missing python or js/ts parsers: {parsers}")

    graph_status = "skipped"
    if require_graph:
        graph_code, graph_payload, _ = run_script(
            "build_knowledge_graph.py",
            ["--project-root", str(project_root), "--format", "json"],
            timeout=max(budget_seconds // 2, 120),
        )
        graph_status = str(graph_payload.get("status", "error"))
        if graph_code != 0 or graph_status != "generated":
            failures.append(f"build_knowledge_graph failed: status={graph_status} code={graph_code}")

    status_code, status_payload, _ = run_script(
        "memory_status.py",
        ["--project-root", str(project_root), "--format", "json"],
    )
    memory_status = str(status_payload.get("status", "error"))
    if status_code != 0 or memory_status == "fail":
        failures.append(f"memory_status failed: status={memory_status} code={status_code}")
    elif memory_status not in {"pass", "warn"}:
        failures.append(f"unexpected memory_status: {memory_status}")

    touch_target: Path | None = None
    for candidate in sorted(project_root.rglob("*")):
        if candidate.is_file() and candidate.suffix.lower() in {".py", ".js", ".ts", ".tsx", ".go", ".java", ".rs"}:
            touch_target = candidate
            break
    if touch_target and touch_target.exists():
        touch_target.write_text(touch_target.read_text(encoding="utf-8") + "\n# scale-gate touch\n", encoding="utf-8")
    else:
        failures.append("incremental touch file not found in polyglot fixture")
    inc_code, inc_payload, _ = run_script(
        "build_knowledge_index.py",
        [
            "--project-root",
            str(project_root),
            "--incremental",
            "--max-files",
            str(max_files),
            "--format",
            "json",
        ],
        timeout=max(budget_seconds, 120),
    )
    incremental_reused = read_codebase_incremental(project_root)
    if inc_code != 0 or inc_payload.get("status") != "built":
        failures.append(f"incremental build_knowledge_index failed: {inc_payload.get('status')} code={inc_code}")
    elif incremental_reused <= 0:
        failures.append("incremental reuse expected reused_files > 0")

    duration_seconds = round(time.monotonic() - started, 2)
    within_budget = duration_seconds <= budget_seconds
    if not within_budget:
        failures.append(f"duration {duration_seconds}s exceeds budget {budget_seconds}s")

    report = {
        "status": "pass" if not failures else "fail",
        "tier": tier,
        "file_count": file_count,
        "max_files": max_files,
        "budget_seconds": budget_seconds,
        "duration_seconds": duration_seconds,
        "within_budget": within_budget,
        "project_root": str(project_root),
        "index_status": index_status,
        "graph_status": graph_status,
        "memory_status": memory_status,
        "incremental_reused": incremental_reused,
        "fixture_extension_counts": extension_counts,
        "index_parsers": index_summary.get("parsers", {}),
        "index_languages": index_summary.get("languages", {}),
        "files_indexed": index_summary.get("files_indexed", 0),
        "failures": failures,
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run synthetic memory scale gate and emit JSON report.")
    parser.add_argument("--project-root", default="", help="Fixture project root (default: temp under cwd)")
    parser.add_argument("--tier", choices=tuple(TIER_DEFAULTS), default="medium")
    parser.add_argument("--file-count", type=int, default=0)
    parser.add_argument("--max-files", type=int, default=0)
    parser.add_argument("--budget-seconds", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--keep-fixture", action="store_true", help="Do not delete existing project root before run")
    parser.add_argument("--report-path", default="", help="Optional path to write scale-gate-report.json")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    defaults = TIER_DEFAULTS[args.tier]
    file_count = args.file_count or int(defaults["file_count"])
    max_files = args.max_files or int(defaults["max_files"])
    budget_seconds = args.budget_seconds or int(defaults["budget_seconds"])
    require_graph = bool(defaults["require_graph"])
    if args.project_root:
        project_root = Path(args.project_root)
    else:
        project_root = Path.cwd() / f".scale-gate-{args.tier}"

    report = run_gate(
        project_root=project_root,
        file_count=file_count,
        max_files=max_files,
        budget_seconds=budget_seconds,
        tier=args.tier,
        seed=args.seed,
        require_graph=require_graph,
        keep_fixture=args.keep_fixture,
    )
    if args.report_path:
        report_path = Path(args.report_path).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.format == "text":
        print(f"status={report['status']} duration={report['duration_seconds']}s reused={report['incremental_reused']}")
        for failure in report.get("failures", []):
            print(f"- {failure}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
