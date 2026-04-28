from __future__ import annotations

import importlib.util
import json
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


runtime_hook = load_script_module("full_cycle_runtime_hook", "codex-runtime-hook/scripts/runtime_hook.py")
init_profile = load_script_module("full_cycle_init_profile", "codex-runtime-hook/scripts/init_profile.py")
init_spec = load_script_module("full_cycle_init_spec", "codex-spec-driven-development/scripts/init_spec.py")
check_spec = load_script_module("full_cycle_check_spec", "codex-spec-driven-development/scripts/check_spec.py")
knowledge_index = load_script_module("full_cycle_knowledge_index", "codex-project-memory/scripts/build_knowledge_index.py")
sync_global = load_script_module("full_cycle_sync_global", ".system/scripts/sync_global_skills.py")
auto_gate = load_script_module("full_cycle_auto_gate", "codex-execution-quality-gate/scripts/auto_gate.py")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def test_profile_priority_over_auto_detection(tmp_path: Path) -> None:
    write(tmp_path / "package.json", json.dumps({"dependencies": {"react": "^18.0.0"}}))
    write(
        tmp_path / ".codex" / "profile.json",
        json.dumps(
            {
                "schema_version": "1.0",
                "name": "sample",
                "stack": ["express", "postgres"],
                "primary_domain": "backend",
                "test_framework": "pytest",
                "deploy_target": "docker",
                "custom_references": [],
                "preferences": {
                    "response_language": "en",
                    "output_style": "evidence-first",
                    "verification_preference": "auto_gate_full",
                },
            }
        ),
    )

    report = runtime_hook.build_report(tmp_path)

    assert report["schema_version"] == "1.0"
    assert report["profile_status"]["status"] == "conflicting"
    assert "backend" in report["detected_domains"]
    assert "frontend" not in report["detected_domains"]
    assert "qa" in report["detected_domains"]
    assert "devops" in report["detected_domains"]


def test_malformed_profile_falls_back_to_auto_detection(tmp_path: Path) -> None:
    write(tmp_path / "package.json", json.dumps({"dependencies": {"react": "^18.0.0"}}))
    write(tmp_path / ".codex" / "profile.json", json.dumps({"schema_version": "1.0", "primary_domain": "made-up-domain"}))

    report = runtime_hook.build_report(tmp_path)

    assert report["profile_status"]["status"] == "malformed"
    assert "frontend" in report["detected_domains"]


def test_init_profile_builds_optional_profile_payload(tmp_path: Path) -> None:
    write(tmp_path / "package.json", json.dumps({"dependencies": {"react": "^18.0.0"}, "devDependencies": {"vitest": "^1.0.0"}}))
    args = type(
        "Args",
        (),
        {
            "name": "",
            "stack": "",
            "primary_domain": "",
            "test_framework": "",
            "deploy_target": "",
            "custom_references": "docs/design.md",
            "language": "vi",
            "output_style": "evidence-first",
            "verification_preference": "auto_gate_full",
        },
    )()

    profile = init_profile.build_profile(tmp_path, args)

    assert profile["primary_domain"] == "frontend"
    assert profile["test_framework"] == "vitest"
    assert profile["schema_version"] == "1.0"
    assert profile["custom_references"] == [{"path": "docs/design.md", "type": "reference", "trusted": False}]
    assert '"schema_version": "1.0"' in init_profile.render_profile(profile)


def test_runtime_hook_rejects_unsafe_custom_references(tmp_path: Path) -> None:
    write(
        tmp_path / ".codex" / "profile.json",
        json.dumps(
            {
                "schema_version": "1.0",
                "name": "sample",
                "stack": [],
                "primary_domain": "unknown",
                "test_framework": "unknown",
                "deploy_target": "unknown",
                "custom_references": [{"path": "../secret.md", "type": "architecture", "trusted": False}],
                "preferences": {
                    "response_language": "en",
                    "output_style": "evidence-first",
                    "verification_preference": "auto_gate_full",
                },
            }
        ),
    )

    report = runtime_hook.build_report(tmp_path)

    assert report["profile_status"]["status"] == "warn"
    assert report["profile_status"]["invalid_references"] == ["../secret.md"]


def test_spec_init_and_check_maps_changed_files(tmp_path: Path) -> None:
    spec_dir = tmp_path / ".codex" / "specs" / "admin-dashboard"
    spec_dir.mkdir(parents=True)
    spec = init_spec.render_spec("Admin Dashboard", "Build admin dashboard", ["frontend", "backend"])
    write(spec_dir / "SPEC.md", spec)

    report = check_spec.build_report(tmp_path, ["src/components/Admin.tsx", "server/routes/admin.js"])

    assert report["schema_version"] == "1.0"
    assert report["overall"] == "pass"
    assert report["matched_specs"] == ["admin-dashboard"]
    assert "AC-001" in report["matched_acceptance_criteria"]
    assert report["unmapped_files"] == []


def test_spec_check_skips_when_no_specs_exist(tmp_path: Path) -> None:
    report = check_spec.build_report(tmp_path, ["src/App.tsx"])

    assert report["overall"] == "skip"
    assert report["specs_found"] == 0


