from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
DESIGN_SKILL = SKILLS_ROOT / "codex-frontend-design" / "SKILL.md"
AUDIT_GUIDE = SKILLS_ROOT / "codex-frontend-design" / "references" / "existing-product-audit.md"
PROTOTYPE_PIPELINE = SKILLS_ROOT / "codex-frontend-design" / "references" / "prototype-pipeline.md"
LAYOUT_DECISIONS = SKILLS_ROOT / "codex-frontend-design" / "references" / "layout-decision-framework.md"
LAYOUT_ADAPTATION = SKILLS_ROOT / "codex-frontend-design" / "references" / "layout-adaptation.md"
COMPOSITION = SKILLS_ROOT / "codex-frontend-design" / "references" / "composition.md"
MOTION_GUIDE = SKILLS_ROOT / "codex-frontend-design" / "references" / "motion.md"
IMAGERY_GUIDE = SKILLS_ROOT / "codex-frontend-design" / "references" / "imagery.md"
IMPLEMENTATION_SKILL = SKILLS_ROOT / "codex-frontend-implementation" / "SKILL.md"
FRONTEND_RULES = SKILLS_ROOT / "codex-frontend-implementation" / "references" / "frontend-rules.md"
VISUAL_GATE_SKILL = SKILLS_ROOT / "codex-visual-quality-gate" / "SKILL.md"
CAPABILITY_MATRIX = SKILLS_ROOT / ".system" / "skill-capabilities.json"
DESIGN_UI_METADATA = SKILLS_ROOT / "codex-frontend-design" / "agents" / "openai.yaml"


