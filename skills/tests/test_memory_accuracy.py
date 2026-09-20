from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from test_full_cycle_hardening import (
    codebase_indexer,
    knowledge_graph,
    knowledge_index,
    memory_status,
    project_traversal,
    write,
)


SKILLS_ROOT = Path(__file__).resolve().parents[1]
BUILD_INDEX_SCRIPT = SKILLS_ROOT / "codex-project-memory" / "scripts" / "build_knowledge_index.py"


def load_redaction():
    path = SKILLS_ROOT / "codex-project-memory" / "scripts" / "redaction.py"
    spec = importlib.util.spec_from_file_location("memory_accuracy_redaction", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_indexer_respects_gitignore_and_codexignore(tmp_path: Path) -> None:
    write(tmp_path / ".gitignore", "ignored-by-git/\n*.tmp\n")
    write(tmp_path / ".codexignore", "ignored-by-codex/\nsecret.txt\n")
    write(tmp_path / "src" / "keep.py", "def keep():\n    return True\n")
    write(tmp_path / "ignored-by-git" / "skip.py", "def skip():\n    return False\n")
    write(tmp_path / "ignored-by-codex" / "skip.py", "def skip():\n    return False\n")
    write(tmp_path / "notes.tmp", "temporary\n")
    write(tmp_path / "secret.txt", "secret\n")

    discovered = codebase_indexer.discover_files(tmp_path, max_files=50)
    rels = [path.relative_to(tmp_path).as_posix() for path in discovered]

    assert "src/keep.py" in rels
    assert "ignored-by-git/skip.py" not in rels
    assert "ignored-by-codex/skip.py" not in rels
    assert "notes.tmp" not in rels
    assert "secret.txt" not in rels


def test_indexer_and_traversal_share_capped_sorted_file_set(tmp_path: Path) -> None:
    for index in range(12):
        write(tmp_path / "src" / f"file_{index:02d}.py", f"def fn_{index}():\n    return {index}\n")
    config = project_traversal.TraversalConfig(max_files=5)

    listing = project_traversal.list_project_files(
        tmp_path,
        config,
        file_filter=codebase_indexer.indexable_file_filter,
    )
    discovered = codebase_indexer.discover_files(tmp_path, max_files=5, traversal_config=config)

    assert [entry.rel_path for entry in listing.files] == [
        path.relative_to(tmp_path).as_posix() for path in discovered
    ]
    assert [entry.rel_path for entry in listing.files] == sorted(entry.rel_path for entry in listing.files)
    assert len(listing.files) == 5


def test_query_index_finds_tokens_beyond_preview(tmp_path: Path) -> None:
    unique = "zxqvuniqueidentifier42"
    lines = ["def header():", "    return 1"] + [f"    # filler {index}" for index in range(40)] + [f"    return '{unique}'"]
    write(tmp_path / "src" / "deep.py", "\n".join(lines) + "\n")

    index = codebase_indexer.build_codebase_index(
        tmp_path,
        output_path=tmp_path / ".codex" / "knowledge" / "codebase-index.json",
        rebuild=True,
    )
    hits = codebase_indexer.query_index(index, unique, top_k=5)

    assert hits
    body = str(hits[0].get("text") or "")
    preview = str(hits[0].get("text_preview") or "")
    assert unique in body
    assert unique not in preview


def test_incremental_reuses_unchanged_file_payload(tmp_path: Path) -> None:
    write(tmp_path / "src" / "stable.py", "def stable():\n    return 1\n")
    write(tmp_path / "src" / "changing.py", "def changing():\n    return 1\n")
    output = tmp_path / ".codex" / "knowledge" / "codebase-index.json"

    first = codebase_indexer.build_codebase_index(tmp_path, output_path=output, rebuild=True)
    first_stable_at = first["files"]["src/stable.py"]["last_indexed_at"]
    first_chunk_ids = set(first["files"]["src/stable.py"]["chunks"])

    write(tmp_path / "src" / "changing.py", "def changing():\n    return 2\n")
    second = codebase_indexer.build_codebase_index(tmp_path, output_path=output, incremental=True, rebuild=False)

    assert second["incremental"]["reused_files"] == 1
    assert second["incremental"]["indexed_files"] == 1
    assert second["files"]["src/stable.py"]["last_indexed_at"] == first_stable_at
    assert set(second["files"]["src/stable.py"]["chunks"]) == first_chunk_ids
    assert second["files"]["src/changing.py"]["last_indexed_at"] != first["files"]["src/changing.py"]["last_indexed_at"]


def test_redaction_preserves_git_sha_and_content_hash(tmp_path: Path) -> None:
    redaction = load_redaction()
    git_sha = "a" * 40
    digest = "b" * 64
    md5_like = "c" * 32
    secret = "sk-sampleSecretKey1234567890"

    redacted = redaction.redact_text(f"commit {git_sha} hash {digest} md5 {md5_like} key {secret}")
    assert git_sha in redacted
    assert digest in redacted
    assert "[REDACTED]" in redacted
    assert md5_like not in redacted
    assert secret not in redacted

    write(tmp_path / "src" / "hashed.py", f"COMMIT = '{git_sha}'\n")
    index = codebase_indexer.build_codebase_index(
        tmp_path,
        output_path=tmp_path / ".codex" / "knowledge" / "codebase-index.json",
        rebuild=True,
    )
    stored_hash = index["files"]["src/hashed.py"]["content_hash"]
    assert len(stored_hash) == 64
    assert stored_hash == stored_hash.lower()
    assert git_sha in json.dumps(index)


def test_graph_reuses_prebuilt_index_and_stays_coherent(tmp_path: Path) -> None:
    write(tmp_path / "src" / "app.py", "def run():\n    return True\n")
    write(tmp_path / "src" / "util.py", "def helper():\n    return 2\n")
    output = tmp_path / ".codex" / "knowledge" / "codebase-index.json"
    config = project_traversal.TraversalConfig(max_files=50)

    index = codebase_indexer.build_codebase_index(
        tmp_path,
        output_path=output,
        rebuild=True,
        traversal_config=config,
    )
    generated_at = index["generated_at"]
    graph = knowledge_graph.build_graph(
        tmp_path,
        include_tests=True,
        traversal_config=config,
        codebase_index=index,
    )
    rewritten = json.loads(output.read_text(encoding="utf-8"))

    assert rewritten["generated_at"] == generated_at
    assert graph["redaction"]["enabled"] is True
    assert graph["redaction_applied"] is True
    graph_files = set(graph["code_index"].keys())
    index_code_files = {
        path
        for path in index["files"]
        if Path(path).suffix.lower() in knowledge_graph.LANGUAGE_REGISTRY
    }
    assert graph_files == index_code_files
    assert graph["coherence"]["graph_only"] == []
    assert graph["coherence"]["codebase_only"] == []


def test_knowledge_build_does_not_rebuild_index_twice(tmp_path: Path) -> None:
    write(tmp_path / "src" / "app.py", "def run():\n    return True\n")
    payload = knowledge_index.write_knowledge_artifacts(tmp_path, tmp_path / ".codex" / "knowledge")
    index_path = Path(payload["codebase_index_path"])
    first = json.loads(index_path.read_text(encoding="utf-8"))
    graph = json.loads(Path(payload["graph_path"]).read_text(encoding="utf-8"))
    assert graph["codebase_index"]["generated_at"] == first["generated_at"]
    assert graph["redaction_applied"] is True
    assert graph["redaction"]["enabled"] is True


def test_traversal_hard_skips_build_output_and_backup_dirs(tmp_path: Path) -> None:
    write(tmp_path / "src" / "main.rs", "fn main() {}\n")
    write(tmp_path / "target" / "debug" / "generated.rs", "fn junk() {}\n")
    write(tmp_path / ".codexai-backups" / "old" / "SKILL.md", "# stale backup\n")
    write(tmp_path / "node_modules" / "pkg" / "index.js", "module.exports = 1;\n")

    listing = project_traversal.list_project_files(tmp_path, project_traversal.TraversalConfig())
    rels = [entry.rel_path for entry in listing.files]

    assert rels == ["src/main.rs"]
    assert "target" in project_traversal.HARD_CODED_SKIP_DIRS
    assert ".codexai-backups" in project_traversal.HARD_CODED_SKIP_DIRS
    assert not hasattr(knowledge_index, "IGNORED_DIRS")


def test_atomic_write_keeps_previous_artifact_when_write_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / ".codex" / "knowledge" / "index.json"
    project_traversal.atomic_write_text(target, '{"v": 1}')
    assert json.loads(target.read_text(encoding="utf-8")) == {"v": 1}

    original_write_text = Path.write_text

    def exploding_write_text(self: Path, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self.name.endswith(".tmp"):
            self.touch()
            raise OSError("disk full mid-write")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", exploding_write_text)
    with pytest.raises(OSError):
        project_traversal.atomic_write_text(target, '{"v": 2}')
    monkeypatch.undo()

    assert json.loads(target.read_text(encoding="utf-8")) == {"v": 1}
    assert [path.name for path in target.parent.iterdir()] == ["index.json"]


def test_knowledge_artifacts_are_written_without_leftover_temp_files(tmp_path: Path) -> None:
    write(tmp_path / "src" / "app.py", "def run():\n    return True\n")
    output_dir = tmp_path / ".codex" / "knowledge"
    knowledge_index.write_knowledge_artifacts(tmp_path, output_dir, write_html=True)

    names = sorted(path.name for path in output_dir.iterdir())
    assert not [name for name in names if name.endswith(".tmp")]
    for expected in ("index.json", "INDEX.md", "knowledge-graph.json", "codebase-index.json", "index.html"):
        assert expected in names


def test_index_records_source_fingerprint_stable_across_builds(tmp_path: Path) -> None:
    write(tmp_path / "src" / "app.py", "def run():\n    return True\n")
    output_dir = tmp_path / ".codex" / "knowledge"

    knowledge_index.write_knowledge_artifacts(tmp_path, output_dir)
    first = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))["source"]
    knowledge_index.write_knowledge_artifacts(tmp_path, output_dir)
    second = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))["source"]

    assert first["tree_fingerprint"] == second["tree_fingerprint"]
    assert len(first["tree_fingerprint"]) == 64
    assert first["files_counted"] == 1
    assert "git_head" in first

    write(tmp_path / "src" / "extra.py", "def extra():\n    return 2\n")
    knowledge_index.write_knowledge_artifacts(tmp_path, output_dir)
    third = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))["source"]
    assert third["tree_fingerprint"] != first["tree_fingerprint"]


