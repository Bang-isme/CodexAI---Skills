#!/usr/bin/env python3
"""Build a native Antigravity plugin package from canonical CodexAI skills."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    "node_modules",
    ".mypy_cache",
    "openai-docs",
    "plugin-creator",
    "imagegen",
}
SKIP_FILE_NAMES = {".codex-system-skills.marker"}
STRICT_SKILL_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
DOCUMENTED_TOOLS = [
    "view_file",
    "replace_file_content",
    "run_command",
    "grep_search",
    "glob_search",
]
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
LOAD_PRIORITY_RE = re.compile(r"^load_priority:\s*(.+)$", re.MULTILINE)
VERSION_RE = re.compile(r"^version:\s*(.+)$", re.MULTILINE)


def default_plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Antigravity plugin files from canonical skills source.")
    parser.add_argument("--plugin-root", default="", help="CodexAI repo root")
    parser.add_argument("--output", default="", help="Output directory. Defaults to dist/antigravity-plugin")
    parser.add_argument("--apply", action="store_true", help="Write the package. Default is dry-run.")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_frontmatter(text: str) -> tuple[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end() :]


def parse_simple_frontmatter(block: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("'\"")
    return data


def dump_frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if key == "metadata" and isinstance(value, dict):
            lines.append("metadata:")
            for meta_key, meta_value in value.items():
                lines.append(f"  {meta_key}: {json.dumps(str(meta_value))}")
            continue
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
            continue
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def transform_skill_markdown(text: str) -> str:
    block, body = split_frontmatter(text)
    data = parse_simple_frontmatter(block)
    metadata = {}
    load_priority = data.pop("load_priority", None)
    version = data.pop("version", None)
    if load_priority:
        metadata["codexai-load-priority"] = load_priority.strip("'\"")
    if version:
        metadata["codexai-version"] = version.strip("'\"")
    extra_keys = [key for key in list(data) if key not in STRICT_SKILL_KEYS]
    for key in extra_keys:
        metadata[f"codexai-{key}"] = str(data.pop(key))
    if metadata:
        data["metadata"] = metadata
    kept = {key: data[key] for key in ("name", "description") if key in data}
    for key in ("license", "compatibility", "allowed-tools", "metadata"):
        if key in data:
            kept[key] = data[key]
    return dump_frontmatter(kept) + "\n" + body.lstrip("\n")


def transform_agent_markdown(text: str, name: str) -> str:
    block, body = split_frontmatter(text)
    data = parse_simple_frontmatter(block)
    description = str(data.get("description") or name)
    ownership = data.get("file_ownership") or ""
    tools = "\n".join(f"  - {tool}" for tool in DOCUMENTED_TOOLS)
    header = (
        f"---\nname: {name}\ndescription: {description}\ntools:\n{tools}\n---\n\n"
    )
    policy = (
        "\n## File ownership policy\n\n"
        "Antigravity agent frontmatter does not support `file_ownership`. Keep edits inside this policy:\n\n"
        f"- {ownership or 'project files owned by this role'}\n"
        "- Do not edit files outside this policy; hand off instead.\n"
    )
    if "File ownership policy" in body:
        policy = ""
    return header + body.lstrip("\n") + policy


def workflow_to_skill(text: str, skill_name: str) -> str:
    block, body = split_frontmatter(text)
    data = parse_simple_frontmatter(block)
    description = str(data.get("description") or data.get("name") or skill_name)
    loads = str(data.get("loads") or "").strip()
    trigger = str(data.get("trigger") or "")
    orchestration = ""
    if loads:
        orchestration = (
            "\n## Orchestration\n\n"
            f"Load these canonical skills in order (hosts do not resolve a `loads` field): {loads}\n"
        )
    if trigger:
        orchestration += f"\nSlash/alias trigger: `{trigger}`\n"
    header = dump_frontmatter({"name": skill_name, "description": description[:1024]})
    return header + "\n" + body.lstrip("\n") + orchestration


def should_skip(relative: str) -> bool:
    parts = relative.replace("\\", "/").split("/")
    if any(part in SKIP_DIR_NAMES for part in parts):
        return True
    if parts[-1] in SKIP_FILE_NAMES:
        return True
    if relative.startswith("skills/tests/") or relative == "skills/tests":
        return True
    if relative.startswith("skills/.agents/") or relative.startswith("skills/.workflows/"):
        return True
    if "openai" in parts and "docs" in parts:
        return True
    return False


def copy_skills(skills_root: Path, dest_skills: Path, apply: bool) -> list[str]:
    copied: list[str] = []
    for path in sorted(skills_root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(skills_root).as_posix()
        if should_skip("skills/" + rel):
            continue
        target = dest_skills / rel
        if path.name == "SKILL.md":
            text = transform_skill_markdown(read_text(path))
            if apply:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8", newline="\n")
            copied.append("skills/" + rel)
            continue
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        copied.append("skills/" + rel)
    return copied


def emit_agents(skills_root: Path, dest_agents: Path, apply: bool) -> list[str]:
    emitted: list[str] = []
    for path in sorted((skills_root / ".agents").glob("*.md")):
        name = path.stem
        text = transform_agent_markdown(read_text(path), name)
        target = dest_agents / name / "agent.md"
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
        emitted.append(f"agents/{name}/agent.md")
    kit = skills_root / "codex-scrum-subagents" / "assets" / "scrum-agent-kit" / "agents"
    if kit.is_dir():
        for path in sorted(kit.glob("*.md")):
            name = f"scrum-{path.stem}"
            if name == "scrum-scrum-master":
                name = "scrum-kit-master"
            if (dest_agents / path.stem).exists() or path.stem in {p.stem for p in (skills_root / ".agents").glob("*.md")}:
                if path.stem == "scrum-master":
                    name = "scrum-kit-master"
            text = transform_agent_markdown(read_text(path), name)
            target = dest_agents / name / "agent.md"
            if apply:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8", newline="\n")
            emitted.append(f"agents/{name}/agent.md")
    return emitted


def emit_workflow_skills(skills_root: Path, dest_skills: Path, apply: bool) -> list[str]:
    emitted: list[str] = []
    for path in sorted((skills_root / ".workflows").glob("*.md")):
        skill_name = f"workflow-{path.stem}"
        text = workflow_to_skill(read_text(path), skill_name)
        target = dest_skills / skill_name / "SKILL.md"
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
        emitted.append(f"skills/{skill_name}/SKILL.md")
    kit = skills_root / "codex-scrum-subagents" / "assets" / "scrum-agent-kit" / "workflows"
    if kit.is_dir():
        for path in sorted(kit.glob("*.md")):
            skill_name = f"workflow-{path.stem}"
            text = workflow_to_skill(read_text(path), skill_name)
            target = dest_skills / skill_name / "SKILL.md"
            if apply:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8", newline="\n")
            emitted.append(f"skills/{skill_name}/SKILL.md")
    return emitted


def build_package(plugin_root: Path, output: Path, apply: bool) -> dict[str, Any]:
    skills_root = plugin_root / "skills"
    template_root = plugin_root / "antigravity"
    if not skills_root.is_dir() or not template_root.is_dir():
        raise FileNotFoundError("skills/ and antigravity/ templates are required")
    copied = copy_skills(skills_root, output / "skills", apply)
    agents = emit_agents(skills_root, output / "agents", apply)
    workflows = emit_workflow_skills(skills_root, output / "skills", apply)
    plugin_src = read_text(template_root / "plugin.json")
    rules_src = read_text(template_root / "rules" / "codexai-core.md")
    hooks_src = read_text(template_root / "hooks.json")
    hook_script = read_text(template_root / "scripts" / "pre_tool_use.py")
    if apply:
        output.mkdir(parents=True, exist_ok=True)
        (output / "plugin.json").write_text(plugin_src if plugin_src.endswith("\n") else plugin_src + "\n", encoding="utf-8")
        (output / "rules").mkdir(parents=True, exist_ok=True)
        (output / "rules" / "codexai-core.md").write_text(rules_src, encoding="utf-8", newline="\n")
        (output / "hooks.json").write_text(hooks_src if hooks_src.endswith("\n") else hooks_src + "\n", encoding="utf-8")
        (output / "scripts").mkdir(parents=True, exist_ok=True)
        (output / "scripts" / "pre_tool_use.py").write_text(hook_script, encoding="utf-8", newline="\n")
        (output / "NATIVE_STATUS.txt").write_text(
            "native package candidate\nLive IDE+CLI smoke is required before claiming fully native.\n",
            encoding="utf-8",
        )
    return {
        "status": "generated" if apply else "dry_run",
        "plugin_root": str(plugin_root),
        "output": str(output),
        "skill_files": len(copied),
        "agents": agents,
        "workflow_skills": workflows,
        "skipped_workflows_dir": True,
        "native_status": "native package candidate",
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        plugin_root = Path(args.plugin_root).expanduser().resolve() if args.plugin_root else default_plugin_root()
        output = Path(args.output).expanduser().resolve() if args.output else plugin_root / "dist" / "antigravity-plugin"
        payload = build_package(plugin_root, output, apply=bool(args.apply))
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "text":
        print(f"{payload['status']}: agents={len(payload.get('agents') or [])} output={payload.get('output')}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") in {"dry_run", "generated"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
