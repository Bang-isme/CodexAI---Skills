from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILLS_ROOT.parent


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


render_core_rules = load_script_module("render_core_rules_sync", ".system/scripts/render_core_rules.py")
init_agents_md = load_script_module("init_agents_md_sync", ".system/scripts/init_agents_md.py")


def test_core_rules_hosts_share_source_and_markers() -> None:
    aliases = render_core_rules.load_aliases()
    featured = " ".join(aliases["featured"])
    assert "$plan" in featured
    for host in render_core_rules.HOSTS:
        document = render_core_rules.render_host_document(host, aliases)
        assert render_core_rules.START_MARKER in document
        assert render_core_rules.END_MARKER in document
        assert "codex-master-instructions" in document
        assert "spec-first workflow" in document
        assert "install.py doctor" in document
        if host == "cursor":
            assert "alwaysApply: true" in document


def test_init_agents_md_writes_all_host_bridges(tmp_path: Path) -> None:
    payload = init_agents_md.build_payload(tmp_path, mode="merge", dry_run=False, target="all")
    assert payload["status"] == "created"
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    cursor = (tmp_path / ".cursor" / "rules" / "codexai-core.mdc").read_text(encoding="utf-8")
    antigravity = (tmp_path / "antigravity" / "rules" / "codexai-core.md").read_text(encoding="utf-8")
    for text in (agents, claude, cursor, antigravity):
        assert "Load skill `codex-master-instructions`" in text
        assert text.count(init_agents_md.START_MARKER) == 1
    assert "alwaysApply: true" in cursor
    second = init_agents_md.build_payload(tmp_path, mode="merge", dry_run=False, target="all")
    assert second["status"] == "unchanged"


def test_init_agents_md_check_detects_missing_and_drifted_bridges(tmp_path: Path) -> None:
    missing = init_agents_md.check_payload(tmp_path, target="all")
    assert missing["status"] == "drift"
    assert set(missing["drifted"]) == set(render_core_rules.HOSTS)
    assert all(item["state"] == "missing" for item in missing["hosts"])
    assert "--merge" in missing["next"]

    init_agents_md.build_payload(tmp_path, mode="merge", dry_run=False, target="all")
    in_sync = init_agents_md.check_payload(tmp_path, target="all")
    assert in_sync["status"] == "pass"
    assert in_sync["drifted"] == []

    agents = tmp_path / "AGENTS.md"
    text = agents.read_text(encoding="utf-8")
    agents.write_text(text.replace("Do not bulk-load the pack.", "Bulk-load everything."), encoding="utf-8")
    drifted = init_agents_md.check_payload(tmp_path, target="all")
    assert drifted["status"] == "drift"
    assert drifted["drifted"] == ["agents"]
    assert next(item for item in drifted["hosts"] if item["host"] == "agents")["state"] == "drift"

    (tmp_path / "CLAUDE.md").write_text("# custom file without markers\n", encoding="utf-8")
    unmarked = init_agents_md.check_payload(tmp_path, target="claude")
    assert unmarked["status"] == "drift"
    assert unmarked["hosts"][0]["state"] == "unmarked"


def test_repo_host_bridges_are_in_sync_with_aliases() -> None:
    payload = init_agents_md.check_payload(REPO_ROOT, target="all")
    assert payload["status"] == "pass", payload


def test_pack_antigravity_core_rule_matches_renderer() -> None:
    rendered = render_core_rules.render_host_document("antigravity")
    path = REPO_ROOT / "antigravity" / "rules" / "codexai-core.md"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    assert render_core_rules.START_MARKER in rendered
    merged, _action = render_core_rules.merge_marked(current, rendered)
    assert "Load skill `codex-master-instructions`" in merged
