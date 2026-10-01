from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILLS_ROOT / ".system" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import build_release_zip  # noqa: E402


class ProjectArtifactLayoutTests(unittest.TestCase):
    def test_artifact_map_covers_project_and_host_owned_roots(self) -> None:
        doc_path = Path(__file__).resolve().parents[2] / "docs" / "project-artifact-layout.md"
        text = doc_path.read_text(encoding="utf-8")
        for path in (
            ".codex/context/",
            ".codex/project-docs/",
            ".codex/specs/",
            ".codex/design/",
            ".codex/knowledge/",
            ".codex/quality/",
            ".codex/sessions/",
            ".codex/decisions/",
            ".codex/feedback/",
            ".codex/skill-usage/",
            ".codexai/",
            ".agents/",
            ".claude/",
            ".cursor/",
            ".codex-plugin/",
            ".claude-plugin/",
            ".cursor-plugin/",
        ):
            with self.subTest(path=path):
                self.assertIn(path, text)

    def test_release_archive_excludes_developer_plans_but_keeps_user_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            user_doc = root / "docs" / "INSTALL.md"
            user_doc.parent.mkdir(parents=True)
            user_doc.write_text("Install guide\n", encoding="utf-8")
            plan = root / "docs" / "superpowers" / "plans" / "internal-plan.md"
            plan.parent.mkdir(parents=True)
            plan.write_text("Internal plan\n", encoding="utf-8")
            spec = root / "docs" / "superpowers" / "specs" / "internal-spec.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("Internal spec\n", encoding="utf-8")
            cursor_manifest = root / ".cursor-plugin" / "plugin.json"
            cursor_manifest.parent.mkdir(parents=True)
            cursor_manifest.write_text("{}\n", encoding="utf-8")

            files = build_release_zip.iter_release_files(root)
            relatives = {path.relative_to(root).as_posix() for path in files}

            self.assertIn("docs/INSTALL.md", relatives)
            self.assertIn(".cursor-plugin/plugin.json", relatives)
            self.assertFalse(any(path.startswith("docs/superpowers/") for path in relatives))


if __name__ == "__main__":
    unittest.main()
