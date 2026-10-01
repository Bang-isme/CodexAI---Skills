from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILLS_ROOT / ".system" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import pipeline  # noqa: E402


class PipelineStatusTests(unittest.TestCase):
    def test_advisory_warning_is_reported_without_becoming_a_pass(self) -> None:
        warning_step = {
            "name": "install_doctor",
            "ok": True,
            "exit_code": 0,
            "duration_s": 0.1,
            "command": [],
            "payload": {
                "status": "warn",
                "warnings": ["optional session hook is not installed"],
            },
        }
        with patch.object(pipeline, "stage_lint", return_value=[warning_step]):
            report = pipeline.run_pipeline(
                project_root=SKILLS_ROOT.parent,
                skills_root=SKILLS_ROOT,
                stages=["lint"],
            )

        self.assertEqual(report["status"], "warn")
        self.assertEqual(report["warnings"], ["install_doctor"])
        self.assertEqual(report["stages"][0]["status"], "warn")
        self.assertIn("review warning", report["next"])


if __name__ == "__main__":
    unittest.main()