def test_knowledge_index_builds_from_docs_and_config(tmp_path: Path) -> None:
    write(tmp_path / "package.json", json.dumps({"name": "sample", "dependencies": {"react": "^18.0.0"}, "scripts": {"test": "vitest"}}))
    write(tmp_path / ".codex" / "context" / "genome.md", "# Project Genome\n\n## Architecture Overview\n\n## API Surface\n")
    write(tmp_path / ".codex" / "project-docs" / "index.json", json.dumps({"docs": [{"path": "frontend/FE-00-overview.md"}]}))
    write(tmp_path / ".codex" / "decisions" / "ADR-0001.md", "# Use React\n")

    index = knowledge_index.build_index(tmp_path)

    assert index["schema_version"] == "1.0"
    assert index["status"] == "built"
    assert index["sources"]["genome"] == "present"
    assert index["sources"]["role_docs"]["docs_count"] == 1
    assert "Project Genome" in index["architecture_seams"]
    assert index["tacit_knowledge"]["verification_commands"]
    first_insight = index["tacit_knowledge"]["verification_commands"][0]
    assert {"source", "confidence", "generated_by", "last_seen"}.issubset(first_insight)


def test_knowledge_index_redacts_sensitive_commit_subjects(tmp_path: Path) -> None:
    commits = [{"hash": "abc123", "date": "2026-04-28", "subject": "fix token=super-secret-value"}]
    package = {"dependencies": ["react"], "scripts": {"test": "vitest"}}

    tacit = knowledge_index.infer_tacit_knowledge(tmp_path, package, [], commits, "2026-04-28T00:00:00+00:00")

    combined = json.dumps(tacit)
    assert "super-secret-value" not in combined
    assert "[REDACTED]" in knowledge_index.redact_text("token=super-secret-value")


def test_sync_global_dry_run_includes_dot_dirs_and_preserves_system(tmp_path: Path) -> None:
    source = tmp_path / "source"
    global_root = tmp_path / "global"
    write(source / ".system" / "REGISTRY.md", "# Registry\n")
    write(source / ".agents" / "frontend-specialist.md", "---\nname: frontend-specialist\n---\n")
    write(source / ".workflows" / "prototype.md", "# Prototype\n")
    write(source / ".codex" / "state" / "gate_state.json", "{}\n")
    write(global_root / ".system" / "skill-creator" / "SKILL.md", "---\nname: skill-creator\n---\n")

    dry = sync_global.sync(source, global_root, dry_run=True)
    applied = sync_global.sync(source, global_root, dry_run=False)

    assert ".system" in dry["items"]
    assert ".agents" in dry["items"]
    assert ".workflows" in dry["items"]
    assert ".codex" not in dry["items"]
    assert (global_root / ".system" / "REGISTRY.md").exists()
    assert (global_root / ".system" / "skill-creator" / "SKILL.md").exists()
    assert applied["status"] == "synced"


def test_sync_global_backs_up_overwrites_and_skips_protected_system(tmp_path: Path) -> None:
    source = tmp_path / "source"
    global_root = tmp_path / "global"
    write(source / ".system" / "REGISTRY.md", "# New Registry\n")
    write(source / ".system" / "skill-creator" / "SKILL.md", "source should not overwrite\n")
    write(global_root / ".system" / "REGISTRY.md", "# Old Registry\n")
    write(global_root / ".system" / "skill-creator" / "SKILL.md", "protected built-in\n")

    payload = sync_global.sync(source, global_root, dry_run=False, backup_dir=tmp_path / "backup")

    assert payload["backed_up_files"] == [".system/REGISTRY.md"]
    assert ".system/skill-creator/SKILL.md" in payload["protected_skipped"]
    assert (tmp_path / "backup" / ".system" / "REGISTRY.md").read_text(encoding="utf-8") == "# Old Registry\n"
    assert (global_root / ".system" / "skill-creator" / "SKILL.md").read_text(encoding="utf-8") == "protected built-in\n"


def test_auto_gate_spec_and_knowledge_advisories_are_non_blocking(tmp_path: Path) -> None:
    write(tmp_path / ".codex" / "specs" / "dashboard" / "SPEC.md", init_spec.render_spec("Dashboard", "Build dashboard", ["frontend"]))
    write(
        tmp_path / ".codex" / "knowledge" / "index.json",
        json.dumps({"sources": {"genome": "missing"}, "generated_at": "2026-04-28T00:00:00+00:00"}),
    )

    spec_result = auto_gate.run_specs(tmp_path)
    knowledge_result = auto_gate.run_knowledge(tmp_path)

    assert spec_result["payload"]["status"] in {"pass", "warn"}
    assert spec_result["blocking_issues"] == []
    assert knowledge_result["payload"]["status"] == "pass"
    assert knowledge_result["blocking_issues"] == []


def test_manifest_and_prototype_workflow_are_registered() -> None:
    manifest = json.loads((SKILLS_ROOT / ".system" / "manifest.json").read_text(encoding="utf-8"))
    master = (SKILLS_ROOT / "codex-master-instructions" / "SKILL.md").read_text(encoding="utf-8")

    assert "codex-spec-driven-development" in manifest["skills"]
    assert "prototype" in manifest["workflows"]
    assert "$prototype" in master
    assert (SKILLS_ROOT / ".workflows" / "prototype.md").exists()


def test_contract_schema_files_are_parseable() -> None:
    schema_paths = [
        SKILLS_ROOT / "codex-runtime-hook" / "references" / "profile.schema.json",
        SKILLS_ROOT / "codex-runtime-hook" / "references" / "runtime-hook-output.schema.json",
        SKILLS_ROOT / "codex-spec-driven-development" / "references" / "spec.schema.json",
        SKILLS_ROOT / "codex-project-memory" / "references" / "knowledge-index.schema.json",
    ]

    for path in schema_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == "1.0"
