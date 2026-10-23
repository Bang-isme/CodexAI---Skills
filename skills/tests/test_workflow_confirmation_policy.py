import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "skills/codex-workflow-autopilot/references/workflow-routing-contract.json"
POLICY_REFERENCE = "workflow-routing-contract.json"


class WorkflowConfirmationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def confirmation_policy(self):
        self.assertIn("confirmation_policy", self.contract)
        return self.contract["confirmation_policy"]

    def test_policy_distinguishes_clear_scope_from_required_confirmation(self):
        needs_confirmation = self.confirmation_policy()["needs_confirmation"]

        self.assertIs(needs_confirmation["clear_explicit_request_with_no_open_material_decisions"], False)
        self.assertIs(needs_confirmation["material_ambiguity_without_safe_default"], True)
        self.assertIs(
            needs_confirmation["unrequested_destructive_irreversible_high_impact_or_external_action"],
            True,
        )
        self.assertIs(needs_confirmation["scope_expansion"], True)

    def test_direct_request_authorizes_only_stated_scope_and_reversible_defaults(self):
        authorization = self.confirmation_policy()["authorization"]

        self.assertIs(authorization["explicit_request_authorizes_stated_scope"], True)
        self.assertIs(authorization["extends_to_adjacent_work"], False)
        self.assertIs(authorization["reversible_defaults_allowed_when_scope_is_clear"], True)

    def test_plan_only_stops_but_internal_plan_can_execute_authorized_work(self):
        policy = self.confirmation_policy()
        self.assertIs(policy["plan_only_request"]["stop_after_plan"], True)
        implementation = policy["implementation_request_using_plan"]
        self.assertIs(implementation["proceed_within_authorized_scope"], True)
        self.assertIs(implementation["pause_on_unapproved_scope_or_risk"], True)

    def test_intent_analyzer_uses_conditional_confirmation(self):
        analyzer = (ROOT / "skills/codex-intent-context-analyzer/SKILL.md").read_text(encoding="utf-8")

        self.assertIn(POLICY_REFERENCE, analyzer)
        self.assertIn("needs_confirmation", analyzer)
        self.assertNotIn("Keep `needs_confirmation` true by default", analyzer)
        self.assertNotIn('If user says "just do it", still ask 2 short boundary questions.', analyzer)

    def test_workflow_entrypoints_align_with_shared_policy(self):
        paths = [
            "skills/codex-workflow-autopilot/SKILL.md",
            "skills/codex-workflow-autopilot/agents/openai.yaml",
            "skills/codex-workflow-autopilot/references/workflow-create.md",
            "skills/codex-workflow-autopilot/references/workflow-plan.md",
            "skills/.workflows/create.md",
            "skills/.workflows/plan.md",
            "skills/codex-plan-writer/SKILL.md",
            "skills/codex-master-instructions/references/baseline-policy.md",
        ]
        contents = {path: (ROOT / path).read_text(encoding="utf-8") for path in paths}

        for path, content in contents.items():
            with self.subTest(path=path):
                self.assertIn(POLICY_REFERENCE, content)

        self.assertNotIn("wait for explicit user approval before Phase 3", contents[paths[0]])
        self.assertNotIn("Activate after intent analysis is confirmed.", contents[paths[0]])
        self.assertNotIn("confirm requirements and constraints", contents[paths[0]].lower())
        self.assertNotIn("confirm implementation scope with user constraints", contents[paths[2]].lower())
        self.assertIn("plan-only", contents[paths[3]])
        self.assertIn("continue within the authorized scope", contents[paths[3]].lower())
        self.assertNotIn("Stop before implementation and ask for explicit approval to proceed.", contents[paths[3]])
        self.assertNotIn("confirm requirements, inspect patterns", contents[paths[3]].lower())
        self.assertNotIn("Confirm scope, users, and constraints before touching code.", contents[paths[4]])
        self.assertIn("plan-only", contents[paths[5]])
        self.assertIn("explicitly requested implementation", contents[paths[6]].lower())
        self.assertNotIn("user has reviewed and approved the plan", contents[paths[6]].lower())
        self.assertNotIn("Get approval, then write `$plan`.", contents[paths[7]])

    def test_pipeline_metadata_names_the_runners_used_by_the_source(self):
        registry = json.loads((ROOT / "skills/.system/references/plugin-tools.json").read_text(encoding="utf-8"))
        pipeline = next(tool for tool in registry["tools"] if tool["name"] == "pipeline_run")
        description = pipeline["safety_policy"]["description"].lower()

        self.assertIn("unittest", description)
        self.assertIn("node", description)
        self.assertNotIn("spawn pytest", description)


if __name__ == "__main__":
    unittest.main()
