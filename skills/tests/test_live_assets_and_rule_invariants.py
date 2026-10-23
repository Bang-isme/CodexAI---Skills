from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "skills" / "codex-execution-quality-gate" / "scripts"
SCRIPT = GATE / "verify_live_assets.py"
sys.path.insert(0, str(GATE))

import verify_live_assets  # noqa: E402


MIB = 1024 * 1024
LIMIT = 50 * MIB
CANARY_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".cursor/rules/codexai-core.mdc",
    "antigravity/rules/codexai-core.md",
)
CANARY_PHRASES = (
    "/codex-frontend",
    "4-Tier",
    "7-Stage SDLC + SILC",
    "codex-master-instructions",
)
LADDER_PHRASES = (
    "grep every caller",
    "trust-boundary validation",
    "error handling that prevents data loss",
    "shortcut: <ceiling>, <when to upgrade>",
)
REGISTERED_SCRIPTS = {
    "precision_mode.py": "codex-runtime-hook",
    "reuse_map.py": "codex-runtime-hook",
    "finding_contract.py": "codex-execution-quality-gate",
    "shortcut_ledger.py": "codex-execution-quality-gate",
    "safety_selftest.py": "codex-execution-quality-gate",
    "verify_live_assets.py": "codex-execution-quality-gate",
}
SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".codexai-backups",
}


def _forbidden_needles() -> tuple[bytes, ...]:
    fragments = (
        ("pony", "tail"),
        ("Meng", "To"),
        ("Meng", " To"),
        ("impec", "cable"),
        ("pba", "kaus"),
        ("Nha", "Bar"),
        ("@google/", "design.md"),
        ("CODEX_DESIGN_MD_", "SOURCE_REPO"),
    )
    return tuple("".join(parts).lower().encode("utf-8") for parts in fragments)


def _iter_repo_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        for filename in filenames:
            if filename.endswith((".pyc", ".pyo")):
                continue
            yield Path(dirpath) / filename


def _first_needle(path: Path, needles: tuple[bytes, ...]) -> bytes | None:
    overlap = max(len(needle) for needle in needles) - 1
    try:
        handle = path.open("rb")
    except OSError:
        return None
    with handle:
        tail = b""
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                return None
            window = (tail + chunk).lower()
            for needle in needles:
                if needle in window:
                    return needle
            tail = window[-overlap:] if overlap else b""


def _release(upload_bytes: int, *, fast: bool = True, dirty: bool = False, archiving: bool = False):
    return verify_live_assets.evaluate_release_hygiene(upload_bytes, fast, dirty, archiving)