class FrontendExcellenceProtocolTests(unittest.TestCase):
    def test_design_skill_routes_broad_existing_product_work_to_audit_guide(self):
        design_skill = DESIGN_SKILL.read_text(encoding="utf-8")
        matrix = json.loads(CAPABILITY_MATRIX.read_text(encoding="utf-8"))
        capability = next(
            item for item in matrix["capabilities"] if item["skill"] == "codex-frontend-design"
        )

        self.assertIn("references/existing-product-audit.md", design_skill)
        self.assertIn("broad", design_skill.lower())
        self.assertIn("existing product", design_skill.lower())
        self.assertIn("existing product audit", [trigger.lower() for trigger in capability["triggers"]])
        self.assertTrue(AUDIT_GUIDE.is_file())

    def test_audit_guide_traces_prioritized_findings_to_evidence_and_verification(self):
        guide = AUDIT_GUIDE.read_text(encoding="utf-8").lower()

        for required_concept in (
            "observed symptom",
            "evidence",
            "root cause",
            "user impact",
            "priority",
            "verification",
        ):
            with self.subTest(concept=required_concept):
                self.assertIn(required_concept, guide)

    def test_audit_guide_preserves_working_behavior_and_labels_unverified_work(self):
        guide = AUDIT_GUIDE.read_text(encoding="utf-8").lower()
        implementation = IMPLEMENTATION_SKILL.read_text(encoding="utf-8").lower()

        self.assertIn("preserve", guide)
        self.assertIn("mock", guide)
        self.assertIn("unverified", guide)
        self.assertIn("preserve", implementation)

    def test_visual_gate_uses_user_perspectives_and_records_regressions(self):
        gate = VISUAL_GATE_SKILL.read_text(encoding="utf-8").lower()

        self.assertIn("first-time-user", gate)
        self.assertIn("returning-user", gate)
        self.assertIn("regression", gate)
        self.assertIn("capture key", gate)

    def test_skill_picker_metadata_mentions_audit_capability(self):
        metadata = DESIGN_UI_METADATA.read_text(encoding="utf-8").lower()

        self.assertIn("short_description: \"design, audit", metadata)
        self.assertIn("$codex-frontend-design", metadata)

    def test_broad_audit_keeps_agent_state_in_one_scoped_note(self):
        guide = AUDIT_GUIDE.read_text(encoding="utf-8").lower()
        pipeline = PROTOTYPE_PIPELINE.read_text(encoding="utf-8").lower()

        self.assertIn("single consolidated note", guide)
        self.assertIn("confirmed / assumed / unknown", guide)
        self.assertIn("decision", guide)
        self.assertIn("risk and rollback", guide)
        self.assertIn("regression matrix", guide)
        self.assertIn("do not create separate", pipeline)

    def test_major_design_changes_use_a_keep_to_rebuild_decision_and_change_budget(self):
        guide = AUDIT_GUIDE.read_text(encoding="utf-8").lower()

        for decision in ("keep", "refine", "recompose", "rebuild"):
            with self.subTest(decision=decision):
                self.assertIn(decision, guide)
        for criterion in ("observable problem", "regression risk", "rollback", "simplest"):
            with self.subTest(criterion=criterion):
                self.assertIn(criterion, guide)

    def test_review_uses_before_after_and_persona_checks_with_real_states(self):
        gate = VISUAL_GATE_SKILL.read_text(encoding="utf-8").lower()
        guide = AUDIT_GUIDE.read_text(encoding="utf-8").lower()

        for check in ("before and after", "first visual anchor", "first-time user", "returning user"):
            with self.subTest(check=check):
                self.assertIn(check, gate + guide)
        for state in ("slow loading", "failed network", "long content", "repeated actions"):
            with self.subTest(state=state):
                self.assertIn(state, gate + guide)

    def test_iteration_records_actual_outcomes_and_stops_without_artificial_churn(self):
        guide = AUDIT_GUIDE.read_text(encoding="utf-8").lower()

        self.assertIn("expected outcome", guide)
        self.assertIn("actual outcome", guide)
        self.assertIn("highest-priority unresolved", guide)
        self.assertIn("meaningful, actionable", guide)
        self.assertIn("do not create artificial work", guide)

    def test_deadline_scopes_effort_without_weakening_evidence_status(self):
        guide = AUDIT_GUIDE.read_text(encoding="utf-8").lower()
        pipeline = PROTOTYPE_PIPELINE.read_text(encoding="utf-8").lower()

        self.assertIn("timebox", guide + pipeline)
        self.assertIn("coverage gap", guide + pipeline)
        self.assertIn("degraded", guide + pipeline)

    def test_design_artifacts_have_distinct_roles_and_avoid_duplicate_route_details(self):
        pipeline = PROTOTYPE_PIPELINE.read_text(encoding="utf-8").lower()

        self.assertIn("ux contract", pipeline)
        self.assertIn("direction.md", pipeline)
        self.assertIn("capture manifest", pipeline)
        self.assertIn("do not duplicate route/state details", pipeline)

    def test_creative_layout_decisions_separate_product_fit_from_invariants(self):
        decisions = LAYOUT_DECISIONS.read_text(encoding="utf-8").lower()

        for concept in ("must hold", "safe to explore", "signature move", "expected user benefit"):
            with self.subTest(concept=concept):
                self.assertIn(concept, decisions)

    def test_layout_implementation_uses_content_safe_constraints(self):
        adaptation = LAYOUT_ADAPTATION.read_text(encoding="utf-8").lower()
        implementation = IMPLEMENTATION_SKILL.read_text(encoding="utf-8").lower()

        self.assertIn("layout contract", adaptation + implementation)
        self.assertIn("minmax(0, 1fr)", implementation)
        self.assertIn("fixed height", implementation)

    def test_implementation_does_not_suppress_design_skill_creativity(self):
        implementation = IMPLEMENTATION_SKILL.read_text(encoding="utf-8").lower()

        self.assertIn("keep design exploration in `codex-frontend-design`", implementation)
        self.assertIn("distinctive, product-fit direction first", implementation)

    def test_visual_gate_reviews_layout_invariants_at_stress_cases_and_breakpoint_edges(self):
        gate = VISUAL_GATE_SKILL.read_text(encoding="utf-8").lower()

        for check in ("layout contract", "invariant", "long labels", "breakpoint edges", "overflow", "structural change"):
            with self.subTest(check=check):
                self.assertIn(check, gate)

    def test_narrative_design_is_conditional_and_tracks_user_understanding(self):
        design = DESIGN_SKILL.read_text(encoding="utf-8").lower()
        pipeline = PROTOTYPE_PIPELINE.read_text(encoding="utf-8").lower()
        composition = COMPOSITION.read_text(encoding="utf-8").lower()

        combined = design + pipeline + composition
        for concept in ("content-led", "narrative spine", "utility-heavy", "user question"):
            with self.subTest(concept=concept):
                self.assertIn(concept, combined)

    def test_narrative_map_stays_inside_existing_ux_contract(self):
        pipeline = PROTOTYPE_PIPELINE.read_text(encoding="utf-8").lower()

        self.assertIn("same ux contract", pipeline)
        self.assertIn("narrative beats", pipeline)
        self.assertIn("separate storyboard", pipeline)

    def test_scroll_story_keeps_native_navigation_and_reduced_motion_equivalent(self):
        motion = MOTION_GUIDE.read_text(encoding="utf-8").lower()
        gate = VISUAL_GATE_SKILL.read_text(encoding="utf-8").lower()
        combined = motion + gate

        for concept in (
            "native scroll",
            "direct jump",
            "backward scrolling",
            "browser back/forward",
            "sticky navigation",
            "never moves keyboard focus",
            "reduced motion",
            "static state",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, combined)

    def test_asset_creation_is_conditional_on_product_value_and_existing_alternatives(self):
        imagery = IMAGERY_GUIDE.read_text(encoding="utf-8").lower()

        for concept in (
            "materially improves",
            "css",
            "html",
            "available project assets",
            "not the default",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, imagery)

    def test_asset_brief_covers_role_rendering_and_responsive_behavior(self):
        imagery = IMAGERY_GUIDE.read_text(encoding="utf-8").lower()

        for concept in (
            "user-facing role",
            "focal point",
            "safe area",
            "rendered dimensions",
            "crop",
            "breakpoint",
            "fallback",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, imagery)

    def test_visual_assets_never_replace_semantic_controls_or_accessibility(self):
        imagery = IMAGERY_GUIDE.read_text(encoding="utf-8").lower()

        for concept in (
            "semantic controls",
            "essential product copy",
            "without its visual asset",
            "decorative images",
            "alt text",
            "image-load failure",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, imagery)

    def test_asset_provenance_stays_in_existing_direction_and_gate_checks_rendered_use(self):
        imagery = IMAGERY_GUIDE.read_text(encoding="utf-8").lower()
        pipeline = PROTOTYPE_PIPELINE.read_text(encoding="utf-8").lower()
        gate = VISUAL_GATE_SKILL.read_text(encoding="utf-8").lower()

        self.assertIn("direction file", pipeline)
        self.assertIn("separate asset inventory", pipeline + imagery)
        for concept in ("crop", "focal", "asset", "failure fallback"):
            with self.subTest(concept=concept):
                self.assertIn(concept, gate)

    def test_frontend_architecture_starts_from_existing_conventions_and_simplest_fit(self):
        rules = FRONTEND_RULES.read_text(encoding="utf-8").lower()
        implementation = IMPLEMENTATION_SKILL.read_text(encoding="utf-8").lower()

        for concept in ("inspect", "existing structure", "simplest architecture", "do not impose"):
            with self.subTest(concept=concept):
                self.assertIn(concept, rules + implementation)

    def test_frontend_code_has_clear_ownership_and_dependency_direction(self):
        rules = FRONTEND_RULES.read_text(encoding="utf-8").lower()

        for concept in (
            "route-specific",
            "feature-specific",
            "shared",
            "shared code must not import feature-specific code",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, rules)

    def test_component_extraction_is_based_on_responsibility_not_file_length(self):
        rules = FRONTEND_RULES.read_text(encoding="utf-8").lower()

        for concept in (
            "line count",
            "meaningful responsibility",
            "reuse",
            "test boundary",
            "do not split",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, rules)

    def test_architecture_migrations_are_scoped_incremental_and_verified(self):
        rules = FRONTEND_RULES.read_text(encoding="utf-8").lower()
        implementation = IMPLEMENTATION_SKILL.read_text(encoding="utf-8").lower()

        for concept in (
            "affected consumers",
            "incremental",
            "imports",
            "regression",
            "tests",
            "build",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, rules + implementation)

    def test_frontend_rules_reference_only_available_sibling_guides(self):
        rules = FRONTEND_RULES.read_text(encoding="utf-8")
        references = re.findall(r"`([^`]+\.md)`", rules)

        self.assertTrue(references)
        for reference in references:
            with self.subTest(reference=reference):
                self.assertTrue((FRONTEND_RULES.parent / reference).resolve().is_file())

    def test_prototype_code_organization_follows_project_ownership(self):
        pipeline = PROTOTYPE_PIPELINE.read_text(encoding="utf-8").lower()

        for concept in (
            "existing structure",
            "route, feature, shared-component, and asset ownership",
            "real shared behavior",
            "do not reorganize the project scaffold",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, pipeline)

    def test_visual_gate_reviews_architecture_only_when_ui_structure_changes(self):
        gate = VISUAL_GATE_SKILL.read_text(encoding="utf-8").lower()

        for concept in (
            "moves files",
            "dependency direction",
            "affected consumers",
            "line count alone is not evidence",
            "unrelated project-wide cleanup",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, gate)


if __name__ == "__main__":
    unittest.main()
