"""Regression tests for manifest, router, workflow, and plugin-tool linkage."""
from __future__ import annotations

import importlib.util
import json
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


def test_manifest_router_and_plugin_tools_are_linked() -> None:
    manifest = json.loads((SKILLS_ROOT / ".system/manifest.json").read_text(encoding="utf-8"))
    registry = json.loads((SKILLS_ROOT / ".system/references/plugin-tools.json").read_text(encoding="utf-8"))
    router = load_script_module("prompt_router_linkage", ".system/scripts/prompt_router.py")

    manifest_skills = set(manifest["skills"])
    manifest_agents = set(manifest["agents"])
    manifest_workflows = set(manifest["workflows"])
    issues: list[str] = []

    for route in router.ROUTES:
        agent = route["agent"]
        workflow = route["workflow"]
        for skill in route["skills"]:
            if skill not in manifest_skills:
                issues.append(f"route skill not in manifest: {skill}")
        if agent not in manifest_agents:
            issues.append(f"route agent not in manifest: {agent}")
        if workflow and workflow not in manifest_workflows:
            issues.append(f"route workflow not in manifest: {workflow}")
        if workflow and not (SKILLS_ROOT / ".workflows" / f"{workflow}.md").exists():
            issues.append(f"missing workflow file: {workflow}")
        if not (SKILLS_ROOT / ".agents" / f"{agent}.md").exists():
            issues.append(f"missing agent file: {agent}")

    for tool in registry["tools"]:
        rel = tool["script"].replace("\\", "/").lstrip("/")
        if not (SKILLS_ROOT / rel).exists():
            issues.append(f"plugin tool script missing: {tool['name']}")

    ptc = manifest["plugin_tool_contract"]
    for key, rel in ptc.items():
        if not (SKILLS_ROOT / rel).exists():
            issues.append(f"plugin_tool_contract.{key} missing: {rel}")

    codex = manifest["codex_plugin"]
    for key in ("plugin_validator", "prompt_router", "generic_trust_harness", "release_packager"):
        rel = codex[key]
        if not (SKILLS_ROOT / rel).exists():
            issues.append(f"codex_plugin.{key} missing: {rel}")

    corpus = SKILLS_ROOT / ".system" / "references" / "prompt-router.corpus.json"
    if not corpus.exists():
        issues.append("missing prompt-router.corpus.json")

    deploy_workflow = REPO_ROOT / ".github" / "workflows" / "deploy.yml"
    if deploy_workflow.exists():
        issues.append("deploy.yml should not exist (plugin pack uses CI only, no production CD)")
    local_gate = SKILLS_ROOT / ".system" / "scripts" / "local_release_gate.py"
    if not local_gate.exists():
        issues.append("missing local_release_gate.py")

    assert not issues, "linkage issues:\n" + "\n".join(issues)


def test_ci_workflow_uses_dev_requirements_cache() -> None:
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "cache-dependency-path: requirements-dev.txt" in ci
    assert "python-version: [\"3.12\", \"3.13\"]" in ci or 'python-version: ["3.12", "3.13"]' in ci


def test_plugin_tool_registry_covers_trust_harness_commands() -> None:
    registry = json.loads((SKILLS_ROOT / ".system/references/plugin-tools.json").read_text(encoding="utf-8"))
    names = {tool["name"] for tool in registry["tools"]}
    assert {
        "pack_health",
        "codex_plugin_validate",
        "claude_plugin_validate",
        "release_zip_dry_run",
        "prompt_route",
        "trust_harness",
    }.issubset(names)