def test_memory_status_warns_when_index_is_behind_head_or_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write(tmp_path / "src" / "app.py", "def run():\n    return True\n")
    output_dir = tmp_path / ".codex" / "knowledge"
    knowledge_index.write_knowledge_artifacts(tmp_path, output_dir)
    index_path = output_dir / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["source"]["git_head"] = "a" * 40
    index_path.write_text(json.dumps(index), encoding="utf-8")

    monkeypatch.setattr(memory_status, "git_head", lambda _root: "b" * 40)
    payload = memory_status.build_status(tmp_path, output_dir, max_age_hours=168)
    assert payload["status"] == "warn"
    assert payload["source"]["git_head"] == "drift"
    assert any("HEAD" in warning for warning in payload["warnings"])

    monkeypatch.setattr(memory_status, "git_head", lambda _root: "a" * 40)
    clean = memory_status.build_status(tmp_path, output_dir, max_age_hours=168, verify_tree=True)
    assert clean["source"]["git_head"] == "match"
    assert clean["source"]["tree_fingerprint"] == "match"
    assert not any("HEAD" in warning for warning in clean["warnings"])

    write(tmp_path / "src" / "added.py", "def added():\n    return 3\n")
    drifted = memory_status.build_status(tmp_path, output_dir, max_age_hours=168, verify_tree=True)
    assert drifted["source"]["tree_fingerprint"] == "drift"
    assert any("tree_fingerprint" in warning for warning in drifted["warnings"])


