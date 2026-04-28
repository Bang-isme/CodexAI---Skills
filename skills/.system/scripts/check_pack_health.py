#!/usr/bin/env python3
"""Check CodexAI Skill Pack operational integrity."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_ALIASES = [
    "$hook",
    "$preflight",
    "$health",
    "$init-profile",
    "$knowledge",
    "$spec",
    "$prototype",
    "$think",
    "$decide",
    "$check",
    "$check-full",
    "$check-deploy",
    "$init-docs",
    "$check-docs",
    "$install-hooks",
    "$install-ci",
]
REQUIRED_DOT_DIRS = [".system", ".agents", ".workflows"]
REQUIRED_PLUGIN_ROOT_PATHS = [
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
]
MOJIBAKE_PATTERNS = [
    "\u00e2\u20ac\u201d",
    "\u00e2\u2020\u2019",
    "\u00e2\u20ac\u2122",
    "\u00e2\u20ac\u0153",
    "\u00e2\u20ac\u009d",
]


def default_skills_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check CodexAI Skill Pack operational integrity.")
    parser.add_argument("--skills-root", default="", help="Source or installed skills root")
    parser.add_argument("--global-root", default="", help="Optional global skills root to compare against source")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when warnings are present")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def add(checks: list[dict[str, Any]], name: str, status: str, detail: str, **extra: Any) -> None:
    item: dict[str, Any] = {"name": name, "status": status, "detail": detail}
    item.update(extra)
    checks.append(item)


def clean_backticks(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_registry_rows(registry_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not registry_path.exists():
        return rows
    for line in read_text(registry_path).splitlines():
        if not line.startswith("| `"):
            continue
        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if len(columns) < 3:
            continue
        rows.append(
            {
                "script": clean_backticks(columns[0]),
                "skill": clean_backticks(columns[1]),
                "purpose": columns[2],
            }
        )
    return rows


def registry_script_exists(skills_root: Path, skill: str, script: str) -> bool:
    if skill == "tests":
        return (skills_root / "tests" / script).exists()
    skill_root = skills_root / skill
    candidates = [
        skill_root / "scripts" / script,
        skill_root / script,
    ]
    if any(path.exists() for path in candidates):
        return True
    return any(path.name == script for path in skill_root.rglob(script)) if skill_root.exists() else False


def check_source(skills_root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    add(checks, "skills_root", "pass" if skills_root.is_dir() else "fail", str(skills_root))
    if not skills_root.is_dir():
        return checks

    version_path = skills_root / "VERSION"
    version = read_text(version_path).strip() if version_path.exists() else ""
    add(checks, "version_file", "pass" if version else "fail", version or "VERSION missing")

    manifest_path = skills_root / ".system" / "manifest.json"
    try:
        manifest = json.loads(read_text(manifest_path))
        add(checks, "manifest_json", "pass", "manifest parsed")
    except Exception as exc:
        manifest = {}
        add(checks, "manifest_json", "fail", f"manifest parse failed: {exc}")

    if manifest:
        manifest_version = str(manifest.get("version", ""))
        add(
            checks,
            "manifest_version",
            "pass" if manifest_version == version else "fail",
            f"manifest={manifest_version}, VERSION={version}",
        )

        missing_skills = [
            name for name in manifest.get("skills", []) if not (skills_root / str(name) / "SKILL.md").exists()
        ]
        add(
            checks,
            "manifest_skills",
            "pass" if not missing_skills else "fail",
            "all manifest skills have SKILL.md" if not missing_skills else ", ".join(missing_skills),
            missing=missing_skills,
        )

        missing_agents = [
            name for name in manifest.get("agents", []) if not (skills_root / ".agents" / f"{name}.md").exists()
        ]
        add(
            checks,
            "manifest_agents",
            "pass" if not missing_agents else "fail",
            "all manifest agents exist" if not missing_agents else ", ".join(missing_agents),
            missing=missing_agents,
        )

        missing_workflows = [
            name for name in manifest.get("workflows", []) if not (skills_root / ".workflows" / f"{name}.md").exists()
        ]
        add(
            checks,
            "manifest_workflows",
            "pass" if not missing_workflows else "fail",
            "all manifest workflows exist" if not missing_workflows else ", ".join(missing_workflows),
            missing=missing_workflows,
        )

    missing_dot_dirs = [name for name in REQUIRED_DOT_DIRS if not (skills_root / name).is_dir()]
    add(
        checks,
        "dot_directories",
        "pass" if not missing_dot_dirs else "fail",
        "required dot directories present" if not missing_dot_dirs else ", ".join(missing_dot_dirs),
        missing=missing_dot_dirs,
    )

    repo_root = skills_root.parent
    missing_plugin_paths = [path for path in REQUIRED_PLUGIN_ROOT_PATHS if not (repo_root / path).exists()]
    add(
        checks,
        "codex_native_plugin_paths",
        "pass" if not missing_plugin_paths else "fail",
        "native plugin manifest and marketplace present" if not missing_plugin_paths else ", ".join(missing_plugin_paths),
        missing=missing_plugin_paths,
    )

    plugin_path = repo_root / ".codex-plugin" / "plugin.json"
    if plugin_path.exists():
        try:
            plugin = json.loads(read_text(plugin_path))
            version = read_text(skills_root / "VERSION").strip() if (skills_root / "VERSION").exists() else ""
            add(
                checks,
                "codex_native_plugin_version",
                "pass" if plugin.get("version") == version else "fail",
                f"plugin={plugin.get('version')}, VERSION={version}",
            )
        except Exception as exc:
            add(checks, "codex_native_plugin_version", "fail", f"plugin.json parse failed: {exc}")

    registry_path = skills_root / ".system" / "REGISTRY.md"
    registry_text = read_text(registry_path) if registry_path.exists() else ""
    add(checks, "registry_exists", "pass" if registry_path.exists() else "fail", str(registry_path))
    runbook_path = skills_root / ".system" / "OPERATION_RUNBOOK.md"
    add(checks, "operation_runbook", "pass" if runbook_path.exists() else "fail", str(runbook_path))
    forbidden_registry_tokens = ["$env:USERPROFILE\\.codex\\skills", "$HOME/.codex/skills", "D:\\CodexAI---Skills"]
    leaked_tokens = [token for token in forbidden_registry_tokens if token in registry_text]
    add(
        checks,
        "registry_portable_paths",
        "pass" if not leaked_tokens else "fail",
        "registry uses <SKILLS_ROOT>" if not leaked_tokens else ", ".join(leaked_tokens),
    )

    rows = parse_registry_rows(registry_path)
    missing_scripts = [
        f"{row['skill']}/{row['script']}"
        for row in rows
        if not registry_script_exists(skills_root, row["skill"], row["script"])
    ]
    add(
        checks,
        "registry_scripts",
        "pass" if rows and not missing_scripts else "fail",
        f"{len(rows)} registry script rows checked" if not missing_scripts else ", ".join(missing_scripts),
        missing=missing_scripts,
        total=len(rows),
    )

    schema_paths = [
        "codex-runtime-hook/references/profile.schema.json",
        "codex-runtime-hook/references/runtime-hook-output.schema.json",
        "codex-spec-driven-development/references/spec.schema.json",
        "codex-project-memory/references/knowledge-index.schema.json",
    ]
    schema_failures: list[str] = []
    for rel in schema_paths:
        path = skills_root / rel
        if not path.exists():
            schema_failures.append(f"{rel}: missing")
            continue
        try:
            payload = json.loads(read_text(path))
        except Exception as exc:
            schema_failures.append(f"{rel}: invalid JSON ({exc})")
            continue
        if str(payload.get("schema_version", "")) != "1.0":
            schema_failures.append(f"{rel}: missing schema_version 1.0")
    add(
        checks,
        "contract_schemas",
        "pass" if not schema_failures else "fail",
        "contract schemas parse and declare schema_version 1.0" if not schema_failures else "; ".join(schema_failures),
        failures=schema_failures,
    )

    master_path = skills_root / "codex-master-instructions" / "SKILL.md"
    master_text = read_text(master_path) if master_path.exists() else ""
    missing_aliases = [alias for alias in REQUIRED_ALIASES if alias not in master_text]
    add(
        checks,
        "critical_aliases",
        "pass" if not missing_aliases else "fail",
        "critical aliases present" if not missing_aliases else ", ".join(missing_aliases),
        missing=missing_aliases,
    )

    mojibake_hits: list[str] = []
    for path in skills_root.rglob("*.md"):
        if "tests" in path.parts:
            continue
        text = read_text(path)
        if any(pattern in text for pattern in MOJIBAKE_PATTERNS):
            mojibake_hits.append(path.relative_to(skills_root).as_posix())
            if len(mojibake_hits) >= 20:
                break
    add(
        checks,
        "markdown_mojibake",
        "pass" if not mojibake_hits else "warn",
        "no common mojibake sequences in markdown" if not mojibake_hits else ", ".join(mojibake_hits),
        files=mojibake_hits,
    )

    return checks


def check_native_agent_role_files(agents_root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if not agents_root.exists():
        add(checks, "native_agent_roles", "pass", f"native agents root not installed: {agents_root}")
        return checks

    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
        add(checks, "native_agent_roles", "warn", "tomllib unavailable; native agent role validation skipped")
        return checks

    allowed = {"name", "description", "developer_instructions", "sandbox_mode", "model", "model_reasoning_effort", "mcp_servers", "skills", "nickname_candidates"}
    failures: list[str] = []
    checked = 0
    for path in sorted(agents_root.glob("scrum-*.toml")):
        checked += 1
        try:
            payload = tomllib.loads(read_text(path))
        except Exception as exc:
            failures.append(f"{path.name}: invalid TOML ({exc})")
            continue
        unsupported = sorted(set(payload) - allowed)
        if unsupported:
            failures.append(f"{path.name}: unsupported field(s): {', '.join(unsupported)}")
        if not str(payload.get("name", "")).strip():
            failures.append(f"{path.name}: missing name")
        if not str(payload.get("description", "")).strip():
            failures.append(f"{path.name}: missing description")
        if not str(payload.get("developer_instructions", "")).strip():
            failures.append(f"{path.name}: missing developer_instructions")

    add(
        checks,
        "native_agent_roles",
        "pass" if not failures else "fail",
        f"{checked} native scrum agent role file(s) checked" if not failures else "; ".join(failures[:5]),
        failures=failures,
        total=checked,
    )
    return checks
def check_global_sync(source_root: Path, global_root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    add(checks, "global_root", "pass" if global_root.is_dir() else "fail", str(global_root))
    if not global_root.is_dir():
        return checks

    source_version = read_text(source_root / "VERSION").strip() if (source_root / "VERSION").exists() else ""
    global_version = read_text(global_root / "VERSION").strip() if (global_root / "VERSION").exists() else ""
    add(
        checks,
        "global_version_sync",
        "pass" if source_version and source_version == global_version else "fail",
        f"source={source_version}, global={global_version}",
    )

    required_paths = [
        ".system/manifest.json",
        ".system/REGISTRY.md",
        ".system/OPERATION_RUNBOOK.md",
        ".system/scripts/check_pack_health.py",
        ".system/scripts/sync_global_skills.py",
        ".system/scripts/install_codex_native.py",
        ".system/scripts/validate_codex_plugin.py",
        ".system/scripts/init_agents_md.py",
        ".agents/frontend-specialist.md",
        ".workflows/plan.md",
        ".workflows/prototype.md",
        "codex-runtime-hook/references/profile.schema.json",
        "codex-runtime-hook/references/runtime-hook-output.schema.json",
        "codex-runtime-hook/SKILL.md",
        "codex-runtime-hook/scripts/install_codex_hooks.py",
        "codex-runtime-hook/scripts/validate_codex_hooks.py",
        "codex-project-memory/references/knowledge-index.schema.json",
        "codex-logical-decision-layer/SKILL.md",
        "codex-spec-driven-development/SKILL.md",
        "codex-spec-driven-development/references/spec.schema.json",
    ]
    missing = [path for path in required_paths if not (global_root / path).exists()]
    add(
        checks,
        "global_required_paths",
        "pass" if not missing else "fail",
        "global install includes runtime metadata" if not missing else ", ".join(missing) + " | run sync_global_skills.py from source .system/scripts",
        missing=missing,
    )
    return checks


def summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [item for item in checks if item["status"] == "fail"]
    warned = [item for item in checks if item["status"] == "warn"]
    return {
        "status": "fail" if failed else ("warn" if warned else "pass"),
        "total": len(checks),
        "passed": sum(1 for item in checks if item["status"] == "pass"),
        "warnings": len(warned),
        "failed": len(failed),
        "checks": checks,
    }


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"Status: {payload['status']}",
        f"Checks: {payload['passed']} passed, {payload['warnings']} warnings, {payload['failed']} failed",
        "",
    ]
    for item in payload["checks"]:
        lines.append(f"- {item['status'].upper()}: {item['name']} -- {item['detail']}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    skills_root = Path(args.skills_root).expanduser().resolve() if args.skills_root else default_skills_root()
    checks = check_source(skills_root)
    if args.global_root:
        global_root = Path(args.global_root).expanduser().resolve()
        checks.extend(check_global_sync(skills_root, global_root))
        checks.extend(check_native_agent_role_files(global_root.parent / "agents"))
    payload = summarize(checks)

    if args.format == "text":
        print(render_text(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if payload["failed"]:
        return 1
    if args.strict and payload["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
