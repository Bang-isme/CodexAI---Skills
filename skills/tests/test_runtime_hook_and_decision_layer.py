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


runtime_hook = load_script_module("skills_runtime_hook", "codex-runtime-hook/scripts/runtime_hook.py")
decision_matrix = load_script_module(
    "skills_decision_matrix",
    "codex-logical-decision-layer/scripts/build_decision_matrix.py",
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_react_express_project(root: Path) -> None:
    write(
        root / "package.json",
        json.dumps(
            {
                "dependencies": {
                    "react": "^18.0.0",
                    "express": "^4.0.0",
                    "prisma": "^5.0.0",
                },
                "devDependencies": {"vitest": "^1.0.0"},
                "scripts": {"test": "vitest"},
            }
        ),
    )
    write(root / "src" / "components" / "Header.tsx", "export function Header() { return <header /> }\n")
    write(root / "server" / "routes" / "auth.js", "module.exports = router\n")
    write(root / ".github" / "workflows" / "ci.yml", "name: ci\n")


def test_runtime_hook_detects_domains_and_missing_role_docs(tmp_path: Path) -> None:
    make_react_express_project(tmp_path)

    report = runtime_hook.build_report(tmp_path)

    assert report["overall"] == "warn"
    assert {"frontend", "backend", "data", "qa", "devops"}.issubset(set(report["detected_domains"]))
    assert report["suggested_agent"] in {"frontend-specialist", "backend-specialist"}
    missing_paths = {item["path"] for item in report["missing"]}
    assert ".codex/project-docs/frontend/FE-02-design-system.md" in missing_paths
    assert ".codex/project-docs/backend/BE-01-api-contracts.md" in missing_paths
    assert any("$init-docs" in command for command in report["recommended_commands"])


def test_runtime_hook_changed_files_biases_frontend_agent(tmp_path: Path) -> None:
    make_react_express_project(tmp_path)

    report = runtime_hook.build_report(tmp_path, ["src/components/Header.tsx"])

    assert "frontend" in report["detected_domains"]
    assert report["suggested_agent"] == "frontend-specialist"


def test_runtime_hook_ignores_reference_starter_files_for_domain_detection(tmp_path: Path) -> None:
    write(tmp_path / "skills" / "codex-domain-specialist" / "starters" / "dashboard-layout.css", ".card {}\n")
    write(tmp_path / "skills" / "codex-domain-specialist" / "starters" / "prisma-schema.prisma", "model User {}\n")
    write(tmp_path / "skills" / "codex-domain-specialist" / "references" / "react.md", "React examples\n")

    report = runtime_hook.build_report(tmp_path)

    assert report["overall"] == "pass"
    assert report["detected_domains"] == []
    assert report["suggested_agent"] is None


def test_runtime_hook_cli_returns_json(tmp_path: Path) -> None:
    make_react_express_project(tmp_path)
    script = SKILLS_ROOT / "codex-runtime-hook" / "scripts" / "runtime_hook.py"

    result = subprocess.run(
        [sys.executable, str(script), "--project-root", str(tmp_path), "--format", "json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["status"] == "checked"
    assert "frontend" in payload["detected_domains"]


def test_decision_matrix_limits_options_and_preserves_contract() -> None:
    payload = decision_matrix.build_matrix(
        "Choose frontend state strategy",
        decision_matrix.parse_options("local state,query cache,event bus,global store,extra", 4),
        "No new backend contract",
    )

    assert payload["status"] == "ok"
    assert len(payload["options"]) == 4
    assert payload["constraints"] == "No new backend contract"
    assert payload["recommendation"]
    assert payload["verification"]
    assert payload["stop_conditions"]


def test_decision_matrix_cli_markdown_has_required_sections() -> None:
    script = SKILLS_ROOT / "codex-logical-decision-layer" / "scripts" / "build_decision_matrix.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--problem",
            "Pick API pagination strategy",
            "--options",
            "offset,cursor",
            "--format",
            "markdown",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )

    assert result.returncode == 0
    assert "## Decision Surface" in result.stdout
    assert "## Recommendation" in result.stdout
    assert "## Verification" in result.stdout
