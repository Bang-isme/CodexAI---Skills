from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "codex-execution-quality-gate" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import pre_commit_check  # noqa: E402
import run_gate  # noqa: E402
import smart_test_selector  # noqa: E402


UNITTEST_SOURCE = """import unittest

class ExampleTests(unittest.TestCase):
    def test_passes(self):
        self.assertEqual(1, 1)
"""

NODE_TEST_SOURCE = """import test from 'node:test';
import assert from 'node:assert/strict';

test('example passes', () => assert.equal(1, 1));
"""


def make_unittest_project(root: Path) -> Path:
    tests = root / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    test_file = tests / "test_example.py"
    test_file.write_text(UNITTEST_SOURCE, encoding="utf-8")
    return test_file


def make_node_project(root: Path) -> Path:
    tests = root / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    test_file = tests / "example.test.mjs"
    test_file.write_text(NODE_TEST_SOURCE, encoding="utf-8")
    return test_file


class QualityGateTestRunnerTests(unittest.TestCase):
    def test_selector_discovers_native_node_test_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            test_file = make_node_project(root)
            relative = test_file.relative_to(root).as_posix()

            self.assertTrue(smart_test_selector.is_test_file(Path(relative)))
            self.assertIn(relative, smart_test_selector.collect_test_files(root))
            self.assertEqual(smart_test_selector.detect_runner(root, ""), "node")

    def test_selector_does_not_guess_between_native_runners(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_unittest_project(root)
            make_node_project(root)

            self.assertIsNone(smart_test_selector.detect_runner(root, ""))

    def test_selector_detects_and_runs_unittest_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            test_file = make_unittest_project(root)
            relative = test_file.relative_to(root).as_posix()
            command_result = {
                "ok": True,
                "exit_code": 0,
                "stdout": "Ran 2 tests in 0.01s\n\nOK\n",
                "stderr": "",
                "duration_ms": 10,
            }

            self.assertEqual(smart_test_selector.detect_runner(root, ""), "unittest")
            with patch.object(smart_test_selector, "run_command", return_value=command_result) as run:
                result, warnings = smart_test_selector.maybe_run_tests(root, [relative], "unittest")

        self.assertEqual(run.call_args.args[1], [sys.executable, "-m", "unittest", relative])
        self.assertEqual(warnings, [])
        self.assertEqual((result["runner"], result["passed"], result["failed"]), ("unittest", 2, 0))

    def test_selector_runs_node_tests_and_parses_node_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_unittest_project(root)
            test_file = make_node_project(root)
            relative = test_file.relative_to(root).as_posix()
            command_result = {
                "ok": True,
                "exit_code": 0,
                "stdout": "# tests 3\n# pass 3\n# fail 0\n",
                "stderr": "",
                "duration_ms": 10,
            }

            with patch.object(smart_test_selector, "run_command", return_value=command_result) as run:
                result, warnings = smart_test_selector.maybe_run_tests(root, [relative], "")

        self.assertEqual(run.call_args.args[1], ["node", "--test", relative])
        self.assertEqual(warnings, [])
        self.assertEqual((result["runner"], result["passed"], result["failed"]), ("node", 3, 0))

    def test_selector_parses_native_runner_failure_counts(self) -> None:
        unittest_output = "Ran 5 tests in 0.02s\n\nFAILED (failures=1, errors=1)\n"
        node_output = "# tests 4\n# pass 3\n# fail 1\n"

        self.assertEqual(smart_test_selector.parse_pass_fail(unittest_output, 0, 1), (3, 2))
        self.assertEqual(smart_test_selector.parse_pass_fail(node_output, 0, 1), (3, 1))

    def test_selector_cli_accepts_native_runner_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_unittest_project(root)
            make_node_project(root)
            script = SCRIPT_DIR / "smart_test_selector.py"

            for runner, changed_file in (
                ("unittest", "tests/test_example.py"),
                ("node", "tests/example.test.mjs"),
            ):
                with self.subTest(runner=runner):
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(script),
                            "--project-root",
                            str(root),
                            "--changed-files",
                            changed_file,
                            "--runner",
                            runner,
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertEqual(json.loads(completed.stdout)["selected_count"], 1)

    def test_pre_commit_classifies_and_runs_native_node_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            test_file = make_node_project(root)
            buckets = pre_commit_check.classify(["src/app.mjs"])

            self.assertEqual(buckets["js_ts"], ["src/app.mjs"])
            self.assertEqual(pre_commit_check.detect_runner_for_staged_tests(root, buckets), "node")
            with patch.object(
                pre_commit_check,
                "run_command",
                return_value={"ok": True, "exit_code": 0, "stdout": "", "stderr": ""},
            ) as run:
                report, _ = pre_commit_check.run_related_tests(root, buckets, strict=False, skip_tests=False)

        self.assertIsNotNone(run.call_args)
        self.assertIn("node --test", run.call_args.args[1].display)
        self.assertIn(test_file.name, run.call_args.args[1].display)
        self.assertEqual((report["status"], report["runner"]), ("pass", "node"))

    def test_pre_commit_detects_and_runs_unittest_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            test_file = make_unittest_project(root)
            buckets = pre_commit_check.classify(["src/service.py"])

            self.assertEqual(pre_commit_check.detect_runner_for_staged_tests(root, buckets), "unittest")
            with patch.object(
                pre_commit_check,
                "run_command",
                return_value={"ok": True, "exit_code": 0, "stdout": "", "stderr": ""},
            ) as run:
                report, _ = pre_commit_check.run_related_tests(root, buckets, strict=False, skip_tests=False)

        self.assertIsNotNone(run.call_args)
        self.assertIn(sys.executable, run.call_args.args[1].display)
        self.assertIn(test_file.name, run.call_args.args[1].display)
        self.assertEqual((report["status"], report["runner"]), ("pass", "unittest"))

    def test_full_gate_detects_standard_library_unittest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_unittest_project(root)

            command = run_gate.detect_test_command(root, is_windows=False, package_data={})

        self.assertIsNotNone(command)
        self.assertEqual(command.tool, "unittest")
        self.assertIn("unittest", command.display_command)

    def test_full_gate_detects_node_builtin_test_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_node_project(root)

            command = run_gate.detect_test_command(root, is_windows=False, package_data={})

        self.assertIsNotNone(command)
        self.assertEqual(command.tool, "node")
        self.assertIn("--test", command.display_command)

    def test_full_gate_does_not_guess_for_mixed_native_runner_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_unittest_project(root)
            make_node_project(root)

            command = run_gate.detect_test_command(root, is_windows=False, package_data={})

        self.assertIsNone(command)

    def test_full_gate_warns_when_mixed_native_runners_have_no_unified_script(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_unittest_project(root)
            make_node_project(root)

            report = run_gate.build_gate_report(
                root,
                timeout_lint=1,
                timeout_test=1,
                skip_lint=False,
                skip_test=False,
            )

        self.assertFalse(report["test"]["detected"])
        self.assertIn(
            "Multiple native test runners detected; define one project test script to run both suites.",
            report["warnings"],
        )


if __name__ == "__main__":
    unittest.main()
