from __future__ import annotations

import importlib.util
import json
import subprocess
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
knowledge_graph = load_script_module("full_cycle_knowledge_graph", "codex-project-memory/scripts/build_knowledge_graph.py")
project_traversal = load_script_module("full_cycle_project_traversal", "codex-project-memory/scripts/project_traversal.py")
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


def test_knowledge_graph_builds_code_index_and_ai_context(tmp_path: Path) -> None:
    write(
        tmp_path / "src" / "routes" / "auth.routes.js",
        """
        const router = require('express').Router();
        const authController = require('../controllers/auth.controller');
        router.post('/login', authController.login);
        module.exports = router;
        """,
    )
    write(
        tmp_path / "src" / "controllers" / "auth.controller.js",
        """
        const User = require('../models/user.model');
        exports.login = async function login(req, res) {
          return res.json({ ok: true });
        };
        """,
    )
    write(
        tmp_path / "src" / "models" / "user.model.js",
        """
        const mongoose = require('mongoose');
        const UserSchema = new mongoose.Schema({ email: String, passwordHash: String });
        module.exports = mongoose.model('User', UserSchema);
        """,
    )

    graph = knowledge_graph.build_graph(tmp_path, include_tests=False)

    assert graph["stats"]["total_files"] == 3
    assert graph["code_index"]["src/controllers/auth.controller.js"]["module"] == "controllers"
    assert "src/models/user.model.js" in graph["code_index"]["src/controllers/auth.controller.js"]["imports"]
    assert graph["code_index"]["src/controllers/auth.controller.js"]["definitions"]
    assert graph["external_dependencies"]["express"]["used_by"] == ["src/routes/auth.routes.js"]
    assert graph["risk_signals"]
    assert graph["ai_context"]["summary"]
    assert graph["human_context"]["navigation_hints"]



def test_knowledge_graph_language_registry_detects_polyglot_files(tmp_path: Path) -> None:
    write(
        tmp_path / "services" / "go" / "handler.go",
        """
        package handler
        import "fmt"
        type Server struct {}
        func Handle() {}
        """,
    )
    write(
        tmp_path / "crates" / "api" / "lib.rs",
        """
        pub struct Api {}
        pub enum ApiEvent { Started }
        pub fn serve() {}
        """,
    )
    write(
        tmp_path / "src" / "main" / "java" / "example" / "Widget.java",
        """
        package example;
        public interface Widget {}
        public class DefaultWidget implements Widget {}
        """,
    )
    write(
        tmp_path / "src" / "Services" / "Greeter.cs",
        """
        namespace Sample.Services;
        public interface IGreeter {}
        public class Greeter : IGreeter {}
        """,
    )
    write(
        tmp_path / "frontend" / "components" / "Panel.vue",
        """
        <template><section /></template>
        <script>
        export function openPanel() {}
        </script>
        """,
    )
    write(
        tmp_path / "frontend" / "components" / "Badge.svelte",
        """
        <script>
        export let label = 'new';
        function formatLabel() { return label; }
        </script>
        """,
    )
    write(
        tmp_path / "config" / "app.yaml",
        """
        services:
          api:
            image: sample/api
        routes:
          - path: /health
        """,
    )

    graph = knowledge_graph.build_graph(tmp_path, include_tests=False)
    index = graph["code_index"]

    assert index["services/go/handler.go"]["language"] == "Go"
    assert {"Handle", "Server"}.issubset(index["services/go/handler.go"]["definitions"])
    assert index["crates/api/lib.rs"]["language"] == "Rust"
    assert {"Api", "ApiEvent", "serve"}.issubset(index["crates/api/lib.rs"]["definitions"])
    assert index["src/main/java/example/Widget.java"]["language"] == "Java"
    assert {"Widget", "DefaultWidget"}.issubset(index["src/main/java/example/Widget.java"]["definitions"])
    assert index["src/Services/Greeter.cs"]["language"] == "C#"
    assert {"IGreeter", "Greeter"}.issubset(index["src/Services/Greeter.cs"]["definitions"])
    assert index["frontend/components/Panel.vue"]["language"] == "Vue"
    assert {"Panel", "openPanel"}.issubset(index["frontend/components/Panel.vue"]["definitions"])
    assert index["frontend/components/Badge.svelte"]["language"] == "Svelte"
    assert {"Badge", "formatLabel"}.issubset(index["frontend/components/Badge.svelte"]["definitions"])
    assert index["config/app.yaml"]["language"] == "YAML"
    assert {"config:services", "config:routes"}.issubset(index["config/app.yaml"]["definitions"])
    assert index["config/app.yaml"]["parser"]["confidence"] == "medium"


