from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = ROOT / "skills"
SPEC_SCRIPTS = SKILLS_ROOT / "codex-spec-driven-development" / "scripts"
sys.path.insert(0, str(SPEC_SCRIPTS))

import check_spec  # noqa: E402
import init_spec  # noqa: E402


class SdlcSilcAndUnifiedMemoryTests(unittest.TestCase):
    def test_unified_memory_architecture_defines_four_tier_ssot_and_write_back(self) -> None:
        arch_path = SKILLS_ROOT / "codex-project-memory" / "references" / "unified-memory-architecture.md"
        self.assertTrue(arch_path.is_file())
        content = arch_path.read_text(encoding="utf-8")

        for required in (
            "Tier 1 (L0)",
            "Tier 2 (L1)",
            "Tier 3 (L2)",
            "Tier 4 (L3)",
            "Single Source of Truth (SSOT)",
            "Deterministic Write-Back Protocol",
            "Long-Horizon Continuity Contract",
            "SILC",
        ):
            with self.subTest(required=required):
                self.assertIn(required, content)

    def test_memory_skills_reference_unified_memory_architecture(self) -> None:
        skills = (
            "codex-project-memory/SKILL.md",
            "codex-context-engine/SKILL.md",
            "codex-role-docs/SKILL.md",
            "codex-project-pulse/SKILL.md",
            "codex-master-instructions/SKILL.md",
            "codex-intent-context-analyzer/SKILL.md",
        )
        for rel in skills:
            text = (SKILLS_ROOT / rel).read_text(encoding="utf-8")
            with self.subTest(skill=rel):
                self.assertTrue(
                    "unified-memory-architecture.md" in text or "4-Tier" in text,
                    f"{rel} must reference the 4-Tier Unified Memory Architecture",
                )

    def test_spec_schema_and_generator_include_silc_integration_contracts(self) -> None:
        schema_path = SKILLS_ROOT / "codex-spec-driven-development" / "references" / "spec.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertIn("System Integration Contracts (SILC)", schema["required_fields"])
        self.assertIn("silc_contracts", schema)
        self.assertEqual(schema["silc_contracts"]["id_format"], "SILC-001")

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            spec_dir = project_root / ".codex" / "specs" / "checkout-flow"
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "SPEC.md"
            spec_file.write_text(
                init_spec.render_spec("Checkout Flow", "Build fullstack checkout", ["frontend", "backend", "data"]),
                encoding="utf-8",
            )
            rendered = spec_file.read_text(encoding="utf-8")
            self.assertIn("## System Integration Contracts (SILC)", rendered)
            self.assertIn("SILC-001", rendered)
            self.assertIn("SILC-002", rendered)

            report = check_spec.build_report(project_root, ["src/Checkout.tsx", "api/checkout.py"])
            self.assertEqual(report["overall"], "pass")
            self.assertEqual(report["matched_specs"], ["checkout-flow"])
            self.assertIn("SILC-001", report["matched_silc_contracts"])
            self.assertIn("SILC-002", report["matched_silc_contracts"])
            self.assertTrue(all("SILC-001" in item["candidate_silc_ids"] for item in report["files"]))

    def test_workflows_and_plan_writer_enforce_silc_seams_and_memory_write_back(self) -> None:
        files = (
            "codex-plan-writer/SKILL.md",
            "codex-workflow-autopilot/SKILL.md",
            "codex-workflow-autopilot/references/workflow-create.md",
            "codex-workflow-autopilot/references/workflow-plan.md",
            "codex-workflow-autopilot/references/workflow-handoff.md",
            ".workflows/prototype.md",
            ".workflows/create.md",
            ".workflows/plan.md",
            ".workflows/handoff.md",
        )
        for rel in files:
            text = (SKILLS_ROOT / rel).read_text(encoding="utf-8")
            with self.subTest(file=rel):
                self.assertIn("SILC", text)


if __name__ == "__main__":
    unittest.main()
