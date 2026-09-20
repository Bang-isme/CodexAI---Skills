from __future__ import annotations

import importlib.util
import json
import subprocess
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


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


router = load_script_module("prompt_router_design", ".system/scripts/prompt_router.py")
design_context = load_script_module("design_context_mod", "codex-design-md/scripts/design_context.py")
visual_gate = load_script_module("visual_quality_mod", "codex-visual-quality-gate/scripts/visual_quality_gate.py")
agy_build = load_script_module("agy_build_mod", ".system/scripts/build_antigravity_plugin.py")
agy_install = load_script_module("agy_install_mod", ".system/scripts/install_antigravity_native.py")
agy_validate = load_script_module("agy_validate_mod", ".system/scripts/validate_antigravity_plugin.py")


def test_vague_prompt_loads_creative_studio_before_frontend() -> None:
    routed = router.route_prompt("Make a beautiful landing page for our product")
    assert routed["suggested_agent"] == "design-lead"
    assert routed["design_mode"] == "fast"
    assert routed["supporting_agents"][0] == "frontend-specialist"
    assert "visual-quality-reviewer" in routed["supporting_agents"]
    assert "codex-frontend-design" in routed["required_skills"]
    assert routed["required_skills"].index("codex-frontend-design") < routed["required_skills"].index(
        "codex-visual-quality-gate"
    )


def test_vietnamese_vague_prompt_routes_to_direction() -> None:
    routed = router.route_prompt("Tạo một trang landing đẹp và sáng tạo")
    assert routed["suggested_agent"] == "design-lead"
    assert routed["design_operation"] == "new"
    assert routed["design_mode"] == "fast"


def test_refine_does_not_smuggle_redesign() -> None:
    routed = router.route_prompt("Tweak spacing on the pricing table")
    assert routed["suggested_agent"] == "frontend-specialist"
    assert routed["design_operation"] == "refine"
    assert "design-lead" not in routed["supporting_agents"]


def test_implementation_only_skips_studio() -> None:
    routed = router.route_prompt("Implement the approved dashboard design in React")
    assert routed["suggested_agent"] == "frontend-specialist"
    assert routed["supporting_agents"] == []


def test_visual_reviewer_is_independent_route() -> None:
    routed = router.route_prompt("Independent visual review of the pricing page screenshots")
    assert routed["suggested_agent"] == "visual-quality-reviewer"


def test_design_context_dry_run_does_not_write(tmp_path: Path) -> None:
    payload = design_context.build_report(tmp_path, "scaffold", "pricing", "Pricing", apply=False)
    assert payload["status"] == "dry_run"
    assert payload["written"] == []
    assert not (tmp_path / ".codex" / "design" / "PRODUCT.md").exists()


def test_design_context_apply_and_validate(tmp_path: Path) -> None:
    payload = design_context.build_report(tmp_path, "scaffold", "pricing", "Pricing", apply=True)
    assert payload["status"] == "pass"
    assert (tmp_path / ".codex" / "design" / "PRODUCT.md").exists()
    assert (tmp_path / ".codex" / "design" / "surfaces" / "pricing.md").exists()
    valid = design_context.build_report(tmp_path, "validate", "pricing", "", apply=False)
    assert valid["status"] == "pass"


def test_design_context_rejects_path_escape(tmp_path: Path) -> None:
    try:
        design_context.confined(tmp_path, Path("..") / "outside.md")
        raised = False
    except ValueError:
        raised = True
    assert raised is True


