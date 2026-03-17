from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pre_commit_check = load_script_module(
    "skills_pre_commit_check",
    "codex-execution-quality-gate/scripts/pre_commit_check.py",
)


def git(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def test_pre_commit_blocks_mojibake_in_staged_docs(tmp_path: Path) -> None:
    git(tmp_path, "init")
    write_text(
        tmp_path / "README.md",
        "CodexAI Skill Pack ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â deterministic workflows.\n",
    )
    git(tmp_path, "add", "README.md")

    payload, code = pre_commit_check.run_pre_commit(tmp_path, strict=False, skip_tests=True)

    assert code == 1
    assert payload["status"] == "fail"
    assert "mojibake_scan" in payload["blocking"]
    check = next(item for item in payload["results"] if item["check"] == "mojibake_scan")
    assert check["status"] == "fail"
    assert check["files"] == 1


def test_pre_commit_allows_clean_utf8_docs(tmp_path: Path) -> None:
    git(tmp_path, "init")
    write_text(
        tmp_path / "docs" / "huong-dan-vi.md",
        "# Hướng Dẫn\nLập kế hoạch → thực thi → xác minh.\n",
    )
    git(tmp_path, "add", "docs/huong-dan-vi.md")

    payload, code = pre_commit_check.run_pre_commit(tmp_path, strict=False, skip_tests=True)

    assert code == 0
    check = next(item for item in payload["results"] if item["check"] == "mojibake_scan")
    assert check["status"] == "pass"
