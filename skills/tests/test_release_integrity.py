from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"
ROOT_README = REPO_ROOT / "README.md"
SKILLS_README = SKILLS_ROOT / "README.md"
CHANGELOG = SKILLS_ROOT / "CHANGELOG.md"
VERSION = SKILLS_ROOT / "VERSION"
MANIFEST = SKILLS_ROOT / ".system" / "manifest.json"
BENCHMARK = SKILLS_ROOT / "tests" / "benchmark_quality.py"

EXPECTED_PYTEST = 142
EXPECTED_SMOKE = 51
EXPECTED_TOTAL = EXPECTED_PYTEST + EXPECTED_SMOKE


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_release_version_metadata_matches_single_source_of_truth() -> None:
    version = read(VERSION).strip()
    manifest = json.loads(read(MANIFEST))
    root_readme = read(ROOT_README)
    skills_readme = read(SKILLS_README)
    changelog = read(CHANGELOG)

    assert manifest["version"] == version
    assert f"version-{version}-blue" in root_readme
    assert f"| Version | `{version}` |" in skills_readme
    assert changelog.startswith(f"# Changelog\n\n## [{version}]")


def test_public_test_count_metadata_matches_verified_suite_target() -> None:
    root_readme = read(ROOT_README)
    skills_readme = read(SKILLS_README)
    changelog = read(CHANGELOG)

    assert f"pytest-{EXPECTED_PYTEST}%2F{EXPECTED_PYTEST}%20passed" in root_readme
    assert f"smoke-{EXPECTED_SMOKE}%2F{EXPECTED_SMOKE}%20passed" in root_readme
    assert f"{EXPECTED_PYTEST} unit + {EXPECTED_SMOKE} smoke = {EXPECTED_TOTAL} tests" in root_readme
    assert f"| Pytest | {EXPECTED_PYTEST}/{EXPECTED_PYTEST} |" in skills_readme
    assert f"| Smoke | {EXPECTED_SMOKE}/{EXPECTED_SMOKE} |" in skills_readme
    assert f"`{EXPECTED_PYTEST}` unit tests + `{EXPECTED_SMOKE}` smoke checks" in changelog


def test_benchmark_version_and_documented_scope_are_current() -> None:
    benchmark_source = read(BENCHMARK)
    root_readme = read(ROOT_README)
    changelog = read(CHANGELOG)

    match = re.search(r'^BENCHMARK_VERSION = "([^"]+)"$', benchmark_source, re.MULTILINE)
    assert match, "benchmark_quality.py must declare BENCHMARK_VERSION"
    assert match.group(1) == "1.2"
    assert "12-case static corpus" in root_readme
    assert "output score, editorial score, quality index, and expectation hit rate" in changelog
