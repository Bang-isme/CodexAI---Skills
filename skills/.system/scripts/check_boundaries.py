#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Iterable

import yaml


SKILLS_ROOT = Path(__file__).resolve().parents[2]
AGENTS_ROOT = SKILLS_ROOT / ".agents"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


@dataclass(frozen=True)
class AgentSpec:
    name: str
    description: str
    skills: tuple[str, ...]
    file_ownership: tuple[str, ...]
    path: Path


def normalize_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def parse_frontmatter(path: Path) -> dict[str, object]:
    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        raise ValueError(f"{path} is missing YAML frontmatter")
    payload = yaml.safe_load(match.group(1))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} frontmatter must be a YAML object")
    return payload


def load_agent(agent_name: str, agents_root: Path = AGENTS_ROOT) -> AgentSpec:
    path = agents_root / f"{agent_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Agent file not found: {path}")

    payload = parse_frontmatter(path)
    skills = payload.get("skills")
    file_ownership = payload.get("file_ownership")
    if not isinstance(payload.get("name"), str):
        raise ValueError(f"{path} frontmatter missing string 'name'")
    if not isinstance(payload.get("description"), str):
        raise ValueError(f"{path} frontmatter missing string 'description'")
    if not isinstance(skills, list) or not all(isinstance(item, str) for item in skills):
        raise ValueError(f"{path} frontmatter 'skills' must be a list of strings")
    if not isinstance(file_ownership, list) or not all(isinstance(item, str) for item in file_ownership):
        raise ValueError(f"{path} frontmatter 'file_ownership' must be a list of strings")

    return AgentSpec(
        name=payload["name"],
        description=payload["description"],
        skills=tuple(skills),
        file_ownership=tuple(file_ownership),
        path=path,
    )


def load_all_agents(agents_root: Path = AGENTS_ROOT) -> list[AgentSpec]:
    if not agents_root.exists():
        return []
    agents: list[AgentSpec] = []
    for path in sorted(agents_root.glob("*.md")):
        agents.append(load_agent(path.stem, agents_root))
    return agents


def pattern_variants(pattern: str) -> set[str]:
    variants = {normalize_path(pattern)}
    if "/**/" in pattern:
        variants.add(normalize_path(pattern).replace("/**/", "/"))
    return {variant for variant in variants if variant}


def matches_pattern(file_path: str, pattern: str) -> bool:
    normalized_file = normalize_path(file_path)
    pure_path = PurePosixPath(normalized_file)
    for candidate in pattern_variants(pattern):
        if pure_path.match(candidate) or fnmatchcase(normalized_file, candidate):
            return True
    return False


def matching_patterns(file_path: str, agent: AgentSpec) -> list[str]:
    return [pattern for pattern in agent.file_ownership if matches_pattern(file_path, pattern)]


def specificity(pattern: str) -> tuple[int, int, int, int]:
    normalized = normalize_path(pattern)
    wildcard_count = sum(normalized.count(token) for token in ("*", "?", "["))
    literal_chars = sum(1 for char in normalized if char not in "*?[]")
    return (literal_chars, normalized.count("/"), -wildcard_count, len(normalized))


def suggest_handoff(file_path: str, current_agent: str, agents_root: Path = AGENTS_ROOT) -> str | None:
    candidates: list[tuple[tuple[int, int, int, int], str]] = []
    for agent in load_all_agents(agents_root):
        if agent.name == current_agent:
            continue
        patterns = matching_patterns(file_path, agent)
        if patterns:
            best_pattern = max(patterns, key=specificity)
            candidates.append((specificity(best_pattern), agent.name))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates[0][1]


def build_report(agent_name: str, files: Iterable[str], agents_root: Path = AGENTS_ROOT) -> dict[str, object]:
    agent = load_agent(agent_name, agents_root)
    files_allowed: list[str] = []
    files_blocked: list[str] = []
    suggested_handoff: dict[str, str] = {}

    for file_path in [normalize_path(item) for item in files if normalize_path(item)]:
        if matching_patterns(file_path, agent):
            files_allowed.append(file_path)
            continue
        files_blocked.append(file_path)
        suggestion = suggest_handoff(file_path, agent.name, agents_root)
        if suggestion:
            suggested_handoff[file_path] = suggestion

    return {
        "agent": agent.name,
        "files_allowed": files_allowed,
        "files_blocked": files_blocked,
        "suggested_handoff": suggested_handoff,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether changed files stay inside an agent's ownership boundary.")
    parser.add_argument("--agent", required=True, help="Agent name from skills/.agents without the .md suffix.")
    parser.add_argument(
        "--files",
        required=True,
        help="Comma-separated list of relative file paths to validate against file_ownership globs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args.agent, args.files.split(","))
    except Exception as exc:  # pragma: no cover - exercised via CLI error path
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
