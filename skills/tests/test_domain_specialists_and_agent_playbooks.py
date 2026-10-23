from __future__ import annotations

import json
import unittest
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_REFS = SKILLS_ROOT / "codex-domain-specialist" / "references"
AGENTS_DIR = SKILLS_ROOT / ".agents"
MANIFEST_PATH = SKILLS_ROOT / ".system" / "manifest.json"


class DomainSpecialistsAndAgentPlaybookTests(unittest.TestCase):
    def test_backend_and_api_references_enforce_modern_contract_and_outbox_patterns(self) -> None:
        backend = (DOMAIN_REFS / "backend-rules.md").read_text(encoding="utf-8")
        api_design = (DOMAIN_REFS / "api-design-rules.md").read_text(encoding="utf-8")
        error_handling = (DOMAIN_REFS / "error-handling-patterns.md").read_text(encoding="utf-8")
        validation = (DOMAIN_REFS / "validation-patterns.md").read_text(encoding="utf-8")

        self.assertIn("Transactional Outbox Pattern", backend)
        self.assertIn("Idempotency-Key", backend)
        self.assertIn("RFC 9457", api_design)
        self.assertIn("fieldErrors", api_design)
        self.assertIn("nextCursor", api_design)
        self.assertIn("AppError", error_handling)
        self.assertIn("SILC-###", error_handling)
        self.assertIn("zod", validation.lower())
        self.assertIn(".strict()", validation)

    def test_database_qa_and_devops_references_enforce_modern_sre_and_testing_trophy(self) -> None:
        db_rules = (DOMAIN_REFS / "database-rules.md").read_text(encoding="utf-8")
        migration = (DOMAIN_REFS / "data-migration.md").read_text(encoding="utf-8")
        caching = (DOMAIN_REFS / "caching-patterns.md").read_text(encoding="utf-8")
        testing_rules = (DOMAIN_REFS / "testing-rules.md").read_text(encoding="utf-8")
        testing_strategy = (DOMAIN_REFS / "testing-strategy.md").read_text(encoding="utf-8")
        devops_rules = (DOMAIN_REFS / "devops-rules.md").read_text(encoding="utf-8")
        observability = (DOMAIN_REFS / "observability.md").read_text(encoding="utf-8")
        deployment = (DOMAIN_REFS / "deployment-strategy.md").read_text(encoding="utf-8")

        self.assertIn("Expand-and-Contract", db_rules)
        self.assertIn("EXPLAIN (ANALYZE, BUFFERS)", db_rules)
        self.assertIn("FOR UPDATE SKIP LOCKED", db_rules)
        self.assertIn("CREATE INDEX CONCURRENTLY", migration)
        self.assertIn("Singleflight", caching)
        self.assertIn("Testing Trophy", testing_rules)
        self.assertIn("SILC-###", testing_rules)
        self.assertIn("MSW", testing_strategy)
        self.assertIn("USER 10001", devops_rules)
        self.assertIn("/health/live", devops_rules)
        self.assertIn("/health/ready", devops_rules)
        self.assertIn("OpenTelemetry", observability)
        self.assertIn("RED & USE Metrics", observability)
        self.assertIn("Quantitative Canary & Rollout Abort Criteria", deployment)

    def test_all_ten_agent_personas_are_deep_playbooks_with_silc_and_verification_gates(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        agents = manifest.get("agents", [])
        self.assertEqual(len(agents), 10)

        for agent_name in agents:
            path = AGENTS_DIR / f"{agent_name}.md"
            text = path.read_text(encoding="utf-8")
            with self.subTest(agent=agent_name):
                self.assertIn("file_ownership:", text)
                self.assertIn("## 1. Mission & Ownership Boundaries", text)
                self.assertIn("## 2. 4-Tier Memory & SILC Seam Protocol", text)
                self.assertIn("## 4. Pre-Handoff Verification Gate", text)
                self.assertIn("- [ ]", text)


if __name__ == "__main__":
    unittest.main()