class LiveAssetEvaluationTests(unittest.TestCase):
    def test_ceiling_is_fifty_mebibytes(self) -> None:
        self.assertEqual(verify_live_assets.DEFAULT_MAX_UPLOAD_BYTES, LIMIT)

    def test_html_200_with_image_404_fails(self) -> None:
        result = verify_live_assets.evaluate_page_and_assets(
            200,
            [{"kind": "image", "path": "/hero.png", "status": 404}],
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "fail")
        self.assertNotEqual(result["status"], "pass")
        self.assertIn("required_asset_unavailable", result["codes"])
        self.assertEqual(result["code"], "required_asset_unavailable")

    def test_required_script_and_stylesheet_5xx_fail(self) -> None:
        cases = (
            ("script", 500),
            ("script", 599),
            ("stylesheet", 502),
            ("stylesheet", 503),
            ("image", 404),
        )
        for kind, status in cases:
            with self.subTest(kind=kind, status=status):
                result = verify_live_assets.evaluate_page_and_assets(
                    200,
                    [{"kind": kind, "status": status, "required": True}],
                )
                self.assertEqual(result["status"], "fail")
                self.assertFalse(result["ok"])
                self.assertIn("required_asset_unavailable", result["codes"])

    def test_html_200_with_redirect_to_200_passes(self) -> None:
        for status, final_key in ((302, "final_status"), (301, "resolved_status")):
            with self.subTest(status=status, final_key=final_key):
                asset = {"kind": "image", "path": "/hero.png", "status": status, final_key: 200}
                result = verify_live_assets.evaluate_page_and_assets(200, [asset])
                self.assertTrue(result["ok"])
                self.assertEqual(result["status"], "pass")
                self.assertEqual(result["failures"], [])

    def test_redirect_to_404_or_unresolved_redirect_fails(self) -> None:
        broken = verify_live_assets.evaluate_page_and_assets(
            200,
            [{"kind": "image", "status": 302, "final_status": 404}],
        )
        self.assertEqual(broken["status"], "fail")
        self.assertIn("required_asset_unavailable", broken["codes"])
        unresolved = verify_live_assets.evaluate_page_and_assets(
            200,
            [{"kind": "stylesheet", "status": 301}],
        )
        self.assertEqual(unresolved["status"], "fail")
        self.assertIn("redirect_unresolved", unresolved["codes"])

    def test_healthy_redirect_does_not_hide_a_broken_script(self) -> None:
        result = verify_live_assets.evaluate_page_and_assets(
            200,
            [
                {"kind": "image", "status": 302, "final_status": 200},
                {"kind": "script", "status": 500},
            ],
        )
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["ok"])
        self.assertIn("required_asset_unavailable", result["codes"])

    def test_optional_missing_image_and_healthy_assets_pass(self) -> None:
        optional = verify_live_assets.evaluate_page_and_assets(
            200,
            [{"kind": "image", "status": 404, "required": False}],
        )
        self.assertTrue(optional["ok"])
        self.assertEqual(optional["status"], "pass")
        healthy = verify_live_assets.evaluate_page_and_assets(
            200,
            [
                {"kind": "script", "status": 200},
                {"kind": "stylesheet", "status": 304},
                {"type": "image", "status": 200},
            ],
        )
        self.assertTrue(healthy["ok"])
        self.assertEqual(healthy["status"], "pass")

    def test_content_type_and_extension_are_required_assets(self) -> None:
        by_type = verify_live_assets.evaluate_page_and_assets(
            200,
            [{"content_type": "image/png", "path": "/a", "status": 404}],
        )
        self.assertEqual(by_type["status"], "fail")
        by_extension = verify_live_assets.evaluate_page_and_assets(
            200,
            [{"path": "/static/app.css", "status": 503}],
        )
        self.assertEqual(by_extension["status"], "fail")
        self.assertEqual(by_extension["failures"][0]["kind"], "stylesheet")

    def test_non_200_page_fails_even_when_assets_are_healthy(self) -> None:
        result = verify_live_assets.evaluate_page_and_assets(500, [{"kind": "script", "status": 200}])
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["ok"])
        self.assertIn("page_not_ok", result["codes"])

    def test_auth_404_fails_and_400_401_403_pass(self) -> None:
        missing = verify_live_assets.evaluate_auth_and_private_probes(404, [])
        self.assertFalse(missing["ok"])
        self.assertEqual(missing["status"], "fail")
        self.assertEqual(missing["code"], "auth_gate_missing")
        self.assertIn("auth_gate_missing", missing["codes"])
        for status in (400, 401, 403):
            with self.subTest(status=status):
                present = verify_live_assets.evaluate_auth_and_private_probes(status, [])
                self.assertTrue(present["ok"])
                self.assertEqual(present["status"], "pass")
                self.assertIn("auth_gate_present", present["codes"])

    def test_auth_route_200_is_not_a_gate(self) -> None:
        result = verify_live_assets.evaluate_auth_and_private_probes(200, [])
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["ok"])
        self.assertIn("auth_gate_open", result["codes"])

    def test_private_200_fails_and_401_403_pass(self) -> None:
        exposed = verify_live_assets.evaluate_auth_and_private_probes(401, [{"path": "/.env", "status": 200}])
        self.assertFalse(exposed["ok"])
        self.assertEqual(exposed["status"], "fail")
        self.assertEqual(exposed["code"], "private_asset_exposed")
        self.assertIn("private_asset_exposed", exposed["codes"])
        for status in (401, 403):
            with self.subTest(status=status):
                hidden = verify_live_assets.evaluate_auth_and_private_probes(
                    403,
                    [{"path": "/.env", "status": status}],
                )
                self.assertTrue(hidden["ok"], hidden)
                self.assertEqual(hidden["status"], "pass")
                self.assertNotIn("private_asset_exposed", hidden["codes"])

    def test_private_redirect_to_200_is_exposure_and_404_is_not(self) -> None:
        exposed = verify_live_assets.evaluate_auth_and_private_probes(
            None,
            [{"path": "/secret", "status": 302, "final_status": 200}],
        )
        self.assertEqual(exposed["status"], "fail")
        self.assertIn("private_asset_exposed", exposed["codes"])
        hidden = verify_live_assets.evaluate_auth_and_private_probes(401, [{"path": "/.env", "status": 404}])
        self.assertEqual(hidden["status"], "pass")
        self.assertNotIn("private_asset_exposed", hidden["codes"])

    def test_upload_49mb_passes_and_51mb_asks_user(self) -> None:
        under = _release(49 * MIB)
        self.assertTrue(under["ok"])
        self.assertEqual(under["status"], "pass")
        self.assertFalse(under["refused"])
        exact = _release(LIMIT)
        self.assertTrue(exact["ok"])
        self.assertEqual(exact["status"], "pass")
        over = _release(51 * MIB)
        self.assertFalse(over["ok"])
        self.assertEqual(over["status"], "ask_user")
        self.assertEqual(over["code"], "upload_exceeds_50mb")
        self.assertIn("upload_exceeds_50mb", over["codes"])
        one_byte = _release(LIMIT + 1)
        self.assertEqual(one_byte["status"], "ask_user")
        self.assertFalse(one_byte["ok"])

    def test_non_fast_forward_push_is_refused(self) -> None:
        result = _release(1024, fast=False)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["refused"])
        self.assertEqual(result["code"], "non_fast_forward_refused")
        self.assertIn("non_fast_forward_refused", result["codes"])

    def test_dirty_worktree_capture_archive_is_refused(self) -> None:
        refused = _release(1024, dirty=True, archiving=True)
        self.assertFalse(refused["ok"])
        self.assertEqual(refused["status"], "fail")
        self.assertTrue(refused["refused"])
        self.assertEqual(refused["code"], "dirty_worktree_capture_archive_refused")
        self.assertIn("dirty_worktree_capture_archive_refused", refused["codes"])
        dirty_without_archive = _release(1024, dirty=True, archiving=False)
        self.assertTrue(dirty_without_archive["ok"])
        self.assertFalse(dirty_without_archive["refused"])
        clean_archive = _release(1024, dirty=False, archiving=True)
        self.assertTrue(clean_archive["ok"])
        self.assertFalse(clean_archive["refused"])

    def test_size_question_does_not_hide_a_hard_refusal(self) -> None:
        result = _release(51 * MIB, fast=False, dirty=True, archiving=True)
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "non_fast_forward_refused")
        for code in (
            "upload_exceeds_50mb",
            "non_fast_forward_refused",
            "dirty_worktree_capture_archive_refused",
        ):
            self.assertIn(code, result["codes"])

    def test_cli_help_lists_flags(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for flag in ("--project-root", "--manifest", "--format"):
            self.assertIn(flag, completed.stdout)
        self.assertIn("json", completed.stdout)
        self.assertIn("text", completed.stdout)

    def test_cli_manifest_fail_and_pass(self) -> None:
        failing = {
            "page_status": 200,
            "assets": [{"kind": "image", "status": 404, "path": "/hero.png"}],
            "auth_probe_status": 404,
            "private_probes": [{"path": "/.env", "status": 200}],
            "release": {
                "upload_bytes": 51 * MIB,
                "is_fast_forward": False,
                "worktree_dirty": True,
                "archiving_captures": True,
            },
        }
        passing = {
            "page_status": 200,
            "assets": [
                {"kind": "script", "status": 200},
                {"kind": "stylesheet", "status": 200},
                {"kind": "image", "status": 302, "final_status": 200},
            ],
            "auth_probe_status": 401,
            "private_probes": [{"path": "/.env", "status": 403}],
            "release": {
                "upload_bytes": 49 * MIB,
                "is_fast_forward": True,
                "worktree_dirty": False,
                "archiving_captures": False,
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fail_path = root / "fail.json"
            pass_path = root / "pass.json"
            fail_path.write_text(json.dumps(failing), encoding="utf-8")
            pass_path.write_text(json.dumps(passing), encoding="utf-8")
            failed = _run_cli(root, fail_path, "text")
            self.assertEqual(failed.returncode, 1, failed.stderr)
            self.assertIn("status=fail", failed.stdout)
            self.assertIn("required_asset_unavailable", failed.stdout)
            self.assertIn("auth_gate_missing", failed.stdout)
            self.assertIn("private_asset_exposed", failed.stdout)
            self.assertIn("non_fast_forward_refused", failed.stdout)
            passed = _run_cli(root, pass_path, "json")
            self.assertEqual(passed.returncode, 0, passed.stderr)
            payload = json.loads(passed.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(payload["checks"]["page_and_assets"]["status"], "pass")
            self.assertEqual(payload["checks"]["auth_and_private"]["status"], "pass")
            self.assertEqual(payload["checks"]["release_hygiene"]["status"], "pass")

    def test_cli_without_manifest_fails_closed(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(ROOT), "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(completed.returncode, 1, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["code"], "manifest_required")


def _run_cli(project_root: Path, manifest: Path, report_format: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--project-root",
            str(project_root),
            "--manifest",
            str(manifest),
            "--format",
            report_format,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


class RuleInvariantTests(unittest.TestCase):
    def test_core_rules_check_passes(self) -> None:
        script = ROOT / "skills" / ".system" / "scripts" / "init_agents_md.py"
        completed = subprocess.run(
            [sys.executable, str(script), "--repo-root", ".", "--target", "all", "--check", "--format", "json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["drifted"], [])

    def test_host_bridges_contain_load_bearing_phrases(self) -> None:
        for relative in CANARY_FILES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for phrase in CANARY_PHRASES:
                with self.subTest(file=relative, phrase=phrase):
                    self.assertIn(phrase, text)

    def test_precision_ladder_contains_never_cut_and_caller_grep_phrases(self) -> None:
        ladder = (ROOT / "skills" / "codex-reasoning-rigor" / "references" / "precision-ladder.md").read_text(encoding="utf-8")
        for phrase in LADDER_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, ladder)

    def test_new_scripts_are_registered_and_referenced(self) -> None:
        registry = (ROOT / "skills" / ".system" / "REGISTRY.md").read_text(encoding="utf-8")
        for script, owner in REGISTERED_SCRIPTS.items():
            with self.subTest(script=script):
                self.assertIn(f"| `{script}` | `{owner}` |", registry)
                self.assertTrue((ROOT / "skills" / owner / "scripts" / script).is_file())
        for line in registry.splitlines():
            if any(script in line for script in REGISTERED_SCRIPTS):
                self.assertIn("<SKILLS_ROOT>", line)
                self.assertNotIn("D:\\", line)
        runtime = (ROOT / "skills" / "codex-runtime-hook" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("precision_mode.py", runtime)
        self.assertIn("reuse_map.py", runtime)
        gate = (ROOT / "skills" / "codex-execution-quality-gate" / "SKILL.md").read_text(encoding="utf-8")
        for script in (
            "finding_contract.py",
            "shortcut_ledger.py",
            "safety_selftest.py",
            "verify_live_assets.py",
        ):
            self.assertIn(script, gate)
        release = (ROOT / "skills" / ".system" / "scripts" / "local_release_gate.py").read_text(encoding="utf-8")
        pipeline = (ROOT / "skills" / ".system" / "scripts" / "pipeline.py").read_text(encoding="utf-8")
        contracts = pipeline[pipeline.index("def stage_contracts") : pipeline.index("def stage_test")]
        self.assertIn('"safety_selftest"', release)
        self.assertIn("safety_selftest.py", release)
        self.assertIn('"safety_selftest"', contracts)
        self.assertIn("safety_selftest.py", contracts)

    def test_safety_selftest_json_reports_pass_status(self) -> None:
        script = GATE / "safety_selftest.py"
        completed = subprocess.run(
            [sys.executable, str(script), "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["case_count"], 12)
        self.assertEqual(payload["good_passed"], 12)
        self.assertEqual(payload["bad_rejected"], 12)

    def test_forbidden_third_party_names_are_absent(self) -> None:
        needles = _forbidden_needles()
        hits: list[str] = []
        for path in _iter_repo_files(ROOT):
            found = _first_needle(path, needles)
            if found is None:
                continue
            hits.append(f"{path.relative_to(ROOT).as_posix()} contains {found.decode('utf-8')}")
            if len(hits) >= 20:
                break
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
