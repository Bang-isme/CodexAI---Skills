from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "skills" / "codex-runtime-hook" / "scripts"
sys.path.insert(0, str(RUNTIME))

import install_codex_hooks  # noqa: E402
import precision_mode  # noqa: E402


MANAGED_STATUS = "Checking CodexAI project readiness"


def managed_entry(command: str = "python runtime_hook.py") -> dict:
    return {
        "matcher": "startup|resume",
        "hooks": [
            {
                "type": "command",
                "command": command,
                "timeout": 30,
                "statusMessage": MANAGED_STATUS,
            }
        ],
    }


def foreign_entry(command: str = "echo keep") -> dict:
    return {
        "matcher": "startup",
        "hooks": [{"type": "command", "command": command, "statusMessage": "foreign"}],
    }


class PrecisionModeAndHooksEdgeCaseTests(unittest.TestCase):
    def test_env_overrides_config_and_default(self) -> None:
        level = precision_mode.resolve_precision_mode(
            environ={"CODEX_PRECISION_MODE": "ultra"},
            config={"precision_mode": "lite"},
        )
        self.assertEqual(level, "ultra")
        alias = precision_mode.resolve_precision_mode(environ={}, config={"CODEX_PRECISION_MODE": "lite"})
        self.assertEqual(alias, "lite")

    def test_invalid_env_falls_through_to_config(self) -> None:
        level = precision_mode.resolve_precision_mode(
            environ={"CODEX_PRECISION_MODE": "nope"},
            config_text='{"precision_mode": "lite"}',
        )
        self.assertEqual(level, "lite")

    def test_one_shot_commands_are_rejected_as_default_levels(self) -> None:
        for blocked in ("review", "audit", "debt", "help", "$review", " HELP "):
            level = precision_mode.resolve_precision_mode(
                environ={"CODEX_PRECISION_MODE": blocked},
                config={"precision_mode": "lite"},
            )
            self.assertEqual(level, "lite", blocked)
        self.assertEqual(
            precision_mode.resolve_precision_mode(environ={}, config={"precision_mode": "audit"}),
            "full",
        )

    def test_bom_is_stripped_before_json_load(self) -> None:
        raw = '\ufeff{"precision_mode": "lite", "owner": "codexai"}'
        with self.assertRaises(json.JSONDecodeError):
            json.loads(raw)
        parsed = precision_mode.parse_config_json(raw)
        self.assertEqual(parsed["precision_mode"], "lite")
        self.assertEqual(parsed["owner"], "codexai")
        self.assertEqual(precision_mode.resolve_precision_mode(environ={}, config_text=raw), "lite")

    def test_invalid_config_json_falls_through_to_full(self) -> None:
        self.assertEqual(precision_mode.resolve_precision_mode(environ={}, config_text="{"), "full")
        self.assertEqual(precision_mode.resolve_precision_mode(environ={}, config_text=None), "full")

    def test_merge_write_preserves_unrelated_keys_and_drops_bom(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "precision.json"
            path.write_text('\ufeff{"precision_mode": "lite", "owner": "codexai"}', encoding="utf-8")
            merged = precision_mode.write_precision_config(path, {"precision_mode": "ultra"})
            self.assertEqual(merged["owner"], "codexai")
            self.assertEqual(merged["precision_mode"], "ultra")
            text = path.read_text(encoding="utf-8")
            self.assertFalse(text.startswith("\ufeff"))
            self.assertIn("owner", text)
            self.assertIn("codexai", text)

    def test_deactivation_matches_whole_message_only(self) -> None:
        for message in ("off", "OFF", "stop", "normal mode", "  normal mode  "):
            result = precision_mode.track_prompt_command(message, "ultra", "full")
            self.assertEqual(result["action"], "deactivate", message)
            self.assertEqual(result["level"], "off", message)
            self.assertTrue(result["changed"], message)

    def test_deactivation_ignores_trailing_punctuation(self) -> None:
        for message in ("off.", "stop!", "normal mode?", "normal mode,", "off..."):
            result = precision_mode.track_prompt_command(message, "full", "full")
            self.assertEqual(result["level"], "off", message)
            self.assertEqual(result["action"], "deactivate", message)

    def test_sentence_mention_does_not_deactivate(self) -> None:
        for message in (
            "use normal mode for this summary",
            "please stop the server",
            "I want normal mode for the summary, then stop.",
            "full stop",
            "offline",
        ):
            result = precision_mode.track_prompt_command(message, "ultra", "full")
            self.assertEqual(result["level"], "ultra", message)
            self.assertEqual(result["action"], "unchanged", message)
            self.assertFalse(result["changed"], message)

    def test_bare_on_reports_current_level_when_active(self) -> None:
        result = precision_mode.track_prompt_command("on", "lite", "full")
        self.assertEqual(result["action"], "report")
        self.assertEqual(result["level"], "lite")
        self.assertFalse(result["changed"])

    def test_bare_on_activates_default_or_full_when_default_is_off(self) -> None:
        activated = precision_mode.track_prompt_command("on", "off", "ultra")
        self.assertEqual(activated["action"], "activate")
        self.assertEqual(activated["level"], "ultra")
        fallback = precision_mode.track_prompt_command("On!", "off", "off")
        self.assertEqual(fallback["action"], "activate")
        self.assertEqual(fallback["level"], "full")

    def test_unknown_arguments_leave_level_unchanged(self) -> None:
        for message in ("please refactor the parser", "onward", "turn off", ""):
            result = precision_mode.track_prompt_command(message, "full", "lite")
            self.assertEqual(result["level"], "full", message)
            self.assertEqual(result["action"], "unchanged", message)

    def test_one_shot_commands_do_not_latch(self) -> None:
        for message in ("$review", "$audit", "$debt", "$help", "review", "audit", "debt", "help", "$review the diff", "$debt!"):
            result = precision_mode.track_prompt_command(message, "ultra", "full")
            self.assertEqual(result["level"], "ultra", message)
            self.assertEqual(result["action"], "one_shot", message)
            self.assertFalse(result["changed"], message)
        mentioned = precision_mode.track_prompt_command("please $review", "ultra", "full")
        self.assertEqual(mentioned["action"], "unchanged")
        self.assertEqual(mentioned["level"], "ultra")

    def test_explicit_level_word_sets_intensity(self) -> None:
        changed = precision_mode.track_prompt_command("lite", "full", "full")
        self.assertEqual(changed["action"], "set")
        self.assertEqual(changed["level"], "lite")
        same = precision_mode.track_prompt_command("full", "full", "full")
        self.assertEqual(same["action"], "set")
        self.assertFalse(same["changed"])
        prefixed = precision_mode.track_prompt_command("precision ultra", "lite", "full")
        self.assertEqual(prefixed["level"], "ultra")

    def test_compaction_preserves_live_level(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            project = "D:\\alpha"
            precision_mode.write_session_state(state, project, "ultra")
            kept = precision_mode.start_precision_session(state, project, source="compact", default_level="lite")
            self.assertEqual(kept, "ultra")
            self.assertEqual(precision_mode.read_session_state(state, project)["level"], "ultra")
            self.assertEqual(precision_mode.resolve_session_level("compact", "lite", "full"), "lite")

    def test_fresh_start_uses_resolved_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            project = "D:\\alpha"
            precision_mode.write_session_state(state, project, "ultra")
            fresh = precision_mode.start_precision_session(state, project, source="fresh", default_level="lite")
            self.assertEqual(fresh, "lite")
            self.assertEqual(precision_mode.read_session_state(state, project)["level"], "lite")
            self.assertEqual(precision_mode.resolve_session_level("fresh", "ultra", "full"), "full")

    def test_project_path_hash_preserves_separators_and_isolates_state(self) -> None:
        windows_path = "D:\\work\\app"
        posix_path = "D:/work/app"
        self.assertNotEqual(precision_mode.project_state_id(windows_path), precision_mode.project_state_id(posix_path))
        self.assertEqual(precision_mode.project_state_id(windows_path), precision_mode.project_state_id(windows_path + "\\"))
        normalized = precision_mode.normalize_project_path(windows_path + "\\")
        self.assertEqual(normalized, windows_path)
        self.assertIn("\\", normalized)
        self.assertNotIn("/", normalized)
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            precision_mode.write_session_state(state, windows_path, "ultra")
            precision_mode.write_session_state(state, posix_path, "lite")
            self.assertNotEqual(
                precision_mode.session_state_path(state, windows_path),
                precision_mode.session_state_path(state, posix_path),
            )
            self.assertEqual(precision_mode.read_session_state(state, windows_path)["level"], "ultra")
            self.assertEqual(precision_mode.read_session_state(state, posix_path)["level"], "lite")
            self.assertEqual(precision_mode.read_session_state(state, windows_path)["project_path"], windows_path)

    def test_cache_stable_reinjection_appends_only_on_level_change_or_compaction(self) -> None:
        rules = "\n".join(
            [
                "- lite: keep it short",
                "- full: cover edges",
                "- ultra: show proof",
                "",
                "| level | behavior |",
                "| --- | --- |",
                "| lite | LITE_ROW |",
                "| full | FULL_ROW |",
                "| ultra | ULTRA_ROW |",
            ]
        )
        tracker = precision_mode.InstructionReinjectionTracker()
        first = tracker.append_rules("base", "full", rules, compacted=False)
        self.assertEqual(first.count("FULL_ROW"), 1)
        self.assertNotIn("LITE_ROW", first)
        self.assertIn("- lite:", first)
        second = tracker.append_rules(first, "full", rules, compacted=False)
        self.assertEqual(second, first)
        third = tracker.append_rules(second, "ultra", rules, compacted=False)
        self.assertEqual(third.count("ULTRA_ROW"), 1)
        self.assertGreater(len(third), len(second))
        fourth = tracker.append_rules(third, "ultra", rules, compacted=True)
        self.assertEqual(fourth.count("ULTRA_ROW"), 2)

    def test_instruction_filter_drops_other_levels_and_keeps_rule_bullets(self) -> None:
        rules = "\n".join(
            [
                "- lite: keep the answer short",
                "- full: cover edge cases",
                "- ultra: cite the failing input",
                "- off: do not inject extra rules",
                "",
                "| level | behavior |",
                "| --- | --- |",
                "| lite | LITE_ROW |",
                "| full | FULL_ROW |",
                "| ultra | ULTRA_ROW |",
                "| off | OFF_ROW |",
                "",
                "### Example: lite",
                "LITE_ONLY_SENTENCE",
                "",
                "### Example: full",
                "FULL_ONLY_SENTENCE",
                "",
                "Example: ultra",
                "INLINE_ULTRA_EXAMPLE",
                "",
                "Kept paragraph.",
            ]
        )
        rules += "\n```lite\nprint(\"lite-fence\")\n```\n```full\nprint(\"full-fence\")\n```\n"
        filtered = precision_mode.filter_instructions(rules, "full")
        self.assertIn("- lite:", filtered)
        self.assertIn("- off:", filtered)
        self.assertIn("FULL_ROW", filtered)
        self.assertNotIn("LITE_ROW", filtered)
        self.assertNotIn("ULTRA_ROW", filtered)
        self.assertNotIn("OFF_ROW", filtered)
        self.assertNotIn("LITE_ONLY_SENTENCE", filtered)
        self.assertIn("FULL_ONLY_SENTENCE", filtered)
        self.assertNotIn("INLINE_ULTRA_EXAMPLE", filtered)
        self.assertIn("Kept paragraph.", filtered)
        self.assertNotIn("lite-fence", filtered)
        self.assertIn("full-fence", filtered)

    def test_shell_safe_path_accepts_windows_and_posix(self) -> None:
        for path in (
            r"C:\Users\me\proj",
            "/usr/local/proj",
            "D:/CodexAI---Skills-18.0.0",
            "./scripts/run.py",
            r"..\sibling",
        ):
            self.assertTrue(install_codex_hooks.validate_shell_safe_path(path), path)

    def test_shell_safe_path_rejects_metacharacters(self) -> None:
        for char in ('"', "'", "$", "`", ";", "&", "|", "\n", "\r"):
            self.assertFalse(install_codex_hooks.validate_shell_safe_path(f"C:/safe{char}path"), repr(char))
        self.assertFalse(install_codex_hooks.validate_shell_safe_path(""))
        self.assertFalse(install_codex_hooks.validate_shell_safe_path("   "))

    def test_merge_hooks_preserves_foreign_and_replaces_managed(self) -> None:
        original = {
            "version": 1,
            "hooks": {
                "SessionStart": [
                    foreign_entry("echo keep"),
                    managed_entry("python old"),
                    foreign_entry("echo later"),
                ],
                "PreToolUse": [foreign_entry("echo pre")],
            },
        }
        merged = install_codex_hooks.merge_hooks_config("\ufeff" + json.dumps(original), managed_entry("python new"))
        self.assertEqual(merged["version"], 1)
        session = merged["hooks"]["SessionStart"]
        self.assertEqual([item["hooks"][0]["command"] for item in session], ["echo keep", "python new", "echo later"])
        self.assertEqual(merged["hooks"]["PreToolUse"][0]["hooks"][0]["command"], "echo pre")

    def test_merge_hooks_refuses_malformed_json_and_non_list(self) -> None:
        entry = managed_entry()
        with self.assertRaises(ValueError) as malformed:
            install_codex_hooks.merge_hooks_config("{", entry)
        self.assertIn("malformed", str(malformed.exception).lower())
        with self.assertRaises(ValueError) as non_list:
            install_codex_hooks.merge_hooks_config('{"hooks": {"SessionStart": {}}}', entry)
        self.assertIn("list", str(non_list.exception).lower())
        with self.assertRaises(ValueError):
            install_codex_hooks.merge_hooks_config("[]", entry)
        with self.assertRaises(ValueError):
            install_codex_hooks.merge_hooks_config('{"hooks": []}', entry)

    def test_uninstall_removes_only_codexai_or_deletes_file(self) -> None:
        only_managed, delete_file = install_codex_hooks.uninstall_hooks_document(
            json.dumps({"hooks": {"SessionStart": [managed_entry()]}})
        )
        self.assertTrue(delete_file)
        self.assertEqual(only_managed["hooks"], {})
        mixed_raw = json.dumps(
            {
                "version": 1,
                "hooks": {
                    "SessionStart": [foreign_entry(), managed_entry()],
                    "PreToolUse": [foreign_entry("echo pre")],
                },
            }
        )
        mixed, delete_mixed = install_codex_hooks.uninstall_hooks_document(mixed_raw)
        self.assertFalse(delete_mixed)
        self.assertEqual(mixed["version"], 1)
        self.assertEqual(len(mixed["hooks"]["SessionStart"]), 1)
        self.assertEqual(mixed["hooks"]["SessionStart"][0]["hooks"][0]["command"], "echo keep")
        self.assertEqual(mixed["hooks"]["PreToolUse"][0]["hooks"][0]["command"], "echo pre")

    def test_install_preserves_foreign_hooks_and_blocks_unsafe_paths(self) -> None:
        skills = ROOT / "skills"
        self.assertTrue(install_codex_hooks.validate_shell_safe_path(str(skills)))
        with tempfile.TemporaryDirectory() as temporary:
            unsafe = Path(temporary) / "proj$name"
            unsafe.mkdir()
            with self.assertRaises(ValueError):
                install_codex_hooks.install(unsafe, skills, dry_run=True, force=False)
            project = Path(temporary) / "demo"
            project.mkdir()
            hooks = project / ".codex" / "hooks.json"
            hooks.parent.mkdir(parents=True)
            foreign = {"hooks": {"PreToolUse": [foreign_entry("echo keep")]}}
            hooks.write_text("\ufeff" + json.dumps(foreign), encoding="utf-8")
            result = install_codex_hooks.install(project, skills, dry_run=False, force=False)
            self.assertTrue(result["changed"])
            saved_text = hooks.read_text(encoding="utf-8")
            self.assertFalse(saved_text.startswith("\ufeff"))
            saved = json.loads(saved_text)
            self.assertEqual(saved["hooks"]["PreToolUse"][0]["hooks"][0]["command"], "echo keep")
            messages = [
                hook.get("statusMessage")
                for item in saved["hooks"]["SessionStart"]
                for hook in item.get("hooks", [])
            ]
            self.assertIn(MANAGED_STATUS, messages)
            removed = install_codex_hooks.uninstall(project, dry_run=False)
            self.assertFalse(removed["deleted"])
            after = json.loads(hooks.read_text(encoding="utf-8"))
            self.assertNotIn("SessionStart", after["hooks"])
            self.assertIn("PreToolUse", after["hooks"])

    def test_precision_ladder_is_linked_from_operating_docs(self) -> None:
        ladder = (ROOT / "skills" / "codex-reasoning-rigor" / "references" / "precision-ladder.md").read_text(encoding="utf-8")
        for phrase in (
            "Does it need to exist?",
            "Caller-Grep Rule",
            "shortcut: <ceiling>, <when to upgrade>",
            "Never-Cut",
            "trust-boundary validation",
            "CODEX_PRECISION_MODE",
            "normal mode",
        ):
            self.assertIn(phrase, ladder)
        for relative in (
            "skills/codex-reasoning-rigor/SKILL.md",
            "skills/codex-systematic-debugging/SKILL.md",
            "skills/codex-subagent-execution/agents/implementer-prompt.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("precision-ladder.md", text)


if __name__ == "__main__":
    unittest.main()
