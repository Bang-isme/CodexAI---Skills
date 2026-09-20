from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from test_full_cycle_hardening import (
    codebase_indexer,
    knowledge_graph,
    knowledge_index,
    project_traversal,
    write,
)


SKILLS_ROOT = Path(__file__).resolve().parents[1]


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
