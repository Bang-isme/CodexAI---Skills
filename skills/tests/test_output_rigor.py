#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


SKILLS_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


output_guard = load_script_module(
    "skills_output_guard",
    "codex-execution-quality-gate/scripts/output_guard.py",
)
reasoning_brief = load_script_module(
    "skills_build_reasoning_brief",
    "codex-reasoning-rigor/scripts/build_reasoning_brief.py",
)
editorial_review = load_script_module(
    "skills_editorial_review",
    "codex-execution-quality-gate/scripts/editorial_review.py",
)


def test_output_guard_flags_generic_text() -> None:
    report = output_guard.analyze_text(
        "Use best practices to improve quality and ensure scalability for a robust solution.",
        min_score=60,
    )
    assert report["status"] == "fail"
    assert "best practices" in report["generic_hits"]
    assert report["score"] < 60


def test_output_guard_passes_specific_text() -> None:
    text = "\n".join(
        [
            "Decision: keep `scripts/output_guard.py` in the quality gate.",
            "Evidence: run `python skills/tests/smoke_test.py` and `pytest skills/tests -q`.",
            "Risk: the heuristics may pass a verbose answer that is still wrong.",
            "Next step: tune thresholds in `skills/codex-execution-quality-gate/references/output-guard-spec.md`.",
        ]
    )
    report = output_guard.analyze_text(text, min_score=60)
    assert report["status"] == "pass"
    assert report["counts"]["commands"] >= 1
    assert report["counts"]["artifact_refs"] >= 2


def test_output_guard_requires_runnable_command_evidence() -> None:
    text = "\n".join(
        [
            "Decision: keep `README.md` aligned with the git branching notes.",
            "Evidence: this paragraph mentions python packaging, not a runnable command.",
            "Risk: readers may think verification happened when it did not.",
            "Next step: tighten the checker.",
        ]
    )
    report = output_guard.analyze_text(text, min_score=60)
    assert report["status"] == "fail"
    assert "No verification or command evidence detected" in report["issues"]


def test_output_guard_deduplicates_overlapping_generic_phrases() -> None:
    report = output_guard.analyze_text(
        "Decision: follow best practices. Evidence: keep prose only. Risk: low. Next step: improve quality.",
        min_score=60,
    )
    assert report["counts"]["generic_phrases"] == 2
    assert set(report["generic_hits"]) == {"best practices", "improve quality"}
    assert "best practice" not in report["generic_hits"]


