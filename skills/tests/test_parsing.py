#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import pytest


SKILLS_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name: str, relative_path: str):
    path = SKILLS_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


security_scan = load_script_module(
    "skills_security_scan",
    "codex-execution-quality-gate/scripts/security_scan.py",
)
predict_impact = load_script_module(
    "skills_predict_impact",
    "codex-execution-quality-gate/scripts/predict_impact.py",
)
run_gate = load_script_module(
    "skills_run_gate",
    "codex-execution-quality-gate/scripts/run_gate.py",
)
smart_test_selector = load_script_module(
    "skills_smart_test_selector",
    "codex-execution-quality-gate/scripts/smart_test_selector.py",
)
explain_code = load_script_module(
    "skills_explain_code",
    "codex-workflow-autopilot/scripts/explain_code.py",
)
map_changes_to_docs = load_script_module(
    "skills_map_changes_to_docs",
    "codex-docs-change-sync/scripts/map_changes_to_docs.py",
)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_security_looks_like_placeholder_true() -> None:
    assert security_scan.looks_like_placeholder("ChangeMe-Secret")
    assert security_scan.looks_like_placeholder("dummy_token_value")


def test_security_looks_like_placeholder_false() -> None:
    assert not security_scan.looks_like_placeholder("prod_9f8a7b6c5d4e")


def test_security_is_production_path_variants() -> None:
    assert security_scan.is_production_path("src/services/user.py")
    assert not security_scan.is_production_path("src/tests/user.test.py")
    assert not security_scan.is_production_path("docs/architecture.md")
    assert not security_scan.is_production_path("scripts/build.py")


def test_security_scan_missing_root(tmp_path: Path) -> None:
    report = security_scan.scan(tmp_path / "missing")
    assert report["scan_type"] == "basic"
    assert report["passed"] is False
    assert len(report["critical"]) == 1
    assert "does not exist or is not a directory" in report["critical"][0]["issue"]


def test_security_scan_detects_core_issues(tmp_path: Path) -> None:
    write_text(
        tmp_path / "src" / "app.py",
        "\n".join(
            [
                "password = 'UltraSecret12345'",
                "print('debug line')",
                "# TODO: remove",
                "url = 'http://example.com'",
            ]
        ),
    )
    report = security_scan.scan(tmp_path)
    critical_messages = {item["issue"] for item in report["critical"]}
    warning_messages = {item["issue"] for item in report["warnings"]}
    assert "Potential hardcoded secret value" in critical_messages
    assert "TODO/FIXME/HACK marker present" in warning_messages
    assert "HTTP URL found; prefer HTTPS for production traffic" in warning_messages
    assert "Debug logging statement in production path" in warning_messages


def test_security_scan_ignores_placeholder_secret(tmp_path: Path) -> None:
    write_text(tmp_path / "src" / "settings.py", "password = 'example_value_123456'")
    report = security_scan.scan(tmp_path)
    critical_messages = [item["issue"] for item in report["critical"]]
    assert "Potential hardcoded secret value" not in critical_messages


def test_security_scan_env_warning_respects_gitignore(tmp_path: Path) -> None:
    write_text(tmp_path / ".env", "TOKEN=abc123")
    report_warn = security_scan.scan(tmp_path)
    assert any(".env file found" in item["issue"] for item in report_warn["warnings"])

    write_text(tmp_path / ".gitignore", ".env\n")
    report_ok = security_scan.scan(tmp_path)
    assert not any(".env file found" in item["issue"] for item in report_ok["warnings"])