def test_knowledge_graph_resolves_rust_crate_use_paths(tmp_path: Path) -> None:
    write(tmp_path / "Cargo.toml", '[package]\nname = "sample"\nversion = "0.1.0"\n')
    write(tmp_path / "src" / "lib.rs", "")
    write(tmp_path / "src" / "models" / "user.rs", "pub struct User {}\n")
    write(
        tmp_path / "src" / "main.rs",
        """
        use crate::models::user;
        fn main() {}
        """,
    )

    graph = knowledge_graph.build_graph(tmp_path, include_tests=False)
    main = "src/main.rs"
    user = "src/models/user.rs"

    assert user in graph["code_index"][main]["imports"]
    assert main in graph["code_index"][user]["imported_by"]


def test_knowledge_graph_resolves_local_python_imports_and_skill_modules(tmp_path: Path) -> None:
    write(
        tmp_path / "skills" / "codex-project-memory" / "scripts" / "generate_genome.py",
        "from genome_builder import build_genome_report\n",
    )
    write(
        tmp_path / "skills" / "codex-project-memory" / "scripts" / "genome_builder.py",
        "def build_genome_report():\n    return {}\n",
    )

    graph = knowledge_graph.build_graph(tmp_path, include_tests=False)

    source = "skills/codex-project-memory/scripts/generate_genome.py"
    target = "skills/codex-project-memory/scripts/genome_builder.py"
    assert graph["code_index"][source]["module"] == "codex-project-memory"
    assert target in graph["code_index"][source]["imports"]
    assert source in graph["code_index"][target]["imported_by"]
    assert "genome_builder" not in graph["code_index"][source]["external_imports"]


def test_knowledge_index_writes_interactive_html_and_graph(tmp_path: Path) -> None:
    write(tmp_path / "package.json", json.dumps({"name": "sample", "dependencies": {"express": "^4.19.0"}, "scripts": {"test": "jest"}}))
    write(
        tmp_path / "src" / "routes" / "health.routes.js",
        """
        const router = require('express').Router();
        router.get('/health', (req, res) => res.json({ ok: true }));
        module.exports = router;
        """,
    )
    write(tmp_path / ".codex" / "context" / "genome.md", "# Project Genome\n\n## Architecture Overview\n\n## API Surface\n")

    payload = knowledge_index.write_knowledge_artifacts(tmp_path, tmp_path / ".codex" / "knowledge")
    html = Path(payload["html_path"]).read_text(encoding="utf-8")
    graph = json.loads(Path(payload["graph_path"]).read_text(encoding="utf-8"))

    assert payload["status"] == "built"
    assert "knowledge-dashboard" in html
    assert "data-template=\"codex-project-memory-dashboard\"" in html
    assert "<script id=\"kd\" type=\"application/json\">" in html
    assert "data-tab=\"files\"" in html
    assert "function renderOverview" in html
    assert "src/routes/health.routes.js" in html
    assert "Generated " in html
    assert graph["code_index"]
    assert graph["stats"]["total_files"] >= 1
    assert graph["api_routes"]
    assert graph["ai_context"]["recommended_read_order"]


def test_knowledge_index_template_replaces_metadata_before_json_payload() -> None:
    index = {"project_root": "/tmp/sample-app", "generated_at": "2026-05-18T00:00:00+00:00"}
    graph = {
        "stats": {"total_files": 1},
        "code_index": {
            "docs/guide.md": {
                "language": "Markdown",
                "definitions": ["__PROJECT_NAME__", "__GENERATED_AT__"],
            }
        },
        "module_boundaries": {},
        "api_routes": [],
        "data_models": {},
        "risk_signals": [],
        "ai_context": {},
    }

    html = knowledge_index.render_interactive_html(index, graph)

    assert "Knowledge Graph — sample-app" in html
    assert "Generated 2026-05-18T00:00:00+00:00" in html
    assert '"__PROJECT_NAME__"' in html
    assert '"__GENERATED_AT__"' in html


