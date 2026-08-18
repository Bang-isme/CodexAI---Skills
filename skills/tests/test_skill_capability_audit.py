from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = SKILLS_ROOT / ".system" / "scripts" / "audit_skill_pack.py"
MATRIX_PATH = SKILLS_ROOT / ".system" / "skill-capabilities.json"


def load_audit_module():
    assert AUDIT_PATH.exists(), "skill capability audit script must exist"
    spec = importlib.util.spec_from_file_location("skill_capability_audit", AUDIT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["skill_capability_audit"] = module
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def minimal_skills_root(tmp_path: Path, *, high_risk: bool = False) -> Path:
    root = tmp_path / "skills"
    write(root / "VERSION", "1.0.0\n")
    write(root / ".system" / "manifest.json", json.dumps({"version": "1.0.0", "skills": ["demo"], "agents": [], "workflows": []}))
    write(root / ".system" / "REGISTRY.md", "| Script | Skill | Purpose |\n|---|---|---|\n| `tool.py` | `demo` | fixture tool |\n")
    write(root / "demo" / "SKILL.md", "---\nname: demo\ndescription: Use when testing the capability audit fixture.\n---\n")
    script_text = "print('ok')\n"
    if high_risk:
        script_text = "from pathlib import Path\nPath('artifact.txt').write_text('ok')\n"
    write(root / "demo" / "scripts" / "tool.py", script_text)
    write(root / "tests" / "test_demo.py", "def test_demo():\n    assert True\n")
    classes = ["read_only", "project_write"] if high_risk else ["read_only"]
    matrix = {
        "schema_version": "1.0",
        "capabilities": [
            {
                "skill": "demo",
                "domain": "quality",
                "objective": "Exercise the audit fixture.",
                "triggers": ["fixture"],
                "resources": {"scripts": ["scripts"], "references": [], "assets": [], "agents": []},
                "output_artifacts": ["artifact.txt"],
                "tool_classes": classes,
                "risk_tier": "enforced" if high_risk else "advisory",
                "security_policy": {
                    "network": "none",
                    "path_scope": "project_root_only",
                    "redact_outputs": True,
                    "notes": "Fixture policy.",
                },
                "verification": {"owner": "tests/test_demo.py", "command": "python -m pytest tests/test_demo.py"},
                "handoff": "Return the fixture artifact path.",
            }
        ],
        "shared_components": [],
    }
    write(root / ".system" / "skill-capabilities.json", json.dumps(matrix))
    return root


def test_repository_matrix_has_exactly_one_entry_per_managed_skill() -> None:
    audit = load_audit_module()
    manifest = json.loads((SKILLS_ROOT / ".system" / "manifest.json").read_text(encoding="utf-8"))
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))

    payload = audit.audit_skill_pack(SKILLS_ROOT, write_artifacts=False, strict=True)

    assert matrix["schema_version"] == "1.0"
    assert {item["skill"] for item in matrix["capabilities"]} == set(manifest["skills"])
    assert len(matrix["capabilities"]) == len(manifest["skills"])
    assert payload["status"] == "pass", payload["findings"]
    assert payload["summary"]["scripts"] > 0


def test_audit_covers_every_manifest_skill_and_writes_offline_scorecard(tmp_path: Path) -> None:
    audit = load_audit_module()
    output_dir = tmp_path / "quality"

    payload = audit.audit_skill_pack(minimal_skills_root(tmp_path), output_dir=output_dir, write_artifacts=True)

    assert payload["status"] == "pass"
    assert payload["summary"]["skills"] == 1
    assert payload["summary"]["scripts"] == 1
    assert (output_dir / "skill-scorecard.json").exists()
    assert (output_dir / "SKILL-SCORECARD.md").exists()
    html = (output_dir / "skill-scorecard.html").read_text(encoding="utf-8")
    assert 'data-testid="capability-search"' in html
    assert 'data-testid="domain-filter"' in html
    assert 'data-testid="risk-filter"' in html
    assert 'data-testid="readiness-filter"' in html
    assert "https://" not in html
    assert "http://" not in html


def test_audit_fails_when_high_risk_skill_lacks_enforced_policy_or_test(tmp_path: Path) -> None:
    audit = load_audit_module()
    root = minimal_skills_root(tmp_path, high_risk=True)
    matrix_path = root / ".system" / "skill-capabilities.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    record = matrix["capabilities"][0]
    record["risk_tier"] = "advisory"
    record["security_policy"] = {}
    record["verification"]["owner"] = "tests/missing.py"
    write(matrix_path, json.dumps(matrix))

    payload = audit.audit_skill_pack(root, output_dir=tmp_path / "quality", write_artifacts=False)

    assert payload["status"] == "fail"
    codes = {finding["code"] for finding in payload["findings"]}
    assert "high_risk_requires_enforced_tier" in codes
    assert "verification_owner_missing" in codes
    assert "security_policy_incomplete" in codes


def test_audit_detects_unsafe_resource_path_and_unowned_script(tmp_path: Path) -> None:
    audit = load_audit_module()
    root = minimal_skills_root(tmp_path)
    matrix_path = root / ".system" / "skill-capabilities.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix["capabilities"][0]["resources"]["assets"] = ["../escape"]
    write(root / "orphan.py", "print('orphan')\n")
    write(matrix_path, json.dumps(matrix))

    payload = audit.audit_skill_pack(root, output_dir=tmp_path / "quality", write_artifacts=False)

    codes = {finding["code"] for finding in payload["findings"]}
    assert "resource_path_unsafe" in codes
    assert "script_owner_missing" in codes


def test_classifier_reports_shell_network_git_and_secret_signals() -> None:
    audit = load_audit_module()

    classes = audit.classify_script_text(
        "import subprocess\nimport urllib.request\nsubprocess.run(['git', 'push'])\ntoken = 'secret'\n"
    )

    assert {"shell_execution", "network", "git_remote", "secret_sensitive"} <= set(classes)


def test_classifier_ignores_detection_literals_that_are_not_executed() -> None:
    audit = load_audit_module()

    classes = audit.classify_script_text("PATTERN = r'https?://|secret'\nprint(PATTERN)\n")

    assert classes == ["read_only"]


def test_dashboard_escapes_embedded_data_and_filters_without_external_assets(tmp_path: Path) -> None:
    audit = load_audit_module()
    root = minimal_skills_root(tmp_path)
    matrix_path = root / ".system" / "skill-capabilities.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix["capabilities"][0]["objective"] = "<script>window.pwned=true</script>"
    write(matrix_path, json.dumps(matrix))

    output_dir = tmp_path / "quality"
    payload = audit.audit_skill_pack(root, output_dir=output_dir, write_artifacts=True)
    html = (output_dir / "skill-scorecard.html").read_text(encoding="utf-8")

    assert payload["status"] == "pass"
    assert "window.pwned=true" not in html
    assert "\\u003cscript\\u003e" in html
    assert "addEventListener" in html
    assert "filterRows" in html
