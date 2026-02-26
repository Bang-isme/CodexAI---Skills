#!/usr/bin/env python3
"""
Record and report code quality trends over time.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from _js_parser import count_js_functions


SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".next",
    ".venv",
    "venv",
    ".codex",
    ".idea",
    ".vscode",
    ".yarn",
}
CODE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".py"}
TODO_PATTERN = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Record/report quality trend snapshots.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python quality_trend.py --project-root <path> --report\n"

            "  python quality_trend.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--record", action="store_true", help="Record current quality snapshot")
    parser.add_argument("--report", action="store_true", help="Build quality trend report")
    parser.add_argument("--days", type=int, default=30, help="Days window for report")
    parser.add_argument("--output-dir", default="", help="Output directory (default: <project-root>/.codex/quality)")
    parser.add_argument("--human", action="store_true", help="Print human-readable summary to stderr")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def rel_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def is_test_file(rel_file: str) -> bool:
    file_path = Path(rel_file)
    name = file_path.name.lower()
    text = rel_file.lower()
    return (
        ".test." in name
        or ".spec." in name
        or "/tests/" in text
        or "/__tests__/" in text
        or name.startswith("test_")
    )


def collect_code_files(project_root: Path) -> List[Path]:
    files: List[Path] = []
    for current_root, dirs, names in os.walk(project_root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        root_path = Path(current_root)
        for name in names:
            path = root_path / name
            if path.suffix.lower() in CODE_EXTENSIONS:
                files.append(path)
    return sorted(files)


def count_python_functions(text: str, rel_file: str, warnings: List[str]) -> Tuple[int, int]:
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        warnings.append(f"Python AST parse failed for {rel_file}: {exc.msg}")
        return 0, 0
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"Python AST parse failed for {rel_file}: {exc}")
        return 0, 0

    total = 0
    long_count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total += 1
            start = int(getattr(node, "lineno", 0) or 0)
            end = int(getattr(node, "end_lineno", start) or start)
            if (end - start + 1) > 50:
                long_count += 1
    return total, long_count


def scan_metrics(project_root: Path) -> Tuple[Dict[str, object], List[str]]:
    warnings: List[str] = []
    files = collect_code_files(project_root)
    total_lines = 0
    total_functions = 0
    long_functions = 0
    long_files = 0
    todo_count = 0
    test_files = 0
    source_files = 0

    for file_path in files:
        rel = rel_path(file_path, project_root)
        text = read_text(file_path)
        lines = text.splitlines()
        line_count = len(lines)
        total_lines += line_count
        if line_count > 500:
            long_files += 1
        todo_count += len(TODO_PATTERN.findall(text))

        if is_test_file(rel):
            test_files += 1
        else:
            source_files += 1

        ext = file_path.suffix.lower()
        if ext == ".py":
            fn_total, fn_long = count_python_functions(text, rel, warnings)
        else:
            fn_total, fn_long = count_js_functions(lines, rel, warnings)
        total_functions += fn_total
        long_functions += fn_long

    total_code_files = len(files)
    avg_file_lines = round(total_lines / total_code_files, 2) if total_code_files else 0.0
    avg_functions = round(total_functions / total_code_files, 2) if total_code_files else 0.0
    ratio = round(test_files / source_files, 2) if source_files > 0 else 0.0

    metrics: Dict[str, object] = {
        "total_code_files": total_code_files,
        "total_lines": total_lines,
        "avg_file_lines": avg_file_lines,
        "avg_functions_per_file": avg_functions,
        "todo_count": todo_count,
        "long_functions": long_functions,
        "long_files": long_files,
        "test_files": test_files,
        "test_to_source_ratio": ratio,
    }
    return metrics, warnings


def snapshot_path_for_day(output_dir: Path) -> Path:
    day = date.today().isoformat()
    return output_dir / "snapshots" / f"{day}.json"


def save_snapshot(project_root: Path, output_dir: Path) -> Dict[str, object]:
    metrics, warnings = scan_metrics(project_root)
    payload = {"date": date.today().isoformat(), "metrics": metrics}

    snapshots_dir = output_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    target = snapshot_path_for_day(output_dir)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    result: Dict[str, object] = {
        "status": "recorded",
        "path": target.as_posix(),
        "snapshot": payload,
    }
    if warnings:
        result["warnings"] = sorted(dict.fromkeys(warnings))
    return result


def parse_snapshot_date(snapshot: Dict[str, object], fallback_name: str) -> Optional[date]:
    raw = str(snapshot.get("date", fallback_name)).strip()
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def load_snapshots(output_dir: Path, days: int) -> List[Dict[str, object]]:
    snapshots_dir = output_dir / "snapshots"
    if not snapshots_dir.exists() or not snapshots_dir.is_dir():
        return []

    cutoff = date.today() - timedelta(days=max(1, days) - 1)
    loaded: List[Dict[str, object]] = []
    for path in sorted(snapshots_dir.glob("*.json")):
        try:
            snapshot = json.loads(read_text(path))
        except json.JSONDecodeError:
            continue
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("metrics"), dict):
            continue
        snap_date = parse_snapshot_date(snapshot, path.stem)
        if not snap_date:
            continue
        if snap_date < cutoff:
            continue
        snapshot["date"] = snap_date.isoformat()
        loaded.append(snapshot)

    loaded.sort(key=lambda item: str(item.get("date", "")))
    return loaded


def change_percent(first: float, latest: float) -> float:
    if first == 0:
        if latest == 0:
            return 0.0
        return 100.0
    return ((latest - first) / first) * 100.0


def format_change(metric: str, first: float, latest: float) -> str:
    if metric in {"total_code_files", "test_files"}:
        return f"{int(latest - first):+d}"
    if metric in {"avg_file_lines", "avg_functions_per_file", "test_to_source_ratio"}:
        return f"{change_percent(first, latest):+.0f}%"
    return f"{change_percent(first, latest):+.0f}%"


def trend_label(metric: str, first: float, latest: float) -> str:
    if latest == first:
        return "stable"
    lower_is_better = {"todo_count", "long_functions", "long_files"}
    higher_is_better = {"test_to_source_ratio"}

    if metric in lower_is_better:
        return "improving" if latest < first else "declining"
    if metric in higher_is_better:
        return "improving" if latest > first else "declining"
    return "growing" if latest > first else "shrinking"


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def compute_health_score(first: Dict[str, float], latest: Dict[str, float]) -> int:
    score = 100
    todo_count = int(latest.get("todo_count", 0))
    long_functions = int(latest.get("long_functions", 0))
    long_files = int(latest.get("long_files", 0))
    ratio = float(latest.get("test_to_source_ratio", 0.0))

    score -= min(10, todo_count)
    score -= min(20, long_functions // 8)
    score -= min(15, long_files)
    if ratio < 0.1:
        score -= 25
    elif ratio < 0.3:
        score -= 15

    first_todo = int(first.get("todo_count", 0))
    first_long_functions = int(first.get("long_functions", 0))
    first_long_files = int(first.get("long_files", 0))
    first_ratio = float(first.get("test_to_source_ratio", 0.0))

    if first_todo > 0 and todo_count < first_todo:
        score += min(5, round(((first_todo - todo_count) / first_todo) * 5))
    if first_long_functions > 0 and long_functions < first_long_functions:
        score += min(10, round(((first_long_functions - long_functions) / first_long_functions) * 10))
    if first_long_files > 0 and long_files < first_long_files:
        score += min(10, round(((first_long_files - long_files) / first_long_files) * 10))
    if ratio > first_ratio:
        baseline = first_ratio if first_ratio > 0 else 0.01
        score += min(10, round(((ratio - first_ratio) / baseline) * 3))

    return clamp(int(score), 0, 100)


def grade_for_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B+"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def build_summary(
    snapshots_count: int,
    first: Dict[str, float],
    latest: Dict[str, float],
    trend_map: Dict[str, Dict[str, object]],
) -> Tuple[str, List[str]]:
    recommendations: List[str] = []
    if snapshots_count <= 1:
        summary = "Trend report is limited because only one snapshot is available."
        recommendations.append("Record snapshots periodically to unlock directional trend analysis.")
        return summary, recommendations

    improving = 0
    declining = 0
    for key in ("todo_count", "long_functions", "long_files", "test_to_source_ratio"):
        trend = str(trend_map.get(key, {}).get("trend", "stable"))
        if trend == "improving":
            improving += 1
        elif trend == "declining":
            declining += 1

    if improving > declining:
        quality_line = "Code quality is slightly improving."
    elif declining > improving:
        quality_line = "Code quality is trending downward."
    else:
        quality_line = "Code quality is relatively stable."

    todo_first = int(first.get("todo_count", 0))
    todo_latest = int(latest.get("todo_count", 0))
    if todo_first > 0:
        todo_change = round(((todo_latest - todo_first) / todo_first) * 100)
        todo_line = f"TODO count changed {todo_change:+d}%."
    else:
        todo_line = "TODO trend baseline is zero."

    ratio_latest = float(latest.get("test_to_source_ratio", 0.0))
    ratio_trend = str(trend_map.get("test_to_source_ratio", {}).get("trend", "stable"))
    ratio_line = f"Test ratio is {ratio_trend} (latest {ratio_latest:.2f})."

    long_files_trend = str(trend_map.get("long_files", {}).get("trend", "stable"))
    watch_line = ""
    if long_files_trend == "declining":
        watch_line = "Watch: long files are increasing."
    elif long_files_trend == "improving":
        watch_line = "Long file count is improving."

    if long_files_trend == "declining":
        recommendations.append("Long files increased. Split the largest files by responsibility.")
    if ratio_latest < 0.3:
        recommendations.append("Test-to-source ratio is below 0.3 target; add targeted tests.")
    if str(trend_map.get("todo_count", {}).get("trend", "stable")) == "declining":
        recommendations.append("TODO/FIXME count increased; schedule debt cleanup.")
    if str(trend_map.get("long_functions", {}).get("trend", "stable")) == "declining":
        recommendations.append("Long function count increased; extract helper functions in hotspot files.")
    if not recommendations:
        recommendations.append("Maintain current quality trajectory and continue periodic snapshots.")

    summary = " ".join(part for part in [quality_line, todo_line, ratio_line, watch_line] if part)
    return summary, recommendations[:4]


def build_report(output_dir: Path, days: int) -> Dict[str, object]:
    snapshots = load_snapshots(output_dir, days)
    if not snapshots:
        return {
            "status": "report_ready",
            "period": {"from": "", "to": ""},
            "snapshots_count": 0,
            "trends": {},
            "health_score": 0,
            "health_grade": "D",
            "summary": "No snapshots found in selected period. Run --record first.",
            "recommendations": ["Run quality_trend.py --record to create baseline snapshots."],
        }

    first_snapshot = snapshots[0]
    latest_snapshot = snapshots[-1]
    first_metrics = {key: float(value) for key, value in dict(first_snapshot.get("metrics", {})).items()}
    latest_metrics = {key: float(value) for key, value in dict(latest_snapshot.get("metrics", {})).items()}

    trend_keys = [
        "total_code_files",
        "total_lines",
        "avg_file_lines",
        "avg_functions_per_file",
        "todo_count",
        "long_functions",
        "long_files",
        "test_files",
        "test_to_source_ratio",
    ]
    trends: Dict[str, Dict[str, object]] = {}
    for key in trend_keys:
        first_value = first_metrics.get(key, 0.0)
        latest_value = latest_metrics.get(key, 0.0)
        trends[key] = {
            "first": int(first_value) if key not in {"avg_file_lines", "avg_functions_per_file", "test_to_source_ratio"} else round(first_value, 2),
            "latest": int(latest_value) if key not in {"avg_file_lines", "avg_functions_per_file", "test_to_source_ratio"} else round(latest_value, 2),
            "change": format_change(key, first_value, latest_value),
            "trend": trend_label(key, first_value, latest_value),
        }

    health_score = compute_health_score(first_metrics, latest_metrics)
    health_grade = grade_for_score(health_score)
    summary, recommendations = build_summary(len(snapshots), first_metrics, latest_metrics, trends)

    return {
        "status": "report_ready",
        "period": {"from": str(first_snapshot.get("date", "")), "to": str(latest_snapshot.get("date", ""))},
        "snapshots_count": len(snapshots),
        "trends": trends,
        "health_score": health_score,
        "health_grade": health_grade,
        "summary": summary,
        "recommendations": recommendations,
    }


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


def infer_overall_trend(trend_map: Dict[str, object]) -> str:
    improving = 0
    declining = 0
    for key in ("todo_count", "long_functions", "long_files", "test_to_source_ratio"):
        value = trend_map.get(key, {})
        if not isinstance(value, dict):
            continue
        trend = str(value.get("trend", "stable"))
        if trend == "improving":
            improving += 1
        elif trend == "declining":
            declining += 1
    if improving > declining:
        return "improving"
    if declining > improving:
        return "declining"
    return "stable"


def extract_report_payload(payload: Dict[str, object]) -> Dict[str, object]:
    status = str(payload.get("status", ""))
    if status == "report_ready":
        return payload
    if status == "ok":
        report = payload.get("report", {})
        if isinstance(report, dict):
            return report
    return {}


def print_human_summary(payload: Dict[str, object]) -> None:
    report_payload = extract_report_payload(payload)
    snapshots = int(report_payload.get("snapshots_count", 0) or 0) if report_payload else 0
    trend = infer_overall_trend(report_payload.get("trends", {})) if report_payload else "stable"
    rows: List[str] = [
        f"Snapshots: {snapshots}",
        f"Trend:     {trend}",
    ]
    if str(payload.get("status", "")) == "error":
        rows.append(f"Error: {payload.get('message', '')}")

    print(render_human_box("QUALITY TREND RESULTS", rows), file=sys.stderr)


def emit_with_human(payload: Dict[str, object], human: bool) -> None:
    emit(payload)
    if human:
        print_human_summary(payload)


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else (project_root / ".codex" / "quality")

    if not project_root.exists() or not project_root.is_dir():
        emit_with_human(
            {"status": "error", "path": "", "message": f"Project root does not exist or is not a directory: {project_root}"},
            args.human,
        )
        return 1

    if not args.record and not args.report:
        emit_with_human({"status": "error", "message": "Provide at least one mode: --record and/or --report."}, args.human)
        return 1

    payload: Dict[str, object] = {}
    try:
        if args.record:
            payload["record"] = save_snapshot(project_root, output_dir)
        if args.report:
            payload["report"] = build_report(output_dir, max(1, int(args.days)))
    except PermissionError as exc:
        emit_with_human({"status": "error", "path": "", "message": f"Permission denied: {exc}"}, args.human)
        return 1
    except OSError as exc:
        emit_with_human({"status": "error", "path": "", "message": f"I/O failure: {exc}"}, args.human)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        emit_with_human({"status": "error", "path": "", "message": f"Unexpected error: {exc}"}, args.human)
        return 1

    if args.record and args.report:
        final_payload: Dict[str, object] = {"status": "ok", **payload}
    elif args.record:
        final_payload = payload["record"] if isinstance(payload["record"], dict) else {"status": "error", "message": "Invalid record payload"}
    else:
        final_payload = payload["report"] if isinstance(payload["report"], dict) else {"status": "error", "message": "Invalid report payload"}

    emit_with_human(final_payload, args.human)
    return 0


if __name__ == "__main__":
    sys.exit(main())