def test_knowledge_index_falls_back_when_dashboard_template_placeholder_is_missing(monkeypatch) -> None:
    index = {"project_root": "/tmp/sample", "generated_at": "2026-05-18T00:00:00+00:00"}
    graph = {
        "stats": {"total_files": 1},
        "code_index": {"src/app.py": {"language": "Python"}},
        "module_boundaries": {},
        "api_routes": [],
        "data_models": [],
        "risk_signals": [],
        "ai_context": {"recommended_read_order": ["src/app.py"]},
    }
    monkeypatch.setattr(knowledge_index, "DASHBOARD_TEMPLATE_PLACEHOLDERS", {"__MISSING_PLACEHOLDER__"})

    html = knowledge_index.render_interactive_html(index, graph)

    assert "knowledge-dashboard--fallback" in html
    assert "Dashboard template is missing required placeholder" in html
    assert "__MISSING_PLACEHOLDER__" in html
    assert "warnings" in html
    assert "src/app.py" in html


def test_knowledge_index_redacts_sensitive_commit_subjects(tmp_path: Path) -> None:
    commits = [{"hash": "abc123", "date": "2026-04-28", "subject": "fix token=super-secret-value"}]
    package = {"dependencies": ["react"], "scripts": {"test": "vitest"}}

    tacit = knowledge_index.infer_tacit_knowledge(tmp_path, package, [], commits, "2026-04-28T00:00:00+00:00")
    artifact, count = knowledge_index.redact_artifact({"tacit": tacit, "recent_commits": commits}, "index.json")

    combined = json.dumps(artifact)
    assert count > 0
    assert "super-secret-value" not in combined
    assert "[REDACTED]" in artifact["recent_commits"][0]["subject"]
    assert "[REDACTED]" in knowledge_index.redact_text("token=super-secret-value")



def test_project_traversal_respects_gitignore_and_codexignore(tmp_path: Path) -> None:
    write(tmp_path / ".gitignore", "ignored-by-git/\n*.tmp\n")
    write(tmp_path / ".codexignore", "ignored-by-codex/\nsecret.txt\n")
    write(tmp_path / "src" / "keep.py", "def keep():\n    return True\n")
    write(tmp_path / "ignored-by-git" / "skip.py", "def skip():\n    return False\n")
    write(tmp_path / "ignored-by-codex" / "skip.py", "def skip():\n    return False\n")
    write(tmp_path / "notes.tmp", "temporary\n")
    write(tmp_path / "secret.txt", "secret\n")

    result = project_traversal.traverse_project(tmp_path)
    paths = [entry.rel_path for entry in result.files]

    assert paths == [".codexignore", ".gitignore", "src/keep.py"]
    assert result.coverage["skipped_reasons"]["ignore pattern"] == 4


def test_project_traversal_skips_binary_files(tmp_path: Path) -> None:
    write(tmp_path / "src" / "app.py", "print('ok')\n")
    binary = tmp_path / "src" / "image.png"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_bytes(b"\x89PNG\x00binary")

    result = project_traversal.traverse_project(tmp_path)

    assert [entry.rel_path for entry in result.files] == ["src/app.py"]
    assert any(warning["type"] == "binary_skipped" and warning["path"] == "src/image.png" for warning in result.warnings)


def test_knowledge_graph_warns_and_samples_large_files(tmp_path: Path) -> None:
    large_body = "def header():\n    return 'head'\n" + ("# filler\n" * 2000) + "\ndef tail_symbol():\n    return 'tail'\n"
    write(tmp_path / "src" / "large.py", large_body)
    config = project_traversal.TraversalConfig(max_file_bytes=512)

    graph = knowledge_graph.build_graph(tmp_path, include_tests=False, traversal_config=config)

    assert any(warning["type"] == "large_file_sampled" and warning["path"] == "src/large.py" for warning in graph["warnings"])
    assert graph["coverage"]["bytes_scanned"] <= 512
    assert "header" in graph["code_index"]["src/large.py"]["definitions"]


def test_project_traversal_does_not_follow_symlinks_outside_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    write(outside / "escape.py", "def escaped():\n    return True\n")
    write(tmp_path / "inside.py", "def inside():\n    return True\n")
    (tmp_path / "outside-link").symlink_to(outside, target_is_directory=True)

    result = project_traversal.traverse_project(tmp_path, project_traversal.TraversalConfig(follow_symlinks=False))

    assert [entry.rel_path for entry in result.files] == ["inside.py"]
    assert any(warning["type"] == "symlink_skipped" and warning["path"] == "outside-link" for warning in result.warnings)

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


