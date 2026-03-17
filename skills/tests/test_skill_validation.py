from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


quick_validate = load_script_module(
    "skills_quick_validate",
    ".system/skill-creator/scripts/quick_validate.py",
)


def test_quick_validate_accepts_load_priority_frontmatter() -> None:
    valid, message = quick_validate.validate_skill(SKILLS_ROOT / "codex-execution-quality-gate")
    assert valid is True, message


def test_quick_validate_accepts_version_frontmatter() -> None:
    valid, message = quick_validate.validate_skill(SKILLS_ROOT / "codex-git-autopilot")
    assert valid is True, message


def test_quick_validate_still_rejects_unknown_frontmatter_key(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bad-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: bad-skill\ndescription: Example skill\nsurprise: nope\n---\n\n# Bad Skill\n",
        encoding="utf-8",
        newline="\n",
    )

    valid, message = quick_validate.validate_skill(skill_dir)
    assert valid is False
    assert "Unexpected key(s)" in message
