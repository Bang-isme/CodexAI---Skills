from __future__ import annotations

from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
MATRIX = SKILLS_ROOT / ".system" / "WORKFLOW_DISCIPLINE_MATRIX.md"
MASTER = SKILLS_ROOT / "codex-master-instructions" / "SKILL.md"
SUBAGENT = SKILLS_ROOT / "codex-subagent-execution" / "SKILL.md"
WORKFLOW = SKILLS_ROOT / "codex-workflow-autopilot" / "SKILL.md"


WORKFLOW_DISCIPLINES = [
    "skill invocation discipline",
    "brainstorming",
    "plan writing",
    "plan execution",
    "test-driven development",
    "systematic debugging",
    "verification before completion",
    "requesting code review",
    "receiving code review",
    "parallel agent dispatch",
    "subagent-driven development",
    "git worktree isolation",
    "branch finishing",
    "skill authoring",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_workflow_discipline_matrix_covers_core_capabilities() -> None:
    text = read(MATRIX)

    for discipline in WORKFLOW_DISCIPLINES:
        assert discipline in text
    assert "CodexAI Extensions" in text


def test_master_instructions_enforce_skill_invocation_rule() -> None:
    text = read(MASTER)

    assert "Skill Invocation Rule" in text
    assert "Do not skip a relevant skill because the task \"looks simple\"" in text
    assert "$brainstorm" in text
    assert "$review-feedback" in text


def test_subagent_execution_allows_only_safe_parallel_dispatch() -> None:
    text = read(SUBAGENT)

    assert "Safe Parallel Dispatch" in text
    assert "disjoint write scopes" in text
    assert "overlapping files" in text
    assert "final integration, conflict resolution, and verification" in text


def test_workflow_autopilot_routes_discipline_aliases() -> None:
    text = read(WORKFLOW)

    assert "Activate brainstorm mode on `$brainstorm`" in text
    assert "Activate review-feedback routing on `$review-feedback`" in text
