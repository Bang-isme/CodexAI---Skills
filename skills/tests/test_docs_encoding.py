from __future__ import annotations

from pathlib import Path

import pytest


SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]

README = REPO_ROOT / "README.md"
VI_GUIDE = REPO_ROOT / "docs" / "huong-dan-vi.md"
SKILLS_README = SKILLS_ROOT / "README.md"
CHANGELOG = SKILLS_ROOT / "CHANGELOG.md"

SUSPICIOUS_FRAGMENTS = [
    "\u00c3\u0192",
    "\u00c3\u00a2",
    "\u00c2\u00b0",
    "\u00e2\u20ac",
    "\u00c3\u2020",
    "\u00c3\u00a1\u00c2",
]


def source_pack_available() -> bool:
    return README.exists() and VI_GUIDE.exists()


def test_public_docs_do_not_contain_known_mojibake_fragments() -> None:
    paths = [SKILLS_README, CHANGELOG]
    if source_pack_available():
        paths.extend([README, VI_GUIDE])

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for fragment in SUSPICIOUS_FRAGMENTS:
            assert fragment not in text, f"{path} still contains mojibake fragment {fragment!r}"


def test_public_readme_keeps_utf8_sections_intact() -> None:
    if not source_pack_available():
        pytest.skip("Source-pack README is not installed in global skills runtime")

    text = README.read_text(encoding="utf-8")
    assert "> Production-ready instruction framework for Codex - deterministic workflows" in text
    assert "Intent -> Plan -> Route -> Implement -> Verify -> Persist -> Commit" in text
    assert "|-- README.md" in text


def test_vietnamese_guide_keeps_utf8_sections_intact() -> None:
    if not source_pack_available():
        pytest.skip("Vietnamese guide is not installed in global skills runtime")

    text = VI_GUIDE.read_text(encoding="utf-8")
    assert "# Hướng Dẫn Sử Dụng CodexAI Skill Pack" in text
    assert "## 2. Điểm mạnh chính" in text
    assert "`Phân tích yêu cầu -> Lập kế hoạch -> Route đúng domain -> Triển khai -> Kiểm tra -> Lưu tri thức -> Commit`" in text
