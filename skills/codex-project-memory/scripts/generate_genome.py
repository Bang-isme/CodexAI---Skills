#!/usr/bin/env python3
"""
Generate Project Genome: multi-view context documentation for AI agents.
Writes a single `.codex/context/genome.md` file and emits a JSON summary.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

from genome_builder import build_genome_report, emit_json, write_genome_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Project Genome: multi-view context documentation for AI agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python generate_genome.py --project-root .\n"
            "  python generate_genome.py --project-root . --sections api,security --format json\n"
            "  python generate_genome.py --project-root . --depth shallow\n"
        ),
    )
    parser.add_argument("--project-root", required=True, help="Project root directory")
    parser.add_argument(
        "--depth",
        choices=["shallow", "full", "auto"],
        default="auto",
        help="Scan depth mode. Kept for backward compatibility.",
    )
    parser.add_argument(
        "--sections",
        default="all",
        help="Comma-separated section list: all, architecture, api, data, security, tests, file_map",
    )
    parser.add_argument(
        "--format",
        choices=["md", "json"],
        default="md",
        help="Output summary format for stdout. genome.md is always written.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Retained for backward compatibility; genome now regenerates on each run.",
    )
    return parser.parse_args()


def build_payload(report: Dict[str, Any], genome_path: Path, output_format: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "status": "ok",
        "project": report["project"],
        "generated_at": report["generated_at"],
        "depth": report["depth"],
        "scan_depth": report["scan_depth"],
        "sections_scanned": report["sections_scanned"],
        "total_files": report["total_files"],
        "total_lines": report["total_lines"],
        "genome_path": genome_path.as_posix(),
        "module_maps_count": report["module_maps_count"],
    }
    if output_format == "json":
        payload["sections"] = report["sections"]
    return payload


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit_json({"status": "error", "message": f"Not a directory: {project_root}"})
        return 1

    try:
        report = build_genome_report(project_root, args.depth, args.sections)
        genome_path = write_genome_file(project_root, report["markdown"])
    except OSError as exc:
        emit_json({"status": "error", "message": f"Failed to write genome.md: {exc}"})
        return 1
    except Exception as exc:  # pragma: no cover
        emit_json({"status": "error", "message": f"Genome generation failed: {exc}"})
        return 1

    payload = build_payload(report, genome_path, args.format)
    emit_json(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
