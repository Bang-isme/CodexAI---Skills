#!/usr/bin/env python3
"""
Shared helpers for the Scrum subagent bundle.
"""
from __future__ import annotations

import json
import shutil
import tomllib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


REQUIRED_DIRS = ("agents", "workflows", "services")
REQUIRED_ROOT_FILES = ("ARCHITECTURE.md", "README.md")
REQUIRED_SERVICE_FILES = ("agents.json", "workflows.json", "commands.json")
STAMP_FILE = ".codexai-scrum-kit.json"
PROJECT_NATIVE_AGENTS_REL = Path(".codex") / "agents"
NATIVE_AGENT_PREFIX = "scrum-"


@dataclass(frozen=True)
class BundleStats:
    agent_files: int
    workflow_files: int
    service_files: int
    native_agent_files: int
    total_files: int


def relative_posix(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def iter_tree_files(root: Path) -> List[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def iter_bundle_files(root: Path) -> List[Path]:
    return iter_tree_files(root)


def missing_required_paths(bundle_root: Path) -> List[str]:
    missing = []
    for rel_path in REQUIRED_DIRS:
        if not (bundle_root / rel_path).exists():
            missing.append(rel_path)
    for rel_path in REQUIRED_ROOT_FILES:
        if not (bundle_root / rel_path).exists():
            missing.append(rel_path)
    for rel_path in REQUIRED_SERVICE_FILES:
        if not (bundle_root / "services" / rel_path).exists():
            missing.append(f"services/{rel_path}")
    return missing


def ensure_target_root(target_root: Path) -> None:
    if not target_root.exists():
        raise FileNotFoundError(f"Target root does not exist: {target_root}")
    if not target_root.is_dir():
        raise NotADirectoryError(f"Target root is not a directory: {target_root}")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def file_digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def parse_frontmatter(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError(f"{path.name}: missing frontmatter opening fence")

    frontmatter_lines: List[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        frontmatter_lines.append(line)
    else:
        raise ValueError(f"{path.name}: missing frontmatter closing fence")

    data: Dict[str, str] = {}
    current_key: str | None = None
    for raw_line in frontmatter_lines:
        if not raw_line.strip():
            continue
        if raw_line.startswith("  - ") and current_key:
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        current_key = key.strip()
        data[current_key] = value.strip().strip('"').strip("'")
    return data


def strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return text.strip()
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1 :]).strip()
    return text.strip()


def validate_markdown_descriptors(paths: Sequence[Path], expected_kind: str) -> List[str]:
    errors: List[str] = []
    for path in paths:
        try:
            frontmatter = parse_frontmatter(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        for key in ("name", "description"):
            if not frontmatter.get(key):
                errors.append(f"{expected_kind}/{path.name}: missing '{key}' in frontmatter")
    return errors


def validate_services(bundle_root: Path) -> List[str]:
    errors: List[str] = []
    agents_manifest = bundle_root / "services" / "agents.json"
    workflows_manifest = bundle_root / "services" / "workflows.json"
    commands_manifest = bundle_root / "services" / "commands.json"

    try:
        agents = read_json(agents_manifest)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"services/agents.json: {exc}"]
    try:
        workflows = read_json(workflows_manifest)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"services/workflows.json: {exc}"]
    try:
        commands = read_json(commands_manifest)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"services/commands.json: {exc}"]

    if not isinstance(agents, list):
        errors.append("services/agents.json: root must be a list")
        agents = []
    if not isinstance(workflows, list):
        errors.append("services/workflows.json: root must be a list")
        workflows = []
    if not isinstance(commands, list):
        errors.append("services/commands.json: root must be a list")
        commands = []

    agent_names = sorted(path.stem for path in (bundle_root / "agents").glob("*.md"))
    workflow_names = sorted(path.stem for path in (bundle_root / "workflows").glob("*.md"))

    manifest_agent_names: List[str] = []
    for index, item in enumerate(agents):
        if not isinstance(item, dict):
            errors.append(f"services/agents.json[{index}]: item must be an object")
            continue
        name = item.get("name")
        description = item.get("description")
        skills = item.get("skills")
        if not isinstance(name, str) or not name:
            errors.append(f"services/agents.json[{index}]: missing string 'name'")
            continue
        manifest_agent_names.append(name)
        if not isinstance(description, str) or not description:
            errors.append(f"services/agents.json[{index}]: missing string 'description'")
        if not isinstance(skills, list):
            errors.append(f"services/agents.json[{index}]: 'skills' must be a list")

    manifest_workflow_names: List[str] = []
    for index, item in enumerate(workflows):
        if not isinstance(item, dict):
            errors.append(f"services/workflows.json[{index}]: item must be an object")
            continue
        command = item.get("command")
        description = item.get("description")
        if not isinstance(command, str) or not command.startswith("/"):
            errors.append(f"services/workflows.json[{index}]: 'command' must start with '/'")
            continue
        manifest_workflow_names.append(command[1:])
        if not isinstance(description, str) or not description:
            errors.append(f"services/workflows.json[{index}]: missing string 'description'")

    if sorted(manifest_agent_names) != agent_names:
        errors.append("services/agents.json: manifest names do not match agents/*.md")
    if sorted(manifest_workflow_names) != workflow_names:
        errors.append("services/workflows.json: manifest commands do not match workflows/*.md")

    valid_alias_targets = set(agent_names) | set(workflow_names) | {
        "codex-scrum-subagents.install",
        "codex-scrum-subagents.diff",
        "codex-scrum-subagents.update",
        "codex-scrum-subagents.validate",
    }
    seen_commands: set[str] = set()
    for index, item in enumerate(commands):
        if not isinstance(item, dict):
            errors.append(f"services/commands.json[{index}]: item must be an object")
            continue
        command = item.get("command")
        alias_for = item.get("alias_for")
        description = item.get("description")
        if not isinstance(command, str) or not command.startswith("$"):
            errors.append(f"services/commands.json[{index}]: 'command' must start with '$'")
            continue
        if command in seen_commands:
            errors.append(f"services/commands.json[{index}]: duplicate command '{command}'")
        seen_commands.add(command)
        if not isinstance(alias_for, str) or alias_for not in valid_alias_targets:
            errors.append(
                f"services/commands.json[{index}]: 'alias_for' must reference a known workflow, agent, or installer action"
            )
        if not isinstance(description, str) or not description:
            errors.append(f"services/commands.json[{index}]: missing string 'description'")

    return errors


