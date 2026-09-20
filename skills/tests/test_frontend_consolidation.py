from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


router = load_script_module("prompt_router_frontend", ".system/scripts/prompt_router.py")


def test_redirect_skills_resolve_to_frontend_design() -> None:
    for name in ("codex-ui-ux-design", "codex-creative-direction", "codex-design-system"):
        text = (SKILLS_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
        assert "Merged into `codex-frontend-design`" in text


def test_redirect_agents_point_to_design_lead() -> None:
    for name in ("creative-director", "ui-ux-designer", "creative-designer"):
        text = (SKILLS_ROOT / ".agents" / f"{name}.md").read_text(encoding="utf-8")
        assert "design-lead" in text
        assert "Redirect" in text


def test_craft_provenance_headers_present() -> None:
    craft = SKILLS_ROOT / "codex-frontend-implementation" / "craft"
    files = [path for path in craft.glob("*.md") if path.name != "PROVENANCE.md"]
    assert len(files) >= 15
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "provenance:" in text
        assert "MengTo/Skills" in text
    provenance = (craft / "PROVENANCE.md").read_text(encoding="utf-8")
    assert "https://github.com/MengTo/Skills" in provenance


def test_starters_and_template_do_not_default_to_inter() -> None:
    starter = (SKILLS_ROOT / "codex-frontend-implementation" / "starters" / "design-system.css").read_text(encoding="utf-8")
    template = (SKILLS_ROOT / "codex-design-md" / "assets" / "design-md-template.md").read_text(encoding="utf-8")
    assert "oklch(" in starter
    assert "Inter" not in starter
    assert "oklch(" in template
    assert "use Inter" not in template
    assert "use Space Grotesk" not in template


def test_beautiful_landing_page_routes_fast_design_lead() -> None:
    routed = router.route_prompt("Build a beautiful landing page")
    assert routed["suggested_agent"] == "design-lead"
    assert routed["design_mode"] == "fast"
    assert "codex-frontend-design" in routed["required_skills"]
