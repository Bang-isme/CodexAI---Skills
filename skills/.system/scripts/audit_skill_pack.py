#!/usr/bin/env python3
"""Audit versioned skill capabilities and render an offline scorecard.

The audit is intentionally dependency-free. It validates declared ownership and
security policy without executing plugin tools or loading project source code.
"""
from __future__ import annotations

import argparse
import ast
import html
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
REQUIRED_CAPABILITY_FIELDS = (
    "skill",
    "domain",
    "objective",
    "triggers",
    "resources",
    "output_artifacts",
    "tool_classes",
    "risk_tier",
    "security_policy",
    "verification",
    "handoff",
)
RESOURCE_FIELDS = ("scripts", "references", "assets", "agents", "templates", "starters")
RISK_TIERS = {"advisory", "enforced"}
TOOL_CLASSES = {
    "read_only",
    "project_write",
    "code_generation",
    "shell_execution",
    "network",
    "git_remote",
    "secret_sensitive",
}
HIGH_RISK_CLASSES = TOOL_CLASSES - {"read_only"}
SCRIPT_SUFFIXES = {".py", ".ps1", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts"}
REQUIRED_POLICY_FIELDS = ("network", "path_scope", "redact_outputs", "notes")
SECRET_PATTERN = re.compile(
    r"(?i)(?:sk-[a-z0-9_-]{12,}|gh[pousr]_[a-z0-9]{16,}|(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^\s'\"]{8,})"
)


def default_skills_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def redact_text(value: str) -> str:
    return SECRET_PATTERN.sub("[REDACTED]", value)


def finding(findings: list[dict[str, str]], severity: str, code: str, scope: str, detail: str) -> None:
    findings.append(
        {
            "severity": severity,
            "code": code,
            "scope": redact_text(scope),
            "detail": redact_text(detail),
        }
    )


def is_safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    candidate = Path(value.replace("\\", "/"))
    return not candidate.is_absolute() and ".." not in candidate.parts


def resolve_relative(root: Path, value: str) -> Path:
    if not is_safe_relative_path(value):
        raise ValueError("path must be a non-empty relative path inside its owner")
    resolved = (root / value).resolve()
    root = root.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("path resolves outside its owner")
    return resolved


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def literal_strings(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.List, ast.Tuple)):
        values: list[str] = []
        for item in node.elts:
            values.extend(literal_strings(item))
        return values
    return []


def target_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        return [name for item in node.elts for name in target_names(item)]
    return []


def is_sensitive_identifier(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"api_key", "apikey", "access_token", "token", "secret", "password", "private_key"}:
        return True
    return any(marker in lowered for marker in ("api_key", "apikey", "access_token", "secret", "password", "private_key"))