def native_agent_filename(agent_name: str) -> str:
    stem = agent_name if agent_name.startswith(NATIVE_AGENT_PREFIX) else f"{NATIVE_AGENT_PREFIX}{agent_name}"
    return f"{stem}.toml"


def project_codex_agents_root(target_root: Path) -> Path:
    return target_root / PROJECT_NATIVE_AGENTS_REL


def personal_codex_agents_root() -> Path:
    return Path.home() / ".codex" / "agents"


def load_agent_manifest(bundle_root: Path) -> List[Dict[str, object]]:
    payload = read_json(bundle_root / "services" / "agents.json")
    if not isinstance(payload, list):
        raise ValueError("services/agents.json: root must be a list")
    items: List[Dict[str, object]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"services/agents.json[{index}]: item must be an object")
        items.append(item)
    return items


def render_native_agent_prompt(agent_name: str, description: str, skills: Sequence[str], role_brief: str) -> str:
    skill_lines = "\n".join(f"- {skill}" for skill in skills) if skills else "- rely on the local CodexAI skills available in the session"
    return "\n".join(
        [
            f"You are the Codex Scrum custom agent `{native_agent_filename(agent_name)[:-5]}`.",
            "",
            f"Role summary: {description}",
            "",
            "Operating rules:",
            "- Stay inside this Scrum role instead of absorbing every responsibility.",
            "- Make handoffs explicit when another role should take over.",
            "- Prefer concrete artifacts, acceptance criteria, risks, and evidence over generic advice.",
            "",
            "Preferred local skills when they are available in the session:",
            skill_lines,
            "",
            "Role brief:",
            role_brief.strip(),
        ]
    ).strip()


def render_native_agent_toml(name: str, description: str, developer_instructions: str) -> str:
    if "'''" in developer_instructions:
        raise ValueError("Native agent developer_instructions cannot contain triple single quotes")
    return "\n".join(
        [
            f"name = {json.dumps(name, ensure_ascii=False)}",
            f"description = {json.dumps(description, ensure_ascii=False)}",
            "developer_instructions = '''",
            developer_instructions.rstrip(),
            "'''",
            "",
        ]
    )


