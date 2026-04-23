from __future__ import annotations

import json
from pathlib import Path

import yaml


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = SKILLS_ROOT / "codex-document-writer"
SKILL_MD = SKILL_ROOT / "SKILL.md"
MASTER_MD = SKILLS_ROOT / "codex-master-instructions" / "SKILL.md"
MANIFEST = SKILLS_ROOT / ".system" / "manifest.json"


def parse_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    frontmatter_text = text.split("---\n", 2)[1]
    payload = yaml.safe_load(frontmatter_text)
    assert isinstance(payload, dict)
    return payload


def test_document_writer_skill_contract() -> None:
    payload = parse_frontmatter(SKILL_MD)
    body = SKILL_MD.read_text(encoding="utf-8")

    assert payload["name"] == "codex-document-writer"
    assert payload["load_priority"] == "on-demand"
    assert "$doc" in body
    assert "$report" in body
    assert "soạn tài liệu" in body
    assert "purpose, audience, context, and expected use" in body


def test_document_writer_references_exist_and_cover_required_topics() -> None:
    expected_refs = {
        "document-types.md",
        "sentence-quality.md",
        "tone-reliability.md",
        "vietnamese-style.md",
        "formatting.md",
    }
    actual_refs = {path.name for path in (SKILL_ROOT / "references").glob("*.md")}
    assert expected_refs <= actual_refs

    vietnamese_style = (SKILL_ROOT / "references" / "vietnamese-style.md").read_text(encoding="utf-8")
    assert "Quyết định" in vietnamese_style
    assert "Bằng chứng" in vietnamese_style
    assert "Bước tiếp theo" in vietnamese_style

    tone = (SKILL_ROOT / "references" / "tone-reliability.md").read_text(encoding="utf-8")
    assert "Verified" in tone
    assert "Inferred" in tone
    assert "Unknown" in tone


def test_document_writer_is_routed_from_master_and_manifest() -> None:
    master = MASTER_MD.read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert "| `$doc` | `$codex-document-writer` | codex-document-writer |" in master
    assert "| `$report` | `$codex-document-writer` | codex-document-writer |" in master
    assert "| document |" in master
    assert "codex-document-writer" in manifest["skills"]
    assert "codex-document-writer" in manifest["load_order"]["on-demand"]
