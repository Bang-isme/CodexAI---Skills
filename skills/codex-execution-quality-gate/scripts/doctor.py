#!/usr/bin/env python3
"""
Environment doctor: pre-flight tool dependency checks.
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
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class ToolSpec:
    name: str
    commands: List[List[str]]
    required_by: List[str]
    install_hint: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check external tool dependencies used by Codex skills.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python doctor.py\n"
            "  python doctor.py --skills-root <path> --format table\n\n"
            "Output:\n"
            "  JSON (default): {\"status\":\"checked\",\"total\":N,\"ok\":N,\"missing\":N,\"tools\":[...]}\n"
            "  Table: ASCII summary for human reading"
        ),
    )
    parser.add_argument("--skills-root", default="", help="Optional skills root path (for display/future use)")
    parser.add_argument("--format", choices=["json", "table"], default="json", help="Output format")
    return parser.parse_args()


def is_windows() -> bool:
    return os.name == "nt"


def tool_specs() -> List[ToolSpec]:
    return [
        ToolSpec(
            name="git",
            commands=[["git", "--version"]],
            required_by=["session_summary", "changelog", "smart_test_selector"],
            install_hint="choco install git (Windows) / brew install git (macOS) / apt-get install git (Linux)",
        ),
        ToolSpec(
            name="node",
            commands=[["node", "--version"]],
            required_by=["run_gate", "pre_commit_check"],
            install_hint="Install Node.js LTS: choco install nodejs-lts / brew install node / apt-get install nodejs",
        ),
        ToolSpec(
            name="npm/npx",
            commands=[["npm", "--version"], ["npx", "--version"]],
            required_by=["playwright_runner", "smart_test_selector"],
            install_hint="Install npm/npx with Node.js LTS (same package as node)",
        ),
        ToolSpec(
            name="python",
            commands=[["python", "--version"]],
            required_by=["all scripts"],
            install_hint="Install Python 3 and ensure `python` is available in PATH",
        ),
        ToolSpec(
            name="eslint",
            commands=[["npx", "eslint", "--version"]],
            required_by=["run_gate"],
            install_hint="npm install -D eslint (project) or npm install -g eslint (global)",
        ),
        ToolSpec(
            name="lighthouse",
            commands=[["npx", "lighthouse", "--version"]],
            required_by=["lighthouse_audit"],
            install_hint="npm install -D lighthouse (project) or npm install -g lighthouse (global)",
        ),
        ToolSpec(
            name="playwright",
            commands=[["npx", "playwright", "--version"]],
            required_by=["playwright_runner"],
            install_hint="npm install -D @playwright/test && npx playwright install",
        ),
        ToolSpec(
            name="poppler",
            commands=[["pdftoppm", "-v"]],
            required_by=["render_docx"],
            install_hint="choco install poppler (Windows) / brew install poppler (macOS) / apt-get install poppler-utils (Linux)",
        ),
        ToolSpec(
            name="libreoffice",
            commands=[["soffice", "--version"]],
            required_by=["render_docx"],
            install_hint="choco install libreoffice-fresh (Windows) / brew install --cask libreoffice (macOS) / apt-get install libreoffice (Linux)",
        ),
    ]


def run_command(command: Sequence[str]) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
    except FileNotFoundError:
        return False, "command not found"
    except OSError as exc:
        return False, str(exc)
    except subprocess.TimeoutExpired:
        return False, "timeout"

    output = "\n".join([result.stdout or "", result.stderr or ""]).strip()
    if result.returncode != 0:
        error_line = output.splitlines()[0].strip() if output else f"exit code {result.returncode}"
        return False, error_line
    if not output:
        return True, "available"
    first_line = output.splitlines()[0].strip()
    return True, first_line


def normalize_version(raw: str) -> str:
    text = raw.strip()
    if not text:
        return "available"
    # Prefer a semver-like token when present, otherwise keep first line as-is.
    semver = re.search(r"v?\d+\.\d+(?:\.\d+)?(?:[-+.\w]*)?", text)
    if semver:
        return semver.group(0)
    return text


def check_tool(spec: ToolSpec) -> Dict[str, object]:
    checked_commands = [" ".join(parts) for parts in spec.commands]
    errors: List[str] = []
    version_tokens: List[str] = []

    for command in spec.commands:
        ok, output = run_command(command)
        if not ok:
            errors.append(f"{' '.join(command)} -> {output}")
            continue
        version_tokens.append(normalize_version(output))

    if errors:
        return {
            "name": spec.name,
            "status": "missing",
            "check_command": " && ".join(checked_commands),
            "required_by": spec.required_by,
            "install_hint": spec.install_hint,
            "details": errors,
        }

    version = ", ".join(token for token in version_tokens if token) or "available"
    return {
        "name": spec.name,
        "status": "ok",
        "check_command": " && ".join(checked_commands),
        "required_by": spec.required_by,
        "version": version,
    }


def truncate(value: str, width: int) -> str:
    text = value.strip()
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."


def render_table(rows: List[Dict[str, object]], total: int, ok_count: int, missing_count: int) -> str:
    headers = ["Tool", "Status", "Version/Hint", "Required By"]
    table_rows: List[List[str]] = []
    for row in rows:
        status = str(row.get("status", "missing"))
        version_or_hint = str(row.get("version", "")) if status == "ok" else str(row.get("install_hint", ""))
        required_by = ", ".join(str(item) for item in row.get("required_by", []))
        table_rows.append(
            [
                str(row.get("name", "")),
                status,
                version_or_hint,
                required_by,
            ]
        )

    max_col = [len(header) for header in headers]
    for row in table_rows:
        max_col[0] = max(max_col[0], len(row[0]))
        max_col[1] = max(max_col[1], len(row[1]))
        max_col[2] = max(max_col[2], min(72, len(row[2])))
        max_col[3] = max(max_col[3], min(48, len(row[3])))

    max_col[2] = min(max_col[2], 72)
    max_col[3] = min(max_col[3], 48)

    def border() -> str:
        return "+" + "+".join("-" * (width + 2) for width in max_col) + "+"

    def render_row(values: List[str]) -> str:
        clipped = [
            truncate(values[0], max_col[0]),
            truncate(values[1], max_col[1]),
            truncate(values[2], max_col[2]),
            truncate(values[3], max_col[3]),
        ]
        return "| " + " | ".join(clipped[idx].ljust(max_col[idx]) for idx in range(4)) + " |"

    lines = [
        "Environment Doctor",
        f"Total: {total}  OK: {ok_count}  Missing: {missing_count}",
        border(),
        render_row(headers),
        border(),
    ]
    for row in table_rows:
        lines.append(render_row(row))
    lines.append(border())
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    _skills_root = Path(args.skills_root).expanduser().resolve() if args.skills_root else None

    rows = [check_tool(spec) for spec in tool_specs()]
    total = len(rows)
    ok_count = sum(1 for row in rows if row.get("status") == "ok")
    missing_count = total - ok_count

    payload = {
        "status": "checked",
        "total": total,
        "ok": ok_count,
        "missing": missing_count,
        "tools": rows,
    }

    if args.format == "table":
        print(render_table(rows, total, ok_count, missing_count))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
