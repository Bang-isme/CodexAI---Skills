from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from test_full_cycle_hardening import runtime_hook, write


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


router = load_script_module("routing_sync_prompt_router", ".system/scripts/prompt_router.py")
auto_commit = load_script_module("routing_sync_auto_commit", "codex-git-autopilot/scripts/auto_commit.py")


def test_workflow_enum_is_shared_across_manifest_router_and_contract() -> None:
    manifest = json.loads((SKILLS_ROOT / ".system/manifest.json").read_text(encoding="utf-8"))
    contract = json.loads(
        (SKILLS_ROOT / "codex-workflow-autopilot/references/workflow-routing-contract.json").read_text(encoding="utf-8")
    )
    router_workflows = {route["workflow"] for route in router.ROUTES if route.get("workflow")}
    manifest_workflows = set(manifest["workflows"])
    contract_types = set(contract["workflow_types"])

    assert router_workflows <= manifest_workflows
    assert contract_types <= manifest_workflows
    assert set(contract["workflow_aliases"]) <= manifest_workflows
    assert contract["workflow_aliases"]["build"] == "create"
    assert contract["workflow_aliases"]["fix"] == "debug"
    assert contract["workflow_aliases"]["docs"] == "handoff"


def test_prompt_router_covers_test_scrum_and_pulse_intents() -> None:
    test_route = router.route_prompt("Write pytest coverage for the auth module using TDD")
    scrum_route = router.route_prompt("Facilitate sprint planning and the daily scrum")
    pulse_route = router.route_prompt("$today")
    vi_pulse = router.route_prompt("Hôm nay thế nào?")

    assert test_route["intent"] == "test"
    assert test_route["suggested_agent"] == "test-engineer"
    assert scrum_route["intent"] == "scrum"
    assert scrum_route["suggested_agent"] == "scrum-master"
    assert pulse_route["intent"] == "pulse"
    assert pulse_route["suggested_agent"] == "planner"
    assert "codex-project-pulse" in pulse_route["required_skills"]
    assert vi_pulse["intent"] == "pulse"


def test_prompt_router_user_intent_precedes_runtime_hook_repo_state(tmp_path: Path) -> None:
    write(tmp_path / "package.json", json.dumps({"dependencies": {"react": "^18.0.0"}}))
    write(tmp_path / "src" / "App.tsx", "export default function App() { return null }\n")
    repo_report = runtime_hook.build_report(tmp_path)
    user_route = router.route_prompt("Fix traceback when API auth fails")
    merged = router.merge_routing(user_route, repo_report)

    assert repo_report["suggested_agent"] == "frontend-specialist"
    assert user_route["suggested_agent"] == "debugger"
    assert merged["precedence"] == "prompt_router"
    assert merged["suggested_agent"] == "debugger"
    assert merged["repo_suggested_agent"] == "frontend-specialist"


def test_runtime_hook_fills_gap_when_prompt_router_has_no_agent() -> None:
    write_route = router.fallback_payload("hello world", [])
    merged = router.merge_routing(write_route, {"suggested_agent": "frontend-specialist", "workflow_recommendation": {"workflow": "create", "alias": "$create"}})
    assert merged["precedence"] == "runtime_hook"
    assert merged["suggested_agent"] == "frontend-specialist"


def test_auto_commit_quick_gate_uses_auto_gate(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, list[str]] = {}

    class Result:
        returncode = 0
        stdout = json.dumps({"status": "pass", "overall": "pass", "blocking_issues": [], "warnings": []})
        stderr = ""

    def fake_run(cmd, **kwargs):
        captured["cmd"] = [str(item) for item in cmd]
        return Result()

    monkeypatch.setattr(auto_commit.subprocess, "run", fake_run)
    payload = auto_commit.run_pre_commit_gate(tmp_path, skip_tests=False)

    assert payload["passed"] is True
    assert payload["gate_command"][-1] == "quick"
    assert captured["cmd"][-2:] == ["--mode", "quick"]
    assert captured["cmd"][1].endswith("auto_gate.py")