def test_output_guard_repo_root_rejects_unresolved_grounding(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts" / "smoke_test.py").write_text("print('ok')\n", encoding="utf-8")
    text = "\n".join(
        [
            "Decision: keep `docs/missing.md` aligned with the pack.",
            "Evidence: run `python scripts/missing.py` after updating `docs/missing.md`.",
            "Risk: stale refs can mislead reviewers.",
            "Next step: tighten grounding checks.",
        ]
    )
    report = output_guard.analyze_text(text, min_score=60, repo_root=tmp_path)
    assert report["status"] == "fail"
    assert "docs/missing.md" in report["missing_artifact_refs"]
    assert "scripts/missing.py" in report["missing_command_paths"]


def test_output_guard_repo_root_rewards_real_grounding(tmp_path: Path) -> None:
    (tmp_path / "skills" / "tests").mkdir(parents=True, exist_ok=True)
    (tmp_path / "skills" / "tests" / "smoke_test.py").write_text("print('ok')\n", encoding="utf-8")
    text = "\n".join(
        [
            "Decision: keep `skills/tests/smoke_test.py` in the quality gate.",
            "Evidence: run `python skills/tests/smoke_test.py` before handoff.",
            "Risk: stale docs could drift from real verification paths.",
            "Next step: keep the smoke entry current.",
        ]
    )
    report = output_guard.analyze_text(text, min_score=60, repo_root=tmp_path)
    assert report["status"] == "pass"
    assert report["counts"]["resolved_artifact_refs"] >= 1
    assert report["counts"]["resolved_command_paths"] >= 1


def test_output_guard_llm_judge_without_api_key_falls_back(monkeypatch) -> None:
    monkeypatch.delenv("CODEX_JUDGE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = output_guard.analyze_text(
        "Decision: follow best practices. Evidence: prose only. Risk: low. Next step: improve quality.",
        min_score=60,
        llm_judge=True,
    )
    assert report["evaluation_mode"] == "heuristic"
    assert report["llm_score"] is None
    assert report["heuristic_score"] == report["score"]
    assert report["warnings"]
    assert "falling back to heuristic mode" in report["warnings"][0]


def test_output_guard_llm_judge_merges_scores(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    heuristic_report = output_guard.analyze_text(
        "\n".join(
            [
                "Decision: keep `scripts/output_guard.py` in the quality gate.",
                "Evidence: run `python skills/tests/smoke_test.py` and `pytest skills/tests -q`.",
                "Risk: stale thresholds can drift from the pack.",
                "Next step: tune the score floor after each release.",
            ]
        ),
        min_score=60,
    )

    def fake_evaluate_with_llm(text: str, prompt_template: str, breakdown_keys, **kwargs):
        return {
            "score": 80,
            "breakdown": {
                "specificity": 20,
                "evidence": 22,
                "actionability": 19,
                "completeness": 19,
            },
            "issues": ["Need slightly stronger evidence"],
            "suggestions": ["Add the exact smoke command output"],
            "truncated": False,
            "judged_chars": len(text),
            "estimated_cost_usd": 0.001,
            "model": kwargs["model"],
        }

    monkeypatch.setattr(output_guard, "evaluate_with_llm", fake_evaluate_with_llm)
    report = output_guard.analyze_text(
        "\n".join(
            [
                "Decision: keep `scripts/output_guard.py` in the quality gate.",
                "Evidence: run `python skills/tests/smoke_test.py` and `pytest skills/tests -q`.",
                "Risk: stale thresholds can drift from the pack.",
                "Next step: tune the score floor after each release.",
            ]
        ),
        min_score=60,
        llm_judge=True,
    )
    assert report["evaluation_mode"] == "llm"
    assert report["llm_score"] == 80
    assert report["heuristic_score"] == heuristic_report["score"]
    assert report["score"] == round((80 * 0.7) + (heuristic_report["score"] * 0.3))
    assert report["llm_breakdown"]["specificity"] == 20
    assert report["estimated_cost_usd"] == 0.001


def test_reasoning_brief_renders_expected_sections() -> None:
    markdown = reasoning_brief.render_template(
        Path(reasoning_brief.TEMPLATE_PATH).read_text(encoding="utf-8"),
        {
            "title": "Improve pack quality",
            "goal": "Reduce generic outputs",
            "constraints": "- Keep the pack lean",
            "non_goals": "- Rewrite every skill",
            "evidence": "- pytest passes",
            "quality_bar": "- cites exact files and runnable commands",
            "signals": "- output guard score stays above threshold",
            "risks": "- Too much process overhead",
            "deliverable": "Reasoning-ready upgrade plan",
        },
    )
    assert "# Reasoning Brief: Improve pack quality" in markdown
    assert "## Evidence Required" in markdown
    assert "## Quality Bar" in markdown
    assert "Reasoning-ready upgrade plan" in markdown


def test_reasoning_brief_parse_list_defaults_to_todo() -> None:
    assert reasoning_brief.parse_list("") == []


def test_reasoning_brief_missing_required_fields_detected() -> None:
    args = SimpleNamespace(
        title="Improve pack quality",
        goal="Reduce generic outputs",
        constraints="Keep the pack lean",
        non_goals="",
        evidence="pytest passes",
        signals="output guard score stays above threshold",
        risks="Too much process overhead",
        quality_bar="",
        allow_placeholders=False,
        deliverable="Reasoning-ready upgrade plan",
    )
    assert reasoning_brief.missing_required_fields(args) == ["quality_bar", "non_goals"]


def test_reasoning_brief_build_mapping_scaffold_mode_uses_placeholders() -> None:
    args = SimpleNamespace(
        title="Improve pack quality",
        goal="Reduce generic outputs",
        constraints="",
        non_goals="",
        evidence="",
        signals="",
        risks="",
        quality_bar="",
        allow_placeholders=True,
        deliverable="Reasoning-ready upgrade plan",
    )
    mapping = reasoning_brief.build_mapping(args)
    assert mapping["constraints"] == "- _TODO_"
    assert mapping["quality_bar"] == "_TODO_"


def test_editorial_review_flags_ai_speak_and_hedging() -> None:
    text = "\n".join(
        [
            "Here's a breakdown of what you may want to do.",
            "It depends, and you could consider leveraging best practices.",
            "Overall, the best approach is potentially to revisit this later.",
        ]
    )
    report = editorial_review.analyze_text(text, min_score=65, deliverable_kind="review")
    assert report["status"] == "fail"
    assert "Tone still reads like AI-safe prose" in report["issues"]
    assert report["counts"]["ai_speak_phrases"] >= 1
    assert report["counts"]["hedge_phrases"] >= 2


def test_editorial_review_passes_decision_ready_grounded_text(tmp_path: Path) -> None:
    (tmp_path / "skills" / "tests").mkdir(parents=True, exist_ok=True)
    (tmp_path / "skills" / "tests" / "smoke_test.py").write_text("print('ok')\n", encoding="utf-8")
    text = "\n".join(
        [
            "Decision: keep `skills/tests/smoke_test.py` in the release checklist.",
            "Evidence: run `python skills/tests/smoke_test.py` after updating the gate scripts.",
            "Risk: stale smoke expectations will make release notes look trustworthy when they are not.",
            "Next step: assign the release owner to refresh the checklist after each gate change.",
        ]
    )
    report = editorial_review.analyze_text(text, min_score=65, deliverable_kind="handoff", repo_root=tmp_path)
    assert report["status"] == "pass"
    assert report["rubric"]["decision_clarity"] >= 12
    assert report["rubric"]["grounding"] >= 10
    assert report["rubric"]["tradeoff_awareness"] >= 8


def test_editorial_review_llm_judge_without_api_key_falls_back(monkeypatch) -> None:
    monkeypatch.delenv("CODEX_JUDGE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = editorial_review.analyze_text(
        "Here's a breakdown. Risk: low. Next step: maybe revisit later.",
        min_score=65,
        deliverable_kind="review",
        llm_judge=True,
    )
    assert report["evaluation_mode"] == "heuristic"
    assert report["llm_score"] is None
    assert report["warnings"]
    assert "falling back to heuristic mode" in report["warnings"][0]


def test_editorial_review_llm_judge_merges_scores(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_JUDGE_API_KEY", "test-key")
    text = "\n".join(
        [
            "Decision: keep `skills/tests/smoke_test.py` in the release checklist.",
            "Evidence: run `python skills/tests/smoke_test.py` after updating the gate scripts.",
            "Risk: stale smoke expectations will make release notes look trustworthy when they are not.",
            "Next step: assign the release owner to refresh the checklist after each gate change.",
        ]
    )
    heuristic_report = editorial_review.analyze_text(
        text,
        min_score=65,
        deliverable_kind="handoff",
    )

    def fake_evaluate_with_llm(text: str, prompt_template: str, breakdown_keys, **kwargs):
        return {
            "score": 90,
            "breakdown": {
                "decision_clarity": 23,
                "accountability_tone": 22,
                "tradeoff_awareness": 22,
                "scanability_structure": 23,
            },
            "issues": [],
            "suggestions": ["Add the exact owner name for the next-step item"],
            "truncated": False,
            "judged_chars": len(text),
            "estimated_cost_usd": 0.001,
            "model": kwargs["model"],
        }

    monkeypatch.setattr(editorial_review.output_guard, "evaluate_with_llm", fake_evaluate_with_llm)
    report = editorial_review.analyze_text(
        text,
        min_score=65,
        deliverable_kind="handoff",
        llm_judge=True,
    )
    assert report["evaluation_mode"] == "llm"
    assert report["llm_score"] == 90
    assert report["heuristic_score"] == heuristic_report["score"]
    assert report["score"] == round((90 * 0.7) + (heuristic_report["score"] * 0.3))
    assert report["llm_breakdown"]["accountability_tone"] == 22