def native_agent_specs(bundle_root: Path) -> Dict[str, str]:
    manifest = {str(item.get("name")): item for item in load_agent_manifest(bundle_root)}
    specs: Dict[str, str] = {}
    for path in sorted((bundle_root / "agents").glob("*.md")):
        frontmatter = parse_frontmatter(path)
        agent_name = frontmatter["name"]
        manifest_item = manifest.get(agent_name, {})
        description = str(manifest_item.get("description") or frontmatter.get("description") or "").strip()
        if not description:
            raise ValueError(f"agents/{path.name}: missing description for native custom agent rendering")
        raw_skills = manifest_item.get("skills")
        skills = [str(item) for item in raw_skills] if isinstance(raw_skills, list) else []
        role_brief = strip_frontmatter(path.read_text(encoding="utf-8"))
        prompt = render_native_agent_prompt(agent_name, description, skills, role_brief)
        native_name = native_agent_filename(agent_name)[:-5]
        specs[native_agent_filename(agent_name)] = render_native_agent_toml(native_name, description, prompt)
    return specs


def validate_native_agent_specs(bundle_root: Path) -> List[str]:
    errors: List[str] = []
    try:
        specs = native_agent_specs(bundle_root)
    except ValueError as exc:
        return [str(exc)]

    for filename, content in specs.items():
        try:
            payload = tomllib.loads(content)
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"native-agents/{filename}: invalid TOML ({exc})")
            continue
        name = payload.get("name")
        description = payload.get("description")
        developer_instructions = payload.get("developer_instructions")
        unsupported = sorted(set(payload) - {"name", "description", "developer_instructions", "sandbox_mode", "model", "model_reasoning_effort", "mcp_servers", "skills", "nickname_candidates"})
        if unsupported:
            errors.append(f"native-agents/{filename}: unsupported field(s): {', '.join(unsupported)}")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"native-agents/{filename}: missing non-empty 'name'")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"native-agents/{filename}: missing non-empty 'description'")
        if not isinstance(developer_instructions, str) or not developer_instructions.strip():
            errors.append(f"native-agents/{filename}: missing non-empty 'developer_instructions'")
    return errors


def iter_pack_native_agent_files(install_root: Path) -> List[Path]:
    if not install_root.exists():
        return []
    return sorted(path for path in install_root.glob("*.toml") if path.is_file() and path.name.startswith(NATIVE_AGENT_PREFIX))


def compare_native_agents_to_install(bundle_root: Path, install_root: Path) -> Dict[str, object]:
    source_specs = native_agent_specs(bundle_root)
    installed_files = {path.name: path for path in iter_pack_native_agent_files(install_root)}

    missing = sorted(set(source_specs) - set(installed_files))
    extra = sorted(set(installed_files) - set(source_specs))
    changed: List[str] = []
    same: List[str] = []

    for rel_path in sorted(set(source_specs) & set(installed_files)):
        if text_digest(source_specs[rel_path]) == file_digest(installed_files[rel_path]):
            same.append(rel_path)
        else:
            changed.append(rel_path)

    return {
        "missing": missing,
        "changed": changed,
        "same": same,
        "extra": extra,
        "bundle_files": len(source_specs),
        "installed_files": len(installed_files),
        "install_root": str(install_root),
    }


def detect_native_agent_conflicts(bundle_root: Path, install_root: Path) -> List[str]:
    diff = compare_native_agents_to_install(bundle_root, install_root)
    return sorted(set(diff["changed"]) | set(diff["same"]))  # type: ignore[arg-type]


