#!/usr/bin/env python3
"""Validate plugin-level tool-call contracts for external CLI/MCP wrappers.

This script is a contract validator and safe smoke harness. It is not a production
tool executor or user-facing CLI product.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_TOOL_FIELDS = (
    "name",
    "kind",
    "script",
    "purpose",
    "args_schema",
    "exit_codes",
    "warning_policy",
    "artifact_policy",
    "safety_policy",
)
REQUIRED_EXIT_FIELDS = ("success", "failure")
REQUIRED_POLICY_FIELDS = {
    "warning_policy": ("mode", "description"),
    "artifact_policy": ("mode", "description"),
    "safety_policy": ("network", "writes_artifacts", "reads_secrets", "smoke_allowed", "description"),
}
ALLOWED_KINDS = {"validator", "health", "router", "harness", "memory", "release", "packaging"}
ALLOWED_WARNING_MODES = {"none", "advisory", "strict_exit"}
ALLOWED_ARTIFACT_MODES = {"none", "read_only", "generated_on_success", "optional_outputs"}
ALLOWED_NETWORK = {"none", "optional_external", "github_api"}


def default_skills_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_repo_root(skills_root: Path) -> Path:
    return skills_root.parent


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def add(
    checks: list[dict[str, Any]],
    name: str,
    status: str,
    detail: str,
    *,
    warnings: list[str] | None = None,
    failures: list[str] | None = None,
    **extra: Any,
) -> None:
    item: dict[str, Any] = {"name": name, "status": status, "detail": detail}
    if warnings:
        item["warnings"] = warnings
    if failures:
        item["failures"] = failures
    item.update(extra)
    checks.append(item)


def resolve_script_path(skills_root: Path, script: str) -> Path:
    normalized = script.replace("\\", "/").lstrip("/")
    if normalized.startswith(".."):
        raise ValueError(f"script escapes skills root: {script}")
    resolved = (skills_root / normalized).resolve()
    root = skills_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"script escapes skills root: {script}")
    return resolved


def validate_registry_shape(registry: Any, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[str] = []
    if not isinstance(registry, dict):
        add(checks, "registry_root", "fail", "registry root must be an object")
        return []
    version = registry.get("schema_version")
    if version != SCHEMA_VERSION:
        failures.append(f"schema_version must be {SCHEMA_VERSION}, got {version!r}")
    tools = registry.get("tools")
    if not isinstance(tools, list) or not tools:
        failures.append("tools must be a non-empty array")
        add(
            checks,
            "registry_shape",
            "fail" if failures else "pass",
            "; ".join(failures) if failures else f"{len(tools or [])} tool(s) declared",
            failures=failures,
        )
        return []
    names: set[str] = set()
    validated: list[dict[str, Any]] = []
    for index, tool in enumerate(tools):
        prefix = f"tools[{index}]"
        if not isinstance(tool, dict):
            failures.append(f"{prefix}: not an object")
            continue
        validated.append(tool)
        for field in REQUIRED_TOOL_FIELDS:
            if field not in tool:
                failures.append(f"{prefix}: missing {field}")
        name = str(tool.get("name", ""))
        if name:
            if not NAME_PATTERN.match(name):
                failures.append(f"{prefix}: invalid name {name!r}")
            if name in names:
                failures.append(f"{prefix}: duplicate name {name!r}")
            names.add(name)
        kind = tool.get("kind")
        if kind not in ALLOWED_KINDS:
            failures.append(f"{prefix}: invalid kind {kind!r}")
        args_schema = tool.get("args_schema")
        if not isinstance(args_schema, dict):
            failures.append(f"{prefix}: args_schema must be an object")
        elif args_schema.get("type") != "object":
            failures.append(f"{prefix}: args_schema.type must be object")
        elif "properties" not in args_schema:
            failures.append(f"{prefix}: args_schema.properties required")
        required_args = args_schema.get("required") if isinstance(args_schema, dict) else None
        if name in {
            "pack_health",
            "codex_plugin_validate",
            "claude_plugin_validate",
            "release_zip_dry_run",
            "memory_status",
            "memory_build_index",
        }:
            if not isinstance(required_args, list) or not required_args:
                failures.append(f"{prefix}: args_schema.required must list required wrapper inputs")
        exit_codes = tool.get("exit_codes")
        if not isinstance(exit_codes, dict):
            failures.append(f"{prefix}: exit_codes must be an object")
        else:
            for field in REQUIRED_EXIT_FIELDS:
                if field not in exit_codes:
                    failures.append(f"{prefix}: exit_codes missing {field}")
        for policy_name, policy_fields in REQUIRED_POLICY_FIELDS.items():
            policy = tool.get(policy_name)
            if not isinstance(policy, dict):
                failures.append(f"{prefix}: {policy_name} must be an object")
                continue
            for field in policy_fields:
                if field not in policy:
                    failures.append(f"{prefix}: {policy_name} missing {field}")
        warning = tool.get("warning_policy", {})
        if isinstance(warning, dict) and warning.get("mode") not in ALLOWED_WARNING_MODES:
            failures.append(f"{prefix}: invalid warning_policy.mode")
        artifact = tool.get("artifact_policy", {})
        if isinstance(artifact, dict) and artifact.get("mode") not in ALLOWED_ARTIFACT_MODES:
            failures.append(f"{prefix}: invalid artifact_policy.mode")
        safety = tool.get("safety_policy", {})
        if isinstance(safety, dict):
            if safety.get("network") not in ALLOWED_NETWORK:
                failures.append(f"{prefix}: invalid safety_policy.network")
            for bool_field in ("writes_artifacts", "reads_secrets", "smoke_allowed"):
                if bool_field in safety and not isinstance(safety.get(bool_field), bool):
                    failures.append(f"{prefix}: safety_policy.{bool_field} must be boolean")
            if safety.get("reads_secrets") is True:
                failures.append(f"{prefix}: reads_secrets must remain false in plugin contracts")
        smoke = tool.get("smoke")
        if smoke is not None:
            if not isinstance(smoke, dict):
                failures.append(f"{prefix}: smoke must be an object")
            elif not smoke.get("argv"):
                failures.append(f"{prefix}: smoke.argv required when smoke is present")
    add(
        checks,
        "registry_shape",
        "pass" if not failures else "fail",
        f"{len(validated)} tool contract(s) checked" if not failures else failures[0],
        failures=failures[:20],
        total=len(validated),
    )
    return validated


def validate_script_paths(skills_root: Path, tools: list[dict[str, Any]], checks: list[dict[str, Any]]) -> None:
    failures: list[str] = []
    for tool in tools:
        name = str(tool.get("name", "<unknown>"))
        script = tool.get("script")
        if not isinstance(script, str) or not script:
            failures.append(f"{name}: missing script path")
            continue
        try:
            path = resolve_script_path(skills_root, script)
        except ValueError as exc:
            failures.append(f"{name}: {exc}")
            continue
        if not path.exists():
            failures.append(f"{name}: script not found ({script})")
    add(
        checks,
        "script_paths",
        "pass" if not failures else "fail",
        "all registry scripts exist under skills root" if not failures else failures[0],
        failures=failures,
    )


def validate_schema_file(skills_root: Path, checks: list[dict[str, Any]]) -> None:
    schema_path = skills_root / ".system" / "references" / "plugin-tools.schema.json"
    registry_path = skills_root / ".system" / "references" / "plugin-tools.json"
    failures: list[str] = []
    if not schema_path.exists():
        failures.append("plugin-tools.schema.json missing")
    else:
        try:
            schema = read_json(schema_path)
            if schema.get("schema_version") != SCHEMA_VERSION:
                failures.append("schema file schema_version mismatch")
        except Exception as exc:
            failures.append(f"schema parse error: {exc}")
    if not registry_path.exists():
        failures.append("plugin-tools.json missing")
    add(
        checks,
        "schema_file",
        "pass" if not failures else "fail",
        "plugin tool schema present" if not failures else "; ".join(failures),
        failures=failures,
    )


def substitute_argv(argv: list[str], skills_root: Path, repo_root: Path) -> list[str]:
    mapping = {
        "{skills_root}": str(skills_root),
        "{repo_root}": str(repo_root),
    }
    result: list[str] = []
    for token in argv:
        replaced = token
        for key, value in mapping.items():
            replaced = replaced.replace(key, value)
        result.append(replaced)
    return result


def run_smoke(
    skills_root: Path,
    repo_root: Path,
    tools: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    *,
    include_memory_fixture: bool,
) -> None:
    failures: list[str] = []
    warnings: list[str] = []
    ran = 0
    for tool in tools:
        name = str(tool.get("name", ""))
        safety = tool.get("safety_policy", {})
        if not isinstance(safety, dict) or not safety.get("smoke_allowed"):
            continue
        smoke = tool.get("smoke")
        if not isinstance(smoke, dict):
            warnings.append(f"{name}: smoke_allowed but no smoke block")
            continue
        argv = smoke.get("argv")
        if not isinstance(argv, list) or not argv:
            failures.append(f"{name}: invalid smoke.argv")
            continue
        script = str(tool.get("script", ""))
        try:
            script_path = resolve_script_path(skills_root, script)
        except ValueError as exc:
            failures.append(f"{name}: {exc}")
            continue
        cwd_key = smoke.get("cwd", "repo_root")
        cwd = skills_root if cwd_key == "skills_root" else repo_root
        cmd = [sys.executable, str(script_path), *substitute_argv([str(x) for x in argv], skills_root, repo_root)]
        expect = smoke.get("expect_exit_codes", [0])
        if not isinstance(expect, list):
            expect = [0]
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{name}: smoke timed out")
            continue
        ran += 1
        if completed.returncode not in expect:
            failures.append(
                f"{name}: exit {completed.returncode} not in {expect} (cmd: {' '.join(cmd[-4:])})"
            )
    if include_memory_fixture:
        ran += run_memory_status_fixture(skills_root, repo_root, failures)
    add(
        checks,
        "safe_smoke",
        "pass" if not failures else "fail",
        f"{ran} smoke command(s) executed" if not failures else failures[0],
        failures=failures,
        warnings=warnings,
        total=ran,
    )


def run_memory_status_fixture(skills_root: Path, repo_root: Path, failures: list[str]) -> int:
    script = skills_root / "codex-project-memory" / "scripts" / "memory_status.py"
    if not script.exists():
        failures.append("memory_status fixture: script missing")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        knowledge = project / ".codex" / "knowledge"
        knowledge.mkdir(parents=True)
        minimal_index = {
            "schema_version": "1.0",
            "generated_at": "2026-01-01T00:00:00+00:00",
            "project_root": str(project),
            "entries": [],
        }
        (knowledge / "index.json").write_text(json.dumps(minimal_index), encoding="utf-8")
        (knowledge / "knowledge-graph.json").write_text(
            json.dumps({"schema_version": "1.0", "nodes": [], "edges": []}),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "--project-root",
                str(project),
                "--format",
                "json",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        if completed.returncode not in {0, 1}:
            failures.append(f"memory_status fixture: unexpected exit {completed.returncode}")
        try:
            payload = json.loads(completed.stdout or "{}")
            if payload.get("status") not in {"pass", "warn", "fail", "error"}:
                failures.append("memory_status fixture: missing status in JSON stdout")
        except json.JSONDecodeError:
            failures.append("memory_status fixture: stdout is not JSON")
    return 1


def summarize(checks: list[dict[str, Any]], strict: bool = False) -> dict[str, Any]:
    failed_checks = [item for item in checks if item["status"] == "fail"]
    warning_items = [
        item
        for item in checks
        if item["status"] == "warn" or item.get("warnings")
    ]
    failures = [item["detail"] for item in failed_checks]
    warnings = []
    for item in warning_items:
        warnings.extend(item.get("warnings", []))
        if item["status"] == "warn":
            warnings.append(item["detail"])
    status = "fail" if failed_checks else ("warn" if warning_items else "pass")
    if strict and warning_items and not failed_checks:
        status = "fail"
    return {
        "status": status,
        "checks": checks,
        "warnings": warnings,
        "failures": failures,
        "total": len(checks),
        "failed": len(failed_checks),
    }


def validate(
    skills_root: Path,
    *,
    strict: bool = False,
    run_smokes: bool = True,
    include_memory_fixture: bool = True,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    root = skills_root.expanduser().resolve()
    repo_root = default_repo_root(root)
    add(checks, "skills_root", "pass" if root.is_dir() else "fail", str(root))
    if not root.is_dir():
        return summarize(checks, strict)
    validate_schema_file(root, checks)
    registry_path = root / ".system" / "references" / "plugin-tools.json"
    try:
        registry = read_json(registry_path)
    except Exception as exc:
        add(checks, "registry_load", "fail", f"cannot load registry: {exc}")
        return summarize(checks, strict)
    add(checks, "registry_load", "pass", str(registry_path))
    tools = validate_registry_shape(registry, checks)
    if tools:
        validate_script_paths(root, tools, checks)
    if run_smokes and tools:
        run_smoke(root, repo_root, tools, checks, include_memory_fixture=include_memory_fixture)
    return summarize(checks, strict)


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"Status: {payload['status']}",
        f"Checks: {payload['total']} total, {payload['failed']} failed",
        "",
    ]
    for item in payload["checks"]:
        lines.append(f"- {item['status'].upper()}: {item['name']} -- {item['detail']}")
    if payload.get("warnings"):
        lines.append("")
        lines.append("Warnings:")
        for warning in payload["warnings"]:
            lines.append(f"  - {warning}")
    if payload.get("failures"):
        lines.append("")
        lines.append("Failures:")
        for failure in payload["failures"]:
            lines.append(f"  - {failure}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate plugin tool-call contracts (registry + safe smokes)."
    )
    parser.add_argument("--skills-root", default="", help="Skills root. Defaults to repository skills/.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failure and exit non-zero on warn.")
    parser.add_argument("--no-smoke", action="store_true", help="Skip smoke execution (registry validation only).")
    parser.add_argument(
        "--no-memory-fixture",
        action="store_true",
        help="Skip ephemeral memory_status fixture smoke.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.skills_root) if args.skills_root else default_skills_root()
    payload = validate(
        root,
        strict=args.strict,
        run_smokes=not args.no_smoke,
        include_memory_fixture=not args.no_memory_fixture,
    )
    if args.format == "text":
        print(render_text(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "pass":
        return 0
    if payload["status"] == "warn" and not args.strict:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
