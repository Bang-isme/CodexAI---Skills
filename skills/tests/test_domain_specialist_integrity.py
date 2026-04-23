from __future__ import annotations

import re
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_SKILL = SKILLS_ROOT / "codex-domain-specialist"
SECURITY_SKILL = SKILLS_ROOT / "codex-security-specialist"
SKILL_MD = DOMAIN_SKILL / "SKILL.md"
OUTPUT_GATES = DOMAIN_SKILL / "references" / "output-quality-gates.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_domain_specialist_referenced_reference_files_exist() -> None:
    skill = read(SKILL_MD)
    referenced = set(re.findall(r"`references/([^`]+\.md)`", skill))
    existing = {path.name for path in (DOMAIN_SKILL / "references").glob("*.md")}

    missing = sorted(name for name in referenced if name not in existing)
    assert not missing, f"Missing codex-domain-specialist references: {missing}"


def test_domain_specialist_enforces_scope_fit_before_complexity() -> None:
    skill = read(SKILL_MD)

    assert "Scope-fit enforcement" in skill
    assert "Why simpler option fails" in skill
    assert "Do not add a new dependency, service, worker, cache, queue" in skill


def test_output_quality_gate_contains_anti_overengineering_guardrails() -> None:
    gates = read(OUTPUT_GATES)

    assert "Scope Fit Gate (Anti-Overengineering)" in gates
    assert "Complexity Budget" in gates
    assert "future flexibility" in gates
    assert "Did you add a dependency, queue, cache, service, or abstraction without evidence?" in gates


def test_security_specialist_referenced_reference_files_exist() -> None:
    skill = read(SECURITY_SKILL / "SKILL.md")
    referenced = set(re.findall(r"`references/([^`]+\.md)`", skill))
    existing = {path.name for path in (SECURITY_SKILL / "references").glob("*.md")}

    missing = sorted(name for name in referenced if name not in existing)
    assert not missing, f"Missing codex-security-specialist references: {missing}"


def test_security_specialist_uses_proportional_controls() -> None:
    skill = read(SECURITY_SKILL / "SKILL.md")

    assert "proportional defense-in-depth" in skill
    assert "Security scope-fit enforcement" in skill
    assert "Why simpler control is insufficient" in skill
    assert "not the largest possible security stack" in skill