def test_visual_gate_mechanical_rules_and_degraded(tmp_path: Path) -> None:
    write(
        tmp_path / "src" / "Hero.tsx",
        """
export function Hero() {
  return (
    <section style={{ fontFamily: 'Arial', background: 'linear-gradient(#3B82F6, #7C3AED)' }}>
      <button className="btn-primary">Buy</button>
      <button className="btn-primary">Start</button>
    </section>
  );
}
""",
    )
    payload = visual_gate.build_report(tmp_path, ["src/Hero.tsx"], apply=False, max_rounds=2)
    checks = {item["check"] for item in payload["findings"]}
    assert "competing_ctas" in checks
    assert "default_font" in checks
    assert payload["blocking_count"] >= 1
    assert payload["optional_detector"]["status"] in {"available", "skipped", "failed"}
    assert payload["independent_review"]["status"] in {"DEGRADED", "unknown"}
    assert payload["kind"] == "mechanical_evidence"


def test_visual_gate_apply_writes_review(tmp_path: Path) -> None:
    write(tmp_path / "src" / "Page.tsx", "<h1>Ok</h1>\n")
    payload = visual_gate.build_report(tmp_path, ["src/Page.tsx"], apply=True, max_rounds=2)
    assert payload["written"].endswith("latest-mechanical.json")
    assert (tmp_path / ".codex" / "design" / "reviews" / "latest-mechanical.json").exists()


def test_antigravity_hook_fail_open_and_ui_write() -> None:
    hook = load_script_module("agy_hook", "../antigravity/scripts/pre_tool_use.py")
    payload = hook.allow("x")
    assert payload["permission"] == "allow"
    assert hook.is_ui_path("src/components/Hero.tsx") is True
    assert hook.is_ui_path("src/api/users.py") is False


def test_antigravity_hook_cli_json(tmp_path: Path) -> None:
    script = REPO_ROOT / "antigravity" / "scripts" / "pre_tool_use.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps({"toolName": "replace_file_content", "toolInput": {"path": "src/App.tsx"}}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        check=False,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["permission"] == "allow"
    assert payload["warning"] == "ui_write"


def test_antigravity_build_install_validate_idempotent(tmp_path: Path, monkeypatch) -> None:
    package = tmp_path / "package"
    built = agy_build.build_package(REPO_ROOT, package, apply=True)
    assert built["status"] == "generated"
    assert not (package / ".agents" / "workflows").exists()
    skill = (package / "skills" / "codex-master-instructions" / "SKILL.md").read_text(encoding="utf-8")
    assert "load_priority:" not in skill.split("---", 2)[1]
    assert "codexai-load-priority" in skill
    agent = (package / "agents" / "frontend-specialist" / "agent.md").read_text(encoding="utf-8")
    assert "view_file" in agent
    assert "file_ownership:" not in agent.split("---", 2)[1]
    validated = agy_validate.validate_package(package)
    assert validated["status"] == "pass", json.dumps(validated, indent=2)
    assert validated["agy_smoke"]["status"] in {"skipped", "ran", "failed"}
    if validated["agy_smoke"]["status"] == "skipped":
        assert "binary unavailable" in validated["agy_smoke"]["reason"]

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    project = tmp_path / "project"
    project.mkdir()
    first = agy_install.install(package, agy_install.resolve_targets("workspace", "both", project), apply=True, uninstall=False)
    second = agy_install.install(package, agy_install.resolve_targets("workspace", "both", project), apply=True, uninstall=False)
    assert first["status"] == "pass"
    assert second["status"] == "pass"
    user_targets = agy_install.resolve_targets("user", "both", project)
    assert any("config" in str(path) and "plugins" in str(path) for path in user_targets)
    assert any("antigravity-cli" in str(path) for path in user_targets)
    agy_install.install(package, user_targets, apply=True, uninstall=False)
    removed = agy_install.install(package, user_targets, apply=True, uninstall=True)
    assert removed["results"][0]["action"] == "uninstall"


def test_corpus_has_at_least_forty_cases() -> None:
    payload = json.loads((SKILLS_ROOT / ".system" / "references" / "prompt-router.corpus.json").read_text(encoding="utf-8"))
    assert len(payload["cases"]) >= 40
    result = router.validate_corpus(SKILLS_ROOT / ".system" / "references" / "prompt-router.corpus.json")
    assert result["status"] == "pass"
