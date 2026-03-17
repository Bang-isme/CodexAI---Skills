#!/usr/bin/env python3
"""Validate the bundled or installed Scrum subagent kit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _scrum_agent_kit import (
    compare_bundle_to_install,
    compare_native_agents_to_install,
    personal_codex_agents_root,
    project_codex_agents_root,
    read_stamp,
    validate_bundle,
)


DEFAULT_BUNDLE_ROOT = SCRIPT_DIR.parent / "assets" / "scrum-agent-kit"


def format_table(report: dict[str, object]) -> str:
    bundle = report.get("bundle", {})
    lines = [
        f"status       : {report.get('status')}",
        f"bundle_root  : {report.get('bundle_root')}",
        f"native_scope : {report.get('native_scope', 'project')}",
        f"agents       : {bundle.get('agent_files', 0)}",
        f"workflows    : {bundle.get('workflow_files', 0)}",
        f"services     : {bundle.get('service_files', 0)}",
        f"native_agents: {bundle.get('native_agent_files', 0)}",
        f"bundle_files : {bundle.get('total_files', 0)}",
    ]
    errors = report.get("errors", [])
    warnings = report.get("warnings", [])
    if isinstance(errors, list):
        lines.append(f"errors       : {len(errors)}")
    if isinstance(warnings, list):
        lines.append(f"warnings     : {len(warnings)}")
    diff = report.get("diff")
    if isinstance(diff, dict):
        lines.append(f"missing      : {len(diff.get('missing', []))}")
        lines.append(f"changed      : {len(diff.get('changed', []))}")
        lines.append(f"same         : {len(diff.get('same', []))}")
        lines.append(f"extra        : {len(diff.get('extra', []))}")
    native_diff = report.get("native_agents_diff")
    if isinstance(native_diff, dict):
        lines.append(f"codex_agents : {report.get('codex_agents_root')}")
        lines.append(f"native_miss  : {len(native_diff.get('missing', []))}")
        lines.append(f"native_chg   : {len(native_diff.get('changed', []))}")
        lines.append(f"native_same  : {len(native_diff.get('same', []))}")
        lines.append(f"native_extra : {len(native_diff.get('extra', []))}")
    personal_native_diff = report.get("personal_native_agents_diff")
    if isinstance(personal_native_diff, dict):
        lines.append(f"personal_codex: {report.get('personal_codex_agents_root')}")
        lines.append(f"p_native_miss: {len(personal_native_diff.get('missing', []))}")
        lines.append(f"p_native_chg : {len(personal_native_diff.get('changed', []))}")
        lines.append(f"p_native_same: {len(personal_native_diff.get('same', []))}")
        lines.append(f"p_native_ext : {len(personal_native_diff.get('extra', []))}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the bundled or installed Scrum subagent kit.",
    )
    parser.add_argument(
        "--bundle-root",
        default=str(DEFAULT_BUNDLE_ROOT),
        help="Path to the Scrum kit bundle root",
    )
    parser.add_argument(
        "--install-root",
        help="Optional installed .agent directory to compare against the bundle",
    )
    parser.add_argument(
        "--target-root",
        help="Optional project root; when provided, validator resolves install/native paths symmetrically",
    )
    parser.add_argument(
        "--install-dir",
        default=".agent",
        help="Relative install dir used when --target-root is provided (default: .agent)",
    )
    parser.add_argument(
        "--codex-agents-root",
        help="Optional installed .codex/agents directory for native custom-agent comparison",
    )
    parser.add_argument(
        "--native-scope",
        choices=("project", "personal", "both"),
        default="project",
        help="Which native Codex agent locations to validate (default: project)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format",
    )
    args = parser.parse_args()

    bundle_root = Path(args.bundle_root).resolve()
    report = validate_bundle(bundle_root)
    report["native_scope"] = args.native_scope

    install_root: Path | None = None
    if args.target_root:
        target_root = Path(args.target_root).resolve()
        install_root = target_root / args.install_dir
    elif args.install_root:
        install_root = Path(args.install_root).resolve()

    if install_root is not None:
        report["install_root"] = str(install_root)
        report["diff"] = compare_bundle_to_install(bundle_root, install_root)
        stamp = read_stamp(install_root)
        target_root_from_stamp = stamp.get("target_root")
        codex_agents_root_from_stamp = stamp.get("codex_agents_root")
        if args.codex_agents_root:
            codex_agents_root = Path(args.codex_agents_root).resolve()
        elif isinstance(codex_agents_root_from_stamp, str) and codex_agents_root_from_stamp:
            codex_agents_root = Path(codex_agents_root_from_stamp).resolve()
        elif args.target_root:
            codex_agents_root = project_codex_agents_root(Path(args.target_root).resolve())
        elif isinstance(target_root_from_stamp, str) and target_root_from_stamp:
            codex_agents_root = project_codex_agents_root(Path(target_root_from_stamp).resolve())
        else:
            codex_agents_root = project_codex_agents_root(install_root.parent)
        if args.native_scope in {"project", "both"}:
            report["codex_agents_root"] = str(codex_agents_root)
            report["native_agents_diff"] = compare_native_agents_to_install(bundle_root, codex_agents_root)
        if args.native_scope in {"personal", "both"}:
            personal_root = personal_codex_agents_root()
            report["personal_codex_agents_root"] = str(personal_root)
            report["personal_native_agents_diff"] = compare_native_agents_to_install(bundle_root, personal_root)
            if "native_agents_diff" not in report:
                report["codex_agents_root"] = str(personal_root)
                report["native_agents_diff"] = report["personal_native_agents_diff"]
        if report["status"] == "ok":
            diff = report["diff"]
            assert isinstance(diff, dict)
            native_diff = report.get("native_agents_diff", {})
            assert isinstance(native_diff, dict)
            personal_native_diff = report.get("personal_native_agents_diff", {})
            assert isinstance(personal_native_diff, dict)
            if (
                diff["changed"]
                or diff["missing"]
                or diff["extra"]
                or native_diff["changed"]
                or native_diff["missing"]
                or native_diff["extra"]
                or personal_native_diff.get("changed")
                or personal_native_diff.get("missing")
                or personal_native_diff.get("extra")
            ):
                report["status"] = "drift"

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_table(report))
        errors = report.get("errors", [])
        if isinstance(errors, list) and errors:
            print("\nErrors:")
            for item in errors:
                print(f"- {item}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
