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
    parser.add_argument(
        "--verify-tree",
        action="store_true",
        help="Re-list project files and compare the tree fingerprint recorded in index.json (slower; detects uncommitted changes)",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def _ensure_script_dir_on_path() -> None:
    script_dir = str(Path(__file__).resolve().parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)


def load_traversal():
    _ensure_script_dir_on_path()
    try:
        import project_traversal  # noqa: WPS433 - sibling module, imported lazily
    except ImportError:
        return None
    return project_traversal


def load_graph_builder():
    """Load build_knowledge_graph for LANGUAGE_REGISTRY / is_test_file (same predicate as graph coherence)."""
    _ensure_script_dir_on_path()
    try:
        import build_knowledge_graph  # noqa: WPS433 - sibling module, imported lazily
    except ImportError:
        return None
    return build_knowledge_graph


FALLBACK_GRAPH_EXTENSIONS = frozenset(
    {
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".mjs",
        ".cjs",
        ".py",
        ".go",
        ".rs",
        ".java",
        ".cs",
        ".php",
        ".rb",
        ".kt",
        ".kts",
        ".swift",
        ".vue",
        ".svelte",
        ".html",
        ".css",
        ".scss",
        ".sql",
        ".tf",
        ".yaml",
        ".yml",
        ".json",
    }
)


def graph_language_extensions() -> frozenset[str]:
    builder = load_graph_builder()
    if builder is None:
        return FALLBACK_GRAPH_EXTENSIONS
    return frozenset(builder.LANGUAGE_REGISTRY)


def is_test_file(rel: str) -> bool:
    builder = load_graph_builder()
    if builder is not None:
        return bool(builder.is_test_file(rel))
    lower = rel.replace("\\", "/").lower()
    name = Path(rel).name.lower()
    return (
        ".test." in name
        or ".spec." in name
        or "/tests/" in lower
        or "/__tests__/" in lower
        or name.startswith("test_")
    )


def source_staleness(project_root: Path, index: dict[str, Any], current_head: str, verify_tree: bool) -> dict[str, Any]:
    """Compare index.json `source` provenance against the live repo. Missing `source` is tolerated (older index)."""
    source = index.get("source") if isinstance(index.get("source"), dict) else {}
    warnings: list[str] = []
    recorded_head = str(source.get("git_head") or "")
    recorded_fp = str(source.get("tree_fingerprint") or "")
    head_state = "unknown"
    if recorded_head and current_head:
        head_state = "match" if recorded_head == current_head else "drift"
        if head_state == "drift":
            warnings.append(f"index built at git {recorded_head[:12]} but HEAD is {current_head[:12]}; rebuild the knowledge index")
    elif not source:
        head_state = "not_recorded"
    tree_state = "skipped"
    current_fp = ""
    if verify_tree and recorded_fp:
        traversal = load_traversal()
        if traversal is None:
            tree_state = "unavailable"
        else:
            listing = traversal.list_project_files(project_root, traversal.TraversalConfig())
            current_fp = traversal.tree_fingerprint(listing.files)
            tree_state = "match" if current_fp == recorded_fp else "drift"
            if tree_state == "drift":
                warnings.append("project file tree changed since the index was built (tree_fingerprint drift); rebuild the knowledge index")
    elif verify_tree:
        tree_state = "not_recorded"
    return {
        "status": "warn" if warnings else "pass",
        "recorded_git_head": recorded_head,
        "current_git_head": current_head,
        "git_head": head_state,
        "tree_fingerprint": tree_state,
        "recorded_tree_fingerprint": recorded_fp,
        "current_tree_fingerprint": current_fp,
        "warnings": warnings,
    }


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
    graph_files = {str(path) for path in code_index}
    include_tests = any(is_test_file(path) for path in graph_files)
    extensions = graph_language_extensions()
    comparable: set[str] = set()
    expected_extras: list[str] = []
    for raw_path in codebase_files:
        path = str(raw_path)
        suffix = Path(path).suffix.lower()
        if suffix in extensions and (include_tests or not is_test_file(path)):
            comparable.add(path)
        else:
            expected_extras.append(path)
    expected_extras.sort()
    graph_only = sorted(graph_files - comparable)
    codebase_only = sorted(comparable - graph_files)
    if codebase_files and (graph_only or codebase_only):
        warnings.append(
            "code_index and comparable codebase_index file sets differ "
            f"(graph_only={len(graph_only)}, codebase_only={len(codebase_only)})"
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
        "comparable_index_files": len(comparable),
        "graph_only": graph_only[:25],
        "codebase_only": codebase_only[:25],
        "expected_extras": expected_extras[:25],
        "expected_extras_count": len(expected_extras),
        "include_tests": include_tests,
        "truncated": len(graph_only) > 25 or len(codebase_only) > 25 or len(expected_extras) > 25,
    }


def build_status(
    project_root: Path,
    knowledge_dir: Path,
    max_age_hours: int,
    require_standalone_graph: bool = False,
    strict_warnings: bool = False,
    verify_tree: bool = False,
) -> dict[str, Any]:
    index_path = knowledge_dir / "index.json"
    graph_path = knowledge_dir / "knowledge-graph.json"
    codebase_path = knowledge_dir / "codebase-index.json"
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
    current_head = git_head(project_root)
    source = source_staleness(project_root, index, current_head, verify_tree) if index else {
        "status": "skipped",
        "git_head": "unknown",
        "tree_fingerprint": "skipped",
        "warnings": [],
    }
    failures.extend(item for artifact in artifacts for item in artifact.get("failures", []))
    warnings.extend(item for artifact in artifacts for item in artifact.get("warnings", []))
    failures.extend(coherence.get("failures", []))
    warnings.extend(coherence.get("warnings", []))
    warnings.extend(source.get("warnings", []))
    status = "fail" if failures else "warn" if warnings else "pass"
    return {
        "status": status,
        "project_root": project_root.as_posix(),
        "git_head": current_head,
        "knowledge_dir": knowledge_dir.as_posix(),
        "policy": {
            "standalone_graph": "required" if require_standalone_graph else "optional",
            "strict_warnings_exit_nonzero": strict_warnings,
            "max_age_hours": max_age_hours,
            "verify_tree": verify_tree,
        },
        "artifacts": artifacts,
        "coherence": coherence,
        "source": source,
        "warnings": warnings,
        "failures": failures,
    }


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"status={payload.get('status')}",
        f"project_root={payload.get('project_root')}",
        f"knowledge_dir={payload.get('knowledge_dir')}",
        f"warnings={len(payload.get('warnings') or [])}",
        f"failures={len(payload.get('failures') or [])}",
    ]
    for warning in payload.get("warnings") or []:
        lines.append(f"warning: {warning}")
    for failure in payload.get("failures") or []:
        lines.append(f"failure: {failure}")
    return "\n".join(lines)


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
        verify_tree=args.verify_tree,
    )
    if args.format == "text":
        print(render_text(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.strict and payload["status"] == "warn":
        return 1
    return 0 if payload["status"] in {"pass", "warn"} else 1


if __name__ == "__main__":
    sys.exit(main())
