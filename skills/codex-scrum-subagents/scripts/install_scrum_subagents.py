#!/usr/bin/env python3
"""Install, diff, or update the bundled Scrum subagent kit."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _scrum_agent_kit import (
    BundleStats,
    backup_existing_files,
    collect_bundle_stats,
    compare_bundle_to_install,
    compare_native_agents_to_install,
    copy_native_agents,
    copy_bundle_files,
    copy_entire_bundle,
    default_backup_root,
    detect_conflicts,
    detect_native_agent_conflicts,
    ensure_target_root,
    personal_codex_agents_root,
    project_codex_agents_root,
    validate_bundle,
    write_stamp,
)


BUNDLE_ROOT = SCRIPT_DIR.parent / "assets" / "scrum-agent-kit"


def uses_project_native_agents(native_scope: str) -> bool:
    return native_scope in {"project", "both"}


def uses_personal_native_agents(native_scope: str) -> bool:
    return native_scope in {"personal", "both"}


def build_report(
    target_root: Path,
    install_root: Path,
    stats: BundleStats,
    copied_files: int,
    force: bool,
    dry_run: bool,
    conflicts: Iterable[str],
    native_scope: str,
    project_native_agents_diff: Dict[str, object] | None = None,
    project_codex_agents_root: Path | None = None,
    personal_native_agents_diff: Dict[str, object] | None = None,
    personal_agents_root: Path | None = None,
) -> Dict[str, object]:
    conflict_list = list(conflicts)
    report = {
        "status": "dry_run" if dry_run else "installed",
        "target_root": str(target_root),
        "install_root": str(install_root),
        "native_scope": native_scope,
        "force": force,
        "bundle": asdict(stats),
        "copied_files": copied_files,
        "conflicts": conflict_list,
    }
    if project_codex_agents_root is not None and project_native_agents_diff is not None:
        report["codex_agents_root"] = str(project_codex_agents_root)
        report["native_agents_diff"] = project_native_agents_diff
        report["project_codex_agents_root"] = str(project_codex_agents_root)
        report["project_native_agents_diff"] = project_native_agents_diff
    if personal_agents_root is not None and personal_native_agents_diff is not None:
        report["personal_codex_agents_root"] = str(personal_agents_root)
        report["personal_native_agents_diff"] = personal_native_agents_diff
        if "native_agents_diff" not in report:
            report["codex_agents_root"] = str(personal_agents_root)
            report["native_agents_diff"] = personal_native_agents_diff
    return report


def build_operation_report(
    status: str,
    target_root: Path,
    install_root: Path,
    stats: BundleStats,
    diff: Dict[str, object],
    native_scope: str,
    project_native_agents_diff: Dict[str, object] | None = None,
    project_codex_agents_root: Path | None = None,
    personal_native_agents_diff: Dict[str, object] | None = None,
    personal_agents_root: Path | None = None,
    force: bool = False,
    copied_files: int = 0,
    backed_up_files: int = 0,
    backup_root: Path | None = None,
) -> Dict[str, object]:
    report: Dict[str, object] = {
        "status": status,
        "target_root": str(target_root),
        "install_root": str(install_root),
        "native_scope": native_scope,
        "force": force,
        "bundle": asdict(stats),
        "copied_files": copied_files,
        "backed_up_files": backed_up_files,
        "diff": diff,
    }
    if project_codex_agents_root is not None and project_native_agents_diff is not None:
        report["codex_agents_root"] = str(project_codex_agents_root)
        report["native_agents_diff"] = project_native_agents_diff
        report["project_codex_agents_root"] = str(project_codex_agents_root)
        report["project_native_agents_diff"] = project_native_agents_diff
    if personal_agents_root is not None and personal_native_agents_diff is not None:
        report["personal_codex_agents_root"] = str(personal_agents_root)
        report["personal_native_agents_diff"] = personal_native_agents_diff
        if "native_agents_diff" not in report:
            report["codex_agents_root"] = str(personal_agents_root)
            report["native_agents_diff"] = personal_native_agents_diff
    if backup_root is not None:
        report["backup_root"] = str(backup_root)
    return report


def format_table(report: Dict[str, object]) -> str:
    bundle = report["bundle"]
    assert isinstance(bundle, dict)
    lines = [
        f"status       : {report['status']}",
        f"target_root  : {report['target_root']}",
        f"install_root : {report['install_root']}",
        f"native_scope : {report.get('native_scope', 'project')}",
        f"force        : {report['force']}",
        f"agents       : {bundle['agent_files']}",
        f"workflows    : {bundle['workflow_files']}",
        f"services     : {bundle['service_files']}",
        f"native_agents: {bundle.get('native_agent_files', 0)}",
        f"bundle_files : {bundle['total_files']}",
    ]
    if "copied_files" in report:
        lines.append(f"copied_files : {report['copied_files']}")
    if "backed_up_files" in report:
        lines.append(f"backups      : {report['backed_up_files']}")
    if "backup_root" in report:
        lines.append(f"backup_root  : {report['backup_root']}")
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
    conflicts = report.get("conflicts", [])
    if isinstance(conflicts, list) and conflicts:
        lines.append("conflicts    : " + ", ".join(str(item) for item in conflicts[:5]))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install the bundled Scrum subagent kit into a target project.",
    )
    parser.add_argument("--target-root", required=True, help="Project root that will receive the kit")
    parser.add_argument(
        "--install-dir",
        default=".agent",
        help="Relative directory inside the target root (default: .agent)",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--diff", action="store_true", help="Compare the installed kit with the bundled kit")
    mode_group.add_argument("--update", action="store_true", help="Update only missing or changed bundle files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files in the install directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview the install without copying files")
    parser.add_argument(
        "--backup-dir",
        help="Optional backup directory for overwritten files (relative to target root if not absolute)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format",
    )
    parser.add_argument(
        "--native-scope",
        choices=("project", "personal", "both"),
        default="project",
        help="Where to install and compare native Codex custom agents (default: project)",
    )
    args = parser.parse_args()

    validation = validate_bundle(BUNDLE_ROOT)
    if validation["status"] != "ok":
        report = {"status": "error", "message": "Bundled Scrum kit is invalid", "validation": validation}
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print("status       : error\nmessage      : Bundled Scrum kit is invalid")
        return 1

    target_root = Path(args.target_root).resolve()
    install_root = target_root / args.install_dir
    codex_agents_root = project_codex_agents_root(target_root)
    personal_agents_root = personal_codex_agents_root() if uses_personal_native_agents(args.native_scope) else None

    try:
        ensure_target_root(target_root)
        stats = collect_bundle_stats(BUNDLE_ROOT)
        diff = compare_bundle_to_install(BUNDLE_ROOT, install_root)
        project_native_agents_diff = (
            compare_native_agents_to_install(BUNDLE_ROOT, codex_agents_root)
            if uses_project_native_agents(args.native_scope)
            else None
        )
        personal_native_agents_diff = (
            compare_native_agents_to_install(BUNDLE_ROOT, personal_agents_root)
            if personal_agents_root is not None
            else None
        )

        if args.diff:
            report = build_operation_report(
                status="diff",
                target_root=target_root,
                install_root=install_root,
                stats=stats,
                diff=diff,
                native_scope=args.native_scope,
                project_native_agents_diff=project_native_agents_diff,
                project_codex_agents_root=codex_agents_root if uses_project_native_agents(args.native_scope) else None,
                personal_native_agents_diff=personal_native_agents_diff,
                personal_agents_root=personal_agents_root,
                force=args.force,
            )
        elif args.update:
            paths_to_copy = list(diff["missing"]) + list(diff["changed"])  # type: ignore[arg-type]
            changed_paths = list(diff["changed"])  # type: ignore[arg-type]
            project_native_paths_to_copy = (
                list(project_native_agents_diff["missing"]) + list(project_native_agents_diff["changed"])  # type: ignore[arg-type]
                if isinstance(project_native_agents_diff, dict)
                else []
            )
            changed_project_native_paths = (
                list(project_native_agents_diff["changed"])  # type: ignore[arg-type]
                if isinstance(project_native_agents_diff, dict)
                else []
            )
            personal_native_paths_to_copy = (
                list(personal_native_agents_diff["missing"]) + list(personal_native_agents_diff["changed"])  # type: ignore[arg-type]
                if isinstance(personal_native_agents_diff, dict)
                else []
            )
            changed_personal_native_paths = (
                list(personal_native_agents_diff["changed"])  # type: ignore[arg-type]
                if isinstance(personal_native_agents_diff, dict)
                else []
            )
            backup_root: Path | None = None
            backed_up_files = 0
            if changed_paths or changed_project_native_paths or changed_personal_native_paths:
                backup_root = (
                    Path(args.backup_dir).resolve()
                    if args.backup_dir and Path(args.backup_dir).is_absolute()
                    else (target_root / args.backup_dir if args.backup_dir else default_backup_root(target_root))
                )
                backed_up_files += backup_existing_files(
                    install_root=install_root,
                    backup_root=backup_root,
                    relative_paths=changed_paths,
                    dry_run=args.dry_run,
                )
                backed_up_files += backup_existing_files(
                    install_root=codex_agents_root,
                    backup_root=backup_root / ".codex" / "agents",
                    relative_paths=changed_project_native_paths,
                    dry_run=args.dry_run,
                )
                if personal_agents_root is not None:
                    backed_up_files += backup_existing_files(
                        install_root=personal_agents_root,
                        backup_root=backup_root / "_personal" / ".codex" / "agents",
                        relative_paths=changed_personal_native_paths,
                        dry_run=args.dry_run,
                    )
            copied_files = copy_bundle_files(
                BUNDLE_ROOT,
                install_root,
                paths_to_copy,
                dry_run=args.dry_run,
            )
            if project_native_paths_to_copy:
                copied_files += copy_native_agents(
                    BUNDLE_ROOT,
                    codex_agents_root,
                    project_native_paths_to_copy,
                    dry_run=args.dry_run,
                )
            if personal_agents_root is not None and personal_native_paths_to_copy:
                copied_files += copy_native_agents(
                    BUNDLE_ROOT,
                    personal_agents_root,
                    personal_native_paths_to_copy,
                    dry_run=args.dry_run,
                )
            final_diff = diff
            final_project_native_agents_diff = project_native_agents_diff
            final_personal_native_agents_diff = personal_native_agents_diff
            if not args.dry_run and copied_files:
                install_root.mkdir(parents=True, exist_ok=True)
                write_stamp(install_root, target_root, stats, force=args.force, operation="update")
                final_diff = compare_bundle_to_install(BUNDLE_ROOT, install_root)
                if uses_project_native_agents(args.native_scope):
                    final_project_native_agents_diff = compare_native_agents_to_install(BUNDLE_ROOT, codex_agents_root)
                if personal_agents_root is not None:
                    final_personal_native_agents_diff = compare_native_agents_to_install(BUNDLE_ROOT, personal_agents_root)
            report = build_operation_report(
                status="dry_run_update" if args.dry_run else ("updated" if copied_files else "up_to_date"),
                target_root=target_root,
                install_root=install_root,
                stats=stats,
                diff=final_diff,
                native_scope=args.native_scope,
                project_native_agents_diff=final_project_native_agents_diff,
                project_codex_agents_root=codex_agents_root if uses_project_native_agents(args.native_scope) else None,
                personal_native_agents_diff=final_personal_native_agents_diff,
                personal_agents_root=personal_agents_root,
                force=args.force,
                copied_files=copied_files,
                backed_up_files=backed_up_files,
                backup_root=backup_root,
            )
        else:
            conflicts = detect_conflicts(BUNDLE_ROOT, install_root)
            project_native_conflicts = (
                detect_native_agent_conflicts(BUNDLE_ROOT, codex_agents_root)
                if uses_project_native_agents(args.native_scope)
                else []
            )
            personal_native_conflicts = (
                detect_native_agent_conflicts(BUNDLE_ROOT, personal_agents_root)
                if personal_agents_root is not None
                else []
            )
            all_conflicts = conflicts + [f".codex/agents/{name}" for name in project_native_conflicts]
            all_conflicts += [f"~/.codex/agents/{name}" for name in personal_native_conflicts]
            if all_conflicts and not args.force:
                preview = ", ".join(all_conflicts[:5])
                raise FileExistsError(f"Existing files would be overwritten: {preview}")
            copied_files = copy_entire_bundle(BUNDLE_ROOT, install_root, dry_run=args.dry_run)
            project_native_copy_paths = (
                list(project_native_agents_diff["missing"]) + list(project_native_agents_diff["changed"])  # type: ignore[arg-type]
                if isinstance(project_native_agents_diff, dict)
                else []
            )
            personal_native_copy_paths = (
                list(personal_native_agents_diff["missing"]) + list(personal_native_agents_diff["changed"])  # type: ignore[arg-type]
                if isinstance(personal_native_agents_diff, dict)
                else []
            )
            if project_native_copy_paths:
                copied_files += copy_native_agents(
                    BUNDLE_ROOT,
                    codex_agents_root,
                    project_native_copy_paths,
                    dry_run=args.dry_run,
                )
            if personal_agents_root is not None and personal_native_copy_paths:
                copied_files += copy_native_agents(
                    BUNDLE_ROOT,
                    personal_agents_root,
                    personal_native_copy_paths,
                    dry_run=args.dry_run,
                )
            if not args.dry_run:
                install_root.mkdir(parents=True, exist_ok=True)
                write_stamp(install_root, target_root, stats, args.force, operation="install")
            report = build_report(
                target_root=target_root,
                install_root=install_root,
                stats=stats,
                copied_files=copied_files,
                force=args.force,
                dry_run=args.dry_run,
                conflicts=all_conflicts,
                native_scope=args.native_scope,
                project_native_agents_diff=(
                    compare_native_agents_to_install(BUNDLE_ROOT, codex_agents_root)
                    if uses_project_native_agents(args.native_scope)
                    else None
                ),
                project_codex_agents_root=codex_agents_root if uses_project_native_agents(args.native_scope) else None,
                personal_native_agents_diff=(
                    compare_native_agents_to_install(BUNDLE_ROOT, personal_agents_root)
                    if personal_agents_root is not None
                    else None
                ),
                personal_agents_root=personal_agents_root,
            )
    except (FileExistsError, FileNotFoundError, NotADirectoryError) as exc:
        report = {"status": "error", "message": str(exc)}
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print(f"status       : error\nmessage      : {exc}")
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_table(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
