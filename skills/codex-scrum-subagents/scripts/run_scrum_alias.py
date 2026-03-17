#!/usr/bin/env python3
"""Resolve Scrum shorthand aliases to installer actions or workflow guidance."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_scrum_artifact import build_artifact_payload, parse_fields, template_fields


INSTALLER_SCRIPT = SCRIPT_DIR / "install_scrum_subagents.py"
VALIDATOR_SCRIPT = SCRIPT_DIR / "validate_scrum_agent_kit.py"

ALIAS_REGISTRY: Dict[str, Dict[str, object]] = {
    "$scrum-install": {"kind": "installer", "action": "install"},
    "$scrum-diff": {"kind": "installer", "action": "diff"},
    "$scrum-update": {"kind": "installer", "action": "update"},
    "$scrum-validate": {"kind": "installer", "action": "validate"},
    "$backlog-refinement": {
        "kind": "workflow",
        "workflow": "backlog-refinement",
        "template": "user-story",
        "roles": ["product-owner", "scrum-master"],
        "summary": "Refine a request into a story with acceptance criteria and sequencing notes.",
    },
    "$sprint-plan": {
        "kind": "workflow",
        "workflow": "sprint-planning",
        "template": "sprint-goal",
        "roles": ["scrum-master", "product-owner", "delivery-leads"],
        "summary": "Define sprint goal, scope, ownership, and top risks.",
    },
    "$daily-scrum": {
        "kind": "workflow",
        "workflow": "daily-scrum",
        "template": "daily-scrum",
        "roles": ["scrum-master", "delivery-team"],
        "summary": "Capture progress, plan, and blockers for the current day.",
    },
    "$story-ready-check": {
        "kind": "workflow",
        "workflow": "backlog-refinement",
        "template": "user-story",
        "roles": ["product-owner", "scrum-master"],
        "summary": "Check whether a story is clear enough and small enough to implement.",
    },
    "$story-delivery": {
        "kind": "workflow",
        "workflow": "story-delivery",
        "template": "story-delivery",
        "roles": ["scrum-orchestrator", "delivery-team", "qa-engineer"],
        "summary": "Drive one story through implementation, verification, and handoff.",
    },
    "$sprint-review": {
        "kind": "workflow",
        "workflow": "sprint-review",
        "template": "sprint-goal",
        "roles": ["product-owner", "scrum-master", "qa-engineer"],
        "summary": "Inspect sprint outcomes, demo value, and collect stakeholder feedback.",
    },
    "$retro": {
        "kind": "workflow",
        "workflow": "retrospective",
        "template": "retrospective",
        "roles": ["scrum-master", "delivery-team"],
        "summary": "Capture wins, pain points, and concrete next-sprint improvement actions.",
    },
    "$release-readiness": {
        "kind": "workflow",
        "workflow": "release-readiness",
        "template": "release-readiness",
        "roles": ["scrum-master", "qa-engineer", "security-engineer", "devops-engineer"],
        "summary": "Make a ship or no-ship decision with evidence, risks, and rollback plan.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Scrum alias or generate its recommended artifact.",
    )
    parser.add_argument("--alias", required=True, choices=sorted(ALIAS_REGISTRY), help="Scrum alias to resolve")
    parser.add_argument("--target-root", help="Project root for install/diff/update/validate aliases")
    parser.add_argument("--artifact-output", help="Optional output file for workflow artifact generation")
    parser.add_argument("--field", action="append", default=[], help="Artifact field in key=value form")
    parser.add_argument("--force", action="store_true", help="Forward --force to installer aliases")
    parser.add_argument("--dry-run", action="store_true", help="Forward --dry-run to installer aliases")
    parser.add_argument("--backup-dir", help="Forward --backup-dir to $scrum-update")
    parser.add_argument(
        "--native-scope",
        choices=("project", "personal", "both"),
        default="project",
        help="Forward native-agent scope to installer and validator aliases",
    )
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow scaffold workflow artifacts with _TODO_ placeholders instead of requiring every field",
    )
    parser.add_argument("--format", choices=("json", "table"), default="json", help="Output format")
    return parser.parse_args()


def run_json_command(command: List[str]) -> Dict[str, object]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )
    stdout = result.stdout.strip()
    if stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = {"status": "error", "message": stdout}
    else:
        payload = {"status": "error", "message": result.stderr.strip() or "No output"}
    payload["exit_code"] = result.returncode
    return payload


def build_workflow_payload(
    alias: str,
    artifact_output: str | None,
    fields: Dict[str, str],
    allow_placeholders: bool = False,
) -> Dict[str, object]:
    config = ALIAS_REGISTRY[alias]
    payload: Dict[str, object] = {
        "status": "ok",
        "alias": alias,
        "kind": "workflow",
        "workflow": config["workflow"],
        "summary": config["summary"],
        "recommended_roles": config["roles"],
        "template": config["template"],
        "required_fields": template_fields(str(config["template"])),
    }
    if artifact_output:
        artifact_payload = build_artifact_payload(str(config["template"]), fields, allow_placeholders)
        output_path = Path(artifact_output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(str(artifact_payload["markdown"]), encoding="utf-8", newline="\n")
        payload["status"] = artifact_payload["status"]
        payload["missing_fields"] = artifact_payload["missing_fields"]
        payload["artifact_path"] = output_path.as_posix()
    return payload


def format_table(payload: Dict[str, object]) -> str:
    lines = [
        f"status       : {payload.get('status')}",
        f"alias        : {payload.get('alias', '-')}",
        f"kind         : {payload.get('kind', '-')}",
    ]
    if payload.get("workflow"):
        lines.append(f"workflow     : {payload.get('workflow')}")
    if payload.get("template"):
        lines.append(f"template     : {payload.get('template')}")
    if payload.get("artifact_path"):
        lines.append(f"artifact     : {payload.get('artifact_path')}")
    if payload.get("missing_fields"):
        lines.append(f"missing      : {', '.join(str(item) for item in payload['missing_fields'])}")
    if payload.get("summary"):
        lines.append(f"summary      : {payload.get('summary')}")
    if payload.get("message"):
        lines.append(f"message      : {payload.get('message')}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    config = ALIAS_REGISTRY[args.alias]
    kind = str(config["kind"])

    if kind == "installer":
        if not args.target_root:
            payload = {"status": "error", "alias": args.alias, "message": "--target-root is required"}
            if args.format == "json":
                print(json.dumps(payload, indent=2))
            else:
                print(format_table(payload))
            return 1
        command = [sys.executable]
        action = str(config["action"])
        if action == "validate":
            command.extend(
                [
                    str(VALIDATOR_SCRIPT),
                    "--format",
                    "json",
                    "--target-root",
                    args.target_root,
                    "--native-scope",
                    args.native_scope,
                ]
            )
        else:
            command.extend([str(INSTALLER_SCRIPT), "--target-root", args.target_root, "--format", "json"])
            if action == "diff":
                command.append("--diff")
            elif action == "update":
                command.append("--update")
            if args.native_scope:
                command.extend(["--native-scope", args.native_scope])
            if args.force:
                command.append("--force")
            if args.dry_run:
                command.append("--dry-run")
            if args.backup_dir and action == "update":
                command.extend(["--backup-dir", args.backup_dir])
        payload = run_json_command(command)
        payload["alias"] = args.alias
        payload["kind"] = "installer"
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(format_table(payload))
        return 0 if int(payload.get("exit_code", 1)) == 0 else 1

    try:
        fields = parse_fields(args.field)
    except ValueError as exc:
        payload = {"status": "error", "alias": args.alias, "message": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(format_table(payload))
        return 1

    try:
        payload = build_workflow_payload(args.alias, args.artifact_output, fields, args.allow_placeholders)
    except ValueError as exc:
        payload = {"status": "error", "alias": args.alias, "message": str(exc)}
        if args.format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(format_table(payload))
        return 1

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_table(payload))
    return 0 if payload.get("status") != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
