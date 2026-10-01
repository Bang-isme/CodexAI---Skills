from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / ".system" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import trust_harness  # noqa: E402


NODE_FIXTURE = """import test from 'node:test';
import assert from 'node:assert/strict';

test('fixture passes', () => assert.equal(2, 2));
"""
RESPONSIVE_FIXTURES = (
    "responsive_capture_stitch.test.mjs",
    "responsive_capture_core.test.mjs",
    "responsive_capture_browser.test.mjs",
)


class TrustHarnessCurrentSuiteTests(unittest.TestCase):
    def test_run_tests_executes_checked_in_python_and_node_suite_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills_root = Path(temporary) / "skills"
            tests_root = skills_root / "tests"
            tests_root.mkdir(parents=True)
            (tests_root / "test_fixture.py").write_text(
                "import unittest\n\n"
                "class FixtureTest(unittest.TestCase):\n"
                "    def test_passes(self):\n"
                "        self.assertEqual(2, 2)\n",
                encoding="utf-8",
            )
            for filename in RESPONSIVE_FIXTURES:
                (tests_root / filename).write_text(NODE_FIXTURE, encoding="utf-8")

            checks: list[dict[str, object]] = []
            trust_harness.run_tests(skills_root, checks, skip_tests=False)

        self.assertEqual([item["name"] for item in checks], ["python_unittest", "responsive_capture_tests"])
        self.assertEqual(checks[0]["status"], "pass")
        expected_node_status = "pass" if shutil.which("node") else "warn"
        self.assertEqual(checks[1]["status"], expected_node_status)

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_skipped_node_fixture_is_reported_as_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills_root = Path(temporary) / "skills"
            tests_root = skills_root / "tests"
            tests_root.mkdir(parents=True)
            (tests_root / "test_fixture.py").write_text(
                "import unittest\n\n"
                "class FixtureTest(unittest.TestCase):\n"
                "    def test_passes(self):\n"
                "        self.assertEqual(2, 2)\n",
                encoding="utf-8",
            )
            for filename in RESPONSIVE_FIXTURES:
                content = NODE_FIXTURE
                if filename == "responsive_capture_browser.test.mjs":
                    content = "import test from 'node:test';\ntest('browser fixture', { skip: true }, () => {});\n"
                (tests_root / filename).write_text(content, encoding="utf-8")

            checks: list[dict[str, object]] = []
            trust_harness.run_tests(skills_root, checks, skip_tests=False)

        self.assertEqual(checks[0]["status"], "pass")
        self.assertEqual(checks[1]["status"], "warn")
        self.assertIn("skip", str(checks[1]["detail"]).lower())

    def test_skip_tests_is_reported_as_warning_not_as_a_pass(self) -> None:
        checks: list[dict[str, object]] = []
        trust_harness.run_tests(Path("skills"), checks, skip_tests=True)

        self.assertEqual([item["status"] for item in checks], ["warn", "warn"])
        self.assertEqual(trust_harness.summarize(checks)["status"], "warn")


if __name__ == "__main__":
    unittest.main()
