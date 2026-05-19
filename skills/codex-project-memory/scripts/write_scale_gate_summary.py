#!/usr/bin/env python3
"""Append memory scale-gate metrics to GITHUB_STEP_SUMMARY."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write scale gate report lines to GitHub step summary.")
    parser.add_argument("--report-path", required=True, help="Path to scale-gate JSON report")
    parser.add_argument(
        "--summary-path",
        default="",
        help="GitHub step summary file (default: GITHUB_STEP_SUMMARY env)",
    )
    parser.add_argument("--title", default="Memory scale gate", help="Markdown section title")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_path = Path(args.report_path)
    if not report_path.is_file():
        return 0

    summary_path = Path(args.summary_path or os.environ.get("GITHUB_STEP_SUMMARY", ""))
    if not summary_path:
        return 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    lines = [
        f"## {args.title}",
        f"- status: {report.get('status')}",
        f"- duration_seconds: {report.get('duration_seconds')}",
        f"- within_budget: {report.get('within_budget')}",
        f"- incremental_reused: {report.get('incremental_reused')}",
        f"- files_indexed: {report.get('files_indexed')}",
        "",
    ]
    existing = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
    summary_path.write_text(existing + "\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
