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
        "> Production-ready instruction framework for Codex - deterministic workflows"
        in text
    )
    assert (
        "Intent -> Plan -> Route -> Implement -> Verify -> Persist -> Commit"
        in text
    )
    assert "|-- README.md" in text


def test_vietnamese_guide_keeps_utf8_sections_intact() -> None:
    text = VI_GUIDE.read_text(encoding="utf-8")

    assert "# Hướng Dẫn Sử Dụng CodexAI Skill Pack" in text
    assert "## 2. Điểm mạnh chính" in text
    assert "`Phân tích yêu cầu -> Lập kế hoạch -> Route đúng domain -> Triển khai -> Kiểm tra -> Lưu tri thức -> Commit`" in text
