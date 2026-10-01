from __future__ import annotations

import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILLS_ROOT / ".system" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import local_release_gate  # noqa: E402


class LocalReleaseGateOutputTests(unittest.TestCase):
    def test_json_output_handles_legacy_windows_console_encoding(self) -> None:
        output = io.BytesIO()
        console = io.TextIOWrapper(output, encoding="cp1252", errors="strict")

        def passing_step(label: str, args: list[str], *, cwd: Path | None = None) -> dict[str, object]:
            return {
                "name": label,
                "ok": True,
                "exit_code": 0,
                "command": args,
                "payload": {"status": "pass", "detail": "Đánh giá giao diện"},
            }

        with (
            patch.object(local_release_gate.sys, "argv", ["local_release_gate.py", "--format", "json"]),
            patch.object(local_release_gate.sys, "stdout", console),
            patch.object(local_release_gate, "run_step", side_effect=passing_step),
        ):
            exit_code = local_release_gate.main()

        console.flush()
        rendered = output.getvalue().decode("utf-8")
        self.assertEqual(exit_code, 0)
        self.assertIn("Đánh giá giao diện", rendered)


if __name__ == "__main__":
    unittest.main()
