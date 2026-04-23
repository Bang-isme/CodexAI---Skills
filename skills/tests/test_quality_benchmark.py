from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = SKILLS_ROOT / "tests" / "benchmark_quality.py"


def run_benchmark(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(BENCHMARK), *args],
        capture_output=True,
        check=False,
        timeout=20,
    )


def test_quality_benchmark_runs_with_utf8_corpus_output() -> None:
    result = run_benchmark()
    assert result.returncode == 0
    payload = json.loads(result.stdout.decode("utf-8"))
    assert payload["status"] == "pass"
    assert payload["test_cases"] >= 12
    assert payload["corpus_cases"] >= 7
    assert payload["avg_score_with_pack"] > payload["avg_score_without_pack"]
    assert payload["avg_editorial_score_with_pack"] > payload["avg_editorial_score_without_pack"]
    assert payload["avg_quality_index_with_pack"] > payload["avg_quality_index_without_pack"]
    assert payload["avg_expectation_hit_rate_with_pack"] > payload["avg_expectation_hit_rate_without_pack"]
    assert all(case["with_pack"]["status"] == "pass" for case in payload["per_case"])
    assert all(case["with_pack"]["editorial_status"] == "pass" for case in payload["per_case"])


def test_quality_benchmark_reports_invalid_corpus_json_as_json_error(tmp_path: Path) -> None:
    (tmp_path / "broken.json").write_text("{", encoding="utf-8-sig")
    result = run_benchmark("--corpus-dir", str(tmp_path))
    assert result.returncode == 2
    payload = json.loads(result.stdout.decode("utf-8"))
    assert payload["status"] == "error"
    assert "invalid JSON" in payload["message"]
    assert "BOM" not in payload["message"]


def test_quality_benchmark_accepts_string_expectation_values(tmp_path: Path) -> None:
    corpus = [
        {
            "name": "single_string_expectation",
            "input_prompt": "Summarize release status",
            "expectations": {"decision": "Decision"},
            "sample_with_pack": [
                "Decision: keep the release candidate open until the smoke test is rerun.",
                "Evidence: run `python skills/tests/smoke_test.py` and verify 51/51 pass.",
                "Risk: stale smoke evidence can make the release note misleading.",
                "Next step: assign the release owner before publishing.",
            ],
            "sample_without_pack": "The release is mostly fine and should be checked again.",
        }
    ]
    (tmp_path / "single.json").write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    result = run_benchmark("--corpus-dir", str(tmp_path))
    assert result.returncode == 0
    payload = json.loads(result.stdout.decode("utf-8"))
    assert payload["corpus_cases"] == 1
    case = payload["per_case"][-1]
    assert case["name"] == "single_string_expectation"
    assert case["with_pack"]["expectation_hits"]["decision"] is True


def test_quality_benchmark_accepts_bom_encoded_corpus_json(tmp_path: Path) -> None:
    corpus = [
        {
            "name": "bom_encoded_corpus",
            "input_prompt": "Create a release handoff",
            "expectations": {"decision": "Decision"},
            "sample_with_pack": [
                "Decision: publish after the release integrity test passes.",
                "Evidence: run `python -m pytest skills/tests/test_release_integrity.py -q` and confirm 3/3 pass.",
                "Risk: publishing without the metadata guard can leave README stats stale.",
                "Next step: keep release badges tied to the integrity test.",
            ],
            "sample_without_pack": "The release looks okay and should be published soon.",
        }
    ]
    (tmp_path / "bom.json").write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8-sig")
    result = run_benchmark("--corpus-dir", str(tmp_path))
    assert result.returncode == 0
    payload = json.loads(result.stdout.decode("utf-8"))
    assert payload["corpus_cases"] == 1
    assert payload["per_case"][-1]["name"] == "bom_encoded_corpus"
