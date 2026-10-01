from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILLS_ROOT / ".system" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import install  # noqa: E402


class InstallDispatcherTests(unittest.TestCase):
    def test_host_must_be_explicit_and_all_is_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "choose an explicit host"):
            install.resolve_hosts(None)

        self.assertEqual(install.resolve_hosts("codex"), ("codex",))
        self.assertEqual(install.resolve_hosts("all"), install.HOSTS)

    def test_user_install_does_not_write_bridge_to_current_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skills"
            (source / "codex-master-instructions").mkdir(parents=True)
            (source / "codex-master-instructions" / "SKILL.md").write_text("---\nname: codex-master-instructions\n---\n", encoding="utf-8")
            workspace = root / "unrelated-workspace"
            workspace.mkdir()
            user_home = root / "user-home"
            user_home.mkdir()
            argv = [
                "install.py",
                "install",
                "--host",
                "codex",
                "--scope",
                "user",
                "--source",
                str(source),
                "--apply",
                "--format",
                "json",
            ]

            with (
                patch.object(install.sys, "argv", argv),
                patch.object(Path, "cwd", return_value=workspace),
                patch.dict(os.environ, {"USERPROFILE": str(user_home), "HOME": str(user_home)}),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                exit_code = install.main()

            self.assertEqual(exit_code, 0)
            self.assertTrue((user_home / ".agents" / "skills" / "codex-master-instructions" / "SKILL.md").exists())
            self.assertFalse((workspace / "AGENTS.md").exists())

    def test_repo_install_writes_only_the_selected_host_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skills"
            (source / "codex-master-instructions").mkdir(parents=True)
            (source / "codex-master-instructions" / "SKILL.md").write_text("---\nname: codex-master-instructions\n---\n", encoding="utf-8")
            workspace = root / "project"
            workspace.mkdir()
            argv = [
                "install.py",
                "install",
                "--host",
                "codex",
                "--scope",
                "repo",
                "--source",
                str(source),
                "--repo-root",
                str(workspace),
                "--apply",
                "--format",
                "json",
            ]

            with (
                patch.object(install.sys, "argv", argv),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                exit_code = install.main()

            self.assertEqual(exit_code, 0)
            self.assertTrue((workspace / "AGENTS.md").exists())
            self.assertTrue((workspace / ".agents" / "skills" / "codex-master-instructions" / "SKILL.md").exists())
            self.assertFalse((workspace / "CLAUDE.md").exists())

    def test_cursor_user_install_does_not_write_a_bridge_under_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-skills"
            skill = source / "codex-master-instructions"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: codex-master-instructions\n---\n", encoding="utf-8")
            user_home = root / "user-home"
            user_home.mkdir()
            argv = [
                "install.py",
                "install",
                "--host",
                "cursor",
                "--scope",
                "user",
                "--source",
                str(source),
                "--apply",
                "--format",
                "json",
            ]

            with (
                patch.object(install.sys, "argv", argv),
                patch.dict(os.environ, {"USERPROFILE": str(user_home), "HOME": str(user_home)}),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                exit_code = install.main()

            self.assertEqual(exit_code, 0)
            self.assertTrue((user_home / ".cursor" / "skills" / "codex-master-instructions" / "SKILL.md").exists())
            self.assertFalse((user_home / "AGENTS.md").exists())
            self.assertFalse((user_home / ".cursor" / "AGENTS.md").exists())

    def test_github_cli_is_not_a_required_plugin_install_tool(self) -> None:
        for manifest_path in (Path(".codex-plugin/plugin.json"), Path(".claude-plugin/plugin.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            requirements = manifest.get("requirements", {})
            tools = requirements.get("tools", []) if isinstance(requirements, dict) else []
            self.assertFalse(any(item.get("binary") == "gh" for item in tools if isinstance(item, dict)))


if __name__ == "__main__":
    unittest.main()