def test_security_scan_handles_binary_unicode_and_permission_denied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_text(tmp_path / "src" / "unicode.py", "note = 'Xin chào 🌟'\n# TODO: giữ lại\n")
    write_bytes(tmp_path / "src" / "binary.py", b"\xff\xfe\x00\x01TODO\x00")
    blocked = tmp_path / "src" / "blocked.py"
    write_text(blocked, "print('blocked')")

    original_stat = Path.stat

    def patched_stat(self: Path, *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
        if self.name == "blocked.py":
            raise PermissionError("denied")
        return original_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", patched_stat)
    report = security_scan.scan(tmp_path)
    assert isinstance(report["critical"], list)
    assert isinstance(report["warnings"], list)
    assert "summary" in report


def test_gate_state_round_trip(tmp_path: Path) -> None:
    run_gate.save_gate_state(tmp_path, {"consecutive_failures": 5})
    loaded = run_gate.load_gate_state(tmp_path)
    assert loaded["consecutive_failures"] == 5


def test_gate_state_missing_file(tmp_path: Path) -> None:
    loaded = run_gate.load_gate_state(tmp_path)
    assert loaded == {"consecutive_failures": 0}


def test_gate_state_corrupted_file(tmp_path: Path) -> None:
    state_file = tmp_path / ".codex" / "state" / "gate_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("NOT VALID JSON", encoding="utf-8")
    loaded = run_gate.load_gate_state(tmp_path)
    assert loaded == {"consecutive_failures": 0}


def test_predict_parse_imports_js() -> None:
    content = "\n".join(
        [
            "import { a } from './utils';",
            "import './polyfills';",
            "const cfg = require('@/config/app');",
        ]
    )
    modules = predict_impact.parse_imports(Path("src/app.ts"), content)
    assert "./utils" in modules
    assert "./polyfills" in modules
    assert "@/config/app" in modules


def test_predict_parse_imports_python() -> None:
    content = "\n".join(
        [
            "import os",
            "from .helpers import run",
            "from package.service import call",
        ]
    )
    modules = predict_impact.parse_imports(Path("pkg/main.py"), content)
    assert "os" in modules
    assert ".helpers" in modules
    assert "package.service" in modules


def test_predict_build_dependency_maps_js_resolution(tmp_path: Path) -> None:
    write_text(tmp_path / "src" / "utils.ts", "export const x = 1")
    write_text(tmp_path / "src" / "app.ts", "import { x } from './utils';\nexport const y = x;")
    forward, reverse, rel_files, warnings = predict_impact.build_dependency_maps(tmp_path)
    assert "src/app.ts" in forward
    assert "src/utils.ts" in forward["src/app.ts"]
    assert "src/app.ts" in reverse["src/utils.ts"]
    assert {"src/app.ts", "src/utils.ts"}.issubset(rel_files)
    assert warnings == []


def test_predict_build_dependency_maps_python_relative(tmp_path: Path) -> None:
    write_text(tmp_path / "pkg" / "__init__.py", "")
    write_text(tmp_path / "pkg" / "helpers.py", "def util():\n    return 1\n")
    write_text(tmp_path / "pkg" / "main.py", "from .helpers import util\n")
    forward, reverse, _, _ = predict_impact.build_dependency_maps(tmp_path)
    assert "pkg/main.py" in forward
    assert "pkg/helpers.py" in forward["pkg/main.py"]
    assert "pkg/main.py" in reverse["pkg/helpers.py"]


def test_predict_build_dependency_maps_ignores_external_modules(tmp_path: Path) -> None:
    write_text(tmp_path / "src" / "a.ts", "import React from 'react';\n")
    forward, reverse, _, _ = predict_impact.build_dependency_maps(tmp_path)
    assert "src/a.ts" not in forward
    assert reverse == {}


def test_predict_build_dependency_maps_missing_root_returns_empty(tmp_path: Path) -> None:
    forward, reverse, rel_files, warnings = predict_impact.build_dependency_maps(tmp_path / "missing")
    assert forward == {}
    assert reverse == {}
    assert rel_files == set()
    assert warnings == []


def test_predict_escalate_to_epic_true(tmp_path: Path) -> None:
    for i in range(25):
        write_text(
            tmp_path / "src" / f"mod_{i}.ts",
            f"import {{ x }} from './mod_{(i + 1) % 25}';\nexport const y_{i} = 1;\n",
        )
    forward, reverse, _, _ = predict_impact.build_dependency_maps(tmp_path)
    all_affected = set(forward.keys()) | set(reverse.keys())
    for deps in forward.values():
        all_affected.update(deps)
    for deps in reverse.values():
        all_affected.update(deps)
    blast_radius_size = len(all_affected)
    escalate_to_epic = blast_radius_size > 20
    assert blast_radius_size > 20
    assert escalate_to_epic is True


def test_predict_escalate_to_epic_false(tmp_path: Path) -> None:
    for i in range(3):
        write_text(tmp_path / "src" / f"small_{i}.ts", f"export const x_{i} = {i};\n")
    forward, reverse, _, _ = predict_impact.build_dependency_maps(tmp_path)
    all_affected = set(forward.keys()) | set(reverse.keys())
    for deps in forward.values():
        all_affected.update(deps)
    for deps in reverse.values():
        all_affected.update(deps)
    blast_radius_size = len(all_affected)
    escalate_to_epic = blast_radius_size > 20
    assert blast_radius_size <= 20
    assert escalate_to_epic is False


def test_selector_is_test_file_variants() -> None:
    assert smart_test_selector.is_test_file(Path("tests/user.test.ts"))
    assert smart_test_selector.is_test_file(Path("src/__tests__/user.ts"))
    assert smart_test_selector.is_test_file(Path("src/tests/flow_runner.ts"))
    assert not smart_test_selector.is_test_file(Path("tests/flow_runner.ts"))
    assert not smart_test_selector.is_test_file(Path("src/user.ts"))


def test_selector_strategy_convention_changed_test_file(tmp_path: Path) -> None:
    changed = ["tests/user.test.ts"]
    write_text(tmp_path / "tests" / "user.test.ts", "test('x', () => {})")
    all_tests = {"tests/user.test.ts"}
    reasons: Dict[str, Set[str]] = {}
    found = smart_test_selector.strategy_convention(tmp_path, changed, all_tests, reasons)
    assert found["tests/user.test.ts"] is True
    assert "changed test file" in reasons["tests/user.test.ts"]


def test_selector_strategy_convention_pattern_match(tmp_path: Path) -> None:
    write_text(tmp_path / "src" / "user.ts", "export const user = 1")
    write_text(tmp_path / "tests" / "user.test.ts", "test('u', () => {})")
    reasons: Dict[str, Set[str]] = {}
    found = smart_test_selector.strategy_convention(
        tmp_path,
        ["src/user.ts"],
        {"tests/user.test.ts"},
        reasons,
    )
    assert found["src/user.ts"] is True
    assert "convention match" in reasons["tests/user.test.ts"]


def test_selector_strategy_convention_controller_heuristic(tmp_path: Path) -> None:
    write_text(tmp_path / "src" / "auth.controller.ts", "export const x = 1")
    write_text(tmp_path / "tests" / "controller_auth.ts", "test('controller', () => {})")
    reasons: Dict[str, Set[str]] = {}
    found = smart_test_selector.strategy_convention(
        tmp_path,
        ["src/auth.controller.ts"],
        {"tests/controller_auth.ts"},
        reasons,
    )
    assert found["src/auth.controller.ts"] is True
    assert "convention match" in reasons["tests/controller_auth.ts"]


def test_selector_strategy_convention_no_match(tmp_path: Path) -> None:
    write_text(tmp_path / "src" / "order.ts", "export const order = 1")
    reasons: Dict[str, Set[str]] = {}
    found = smart_test_selector.strategy_convention(
        tmp_path,
        ["src/order.ts"],
        {"tests/unrelated_helper.ts"},
        reasons,
    )
    assert found["src/order.ts"] is False
    assert reasons == {}


def test_explain_parse_python_file_happy_path(tmp_path: Path) -> None:
    file_path = tmp_path / "pkg" / "service.py"
    write_text(
        file_path,
        "\n".join(
            [
                "import os",
                "from .helpers import util as helper",
                "def run(a, b=1, *args, **kwargs):",
                "    return a + b",
                "async def load(x):",
                "    return x",
            ]
        ),
    )
    warnings: List[str] = []
    functions, imports = explain_code.parse_python_file(file_path, tmp_path, warnings)
    names = [item["name"] for item in functions]
    modules = [item["module"] for item in imports]
    assert warnings == []
    assert names == ["run", "load"]
    assert "os" in modules
    assert ".helpers" in modules


def test_explain_parse_python_file_syntax_error(tmp_path: Path) -> None:
    file_path = tmp_path / "bad.py"
    write_text(file_path, "def broken(:\n    pass\n")
    warnings: List[str] = []
    functions, imports = explain_code.parse_python_file(file_path, tmp_path, warnings)
    assert functions == []
    assert imports == []
    assert any("Python AST parse failed" in item for item in warnings)


def test_explain_parse_python_file_handles_permission_denied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    file_path = tmp_path / "locked.py"
    write_text(file_path, "def ok():\n    return 1\n")
    original_read_text = Path.read_text

    def blocked_read(self: Path, *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
        if self == file_path:
            raise PermissionError("permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", blocked_read)
    warnings: List[str] = []
    functions, imports = explain_code.parse_python_file(file_path, tmp_path, warnings)
    assert functions == []
    assert imports == []


def test_explain_parse_js_file_happy_path(tmp_path: Path) -> None:
    file_path = tmp_path / "src" / "logic.ts"
    write_text(
        file_path,
        "\n".join(
            [
                "import core, { util as helper } from './core';",
                "import './polyfill';",
                "const pkg = require('./pkg');",
                "function greet(name) {",
                "  return name;",
                "}",
                "const run = (value) => {",
                "  return greet(value);",
                "};",
            ]
        ),
    )
    warnings: List[str] = []
    functions, imports = explain_code.parse_js_file(file_path, tmp_path, warnings)
    function_names = [item["name"] for item in functions]
    import_modules = [item["module"] for item in imports]
    assert warnings == []
    assert "greet" in function_names
    assert "run" in function_names
    assert "./core" in import_modules
    assert "./polyfill" in import_modules
    assert "./pkg" in import_modules


def test_explain_parse_js_file_unclosed_block_warns(tmp_path: Path) -> None:
    file_path = tmp_path / "src" / "broken.js"
    write_text(file_path, "function broken(a) {\n  return a;\n")
    warnings: List[str] = []
    functions, _ = explain_code.parse_js_file(file_path, tmp_path, warnings)
    assert functions == []
    assert any("JS/TS block parse failed" in item for item in warnings)


def test_explain_parse_js_file_unicode_and_empty(tmp_path: Path) -> None:
    unicode_file = tmp_path / "src" / "unicode.js"
    write_text(unicode_file, "const msg = 'Xin chào';\nconst ping = (x) => { return x; };\n")
    warnings: List[str] = []
    functions, imports = explain_code.parse_js_file(unicode_file, tmp_path, warnings)
    assert any(item["name"] == "ping" for item in functions)
    assert imports == []
    assert warnings == []

    empty_file = tmp_path / "src" / "empty.js"
    write_text(empty_file, "")
    functions_empty, imports_empty = explain_code.parse_js_file(empty_file, tmp_path, warnings=[])
    assert functions_empty == []
    assert imports_empty == []


def test_docs_build_reference_tokens_extracts_expected() -> None:
    changed = [
        "src/payments/payment_service.ts",
        "lib/auth/session_manager.py",
        "src/index.ts",
    ]
    tokens = map_changes_to_docs.build_reference_tokens(changed)
    assert "payment_service" in tokens
    assert "payments" in tokens
    assert "session_manager" in tokens
    assert "api" not in tokens


def test_docs_convention_mapping_prefers_existing_docs_file(tmp_path: Path) -> None:
    write_text(tmp_path / "docs" / "payments.md", "# payments")
    candidates: Dict[str, Dict[str, str]] = {}
    map_changes_to_docs.convention_mapping(["src/payments/service.ts"], tmp_path, candidates)
    assert "docs/payments.md" in candidates
    assert candidates["docs/payments.md"]["confidence"] == "high"


def test_docs_convention_mapping_suggests_when_docs_missing(tmp_path: Path) -> None:
    candidates: Dict[str, Dict[str, str]] = {}
    map_changes_to_docs.convention_mapping(["src/inventory/service.ts"], tmp_path, candidates)
    assert "docs/inventory.md" in candidates
    assert candidates["docs/inventory.md"]["confidence"] == "medium"


def test_docs_reference_search_mapping_matches_tokens(tmp_path: Path) -> None:
    write_text(tmp_path / "docs" / "api.md", "Payments module endpoint and billing flow.")
    candidates: Dict[str, Dict[str, str]] = {}
    map_changes_to_docs.reference_search_mapping(["src/payments/payment_service.ts"], tmp_path, candidates)
    assert "docs/api.md" in candidates
    assert candidates["docs/api.md"]["confidence"] == "medium"


def test_docs_reference_search_mapping_handles_permission_denied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    file_path = tmp_path / "docs" / "blocked.md"
    write_text(file_path, "auth provider details")
    candidates: Dict[str, Dict[str, str]] = {}
    original_read_text = Path.read_text

    def blocked_read(self: Path, *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
        if self == file_path:
            raise PermissionError("denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", blocked_read)
    map_changes_to_docs.reference_search_mapping(["src/auth/provider.ts"], tmp_path, candidates)
    assert candidates == {}


def test_docs_always_include_mapping_adds_readme_and_changelog(tmp_path: Path) -> None:
    write_text(tmp_path / "CHANGELOG.md", "## Changelog")
    candidates: Dict[str, Dict[str, str]] = {}
    map_changes_to_docs.always_include_mapping(["src/api/user_controller.ts"], tmp_path, candidates)
    assert "README.md" in candidates
    assert "CHANGELOG.md" in candidates


def test_docs_build_report_missing_root(tmp_path: Path) -> None:
    report = map_changes_to_docs.build_report(tmp_path / "missing", "auto")
    assert report["status"] == "error"
    assert report["docs_candidates"] == []


def test_docs_build_report_no_git(tmp_path: Path) -> None:
    report = map_changes_to_docs.build_report(tmp_path, "auto")
    assert report["status"] == "no_git"
    assert report["docs_candidates"] == []


def test_docs_build_report_ok_with_mocked_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_text(tmp_path / "docs" / "billing.md", "# Billing\npayment flow details")
    write_text(tmp_path / "README.md", "Root readme")
    write_text(tmp_path / "CHANGELOG.md", "history")
    write_text(tmp_path / "src" / "billing" / "engine.ts", "export const x = 1")
    write_text(tmp_path / "src" / "index.ts", "export * from './billing/engine'")

    monkeypatch.setattr(map_changes_to_docs, "is_git_repo", lambda _root: True)
    monkeypatch.setattr(
        map_changes_to_docs,
        "get_changed_files",
        lambda _root, _scope: (["src/billing/engine.ts", "src/index.ts"], ["mock diff"]),
    )

    report = map_changes_to_docs.build_report(tmp_path, "auto")
    assert report["status"] == "ok"
    assert report["changed_files"] == ["src/billing/engine.ts", "src/index.ts"]
    doc_paths = {item["doc_path"] for item in report["docs_candidates"]}
    assert "README.md" in doc_paths
    assert "CHANGELOG.md" in doc_paths
