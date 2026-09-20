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


def test_pack_antigravity_core_rule_matches_renderer() -> None:
    rendered = render_core_rules.render_host_document("antigravity")
    path = REPO_ROOT / "antigravity" / "rules" / "codexai-core.md"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    assert render_core_rules.START_MARKER in rendered
    merged, _action = render_core_rules.merge_marked(current, rendered)
    assert "Load skill `codex-master-instructions`" in merged
