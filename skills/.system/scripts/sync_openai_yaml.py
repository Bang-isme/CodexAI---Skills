#!/usr/bin/env python3
"""Generate missing agents/openai.yaml files from SKILL.md frontmatter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def display_name(skill: str) -> str:
    return skill.replace("codex-", "").replace("-", " ").title()


def yaml_for(skill: str, description: str) -> str:
    short = description[:140].rstrip(" .") + ("." if description else "")
    return (
        "interface:\n"
        f'  display_name: "{display_name(skill)}"\n'
        f'  short_description: "{short}"\n'
        f'  default_prompt: "Use ${skill} for this task. Load it before acting."\n'
    )


def sync(skills_root: Path, apply: bool) -> dict[str, Any]:
    written: list[str] = []
    skipped: list[str] = []
    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir() and path.name.startswith("codex-")):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        target = skill_dir / "agents" / "openai.yaml"
        if target.exists():
            skipped.append(skill_dir.name)
            continue
        description = parse_frontmatter(skill_md.read_text(encoding="utf-8")).get("description", f"Use when {skill_dir.name} applies.")
        content = yaml_for(skill_dir.name, description)
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")
        written.append(skill_dir.name)
    return {
        "status": "ok" if apply or written or skipped else "ok",
        "written": written,
        "skipped_existing": skipped,
        "apply": apply,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate missing agents/openai.yaml files from SKILL.md descriptions.")
    parser.add_argument("--skills-root", default="", help="Skills root. Defaults to this pack.")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skills_root = Path(args.skills_root).expanduser().resolve() if args.skills_root else Path(__file__).resolve().parents[2]
    payload = sync(skills_root, apply=args.apply)
    if args.format == "text":
        print(f"{payload['status']}: written={len(payload['written'])} skipped={len(payload['skipped_existing'])}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