def test_redact_artifact_preserves_dict_keys_that_would_collide() -> None:
    from redaction import redact_artifact

    sample_key = "sk-sampleSecretKey1234567890"
    payload = {
        "code_index": {
            "src/token.py": {"preview": sample_key},
            "src/secret.py": {"preview": "plain text"},
        }
    }
    redacted, _count = redact_artifact(payload, "knowledge-graph.json")
    assert "src/token.py" in redacted["code_index"]
    assert "src/secret.py" in redacted["code_index"]
    assert sample_key not in redacted["code_index"]["src/token.py"]["preview"]
    assert "[REDACTED]" in redacted["code_index"]["src/token.py"]["preview"]


def test_knowledge_artifacts_redact_index_graph_chunks_and_dashboard_json(tmp_path: Path) -> None:
    sample_email = "alice@example.com"
    sample_api_key = "sk-sampleSecretKey1234567890"
    sample_gh_token = "ghp_abcdefghijklmnopqrstuvwxyz123456"
    write(tmp_path / "package.json", json.dumps({"name": sample_email, "dependencies": {"express": "^4.19.0", "mongoose": "^8.0.0"}}))
    write(tmp_path / ".codex" / "context" / "genome.md", f"# Genome for {sample_email}\n")
    write(
        tmp_path / "src" / "routes" / "leak.routes.js",
        f"""
        const router = require('express').Router();
        const token = '{sample_api_key}';
        router.get('/leak', token);
        module.exports = router;
        """,
    )
    write(
        tmp_path / "src" / "models" / "user.model.js",
        f"""
        const mongoose = require('mongoose');
        const schema = new mongoose.Schema({{
          token: String,
          ownerEmail: {{ type: String, default: '{sample_email}' }}
        }});
        module.exports = mongoose.model('User', schema);
        """,
    )
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "tester@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", f"fix leak {sample_gh_token}"], cwd=tmp_path, check=True, capture_output=True, text=True)

    payload = knowledge_index.write_knowledge_artifacts(tmp_path, tmp_path / ".codex" / "knowledge")
    index = json.loads(Path(payload["index_path"]).read_text(encoding="utf-8"))
    graph = json.loads(Path(payload["graph_path"]).read_text(encoding="utf-8"))
    markdown = Path(payload["markdown_path"]).read_text(encoding="utf-8")
    html = Path(payload["html_path"]).read_text(encoding="utf-8")
    if '<script id="kd" type="application/json">' in html:
        embedded = html.split('<script id="kd" type="application/json">', 1)[1].split("</script>", 1)[0]
    else:
        embedded = html.split('<script id="knowledge-data" type="application/json">', 1)[1].split("</script>", 1)[0]
    all_artifacts = "\n".join([json.dumps(index), json.dumps(graph), markdown, embedded])

    assert payload["redaction_applied"] is True
    assert index["redaction_applied"] is True
    assert graph["redaction_applied"] is True
    assert index["redaction_patterns_version"] == knowledge_index.REDACTION_PATTERNS_VERSION
    assert payload["redaction_counts"]["index.json"] > 0
    assert payload["redaction_counts"]["knowledge-graph.json"] > 0
    assert sample_email not in all_artifacts
    assert sample_api_key not in all_artifacts
    assert sample_gh_token not in all_artifacts
    assert "[REDACTED]" in index["recent_commits"][0]["subject"]
    assert graph["api_routes"][0]["handler"] == "[REDACTED]"
    assert "[REDACTED]" in graph["data_models"]["User"]["fields"]
    assert "[REDACTED]" in graph["code_index"]["src/routes/leak.routes.js"]["preview"]
    assert "[REDACTED]" in graph["code_index"]["src/routes/leak.routes.js"]["chunks"][0]["preview"]
    assert "Redaction Status" in html


def test_knowledge_dashboard_warns_when_redaction_disabled(tmp_path: Path) -> None:
    write(tmp_path / "src" / "routes" / "unsafe.routes.js", "router.get('/x', token)\n")

    payload = knowledge_index.write_knowledge_artifacts(tmp_path, tmp_path / ".codex" / "knowledge", redaction_enabled=False)
    graph = json.loads(Path(payload["graph_path"]).read_text(encoding="utf-8"))
    html = Path(payload["html_path"]).read_text(encoding="utf-8")

    assert payload["redaction_applied"] is False
    assert graph["redaction_applied"] is False
    assert any("Redaction disabled" in warning for warning in graph["warnings"])
    assert "DISABLED - artifact may contain secrets" in html
    assert "Redaction warning" in html
