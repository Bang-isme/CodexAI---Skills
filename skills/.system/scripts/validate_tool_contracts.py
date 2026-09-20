#!/usr/bin/env python3
"""Validate plugin-level tool-call contracts for external CLI/MCP wrappers.

This script is a contract validator and safe smoke harness. It is not a production
tool executor or user-facing CLI product.
"""
from __future__ import annotations

import argparse
import ast
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
ALLOWED_KINDS = {"validator", "health", "router", "harness", "memory", "release", "packaging", "audit"}
ALLOWED_WARNING_MODES = {"none", "advisory", "strict_exit"}
ALLOWED_ARTIFACT_MODES = {"none", "read_only", "generated_on_success", "optional_outputs"}
ALLOWED_NETWORK = {"none", "optional_external", "github_api"}
ALLOWED_SMOKE_CWD = {"skills_root", "repo_root"}


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
            "memory_scale_gate",
            "skill_capability_audit",
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
            else:
                cwd = smoke.get("cwd", "repo_root")
                if cwd not in ALLOWED_SMOKE_CWD:
                    failures.append(f"{prefix}: invalid smoke.cwd {cwd!r}")
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


def json_instance_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def validate_against_schema(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Minimal JSON Schema checker covering the plugin-tools schema dialect."""
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type:
        types = expected_type if isinstance(expected_type, list) else [expected_type]
        actual = json_instance_type(instance)
        if actual not in types and not (actual == "integer" and "number" in types):
            errors.append(f"{path}: expected {expected_type}, got {actual}")
            return errors
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not in enum")
    if isinstance(instance, str):
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, instance) is None:
            errors.append(f"{path}: does not match pattern {pattern}")
        min_length = schema.get("minLength")
        if min_length is not None and len(instance) < int(min_length):
            errors.append(f"{path}: shorter than minLength {min_length}")
    if isinstance(instance, list):
        min_items = schema.get("minItems")
        if min_items is not None and len(instance) < int(min_items):
            errors.append(f"{path}: fewer than minItems {min_items}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                errors.extend(validate_against_schema(item, item_schema, f"{path}[{index}]"))
    if isinstance(instance, dict):
        for key in schema.get("required") or []:
            if key not in instance:
                errors.append(f"{path}: missing required {key}")
        properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                errors.extend(validate_against_schema(value, properties[key], f"{path}.{key}"))
            elif additional is False:
                errors.append(f"{path}: additional property {key!r} is not allowed")
            elif isinstance(additional, dict):
                errors.extend(validate_against_schema(value, additional, f"{path}.{key}"))
    return errors


def ast_literal(node: ast.AST | None) -> Any:
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [ast_literal(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(ast_literal(item) for item in node.elts)
    if isinstance(node, ast.Set):
        return {ast_literal(item) for item in node.elts}
    return None


def extract_argparse_specs(script_path: Path) -> dict[str, dict[str, Any]]:
    try:
        tree = ast.parse(script_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return {}
    specs: dict[str, dict[str, Any]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "add_argument"):
            continue
        flags = [
            arg.value
            for arg in node.args
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        ]
        names = [flag[2:].replace("-", "_") for flag in flags if flag.startswith("--")]
        if not names:
            continue
        info: dict[str, Any] = {"required": False, "choices": None}
        for keyword in node.keywords:
            if keyword.arg == "required" and isinstance(keyword.value, ast.Constant):
                info["required"] = bool(keyword.value.value)
            if keyword.arg == "choices":
                info["choices"] = ast_literal(keyword.value)
        specs[names[0]] = info
    return specs


def validate_schema_file(skills_root: Path, checks: list[dict[str, Any]]) -> dict[str, Any] | None:
    schema_path = skills_root / ".system" / "references" / "plugin-tools.schema.json"
    registry_path = skills_root / ".system" / "references" / "plugin-tools.json"
    failures: list[str] = []
    schema: dict[str, Any] | None = None
    registry: dict[str, Any] | None = None
    if not schema_path.exists():
        failures.append("plugin-tools.schema.json missing")
    else:
        try:
            loaded = read_json(schema_path)
            if not isinstance(loaded, dict) or loaded.get("schema_version") != SCHEMA_VERSION:
                failures.append("schema file schema_version mismatch")
            else:
                schema = loaded
        except Exception as exc:
            failures.append(f"schema parse error: {exc}")
    if not registry_path.exists():
        failures.append("plugin-tools.json missing")
    else:
        try:
            loaded_registry = read_json(registry_path)
            if isinstance(loaded_registry, dict):
                registry = loaded_registry
        except Exception as exc:
            failures.append(f"registry parse error: {exc}")
    if schema and registry:
        schema_errors = validate_against_schema(registry, schema)
        failures.extend(schema_errors[:20])
    add(
        checks,
        "schema_file",
        "pass" if not failures else "fail",
        "plugin tool schema present" if not failures else "; ".join(failures[:5]),
        failures=failures,
    )
    return registry


def validate_cli_contracts(skills_root: Path, tools: list[dict[str, Any]], checks: list[dict[str, Any]]) -> None:
    failures: list[str] = []
    compared = 0
    for tool in tools:
        name = str(tool.get("name", "<unknown>"))
        script = tool.get("script")
        if not isinstance(script, str) or not script:
            continue
        try:
            path = resolve_script_path(skills_root, script)
        except ValueError:
            continue
        if not path.exists():
            continue
        specs = extract_argparse_specs(path)
        args_schema = tool.get("args_schema") if isinstance(tool.get("args_schema"), dict) else {}
        properties = args_schema.get("properties") if isinstance(args_schema.get("properties"), dict) else {}
        required = args_schema.get("required") if isinstance(args_schema.get("required"), list) else []
        for field, spec in specs.items():
            compared += 1
            prop = properties.get(field) if isinstance(properties.get(field), dict) else {}
            cli_choices = spec.get("choices")
            if isinstance(cli_choices, (list, tuple, set)):
                schema_enum = prop.get("enum") if isinstance(prop, dict) else None
                if not isinstance(schema_enum, list):
                    failures.append(f"{name}: --{field.replace('_', '-')} has CLI choices but args_schema.{field} has no enum")
                    continue
                missing = sorted(str(item) for item in cli_choices if item not in schema_enum)
                extra = sorted(str(item) for item in schema_enum if item not in cli_choices)
                if missing or extra:
                    failures.append(
                        f"{name}: --{field.replace('_', '-')} choices drift (cli_only={missing} schema_only={extra})"
                    )
            if spec.get("required") and field not in required:
                failures.append(f"{name}: --{field.replace('_', '-')} is required in CLI but missing from args_schema.required")
    add(
        checks,
        "cli_contract",
        "pass" if not failures else "fail",
        f"{compared} CLI argument(s) compared" if not failures else failures[0],
        failures=failures[:20],
        total=compared,
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
        if cwd_key not in ALLOWED_SMOKE_CWD:
            failures.append(f"{name}: invalid smoke.cwd {cwd_key!r}")
            continue
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
        validate_cli_contracts(root, tools, checks)
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
