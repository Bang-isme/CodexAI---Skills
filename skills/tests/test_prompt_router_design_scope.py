from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROUTER_PATH = Path(__file__).resolve().parents[1] / ".system" / "scripts" / "prompt_router.py"
SPEC = importlib.util.spec_from_file_location("prompt_router", ROUTER_PATH)
assert SPEC and SPEC.loader
prompt_router = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prompt_router
SPEC.loader.exec_module(prompt_router)


class DesignScopeRoutingTests(unittest.TestCase):
    def test_single_page_stays_fast(self):
        route = prompt_router.route_prompt("Make a beautiful landing page for our product")
        self.assertEqual(route["suggested_agent"], "design-lead")
        self.assertEqual(route["design_mode"], "fast")

    def test_multiscreen_prototype_selects_internal_prototype_mode(self):
        route = prompt_router.route_prompt("Build a multi-screen onboarding prototype with working steps")
        self.assertEqual(route["suggested_agent"], "design-lead")
        self.assertEqual(route["workflow"], "create")
        self.assertEqual(route["design_mode"], "prototype")
        self.assertIn("codex-visual-quality-gate", route["required_skills"])

    def test_flow_mapping_does_not_claim_a_visual_prototype(self):
        route = prompt_router.route_prompt("Map the onboarding user flow and empty states")
        self.assertEqual(route["workflow"], "plan")
        self.assertIsNone(route["design_mode"])

    def test_redesign_alone_does_not_force_studio(self):
        route = prompt_router.route_prompt("Redesign one settings page within the existing design system")
        self.assertEqual(route["design_mode"], "fast")

    def test_requested_new_brand_directions_select_studio(self):
        route = prompt_router.route_prompt("Create three visual directions for a new brand identity")
        self.assertEqual(route["suggested_agent"], "design-lead")
        self.assertEqual(route["design_mode"], "studio")

    def test_approved_design_implementation_skips_design_lead(self):
        route = prompt_router.route_prompt("Implement the approved dashboard design in React")
        self.assertEqual(route["suggested_agent"], "frontend-specialist")
        self.assertNotEqual(route["design_mode"], "prototype")

    def test_generic_fullstack_mvp_prototype_stays_on_fullstack_route(self):
        route = prompt_router.route_prompt("Prototype a fullstack MVP from scratch")
        self.assertEqual(route["suggested_agent"], "planner")
        self.assertEqual(route["workflow"], "prototype")


if __name__ == "__main__":
    unittest.main()