def classify_script_text(text: str) -> list[str]:
    """Return risk classes backed by executable Python syntax when available."""
    try:
        tree = ast.parse(text.lstrip("\ufeff"))
    except SyntaxError:
        source = text.lower()
        classes = set()
        if re.search(r"\b(?:powershell|cmd\.exe|/bin/sh|shell\s*=\s*true)\b", source):
            classes.add("shell_execution")
        if re.search(r"\b(?:curl|wget|https?://)\b", source):
            classes.add("network")
        if re.search(r"\bgit\s+(?:push|pull|fetch|clone|remote)\b", source):
            classes.add("git_remote")
        if re.search(r"\b(?:api[_-]?key|access[_-]?token|secret|password)\s*=", source):
            classes.add("secret_sensitive")
        if re.search(r"(?:>|>>|out-file|set-content|add-content)", source):
            classes.add("project_write")
        return sorted(classes or {"read_only"})

    classes: set[str] = set()
    write_calls = {"write", "write_text", "write_bytes", "writelines", "mkdir", "replace", "rename", "unlink", "rmtree", "copy", "copy2", "copytree", "move", "dump"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = [alias.name.split(".", 1)[0] for alias in node.names] if isinstance(node, ast.Import) else [str(node.module or "").split(".", 1)[0]]
            if "subprocess" in imported:
                classes.add("shell_execution")
            if set(imported) & {"urllib", "requests", "http", "aiohttp", "socket", "websocket"}:
                classes.add("network")
            if set(imported) & {"jinja2", "jinja"}:
                classes.add("code_generation")
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if value is not None and literal_strings(value):
                names = {name.lower() for target in targets for name in target_names(target)}
                if any(is_sensitive_identifier(name) for name in names):
                    classes.add("secret_sensitive")
        if not isinstance(node, ast.Call):
            continue
        call = dotted_name(node.func)
        last = call.rsplit(".", 1)[-1]
        if call.startswith(("subprocess.", "os.system", "os.popen")) or last in {"Popen", "run", "call", "check_call", "check_output"} and call.startswith("subprocess"):
            classes.add("shell_execution")
            command_values = [value.lower() for argument in node.args for value in literal_strings(argument)]
            if command_values and command_values[0] in {"git", "gh"} and set(command_values[1:]) & {"push", "pull", "fetch", "clone", "remote", "api", "pr", "repo"}:
                classes.add("git_remote")
        if call.startswith(("requests.", "urllib.", "http.", "aiohttp.", "socket.", "websocket.")):
            classes.add("network")
        if last in write_calls:
            classes.add("project_write")
        if call == "open" and len(node.args) >= 2 and any(mode[:1] in {"w", "a", "x"} for mode in literal_strings(node.args[1])):
            classes.add("project_write")
        if call in {"os.getenv", "os.environ.get"} and any(
            is_sensitive_identifier(value) for argument in node.args for value in literal_strings(argument)
        ):
            classes.add("secret_sensitive")
        if call.endswith((".render", ".render_template")):
            classes.add("code_generation")
    return sorted(classes or {"read_only"})


def classify_script(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ["read_only"]
    classes = set(classify_script_text(text))
    if re.search(r"(?:^|_)(?:generate|render|build)(?:_|$)", path.stem.lower()):
        classes.add("code_generation")
        classes.discard("read_only")
    return sorted(classes or {"read_only"})


def parse_registry_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.lstrip().startswith("|") or "`" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "script":
            continue
        script_match = re.fullmatch(r"`([^`]+)`", cells[0])
        skill_match = re.fullmatch(r"`([^`]+)`", cells[1])
        if script_match and skill_match:
            rows.append({"script": script_match.group(1), "owner": skill_match.group(1)})
    return rows


def managed_skill_directories(skills_root: Path) -> set[str]:
    return {
        path.name
        for path in skills_root.iterdir()
        if path.is_dir() and not path.name.startswith(".") and (path / "SKILL.md").is_file()
    }


def validation_owner_exists(skills_root: Path, owner: Any) -> bool:
    try:
        return resolve_relative(skills_root, str(owner)).is_file()
    except ValueError:
        return False


def component_paths(component: dict[str, Any]) -> list[str]:
    resources = component.get("resources", {})
    if not isinstance(resources, dict):
        return []
    scripts = resources.get("scripts", [])
    return [item for item in scripts if isinstance(item, str)] if isinstance(scripts, list) else []


def collect_scripts(skills_root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in skills_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCRIPT_SUFFIXES:
            continue
        rel = path.relative_to(skills_root)
        if "tests" in rel.parts or "__pycache__" in rel.parts:
            continue
        if "scripts" in rel.parts or len(rel.parts) == 1:
            paths.append(path)
    return sorted(paths)


def component_for_script(
    skills_root: Path,
    path: Path,
    capabilities: dict[str, dict[str, Any]],
    shared_components: dict[str, dict[str, Any]],
) -> tuple[str | None, dict[str, Any] | None]:
    rel = path.relative_to(skills_root).as_posix()
    first = rel.split("/", 1)[0]
    if first in capabilities:
        return first, capabilities[first]
    for name, component in shared_components.items():
        for declared in component_paths(component):
            try:
                resolved = resolve_relative(skills_root, declared)
            except ValueError:
                continue
            if path == resolved or resolved in path.parents:
                return name, component
    return None, None


def is_policy_complete(policy: Any) -> bool:
    return isinstance(policy, dict) and all(field in policy for field in REQUIRED_POLICY_FIELDS)


def readiness_for(scope: str, findings: list[dict[str, str]]) -> str:
    own = [item for item in findings if item["scope"] == scope]
    if any(item["severity"] == "error" for item in own):
        return "blocked"
    if own:
        return "advisory"
    return "ready"


def safe_json_for_html(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("=", "\\u003d")


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Skill Capability Scorecard",
        "",
        f"Status: **{payload['status']}**",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Skills | {summary['skills']} |",
        f"| Scripts audited | {summary['scripts']} |",
        f"| Enforced skills | {summary['enforced']} |",
        f"| Ready skills | {summary['ready']} |",
        f"| Findings | {summary['findings']} |",
        "",
        "| Skill | Domain | Risk | Readiness | Scripts | Verification |",
        "|---|---|---|---|---:|---|",
    ]
    for item in payload["capabilities"]:
        lines.append(
            "| {skill} | {domain} | {risk} | {readiness} | {scripts} | {owner} |".format(
                skill=redact_text(str(item["skill"])),
                domain=redact_text(str(item["domain"])),
                risk=item["risk_tier"],
                readiness=item["readiness"],
                scripts=item["script_count"],
                owner=redact_text(str(item["verification_owner"])),
            )
        )
    if payload["findings"]:
        lines.extend(["", "## Findings", ""])
        for item in payload["findings"]:
            lines.append(f"- `{item['severity']}` `{item['code']}` {item['scope']}: {item['detail']}")
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any]) -> str:
    data = safe_json_for_html(payload)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skill Capability Scorecard</title>
<style>
:root {{ color-scheme: light; font-family: Arial, sans-serif; background: #f5f7fa; color: #172033; }}
body {{ margin: 0; }} main {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
h1 {{ margin: 0 0 8px; font-size: 24px; }} .summary {{ display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0; }}
.metric {{ background: #fff; border: 1px solid #d8dee8; border-radius: 6px; padding: 10px 12px; min-width: 112px; }}
.metric b {{ display: block; font-size: 19px; }} .filters {{ display: grid; grid-template-columns: 2fr repeat(3, 1fr); gap: 10px; margin: 18px 0; }}
input, select {{ width: 100%; box-sizing: border-box; padding: 8px; border: 1px solid #9aa7b8; border-radius: 4px; background: #fff; color: inherit; }}
.table-wrap {{ overflow-x: auto; background: #fff; border: 1px solid #d8dee8; border-radius: 6px; }} table {{ width: 100%; border-collapse: collapse; }}
th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid #e5e9f0; vertical-align: top; }} th {{ background: #eef2f7; font-size: 12px; }}
.ready {{ color: #146c43; }} .blocked {{ color: #b42318; }} .advisory {{ color: #8a5700; }} #empty {{ display: none; padding: 16px; }}
</style></head><body><main>
<h1>Skill Capability Scorecard</h1><div id="status"></div><div class="summary" id="summary"></div>
<div class="filters"><input data-testid="capability-search" id="search" type="search" placeholder="Search skills, objectives, artifacts">
<select data-testid="domain-filter" id="domain"><option value="">All domains</option></select>
<select data-testid="risk-filter" id="risk"><option value="">All risk tiers</option></select>
<select data-testid="readiness-filter" id="readiness"><option value="">All readiness</option></select></div>
<div class="table-wrap"><table><thead><tr><th>Skill</th><th>Domain</th><th>Risk</th><th>Readiness</th><th>Scripts</th><th>Verification</th><th>Artifacts</th></tr></thead><tbody id="rows"></tbody></table><div id="empty">No capabilities match these filters.</div></div>
</main><script id="scorecard-data" type="application/json">{data}</script><script>
const payload = JSON.parse(document.getElementById('scorecard-data').textContent);
const rows = document.getElementById('rows'); const empty = document.getElementById('empty');
const search = document.getElementById('search'); const domain = document.getElementById('domain'); const risk = document.getElementById('risk'); const readiness = document.getElementById('readiness');
function options(element, values) {{ for (const value of [...new Set(values)].sort()) {{ const option = document.createElement('option'); option.value = value; option.textContent = value; element.appendChild(option); }} }}
options(domain, payload.capabilities.map(item => item.domain)); options(risk, payload.capabilities.map(item => item.risk_tier)); options(readiness, payload.capabilities.map(item => item.readiness));
function td(tr, value, className = '') {{ const cell = document.createElement('td'); cell.textContent = String(value || ''); if (className) cell.className = className; tr.appendChild(cell); }}
function filterRows() {{ const query = search.value.trim().toLowerCase(); const visible = payload.capabilities.filter(item => {{ const text = [item.skill, item.domain, item.objective, ...(item.output_artifacts || [])].join(' ').toLowerCase(); return (!query || text.includes(query)) && (!domain.value || item.domain === domain.value) && (!risk.value || item.risk_tier === risk.value) && (!readiness.value || item.readiness === readiness.value); }}); rows.replaceChildren(); for (const item of visible) {{ const tr = document.createElement('tr'); td(tr, item.skill); td(tr, item.domain); td(tr, item.risk_tier); td(tr, item.readiness, item.readiness); td(tr, item.script_count); td(tr, item.verification_owner); td(tr, (item.output_artifacts || []).join(', ')); rows.appendChild(tr); }} empty.style.display = visible.length ? 'none' : 'block'; }}
for (const control of [search, domain, risk, readiness]) control.addEventListener('input', filterRows); document.getElementById('status').textContent = `Status: ${{payload.status}}`; const metrics = payload.summary; document.getElementById('summary').replaceChildren(...Object.entries(metrics).map(([key, value]) => {{ const box = document.createElement('div'); box.className = 'metric'; const number = document.createElement('b'); number.textContent = value; box.append(number, document.createTextNode(key.replaceAll('_', ' '))); return box; }})); filterRows();
</script></body></html>"""


def emit_artifacts(output_dir: Path, payload: dict[str, Any]) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "json": output_dir / "skill-scorecard.json",
        "markdown": output_dir / "SKILL-SCORECARD.md",
        "html": output_dir / "skill-scorecard.html",
    }
    artifacts["json"].write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifacts["markdown"].write_text(render_markdown(payload), encoding="utf-8")
    artifacts["html"].write_text(render_html(payload), encoding="utf-8")
    return {name: str(path) for name, path in artifacts.items()}


def resolve_output_dir(skills_root: Path, output_dir: Path | None) -> Path:
    repo_root = skills_root.resolve().parent
    candidate = (output_dir if output_dir is not None else repo_root / ".codex" / "quality").expanduser().resolve()
    if candidate != repo_root and repo_root not in candidate.parents:
        raise ValueError("output directory must remain inside the repository root")
    return candidate


def audit_skill_pack(skills_root: Path, *, output_dir: Path | None = None, write_artifacts: bool = True, strict: bool = False) -> dict[str, Any]:
    root = skills_root.expanduser().resolve()
    findings: list[dict[str, str]] = []
    if not root.is_dir():
        finding(findings, "error", "skills_root_missing", "skills_root", str(root))
        return {"status": "fail", "summary": {"skills": 0, "scripts": 0, "enforced": 0, "ready": 0, "findings": 1}, "capabilities": [], "scripts": [], "findings": findings}

    manifest_path = root / ".system" / "manifest.json"
    matrix_path = root / ".system" / "skill-capabilities.json"
    try:
        manifest = read_json(manifest_path)
    except Exception as exc:
        manifest = {}
        finding(findings, "error", "manifest_unreadable", "manifest", str(exc))
    try:
        matrix = read_json(matrix_path)
    except Exception as exc:
        matrix = {}
        finding(findings, "error", "matrix_unreadable", "matrix", str(exc))

    manifest_skills = set(manifest.get("skills", [])) if isinstance(manifest.get("skills", []), list) else set()
    capabilities_raw = matrix.get("capabilities", []) if isinstance(matrix, dict) else []
    shared_raw = matrix.get("shared_components", []) if isinstance(matrix, dict) else []
    if not isinstance(matrix, dict) or matrix.get("schema_version") != SCHEMA_VERSION:
        finding(findings, "error", "matrix_schema_invalid", "matrix", f"schema_version must be {SCHEMA_VERSION}")
    if not isinstance(capabilities_raw, list):
        capabilities_raw = []
        finding(findings, "error", "capabilities_invalid", "matrix", "capabilities must be an array")
    if not isinstance(shared_raw, list):
        shared_raw = []
        finding(findings, "error", "shared_components_invalid", "matrix", "shared_components must be an array")

    capabilities: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(capabilities_raw):
        scope = f"capabilities[{index}]"
        if not isinstance(item, dict):
            finding(findings, "error", "capability_invalid", scope, "entry must be an object")
            continue
        skill = item.get("skill")
        if not isinstance(skill, str) or not skill:
            finding(findings, "error", "capability_skill_invalid", scope, "skill must be a non-empty string")
            continue
        if skill in capabilities:
            finding(findings, "error", "capability_duplicate", skill, "skill has more than one capability entry")
            continue
        capabilities[skill] = item
        missing = [field for field in REQUIRED_CAPABILITY_FIELDS if field not in item]
        if missing:
            finding(findings, "error", "capability_fields_missing", skill, ", ".join(missing))
        if item.get("risk_tier") not in RISK_TIERS:
            finding(findings, "error", "risk_tier_invalid", skill, "risk_tier must be advisory or enforced")
        if not isinstance(item.get("triggers"), list) or not item.get("triggers"):
            finding(findings, "error", "triggers_invalid", skill, "triggers must be a non-empty array")
        if not isinstance(item.get("tool_classes"), list) or not set(item.get("tool_classes", [])).issubset(TOOL_CLASSES):
            finding(findings, "error", "tool_classes_invalid", skill, "tool_classes must contain known classifications")
        resources = item.get("resources")
        if not isinstance(resources, dict):
            finding(findings, "error", "resources_invalid", skill, "resources must be an object")
            resources = {}
        skill_root = root / skill
        for field in RESOURCE_FIELDS:
            values = resources.get(field, [])
            if not isinstance(values, list):
                finding(findings, "error", "resource_list_invalid", skill, f"resources.{field} must be an array")
                continue
            for resource in values:
                try:
                    resolved = resolve_relative(skill_root, str(resource))
                except ValueError:
                    finding(findings, "error", "resource_path_unsafe", skill, f"resources.{field} contains unsafe path")
                    continue
                if not resolved.exists():
                    finding(findings, "error", "resource_missing", skill, f"{field} resource not found: {resource}")
        verification = item.get("verification")
        owner = verification.get("owner") if isinstance(verification, dict) else None
        if not validation_owner_exists(root, owner):
            finding(findings, "error", "verification_owner_missing", skill, "verification.owner must reference an existing file")

    shared_components: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(shared_raw):
        scope = f"shared_components[{index}]"
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"]:
            finding(findings, "error", "shared_component_invalid", scope, "shared component requires name")
            continue
        name = item["name"]
        if name in shared_components:
            finding(findings, "error", "shared_component_duplicate", name, "name must be unique")
            continue
        shared_components[name] = item
        for declared in component_paths(item):
            try:
                resolved = resolve_relative(root, declared)
            except ValueError:
                finding(findings, "error", "resource_path_unsafe", name, "shared script path is unsafe")
                continue
            if not resolved.exists():
                finding(findings, "error", "resource_missing", name, f"shared script path not found: {declared}")
        verification = item.get("verification", {})
        if not validation_owner_exists(root, verification.get("owner") if isinstance(verification, dict) else None):
            finding(findings, "error", "verification_owner_missing", name, "verification.owner must reference an existing file")

    discovered = managed_skill_directories(root)
    for skill in sorted(manifest_skills - set(capabilities)):
        finding(findings, "error", "capability_missing", skill, "manifest skill has no capability entry")
    for skill in sorted(set(capabilities) - manifest_skills):
        finding(findings, "error", "capability_not_manifested", skill, "capability is not listed in manifest")
    for skill in sorted(discovered - set(capabilities)):
        finding(findings, "error", "skill_not_matrixed", skill, "SKILL.md exists without exactly one capability entry")
    for skill in sorted(manifest_skills - discovered):
        finding(findings, "error", "manifest_skill_missing", skill, "manifest skill directory or SKILL.md is missing")

    registry_rows = parse_registry_rows(root / ".system" / "REGISTRY.md")
    for row in registry_rows:
        if row["owner"] in capabilities:
            expected = root / row["owner"] / "scripts" / row["script"]
            if not expected.exists():
                finding(findings, "error", "registry_script_missing", row["owner"], f"registered script missing: {row['script']}")
        elif row["owner"] not in {"tests", ".system"}:
            finding(findings, "warn", "registry_owner_unknown", row["owner"], f"registry owner is not capability-managed: {row['script']}")

    scripts: list[dict[str, Any]] = []
    by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in collect_scripts(root):
        rel = path.relative_to(root).as_posix()
        owner_name, owner = component_for_script(root, path, capabilities, shared_components)
        classes = classify_script(path)
        script = {"path": redact_text(rel), "owner": owner_name, "classes": classes}
        scripts.append(script)
        if owner_name is None or owner is None:
            finding(findings, "error", "script_owner_missing", rel, "script has no capability or shared-component owner")
            continue
        by_owner[owner_name].append(script)
        declared = set(owner.get("tool_classes", []))
        missing_classes = sorted(set(classes) - declared)
        if missing_classes:
            finding(findings, "error", "script_class_undeclared", owner_name, f"{rel} requires: {', '.join(missing_classes)}")
        if set(classes) & HIGH_RISK_CLASSES:
            if owner.get("risk_tier") != "enforced":
                finding(findings, "error", "high_risk_requires_enforced_tier", owner_name, f"{rel} is classified as {', '.join(classes)}")
            if not is_policy_complete(owner.get("security_policy")):
                finding(findings, "error", "security_policy_incomplete", owner_name, "high-risk component needs network, path_scope, redact_outputs, and notes")

    capability_rows: list[dict[str, Any]] = []
    for skill in sorted(capabilities):
        item = capabilities[skill]
        verification = item.get("verification", {}) if isinstance(item.get("verification"), dict) else {}
        capability_rows.append(
            {
                "skill": skill,
                "domain": item.get("domain", "unknown"),
                "objective": redact_text(str(item.get("objective", ""))),
                "risk_tier": item.get("risk_tier", "invalid"),
                "readiness": readiness_for(skill, findings),
                "script_count": len(by_owner.get(skill, [])),
                "tool_classes": item.get("tool_classes", []),
                "output_artifacts": item.get("output_artifacts", []),
                "verification_owner": verification.get("owner", ""),
            }
        )

    errors = [item for item in findings if item["severity"] == "error"]
    warnings = [item for item in findings if item["severity"] == "warn"]
    status = "fail" if errors else ("warn" if warnings else "pass")
    if strict and warnings and not errors:
        status = "fail"
    summary = {
        "skills": len(capabilities),
        "scripts": len(scripts),
        "enforced": sum(1 for item in capabilities.values() if item.get("risk_tier") == "enforced"),
        "ready": sum(1 for item in capability_rows if item["readiness"] == "ready"),
        "findings": len(findings),
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "summary": summary,
        "capabilities": capability_rows,
        "scripts": scripts,
        "findings": findings,
    }
    if write_artifacts:
        output = resolve_output_dir(root, output_dir)
        payload["artifacts"] = emit_artifacts(output, payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the skill capability matrix and produce an offline scorecard.")
    parser.add_argument("--skills-root", default="", help="Skills root. Defaults to repository skills/.")
    parser.add_argument("--output-dir", default="", help="Output directory under the repository root (default: .codex/quality).")
    parser.add_argument("--no-write", action="store_true", help="Validate without writing scorecard artifacts.")
    parser.add_argument("--strict", action="store_true", help="Treat advisory findings as failure.")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.skills_root) if args.skills_root else default_skills_root()
    output = Path(args.output_dir) if args.output_dir else None
    try:
        payload = audit_skill_pack(root, output_dir=output, write_artifacts=not args.no_write, strict=args.strict)
    except ValueError as exc:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "summary": {"skills": 0, "scripts": 0, "enforced": 0, "ready": 0, "findings": 1},
            "capabilities": [],
            "scripts": [],
            "findings": [{"severity": "error", "code": "output_path_unsafe", "scope": "output_dir", "detail": str(exc)}],
        }
    if args.format == "text":
        print(render_markdown(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "pass" or (payload["status"] == "warn" and not args.strict) else 1


if __name__ == "__main__":
    sys.exit(main())
