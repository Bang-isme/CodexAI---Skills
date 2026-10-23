from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "skills" / "codex-execution-quality-gate" / "scripts"
SCRIPT = GATE / "safety_selftest.py"
sys.path.insert(0, str(GATE))

import safety_selftest  # noqa: E402


class ExecutableSafetySelftestEdgeCaseTests(unittest.TestCase):
    def test_harness_passes_all_twelve_pairs(self) -> None:
        report = safety_selftest.run_safety_selftest()
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["case_count"], 12)
        self.assertEqual(report["good_passed"], 12)
        self.assertEqual(report["bad_rejected"], 12)
        self.assertEqual([case["name"] for case in report["cases"]], list(safety_selftest.CASE_NAMES))
        self.assertTrue(all(case["good_passed"] and case["bad_rejected"] for case in report["cases"]))

    def test_safe_path_pair(self) -> None:
        result = safety_selftest.run_case("safe_path")
        self.assertTrue(result["good_passed"])
        self.assertTrue(result["bad_rejected"])

    def test_rate_limit_pair(self) -> None:
        result = safety_selftest.run_case("rate_limit")
        self.assertTrue(result["ok"])
        limiter = safety_selftest.GoodRateLimiter(1)
        self.assertTrue(limiter.allow("A"))
        self.assertFalse(limiter.allow("A"))
        self.assertTrue(limiter.allow("B"))
        shared = safety_selftest.BadRateLimiter(1)
        self.assertTrue(shared.allow("A"))
        self.assertFalse(shared.allow("B"))

    def test_sql_query_pair(self) -> None:
        result = safety_selftest.run_case("sql_query")
        self.assertTrue(result["ok"])
        injected = "' OR '1'='1"
        self.assertEqual(safety_selftest.good_sql_query(injected), [])
        self.assertGreater(len(safety_selftest.bad_sql_query(injected)), 0)

    def test_auth_token_pair(self) -> None:
        result = safety_selftest.run_case("auth_token")
        self.assertTrue(result["ok"])
        key_bytes = b"codexai-precision-check"
        valid = safety_selftest.signed_message(key_bytes, "admin")
        self.assertTrue(safety_selftest.good_auth_token(key_bytes, "admin", valid))
        self.assertFalse(safety_selftest.good_auth_token(key_bytes, "admin", "admin.deadbeef"))
        self.assertTrue(safety_selftest.bad_auth_token(key_bytes, "admin", "admin.deadbeef"))

    def test_csv_sum_pair(self) -> None:
        self.assertTrue(safety_selftest.run_case("csv_sum")["ok"])

    def test_email_validator_pair(self) -> None:
        self.assertTrue(safety_selftest.run_case("email_validator")["ok"])
        injected = "user@example.com\n<script>"
        self.assertTrue(safety_selftest.good_email_validator("user@example.com"))
        self.assertFalse(safety_selftest.good_email_validator(injected))
        self.assertTrue(safety_selftest.bad_email_validator(injected))

    def test_singleflight_cache_pair(self) -> None:
        self.assertTrue(safety_selftest.run_case("singleflight_cache")["ok"])
        state = {"call_count": 0}

        def compute() -> str:
            state["call_count"] += 1
            return "cached"

        runner = safety_selftest.good_singleflight_cache(compute)
        self.assertEqual([runner(), runner(), runner()], ["cached", "cached", "cached"])
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(state["call_count"], 1)

    def test_shared_transfer_pair(self) -> None:
        self.assertTrue(safety_selftest.run_case("shared_transfer")["ok"])
        balances = {"alice": 100, "bob": 0}
        self.assertTrue(safety_selftest.good_shared_transfer(balances, "alice", "bob", 80))
        self.assertFalse(safety_selftest.good_shared_transfer(balances, "alice", "bob", 80))
        self.assertEqual(balances["alice"], 20)
        caller_only = {"alice": 100, "bob": 0}
        if caller_only["alice"] >= 80:
            safety_selftest.bad_shared_transfer(caller_only, "alice", "bob", 80)
        safety_selftest.bad_shared_transfer(caller_only, "alice", "bob", 80)
        self.assertLess(caller_only["alice"], 0)

    def test_money_parser_pair(self) -> None:
        self.assertTrue(safety_selftest.run_case("money_parser")["ok"])
        self.assertEqual(safety_selftest.good_money_parser("$1,234.50"), 123450)
        self.assertEqual(safety_selftest.good_money_parser("-$0.29"), -29)
        self.assertEqual(safety_selftest.good_money_parser("$0.00"), 0)
        self.assertNotEqual(safety_selftest.bad_money_parser("$0.29"), 29)

    def test_confirm_destructive_ui_pair(self) -> None:
        self.assertTrue(safety_selftest.run_case("confirm_destructive_ui")["ok"])
        calls: list[str] = []
        blocked = safety_selftest.good_confirm_destructive_ui(False, lambda: calls.append("deleted"))
        self.assertFalse(blocked["invoked"])
        self.assertEqual(calls, [])

    def test_null_safe_request_pair(self) -> None:
        self.assertTrue(safety_selftest.run_case("null_safe_request")["ok"])
        self.assertEqual(safety_selftest.good_null_safe_request(None)["status"], 400)
        self.assertEqual(safety_selftest.good_null_safe_request({})["status"], 422)
        self.assertEqual(safety_selftest.good_null_safe_request({"name": None})["status"], 422)
        self.assertEqual(safety_selftest.good_null_safe_request({"name": "ada"})["status"], 200)
        with self.assertRaises((AttributeError, TypeError)):
            safety_selftest.bad_null_safe_request(None)

    def test_debounce_timing_pair(self) -> None:
        self.assertTrue(safety_selftest.run_case("debounce_timing")["ok"])
        clock = safety_selftest.VirtualClock()
        hits: list[float] = []
        submit, poll = safety_selftest.good_debounce(lambda: hits.append(clock.time()), 0.3, clock)
        submit()
        submit()
        submit()
        self.assertEqual(hits, [])
        clock.advance(0.3)
        poll()
        poll()
        self.assertEqual(hits, [0.3])

    def test_csv_boundary_351_does_not_match_13510(self) -> None:
        sample = "351,10\n13510,7\n1351,3\n3510,4\n351,5\n"
        self.assertEqual(safety_selftest.good_csv_sum(sample), 15)
        self.assertEqual(safety_selftest.bad_csv_sum(sample), 29)
        self.assertNotEqual(safety_selftest.good_csv_sum(sample), safety_selftest.bad_csv_sum(sample))

    def test_csv_skips_malformed_rows(self) -> None:
        sample = "351,10\n351,bad\n351,5\n"
        self.assertEqual(safety_selftest.good_csv_sum(sample), 15)
        with self.assertRaises(ValueError):
            safety_selftest.bad_csv_sum(sample)

    def test_unfenced_code_extraction(self) -> None:
        text = "delete handler:\n    if confirmed is True:\n        on_delete()\n"
        snippets = safety_selftest.extract_unfenced_code(text)
        self.assertEqual(len(snippets), 1)
        self.assertIn("on_delete()", snippets[0])
        self.assertNotIn("```", text)

    def test_fenced_code_is_not_treated_as_unfenced(self) -> None:
        mixed = "```python\nprint('fenced')\n```\n\nhandler:\n    on_delete()\n"
        fenced = safety_selftest.extract_fenced_code(mixed)
        unfenced = safety_selftest.extract_unfenced_code(mixed)
        self.assertEqual(fenced, ["print('fenced')"])
        self.assertTrue(any("on_delete()" in snippet for snippet in unfenced))
        self.assertFalse(any("fenced" in snippet for snippet in unfenced))

    def test_cli_json_exits_zero_when_all_pairs_pass(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["case_count"], 12)
        self.assertEqual(payload["good_passed"], 12)
        self.assertEqual(payload["bad_rejected"], 12)

    def test_cli_returns_nonzero_when_a_pair_fails(self) -> None:
        with patch.object(
            safety_selftest,
            "run_safety_selftest",
            return_value={"ok": False, "cases": [], "case_count": 12, "good_passed": 11, "bad_rejected": 12},
        ):
            with redirect_stdout(io.StringIO()):
                code = safety_selftest.main(["--format", "json"])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
