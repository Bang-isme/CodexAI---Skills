from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILLS_ROOT / "codex-role-docs" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import init_role_docs  # noqa: E402


class RoleDocsInitializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = init_role_docs.load_manifest()

    def test_default_role_selection_is_empty_and_all_is_explicit(self) -> None:
        self.assertEqual(init_role_docs.parse_roles("", self.manifest), [])
        self.assertEqual(init_role_docs.parse_roles("frontend,qa", self.manifest), ["frontend", "qa"])
        self.assertEqual(init_role_docs.parse_roles("all", self.manifest), list(self.manifest["roles"]))

    def test_minimal_initialization_creates_only_project_level_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            payload = init_role_docs.initialize_role_docs(project, roles=[])

            self.assertEqual(payload["status"], "created")
            self.assertEqual(
                set(payload["files_created"]),
                {
                    ".codex/project-docs/PROJECT-BRIEF.md",
                    ".codex/project-docs/decisions/ADR-0001-template.md",
                },
            )
            self.assertFalse((project / ".codex/project-docs/frontend").exists())
            self.assertFalse((project / ".codex/project-docs/backend").exists())

    def test_selected_roles_create_only_the_requested_role_tree_and_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            selected = init_role_docs.parse_roles("frontend,qa", self.manifest)
            first = init_role_docs.initialize_role_docs(project, roles=selected)
            second = init_role_docs.initialize_role_docs(project, roles=selected)

            self.assertTrue((project / ".codex/project-docs/frontend").is_dir())
            self.assertTrue((project / ".codex/project-docs/qa").is_dir())
            self.assertFalse((project / ".codex/project-docs/backend").exists())
            self.assertEqual(first["status"], "created")
            self.assertEqual(second["status"], "up_to_date")
            self.assertEqual(second["files_created"], [])

    def test_cli_role_default_is_minimal(self) -> None:
        with patch.object(sys, "argv", ["init_role_docs.py", "--project-root", "."]):
            args = init_role_docs.parse_args()
        self.assertEqual(args.roles, "")


if __name__ == "__main__":
    unittest.main()