def test_memory_status_tolerates_index_without_source_block(tmp_path: Path) -> None:
    write(tmp_path / "src" / "app.py", "def run():\n    return True\n")
    output_dir = tmp_path / ".codex" / "knowledge"
    knowledge_index.write_knowledge_artifacts(tmp_path, output_dir)
    index_path = output_dir / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index.pop("source", None)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    payload = memory_status.build_status(tmp_path, output_dir, max_age_hours=168, verify_tree=True)
    assert payload["status"] != "fail"
    assert payload["source"]["git_head"] == "not_recorded"
    assert payload["source"]["tree_fingerprint"] == "not_recorded"


def test_indexer_handles_unicode_paths(tmp_path: Path) -> None:
    write(tmp_path / "src" / "tiếng-việt" / "mô_đun.py", "def chào():\n    return 'xin chào'\n")
    write(tmp_path / "docs" / "説明.md", "# 説明\n")
    output = tmp_path / ".codex" / "knowledge" / "codebase-index.json"

    index = codebase_indexer.build_codebase_index(tmp_path, output_path=output, rebuild=True)
    assert "src/tiếng-việt/mô_đun.py" in index["files"]
    assert "docs/説明.md" in index["files"]
    reloaded = json.loads(output.read_text(encoding="utf-8"))
    assert set(reloaded["files"]) == set(index["files"])
    assert project_traversal.tree_fingerprint(
        [{"rel_path": "src/tiếng-việt/mô_đun.py", "size_bytes": 1}]
    ) == project_traversal.tree_fingerprint([{"rel_path": "src/tiếng-việt/mô_đun.py", "size_bytes": 1}])


