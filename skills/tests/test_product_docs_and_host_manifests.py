from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / ".system" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import validate_claude_plugin  # noqa: E402
import validate_codex_plugin  # noqa: E402
import validate_cursor_plugin  # noqa: E402


LOCAL_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


class ProductDocsAndHostManifestTests(unittest.TestCase):
    def test_customer_readme_keeps_detailed_sections_and_points_to_existing_local_files(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Public Pipeline", readme)
        self.assertIn("## Skill Inventory", readme)
        self.assertIn("## Quick Start", readme)
        self.assertIn("## Repository Layout", readme)
        self.assertIn("docs/INSTALL.md", readme)
        self.assertIn("docs/huong-dan-vi.md", readme)
        self.assert_local_links_exist(readme, ROOT)

    def test_install_guides_cover_each_host_without_overclaiming(self) -> None:
        install_doc = (ROOT / "docs" / "INSTALL.md").read_text(encoding="utf-8")
        vietnamese_doc = (ROOT / "docs" / "huong-dan-vi.md").read_text(encoding="utf-8")
        for host in ("Codex", "Claude Code", "Cursor", "Antigravity"):
            with self.subTest(host=host):
                self.assertIn(host, install_doc)
                self.assertIn(host, vietnamese_doc)
        self.assertIn("Gemini CLI", install_doc)
        self.assertIn("optional", install_doc.lower())
        self.assertIn("DEGRADED", install_doc)
        self.assert_local_links_exist(install_doc, ROOT / "docs")
        self.assert_local_links_exist(vietnamese_doc, ROOT / "docs")

    def test_host_manifests_validate_and_versions_stay_aligned(self) -> None:
        version = (ROOT / "skills" / "VERSION").read_text(encoding="utf-8").strip()
        manifests = [
            ROOT / ".codex-plugin" / "plugin.json",
            ROOT / ".claude-plugin" / "plugin.json",
            ROOT / ".cursor-plugin" / "plugin.json",
            ROOT / ".cursor-plugin" / "marketplace.json",
            ROOT / "antigravity" / "plugin.json",
        ]
        for path in manifests:
            with self.subTest(path=path):
                manifest = json.loads(path.read_text(encoding="utf-8"))
                if path.name == "marketplace.json":
                    entry = manifest["plugins"][0]
                    self.assertEqual(entry["version"], version)
                else:
                    self.assertEqual(manifest["version"], version)

        self.assertEqual(validate_codex_plugin.validate(ROOT, strict=True)["status"], "pass")
        self.assertIn(validate_claude_plugin.validate(ROOT)["status"], {"pass", "warn"})
        self.assertEqual(validate_cursor_plugin.validate(ROOT)["status"], "pass")

    def assert_local_links_exist(self, markdown: str, base: Path) -> None:
        for match in LOCAL_LINK.finditer(markdown):
            target = match.group(1).split("#", 1)[0]
            if not target or target.startswith(("https://", "http://", "mailto:")):
                continue
            with self.subTest(link=target):
                self.assertTrue((base / target).resolve().exists(), f"missing local link target: {target}")


if __name__ == "__main__":
    unittest.main()
