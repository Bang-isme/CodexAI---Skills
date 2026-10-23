from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = ROOT / "skills"
RUNTIME_HOOK_SCRIPTS = SKILLS_ROOT / "codex-runtime-hook" / "scripts"
GATE_SCRIPTS = SKILLS_ROOT / "codex-execution-quality-gate" / "scripts"

for p in (RUNTIME_HOOK_SCRIPTS, GATE_SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import auto_gate  # noqa: E402
import run_gate  # noqa: E402
import runtime_hook  # noqa: E402
import security_scan  # noqa: E402
import tech_debt_scan  # noqa: E402


class Argon4RealityAuditFixesTests(unittest.TestCase):
    def test_runtime_hook_emits_precision_mode_and_reuse_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            shared = project / "src" / "utils"
            shared.mkdir(parents=True)
            (shared / "money.py").write_text("def format_cents(cents: int) -> str:\n    return str(cents)\n", encoding="utf-8")

            report = runtime_hook.build_report(project)
            prompt_text = runtime_hook.render_prompt(report)

        self.assertIn("precision_mode", report)
        self.assertEqual(report["precision_mode"]["level"], "full")
        self.assertIn("format_cents", report["reuse_map"])
        self.assertIn("Precision mode: full", prompt_text)
        self.assertIn("Reuse map:", prompt_text)

    def test_tech_debt_scan_and_auto_gate_surface_shortcut_ledger_and_no_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            src = project / "src"
            src.mkdir()
            (src / "worker.py").write_text(
                "# shortcut: 500 items, switch to batch queue above 500 items\n"
                "# shortcut: 100 rows\n"
                "def process():\n    return 1\n",
                encoding="utf-8",
            )
            debt = tech_debt_scan.scan_project(project, max_function_lines=50, max_file_lines=500, todo_age_days=30)
            gate_res = auto_gate.run_tech_debt(project)

        self.assertEqual(debt["shortcut_ledger"]["total"], 2)
        self.assertEqual(debt["shortcut_ledger"]["no_trigger_count"], 1)
        self.assertTrue(any("no-trigger" in w for w in debt["warnings"]))
        self.assertEqual(gate_res["payload"]["shortcuts_total"], 2)
        self.assertEqual(gate_res["payload"]["shortcuts_no_trigger"], 1)
        self.assertEqual(gate_res["payload"]["status"], "warn")

    def test_run_gate_enforces_finding_contract_for_review_deliverables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            bad_review = (
                "# Code Review\n\n"
                "Decision: Needs fixes in `src/app.py`.\n"
                "Run `python -m unittest` to verify `src/app.py`.\n"
                "Tradeoff: keeping the change minimal vs refactoring `src/app.py`.\n"
            )
            bad_report = run_gate.build_gate_report(
                project_root=project,
                timeout_lint=30,
                timeout_test=30,
                skip_lint=True,
                skip_test=True,
                output_text=bad_review,
                deliverable_kind="review",
            )
            self.assertTrue(bad_report["finding_contract"]["executed"])
            self.assertFalse(bad_report["finding_contract"]["ok"])
            self.assertFalse(bad_report["gate_passed"])
            self.assertTrue(
                any("4-part finding contract" in issue for issue in bad_report["blocking_issues"]),
                bad_report["blocking_issues"],
            )

            (project / "src").mkdir(exist_ok=True)
            (project / "src" / "auth.py").write_text("def verify_token(token):\n    return bool(token)\n", encoding="utf-8")
            good_review = (
                "# Code Review Report: Authentication Guard (`src/auth.py`)\n\n"
                "**Decision:** Hold merge until `Must-Fix` item 1 in `src/auth.py` is patched and verified.\n\n"
                "Priority: Correct -> Safe -> Holds at expected load -> Tested -> Fast -> Lean\n"
                "Assumed Load: 1000 req/min\n"
                "Not Checked / Out of Scope: Third-party billing webhook sandbox\n\n"
                "## Tradeoffs & Risk Analysis\n\n"
                "- **Option A (Selected):** Reject empty bearer tokens directly in `src/auth.py:1` before session lookup. "
                "Cost: 2 lines of code. Risk: None. Reversibility: Instant.\n"
                "- **Option B (Rejected):** Rely on downstream database lookup to fail on blank token. "
                "Rejected because it wastes connection pool capacity at 1000 req/min.\n\n"
                "### Must-Fix\n\n"
                "1. Auth bypass on whitespace token in `src/auth.py:1`\n"
                "- What it is (file:line): `src/auth.py:1` in `verify_token`\n"
                "- The problem (concrete failing input/case): Calling `verify_token('   ')` returns `True` for a whitespace-only token\n"
                "- The smallest fix: Strip whitespace with `bool(token and token.strip())` in `src/auth.py:2`\n"
                "- What happens if skipped: Whitespace bearer headers bypass the guard and hit protected handlers\n\n"
                "## Verification Commands & Next Steps\n\n"
                "- Patch `src/auth.py`.\n"
                "- Run `python -m unittest discover -s tests -p \"test_*.py\"` and confirm `0` failures.\n"
            )
            good_report = run_gate.build_gate_report(
                project_root=project,
                timeout_lint=30,
                timeout_test=30,
                skip_lint=True,
                skip_test=True,
                output_text=good_review,
                deliverable_kind="review",
            )
            self.assertTrue(good_report["finding_contract"]["executed"])
            self.assertTrue(good_report["finding_contract"]["ok"], good_report["finding_contract"])
            self.assertTrue(good_report["gate_passed"], good_report["blocking_issues"])

    def test_security_scan_avoids_false_positives_and_catches_pkcs8_and_eval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".gitignore").write_text(".env*\n", encoding="utf-8")
            (project / ".env").write_text("SECRET=placeholder_for_local_dev\n", encoding="utf-8")
            src = project / "src"
            src.mkdir()
            (src / "safe.py").write_text(
                "model.eval()\n"
                "regex.exec(text)\n"
                'svg = "http://www.w3.org/2000/svg"\n'
                'aws_doc = "AKIAIOSFODNN7EXAMPLE"\n',
                encoding="utf-8",
            )
            safe_report = security_scan.scan(project)
            self.assertEqual(safe_report["critical"], [])
            self.assertEqual(safe_report["warnings"], [])

            (src / "unsafe.py").write_text(
                'eval("2 + 2")\n'
                'key = "-----BEGIN PRIVATE KEY-----"\n',
                encoding="utf-8",
            )
            unsafe_report = security_scan.scan(project)
            issues = [item["issue"] for item in unsafe_report["critical"]]
            self.assertIn("Dynamic code execution pattern found (eval/exec)", issues)
            self.assertIn("Private key found in source code", issues)

    def test_auto_gate_deploy_mode_includes_safety_selftest(self) -> None:
        self.assertIn("safety_selftest", auto_gate.MODE_CHECKS["deploy"])
        res = auto_gate.run_safety_selftest(ROOT)
        self.assertEqual(res["payload"]["status"], "pass")
        self.assertEqual(res["payload"]["good_passed"], 12)
        self.assertEqual(res["payload"]["bad_rejected"], 12)

    def test_workflows_and_starters_are_aligned_with_modern_contracts(self) -> None:
        review_wf = (SKILLS_ROOT / ".workflows" / "review.md").read_text(encoding="utf-8")
        self.assertIn("finding_contract.py", review_wf)
        self.assertIn("shortcut_ledger.py", review_wf)
        self.assertIn("Must-Fix", review_wf)

        for wf in ("create.md", "debug.md", "refactor.md"):
            content = (SKILLS_ROOT / ".workflows" / wf).read_text(encoding="utf-8")
            with self.subTest(workflow=wf):
                self.assertIn("precision-ladder.md", content)
                self.assertIn("reuse_map.py", content)
                self.assertIn("Caller-Grep Rule", content)

        starters_dir = SKILLS_ROOT / "codex-domain-specialist" / "starters"
        express_starter = (starters_dir / "express-api.js").read_text(encoding="utf-8")
        auth_starter = (starters_dir / "auth-flow.js").read_text(encoding="utf-8")
        api_client = (starters_dir / "api-client.js").read_text(encoding="utf-8")
        crud_page = (starters_dir / "react-crud-page.jsx").read_text(encoding="utf-8")
        design_css = (starters_dir / "design-system.css").read_text(encoding="utf-8")
        health_starter = (starters_dir / "health-check.js").read_text(encoding="utf-8")

        self.assertIn("fieldErrors", express_starter)
        self.assertIn("Idempotency-Key", express_starter)
        self.assertIn("nextCursor", express_starter)
        self.assertIn("JWT_REFRESH_SECRET", auth_starter)
        self.assertIn("httpOnly: true", auth_starter)
        self.assertNotIn("localStorage", api_client)
        self.assertIn("Idempotency-Key", api_client)
        self.assertIn("fieldErrors", crud_page)
        self.assertIn('role="dialog"', crud_page)
        self.assertIn("oklch(", design_css)
        self.assertNotIn("#3b82f6", design_css)
        self.assertIn("isDraining", health_starter)

    def test_living_docs_ssot_lifecycle_and_handoff_integration(self) -> None:
        role_docs_scripts = SKILLS_ROOT / "codex-role-docs" / "scripts"
        design_scripts = SKILLS_ROOT / "codex-design-md" / "scripts"
        memory_scripts = SKILLS_ROOT / "codex-project-memory" / "scripts"
        for p in (role_docs_scripts, design_scripts, memory_scripts):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))

        import build_knowledge_index  # noqa: E402
        import build_role_docs_index  # noqa: E402
        import check_role_docs  # noqa: E402
        import design_context  # noqa: E402
        import generate_handoff  # noqa: E402
        import init_role_docs  # noqa: E402
        import init_spec  # noqa: E402
        import update_role_docs  # noqa: E402

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            manifest = init_role_docs.load_manifest()
            roles = init_role_docs.parse_roles("fullstack", manifest)
            self.assertEqual(roles, ["frontend", "backend", "devops", "qa"])

            init_role_docs.initialize_role_docs(project, roles=roles)
            brief_text = (project / ".codex/project-docs/PROJECT-BRIEF.md").read_text(encoding="utf-8")
            fe_doc_text = (project / ".codex/project-docs/frontend/FE-01-ui-ux.md").read_text(encoding="utf-8")
            be_doc_text = (project / ".codex/project-docs/backend/BE-01-api-contracts.md").read_text(encoding="utf-8")

            self.assertIn("Stage 0: From-Scratch Bootstrap", brief_text)
            self.assertIn("Surface & UX Contract Matrix (6-State & SILC-001 Alignment)", fe_doc_text)
            self.assertIn("API & Service Contract Matrix (`SILC-001` Producer)", be_doc_text)

            # Initially all created role docs are stubs and flagged by check_role_docs
            initial_check = check_role_docs.check_role_docs(project, ["src/App.tsx"])
            self.assertTrue(len(initial_check["stub_docs"]) > 0)

            # Populate FE-00 via update_role_docs
            update_role_docs.update_role_doc(
                project_root=project,
                role="frontend",
                doc_id="FE-00",
                summary="Locked App Shell and SILC-001 state boundary",
                files=["src/App.tsx"],
                decision="Use 260px + minmax(0, 1fr) workbench layout",
                contract="SILC-001 cursor pagination + RFC 9457 fieldErrors",
                verification="npm test",
                stage="Stage 2: MVP Implementation",
                population="populated",
            )
            idx_payload = build_role_docs_index.build_index(project)
            self.assertGreaterEqual(idx_payload["summary"]["populated"], 1)
            self.assertEqual(len(idx_payload["documents"]), len(idx_payload["docs"]))

            # Knowledge index reads role_docs count accurately
            role_summary = build_knowledge_index.collect_role_docs(project)
            self.assertEqual(role_summary["docs_count"], len(idx_payload["documents"]))
            self.assertGreaterEqual(role_summary["populated_count"], 1)

            # Scaffold design surface & spec, then generate handoff
            design_context.build_report(project, "scaffold", "checkout", "Checkout Surface", apply=True)
            surface_md = (project / ".codex/design/surfaces/checkout.md").read_text(encoding="utf-8")
            self.assertIn("Linked `SILC-001` Status / Error Code", surface_md)

            spec_dir = project / ".codex/specs/checkout"
            spec_dir.mkdir(parents=True, exist_ok=True)
            (spec_dir / "SPEC.md").write_text(
                init_spec.render_spec("Checkout", "Build fullstack checkout", ["frontend", "backend"]),
                encoding="utf-8",
            )
            (project / "DESIGN.md").write_text("# DESIGN\n", encoding="utf-8")

            handoff_out = project / ".codex/handoff.md"
            generate_handoff.generate_handoff(
                project_root=project,
                output_path=handoff_out,
                max_depth=2,
                include_decisions=True,
                include_git_status=False,
            )
            handoff_text = handoff_out.read_text(encoding="utf-8")
            self.assertIn("## Living Source of Truth (Specs, SILC & Role Docs)", handoff_text)
            self.assertIn("SILC-001", handoff_text)
            self.assertIn("DESIGN.md", handoff_text)
            self.assertIn(".codex/design/surfaces/checkout.md", handoff_text)

    def test_scanners_handle_react_htmlfor_tanstack_ispending_and_python_test_selection(self) -> None:
        import accessibility_check  # noqa: E402
        import pre_commit_check  # noqa: E402
        import predict_impact  # noqa: E402
        import smart_test_selector  # noqa: E402
        import ux_audit  # noqa: E402

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            src = project / "src"
            tests = project / "tests"
            src.mkdir()
            tests.mkdir()

            # React component with htmlFor, wrapping <label>, and TanStack Query isPending
            tsx_file = src / "ProfileForm.tsx"
            tsx_file.write_text(
                "export function ProfileForm() {\n"
                "  const { data, isPending, error } = useQuery({ queryKey: ['profile'] });\n"
                "  if (isPending) return <div aria-busy='true'>Loading</div>;\n"
                "  if (error) return <div role='alert'>{error.message}</div>;\n"
                "  return (\n"
                "    <form>\n"
                "      <label htmlFor='email-input'>Email</label>\n"
                "      <input id='email-input' type='email' required />\n"
                "      <label>Full Name <input type='text' required /></label>\n"
                "      <input type='submit' value='Save' />\n"
                "    </form>\n"
                "  );\n"
                "}\n",
                encoding="utf-8",
            )

            a11y_issues = []
            a11y_seen = set()
            by_wcag = {}
            accessibility_check.check_markup_file(tsx_file, project, a11y_issues, a11y_seen, by_wcag)
            label_issues = [i for i in a11y_issues if i["wcag"] == "3.3.2"]
            self.assertEqual(label_issues, [], f"Expected 0 label issues for htmlFor and wrapped label, got: {label_issues}")

            ux_issues = []
            ux_seen = set()
            ux_audit.scan_ui_file(tsx_file, project, ux_issues, ux_seen)
            loading_issues = [i for i in ux_issues if i["category"] == "missing_loading_state"]
            self.assertEqual(loading_issues, [], f"Expected 0 missing_loading_state for isPending, got: {loading_issues}")

            # Python test selection for test_<module>.py and Python imports
            (src / "billing_engine.py").write_text("def compute_invoice():\n    return 100\n", encoding="utf-8")
            (tests / "test_billing_engine.py").write_text(
                "from src.billing_engine import compute_invoice\n"
                "def test_invoice():\n    assert compute_invoice() == 100\n",
                encoding="utf-8",
            )
            all_tests = set(smart_test_selector.collect_test_files(project))
            reasons = {}
            found = smart_test_selector.strategy_convention(project, ["src/billing_engine.py"], all_tests, reasons)
            smart_test_selector.strategy_import_tracing(project, ["src/billing_engine.py"], all_tests, reasons, found)
            self.assertIn("tests/test_billing_engine.py", reasons)

            # Multiline import and re-export in predict_impact
            (src / "barrel.ts").write_text("export {\n  ProfileForm\n} from './ProfileForm';\n", encoding="utf-8")
            parsed_mods = predict_impact.parse_imports(src / "barrel.ts", (src / "barrel.ts").read_text(encoding="utf-8"))
            self.assertIn("./ProfileForm", parsed_mods)

            # Pre-commit secret scan ignores ordinary variable names like password = req.body.password
            added = {"src/auth.ts": [(10, "const password = req.body.password;"), (11, "print('hello')")]}
            sec_res, sec_ok = pre_commit_check.secret_scan(added)
            self.assertTrue(sec_ok)
            self.assertEqual(sec_res["status"], "pass")


if __name__ == "__main__":
    unittest.main()