def test_large_file_hash_uses_sampled_prefix_and_size(tmp_path: Path) -> None:
    big = tmp_path / "big.py"
    head = b"# header\n" * 1000
    big.write_bytes(head + b"x" * 50_000)
    size = big.stat().st_size

    sampled = codebase_indexer.content_hash(big, max_bytes=4096, size_bytes=size)
    full = codebase_indexer.content_hash(big)
    assert sampled != full
    assert sampled == codebase_indexer.content_hash(big, max_bytes=4096, size_bytes=size)

    big.write_bytes(head + b"y" * 50_000)
    assert codebase_indexer.content_hash(big, max_bytes=4096, size_bytes=big.stat().st_size) == sampled
    big.write_bytes(head + b"y" * 50_001)
    assert codebase_indexer.content_hash(big, max_bytes=4096, size_bytes=big.stat().st_size) != sampled
    small = tmp_path / "small.py"
    small.write_bytes(b"tiny")
    assert codebase_indexer.content_hash(small, max_bytes=4096, size_bytes=4) == codebase_indexer.content_hash(small)


def test_build_knowledge_index_cli_defaults_to_incremental(tmp_path: Path) -> None:
    import subprocess

    write(tmp_path / "src" / "app.py", "def run():\n    return True\n")
    base = [sys.executable, str(BUILD_INDEX_SCRIPT), "--project-root", str(tmp_path), "--format", "json"]

    first = json.loads(subprocess.run(base, capture_output=True, text=True, encoding="utf-8", check=True).stdout)
    assert first["status"] == "built"
    second = json.loads(subprocess.run(base, capture_output=True, text=True, encoding="utf-8", check=True).stdout)
    codebase = json.loads(Path(second["codebase_index_path"]).read_text(encoding="utf-8"))
    assert codebase["incremental"]["enabled"] is True
    assert codebase["incremental"]["reused_files"] == 1

    third = json.loads(
        subprocess.run(base + ["--no-incremental"], capture_output=True, text=True, encoding="utf-8", check=True).stdout
    )
    codebase = json.loads(Path(third["codebase_index_path"]).read_text(encoding="utf-8"))
    assert codebase["incremental"]["enabled"] is False
    assert codebase["incremental"]["reused_files"] == 0
