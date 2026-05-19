#!/usr/bin/env python3
"""Validate generated project-memory artifacts for operational readiness."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_INDEX_FIELDS = {"schema_version", "artifact_type", "generated_at", "project_root", "stats", "warnings", "redaction"}
REQUIRED_GRAPH_FIELDS = REQUIRED_INDEX_FIELDS | {"code_index", "module_boundaries", "api_routes", "coherence"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate .codex/knowledge artifacts for staleness and coherence.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--knowledge-dir", default=".codex/knowledge", help="Knowledge output directory relative to project root")
    parser.add_argument("--max-age-hours", type=int, default=168, help="Warn when artifacts are older than this many hours")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on 'warn' status (for CI gating)")
    parser.add_argument(
        "--require-standalone-graph",
        action="store_true",
        help="Treat missing or invalid standalone .codex/knowledge-graph.json as failures instead of warnings",
    )
    parser.add_argument("--format", choices=("json",), default="json")
    return parser.parse_args()


def read_json(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, f"invalid_json: {exc}"
    if not isinstance(payload, dict):
        return {}, "invalid_json: top-level value is not an object"
    return payload, ""


def git_head(project_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""
    return result.stdout.strip()


def age_hours(value: Any) -> float | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 3600


def artifact_check(name: str, path: Path, payload: dict[str, Any], required: set[str], max_age_hours: int) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    missing = sorted(required - set(payload))
    if missing:
        failures.append(f"missing required field(s): {', '.join(missing)}")
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str) or "." not in schema_version:
        failures.append("invalid schema_version")
    generated_age = age_hours(payload.get("generated_at"))
    if generated_age is None:
        failures.append("invalid generated_at")
    elif generated_age > max_age_hours:
        warnings.append(f"stale artifact: {generated_age:.1f}h old")
    return {
        "name": name,
        "path": path.as_posix(),
        "exists": path.exists(),
        "status": "fail" if failures else "warn" if warnings else "pass",
        "failures": failures,
        "warnings": warnings,
        "age_hours": generated_age,
    }


def graph_coherence(graph: dict[str, Any], codebase: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    code_index = graph.get("code_index") if isinstance(graph.get("code_index"), dict) else {}
    modules = graph.get("module_boundaries") if isinstance(graph.get("module_boundaries"), dict) else {}
    stats = graph.get("stats") if isinstance(graph.get("stats"), dict) else {}
    if int(stats.get("total_files", len(code_index)) or 0) != len(code_index):
        warnings.append(f"stats.total_files={stats.get('total_files')} but code_index has {len(code_index)} files")
    module_counts: dict[str, int] = {}
    for item in code_index.values():
        if isinstance(item, dict):
            module = str(item.get("module", "root"))
            module_counts[module] = module_counts.get(module, 0) + 1
    empty_modules = sorted(module for module in modules if module_counts.get(module, 0) == 0)
    if empty_modules:
        warnings.append(f"module boundaries without mapped files: {', '.join(empty_modules[:10])}")
    codebase_files = codebase.get("files") if isinstance(codebase.get("files"), dict) else {}
    if codebase_files and set(codebase_files) != set(code_index):
        warnings.append(
            "code_index and codebase_index file sets differ "
            f"(graph={len(code_index)}, codebase={len(codebase_files)})"
        )
    if not code_index:
        failures.append("graph code_index is empty")
    return {
        "status": "fail" if failures else "warn" if warnings else "pass",
        "failures": failures,
        "warnings": warnings,
        "code_index_files": len(code_index),
        "module_file_counts": module_counts,
        "codebase_index_files": len(codebase_files),
    }


def build_status(
    project_root: Path,
    knowledge_dir: Path,
    max_age_hours: int,
    require_standalone_graph: bool = False,
    strict_warnings: bool = False,
) -> dict[str, Any]:
    index_path = knowledge_dir / "index.json"
    graph_path = knowledge_dir / "knowledge-graph.json"
    codebase_path = knowledge_dir / "codebase-index.json"
    html_path = knowledge_dir / "index.html"
    standalone_graph_path = project_root / ".codex" / "knowledge-graph.json"

    index, index_error = read_json(index_path)
    graph, graph_error = read_json(graph_path)
    codebase, codebase_error = read_json(codebase_path)
    failures: list[str] = []
    warnings: list[str] = []
    if index_error:
        failures.append(f"index.json: {index_error}")
    if graph_error:
        failures.append(f"knowledge-graph.json: {graph_error}")
    if codebase_error:
        warnings.append(f"codebase-index.json: {codebase_error}")
    if not html_path.exists():
        warnings.append("index.html missing")

    standalone_graph, standalone_error = read_json(standalone_graph_path)
    if not standalone_graph_path.exists():
        if require_standalone_graph:
            failures.append(f"standalone graph missing at {standalone_graph_path.as_posix()}")
    elif standalone_error:
        if require_standalone_graph:
            failures.append(f"standalone graph unreadable: {standalone_error}")
        else:
            warnings.append(f"standalone graph unreadable: {standalone_error}")

    artifacts = [
        artifact_check("index", index_path, index, REQUIRED_INDEX_FIELDS, max_age_hours) if index else {
            "name": "index",
            "path": index_path.as_posix(),
            "exists": False,
            "status": "fail",
            "failures": [index_error or "missing"],
            "warnings": [],
        },
        artifact_check("knowledge_graph", graph_path, graph, REQUIRED_GRAPH_FIELDS, max_age_hours) if graph else {
            "name": "knowledge_graph",
            "path": graph_path.as_posix(),
            "exists": False,
            "status": "fail",
            "failures": [graph_error or "missing"],
            "warnings": [],
        },
    ]

    if standalone_graph and not standalone_error:
        sc = artifact_check("standalone_graph", standalone_graph_path, standalone_graph, REQUIRED_GRAPH_FIELDS, max_age_hours)
        if sc["failures"] and not require_standalone_graph:
            sc["warnings"].extend(sc["failures"])
            sc["failures"] = []
        sc["status"] = "fail" if sc["failures"] else "warn" if sc["warnings"] else "pass"
        artifacts.append(sc)

    coherence = graph_coherence(graph, codebase) if graph else {"status": "fail", "failures": ["graph missing"], "warnings": []}
    failures.extend(item for artifact in artifacts for item in artifact.get("failures", []))
    warnings.extend(item for artifact in artifacts for item in artifact.get("warnings", []))
    failures.extend(coherence.get("failures", []))
    warnings.extend(coherence.get("warnings", []))
    status = "fail" if failures else "warn" if warnings else "pass"
    return {
        "status": status,
        "project_root": project_root.as_posix(),
        "git_head": git_head(project_root),
        "knowledge_dir": knowledge_dir.as_posix(),
        "policy": {
            "standalone_graph": "required" if require_standalone_graph else "optional",
            "strict_warnings_exit_nonzero": strict_warnings,
            "max_age_hours": max_age_hours,
        },
        "artifacts": artifacts,
        "coherence": coherence,
        "warnings": warnings,
        "failures": failures,
    }


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.is_dir():
        print(json.dumps({"status": "error", "message": f"Not a directory: {project_root}"}, indent=2), file=sys.stdout)
        return 1
    knowledge_dir = Path(args.knowledge_dir)
    if not knowledge_dir.is_absolute():
        knowledge_dir = project_root / knowledge_dir
    payload = build_status(
        project_root,
        knowledge_dir,
        args.max_age_hours,
        require_standalone_graph=args.require_standalone_graph,
        strict_warnings=args.strict,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.strict and payload["status"] == "warn":
        return 1
    return 0 if payload["status"] in {"pass", "warn"} else 1


if __name__ == "__main__":
    sys.exit(main())
