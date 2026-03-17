from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

README = REPO_ROOT / "README.md"
VI_GUIDE = REPO_ROOT / "docs" / "huong-dan-vi.md"
SKILLS_README = REPO_ROOT / "skills" / "README.md"
CHANGELOG = REPO_ROOT / "skills" / "CHANGELOG.md"

SUSPICIOUS_FRAGMENTS = [
    "\u00c3\u0192",
    "\u00c3\u00a2",
    "\u00c2\u00b0",
    "\u00e2\u20ac",
    "\u00c3\u2020",
    "\u00c3\u00a1\u00c2",
]


def test_public_docs_do_not_contain_known_mojibake_fragments() -> None:
    for path in (README, VI_GUIDE, SKILLS_README, CHANGELOG):
        text = path.read_text(encoding="utf-8")
        for fragment in SUSPICIOUS_FRAGMENTS:
            assert fragment not in text, f"{path} still contains mojibake fragment {fragment!r}"


def test_public_readme_keeps_utf8_sections_intact() -> None:
    text = README.read_text(encoding="utf-8")

    assert (
        "> **Production-ready instruction framework for Codex** \u2014 deterministic workflows"
        in text
    )
    assert (
        "understand intent \u2192 plan \u2192 route to domain expertise \u2192 implement"
        in text
    )
    assert "\u251c\u2500\u2500 README.md                    \u2190 You are here" in text


def test_vietnamese_guide_keeps_utf8_sections_intact() -> None:
    text = VI_GUIDE.read_text(encoding="utf-8")

    assert "# H\u01b0\u1edbng D\u1eabn S\u1eed D\u1ee5ng CodexAI Skill Pack" in text
    assert "## 2. Ki\u1ebfn Tr\u00fac H\u1ec7 Th\u1ed1ng" in text
    assert (
        "2. \U0001f4cb L\u1eacP K\u1ebe HO\u1ea0CH  \u2192  Ch\u1ea1y Plan Writer"
        in text
    )