def copy_native_agents(
    bundle_root: Path,
    install_root: Path,
    relative_paths: Iterable[str],
    dry_run: bool = False,
) -> int:
    specs = native_agent_specs(bundle_root)
    copied_files = 0
    for rel_path in relative_paths:
        if rel_path not in specs:
            raise FileNotFoundError(f"Native agent not found in source specs: {rel_path}")
        copied_files += 1
        if dry_run:
            continue
        target_path = install_root / Path(rel_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(specs[rel_path], encoding="utf-8", newline="\n")
    return copied_files


def collect_bundle_stats(bundle_root: Path) -> BundleStats:
    files = iter_bundle_files(bundle_root)
    native_agent_files = len(native_agent_specs(bundle_root))
    return BundleStats(
        agent_files=len(list((bundle_root / "agents").glob("*.md"))),
        workflow_files=len(list((bundle_root / "workflows").glob("*.md"))),
        service_files=len(list((bundle_root / "services").glob("*.json"))),
        native_agent_files=native_agent_files,
        total_files=len(files) + native_agent_files,
    )


def validate_bundle(bundle_root: Path) -> Dict[str, object]:
    errors: List[str] = []
    warnings: List[str] = []
    missing = missing_required_paths(bundle_root)
    if missing:
        errors.extend(f"missing required path: {item}" for item in missing)

    agent_paths = sorted((bundle_root / "agents").glob("*.md"))
    workflow_paths = sorted((bundle_root / "workflows").glob("*.md"))
    errors.extend(validate_markdown_descriptors(agent_paths, "agents"))
    errors.extend(validate_markdown_descriptors(workflow_paths, "workflows"))
    errors.extend(validate_services(bundle_root))

    native_specs: Dict[str, str] = {}
    native_errors = validate_native_agent_specs(bundle_root)
    if native_errors:
        errors.extend(native_errors)
    else:
        native_specs = native_agent_specs(bundle_root)

    stats = BundleStats(
        agent_files=len(agent_paths),
        workflow_files=len(workflow_paths),
        service_files=len(list((bundle_root / "services").glob("*.json"))),
        native_agent_files=len(native_specs),
        total_files=len(iter_bundle_files(bundle_root)) + len(native_specs),
    )
    if stats.agent_files == 0:
        errors.append("bundle must contain at least one agent file")
    if stats.workflow_files == 0:
        errors.append("bundle must contain at least one workflow file")
    if native_specs and len(native_specs) != stats.agent_files:
        errors.append("generated native custom-agent count must match agents/*.md count")

    return {
        "status": "ok" if not errors else "error",
        "bundle_root": str(bundle_root),
        "bundle": asdict(stats),
        "errors": errors,
        "warnings": warnings,
    }


def compare_bundle_to_install(bundle_root: Path, install_root: Path) -> Dict[str, object]:
    bundle_files = {relative_posix(path, bundle_root): path for path in iter_bundle_files(bundle_root)}
    installed_files = {
        relative_posix(path, install_root): path
        for path in iter_tree_files(install_root)
        if relative_posix(path, install_root) != STAMP_FILE
    }

    missing = sorted(set(bundle_files) - set(installed_files))
    extra = sorted(set(installed_files) - set(bundle_files))
    changed: List[str] = []
    same: List[str] = []

    for rel_path in sorted(set(bundle_files) & set(installed_files)):
        if file_digest(bundle_files[rel_path]) == file_digest(installed_files[rel_path]):
            same.append(rel_path)
        else:
            changed.append(rel_path)

    return {
        "missing": missing,
        "changed": changed,
        "same": same,
        "extra": extra,
        "bundle_files": len(bundle_files),
        "installed_files": len(installed_files),
    }


def detect_conflicts(bundle_root: Path, install_root: Path) -> List[str]:
    diff = compare_bundle_to_install(bundle_root, install_root)
    return sorted(set(diff["changed"]) | set(diff["same"]))  # type: ignore[arg-type]


def copy_bundle_files(
    bundle_root: Path,
    install_root: Path,
    relative_paths: Iterable[str],
    dry_run: bool = False,
) -> int:
    copied_files = 0
    for rel_path in relative_paths:
        copied_files += 1
        if dry_run:
            continue
        source_path = bundle_root / Path(rel_path)
        target_path = install_root / Path(rel_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
    return copied_files


def copy_entire_bundle(bundle_root: Path, install_root: Path, dry_run: bool = False) -> int:
    return copy_bundle_files(
        bundle_root,
        install_root,
        [relative_posix(path, bundle_root) for path in iter_bundle_files(bundle_root)],
        dry_run=dry_run,
    )


def default_backup_root(target_root: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return target_root / ".codexai-backups" / f"scrum-agent-kit-{timestamp}"


def backup_existing_files(
    install_root: Path,
    backup_root: Path,
    relative_paths: Iterable[str],
    dry_run: bool = False,
) -> int:
    backed_up = 0
    for rel_path in relative_paths:
        source_path = install_root / Path(rel_path)
        if not source_path.exists():
            continue
        backed_up += 1
        if dry_run:
            continue
        target_path = backup_root / Path(rel_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
    return backed_up


def write_stamp(install_root: Path, target_root: Path, stats: BundleStats, force: bool, operation: str) -> Path:
    stamp_payload = {
        "kit": "codex-scrum-subagents",
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "force": force,
        "operation": operation,
        "bundle": asdict(stats),
        "target_root": str(target_root.resolve()),
        "codex_agents_root": str(project_codex_agents_root(target_root.resolve())),
        "project_codex_agents_rel": str(PROJECT_NATIVE_AGENTS_REL).replace("\\", "/"),
    }
    stamp_path = install_root / STAMP_FILE
    stamp_path.write_text(json.dumps(stamp_payload, indent=2), encoding="utf-8", newline="\n")
    return stamp_path


def read_stamp(install_root: Path) -> Dict[str, object]:
    stamp_path = install_root / STAMP_FILE
    if not stamp_path.exists():
        return {}
    try:
        payload = json.loads(stamp_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
