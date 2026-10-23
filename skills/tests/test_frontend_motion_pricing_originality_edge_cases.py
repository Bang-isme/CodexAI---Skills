from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILLS_ROOT / "codex-visual-quality-gate" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from visual_quality_gate import (  # noqa: E402
    evaluate_motion_contract,
    evaluate_originality_check,
    evaluate_pricing_contract,
    evaluate_scroll_chapter_state,
)


def codes(result: dict) -> set[str]:
    return {item["code"] for item in result.get("issues", [])}


def plan(name: str, highlighted: bool = False, cta: str = "Start trial", limits=None, features=None) -> dict:
    return {
        "name": name,
        "highlighted": highlighted,
        "cta": cta,
        "limits": limits or ["Seats", "Projects", "Retention"],
        "features": features or ["Audit log", "SAML", "Exports"],
    }


def pricing(**overrides) -> dict:
    payload = {
        "plans": [plan("Guide", highlighted=True), plan("Team"), plan("Department")],
        "billing_toggle": {
            "monthly": True,
            "annual": True,
            "savings_math": "Annual billing saves 17% (12 months for the price of 10).",
        },
        "mobile": {"width": 390, "layout": "stacked-cards", "horizontal_overflow": False},
        "faq_topics": [
            "refund policy",
            "trial terms",
            "cancellation behavior",
            "seat/usage definition",
            "procurement/invoicing",
        ],
        "offer_kind": "evergreen",
        "robots": "index,follow",
    }
    payload.update(overrides)
    return payload


def norm(text: str) -> str:
    return text.replace("–", "-").replace("—", "-").lower()


class MotionBandTests(unittest.TestCase):
    def test_control_feedback_band_is_inclusive(self):
        for duration, expected in ((120, "pass"), (180, "pass"), (220, "pass"), (119, "fail"), (221, "fail")):
            with self.subTest(duration=duration):
                result = evaluate_motion_contract({"job": "control-feedback", "duration_ms": duration})
                self.assertEqual(result["status"], expected)

    def test_out_of_band_duration_fails_unless_exception_is_documented(self):
        outside = {"job": "control-feedback", "duration_ms": 400}
        self.assertIn("duration-out-of-band", codes(evaluate_motion_contract(outside)))
        self.assertEqual(evaluate_motion_contract({**outside, "exception": "no"})["status"], "fail")

        waived = evaluate_motion_contract({
            **outside,
            "exception": "Brief records a slower confirm on this operator console.",
        })
        self.assertEqual(waived["status"], "pass")
        self.assertTrue(waived["exception_accepted"])
        self.assertIn("duration-out-of-band", waived["waived_codes"])
        self.assertNotIn("duration-out-of-band", codes(waived))

        capped = evaluate_motion_contract({
            "parallax_viewport_fraction": 0.2,
            "exception": "Brief records a taller hero for this launch.",
        })
        self.assertEqual(capped["status"], "fail")
        self.assertIn("parallax-cap-exceeded", codes(capped))

    def test_duration_bands_are_job_specific(self):
        cases = (
            ("toggle-popover-toast", 180, "pass"),
            ("toggle-popover-toast", 320, "pass"),
            ("toggle-popover-toast", 179, "fail"),
            ("toggle-popover-toast", 321, "fail"),
            ("section-entrance", 400, "pass"),
            ("section-entrance", 800, "pass"),
            ("section-entrance", 450, "pass"),
            ("section-entrance", 399, "fail"),
            ("editorial-mask", 500, "pass"),
            ("editorial-mask", 760, "pass"),
            ("editorial-mask", 450, "fail"),
            ("editorial-mask", 761, "fail"),
            ("hero-sequence", 800, "pass"),
            ("hero-sequence", 1600, "pass"),
            ("hero-sequence", 799, "fail"),
            ("hero-sequence", 1601, "fail"),
        )
        for job, duration, expected in cases:
            with self.subTest(job=job, duration=duration):
                result = evaluate_motion_contract({"job": job, "duration_ms": duration})
                self.assertEqual(result["status"], expected)

    def test_scrub_lag_band_is_inclusive(self):
        for lag, expected in ((0.8, "pass"), (1.1, "pass"), (1.4, "pass"), (0.79, "fail"), (1.41, "fail")):
            with self.subTest(lag=lag):
                result = evaluate_motion_contract({"scrub_lag": lag})
                self.assertEqual(result["status"], expected)
        self.assertEqual(evaluate_motion_contract({"scrub": True})["status"], "pass")

    def test_stagger_bands_are_inclusive(self):
        inside = evaluate_motion_contract({"stagger_s": {"word": 0.035, "line": 0.08, "card": 0.06}})
        self.assertEqual(inside["status"], "pass")
        edges = evaluate_motion_contract({"stagger_s": {"word": 0.07, "line": 0.14, "card": 0.10}})
        self.assertEqual(edges["status"], "pass")
        for key, value in (("word", 0.034), ("line", 0.079), ("card", 0.059), ("card", 0.101)):
            with self.subTest(key=key, value=value):
                result = evaluate_motion_contract({"stagger_s": {key: value}})
                self.assertIn("stagger-out-of-band", codes(result))

    def test_reveal_travel_depends_on_product_or_narrative_context(self):
        for context, distance, expected in (
            ("product", 12, "pass"),
            ("product", 24, "pass"),
            ("product", 11, "fail"),
            ("product", 25, "fail"),
            ("narrative", 24, "pass"),
            ("narrative", 48, "pass"),
            ("narrative", 23, "fail"),
            ("narrative", 49, "fail"),
        ):
            with self.subTest(context=context, distance=distance):
                result = evaluate_motion_contract({
                    "reveal_context": context,
                    "reveal_travel_px": distance,
                })
                self.assertEqual(result["status"], expected)

    def test_text_blur_resolves_to_zero(self):
        self.assertEqual(evaluate_motion_contract({"text_blur_px": 4, "text_blur_end_px": 0})["status"], "pass")
        self.assertEqual(evaluate_motion_contract({"text_blur_px": 10})["status"], "pass")
        self.assertIn("text-blur-out-of-band", codes(evaluate_motion_contract({"text_blur_px": 3})))
        self.assertIn("text-blur-out-of-band", codes(evaluate_motion_contract({"text_blur_px": 11})))
        soft = evaluate_motion_contract({
            "text_blur_px": 6,
            "text_blur_end_px": 2,
            "exception": "Brief records a softer headline for this essay.",
        })
        self.assertIn("text-blur-end-not-zero", codes(soft))
        self.assertEqual(soft["status"], "fail")

    def test_hover_and_parallax_caps_are_strict(self):
        self.assertEqual(
            evaluate_motion_contract({"hover": {"scale": 1.02, "tilt_deg": 3.9, "travel_px": 15}})["status"],
            "pass",
        )
        self.assertIn("hover-cap-exceeded", codes(evaluate_motion_contract({"hover": {"scale": 1.03}})))
        self.assertIn("hover-cap-exceeded", codes(evaluate_motion_contract({"hover": {"tilt_deg": 4}})))
        self.assertIn("hover-cap-exceeded", codes(evaluate_motion_contract({"hover": {"tilt_deg": -4}})))
        self.assertIn("hover-cap-exceeded", codes(evaluate_motion_contract({"hover": {"travel_px": 16}})))
        self.assertEqual(evaluate_motion_contract({"parallax_viewport_fraction": 0.049})["status"], "pass")
        self.assertEqual(evaluate_motion_contract({"parallax_viewport_fraction": -0.04})["status"], "pass")
        self.assertIn("parallax-cap-exceeded", codes(evaluate_motion_contract({"parallax_viewport_fraction": 0.05})))

    def test_reveal_trigger_uses_visibility_or_82_percent_line(self):
        for fraction, expected in ((0.20, "pass"), (0.30, "pass"), (0.19, "fail"), (0.31, "fail")):
            with self.subTest(fraction=fraction):
                result = evaluate_motion_contract({"reveal_visible_fraction": fraction})
                self.assertEqual(result["status"], expected)
        self.assertEqual(evaluate_motion_contract({"reveal_top_viewport_fraction": 0.82})["status"], "pass")
        self.assertIn(
            "reveal-trigger-out-of-band",
            codes(evaluate_motion_contract({"reveal_top_viewport_fraction": 0.85})),
        )

    def test_utility_surface_cannot_stagger_every_card(self):
        utility = evaluate_motion_contract({
            "surface": "utility",
            "stagger_every_card": True,
            "stagger_s": {"card": 0.08},
        })
        self.assertEqual(utility["status"], "fail")
        self.assertIn("utility-card-stagger", codes(utility))
        narrative = evaluate_motion_contract({
            "surface": "experience",
            "stagger_every_card": True,
            "stagger_s": {"card": 0.08},
        })
        self.assertEqual(narrative["status"], "pass")

    def test_collapsed_reduced_motion_fails_when_initial_state_is_hidden(self):
        hidden = evaluate_motion_contract({
            "reduced_motion": {"duration_ms": 0.01, "initial_state_hidden": True},
        })
        self.assertEqual(hidden["status"], "fail")
        self.assertIn("fake-reduced-motion", codes(hidden))
        still_hidden = evaluate_motion_contract({
            "reduced_motion": {"mode": "designed-still", "initial_state_hidden": True, "content_visible": False},
        })
        self.assertIn("fake-reduced-motion", codes(still_hidden))

    def test_designed_still_frame_passes_reduced_motion(self):
        result = evaluate_motion_contract({
            "reduced_motion": {"mode": "designed-still", "content_visible": True, "initial_state_hidden": False},
        })
        self.assertEqual(result["status"], "pass")
        self.assertNotIn("fake-reduced-motion", codes(result))

    def test_scroll_linked_layout_properties_fail(self):
        layout = evaluate_motion_contract({
            "scroll_linked": True,
            "animated_properties": ["width", "height", "top"],
        })
        self.assertEqual(layout["status"], "fail")
        self.assertIn("layout-scroll-property", codes(layout))
        composited = evaluate_motion_contract({
            "scroll_linked": True,
            "animated_properties": ["transform", "opacity"],
        })
        self.assertEqual(composited["status"], "pass")

    def test_hero_sequence_requires_internal_beats(self):
        ready = evaluate_motion_contract({
            "job": "hero-sequence",
            "duration_ms": 1200,
            "beats_ms": [500, 700],
        })
        self.assertEqual(ready["status"], "pass")
        single = evaluate_motion_contract({
            "job": "hero-sequence",
            "duration_ms": 1200,
            "beats_ms": [1200],
        })
        self.assertIn("hero-missing-beats", codes(single))

    def test_runtime_clamps_dt_dpr_visibility_and_ablation_order(self):
        order = [
            "lower DPR",
            "disable post-processing",
            "freeze shadows",
            "disable particles",
            "hide groups",
            "swap LOD",
            "replace materials",
        ]
        healthy = evaluate_motion_contract({"runtime": {
            "dt": 1 / 30,
            "raw_dt": 0.2,
            "device_pixel_ratio": 2,
            "document_hidden": True,
            "paused": True,
            "canvas_offscreen": True,
            "offscreen_running_animations": 0,
            "ablation_order": order,
        }})
        self.assertEqual(healthy["status"], "pass", healthy["issues"])
        broken = evaluate_motion_contract({"runtime": {
            "dt": 0.05,
            "device_pixel_ratio": 3,
            "document_hidden": True,
            "canvas_offscreen": True,
            "offscreen_running_animations": 2,
            "ablation_order": list(reversed(order)),
        }})
        self.assertTrue({
            "dt-unclamped",
            "dpr-above-cap",
            "runtime-not-paused",
            "offscreen-animations-running",
            "ablation-order",
        }.issubset(codes(broken)))


class ScrollChapterStateTests(unittest.TestCase):
    def test_progress_uses_live_inner_height(self):
        tall = evaluate_scroll_chapter_state(500, 3000, 800, 2, [{"id": "orient", "opacity": 1, "inert": False}])
        short = evaluate_scroll_chapter_state(500, 3000, 700, 2, [{"id": "orient", "opacity": 1, "inert": False}])
        self.assertAlmostEqual(tall["progress"], 500 / (3000 - 800))
        self.assertAlmostEqual(short["progress"], 500 / (3000 - 700))
        self.assertNotEqual(tall["scene_signature"], short["scene_signature"])
        self.assertEqual(tall["inner_height"], 800)
        self.assertEqual(short["inner_height"], 700)

    def test_chapter_index_flips_at_0_39_not_0_50(self):
        before = evaluate_scroll_chapter_state(380, 2000, 1000, 2, [{"id": "a", "opacity": 1}])
        boundary = evaluate_scroll_chapter_state(390, 2000, 1000, 2, [{"id": "a", "opacity": 1}])
        after = evaluate_scroll_chapter_state(450, 2000, 1000, 2, [{"id": "a", "opacity": 1}])
        self.assertAlmostEqual(before["progress"], 0.38)
        self.assertAlmostEqual(boundary["progress"], 0.39)
        self.assertAlmostEqual(after["progress"], 0.45)
        self.assertEqual(before["active_index"], 0)
        self.assertEqual(boundary["active_index"], 1)
        self.assertEqual(after["active_index"], 1)

    def test_later_chapters_use_the_same_0_39_fraction(self):
        expected = ((190, 0), (200, 1), (450, 1), (500, 1), (700, 2))
        for scroll_y, index in expected:
            with self.subTest(scroll_y=scroll_y):
                result = evaluate_scroll_chapter_state(scroll_y, 2000, 1000, 3, [{"id": "a", "opacity": 1}])
                self.assertEqual(result["active_index"], index)

    def test_hidden_chapters_require_inert(self):
        exposed = evaluate_scroll_chapter_state(0, 2000, 1000, 2, [
            {"id": "visible", "opacity": 1, "inert": False},
            {"id": "quiet", "opacity": 0, "inert": False},
        ])
        self.assertEqual(exposed["status"], "fail")
        self.assertIn("hidden-chapter-not-inert", codes(exposed))
        protected = evaluate_scroll_chapter_state(0, 2000, 1000, 2, [
            {"id": "visible", "opacity": 1, "inert": False},
            {"id": "quiet", "opacity": 0, "inert": True},
        ])
        self.assertEqual(protected["status"], "pass")

    def test_smooth_scroll_during_capture_is_a_warning(self):
        capturing = evaluate_scroll_chapter_state(0, 2000, 1000, 1, [
            {"id": "a", "opacity": 1, "inert": False},
            {"role": "capture", "capturing": True, "scroll_behavior": "smooth"},
        ])
        self.assertEqual(capturing["status"], "pass")
        self.assertTrue(any(
            item["code"] == "smooth-scroll-during-capture" and item["severity"] == "warning"
            for item in capturing["warnings"]
        ))
        resting = evaluate_scroll_chapter_state(0, 2000, 1000, 1, [
            {"id": "a", "opacity": 1, "inert": False, "scroll_behavior": "smooth"},
        ])
        self.assertNotIn("smooth-scroll-during-capture", codes(resting))

    def test_navigation_modes_share_one_scene_signature(self):
        base = [
            {"id": "orient", "opacity": 1, "inert": False},
            {"id": "proof", "opacity": 0, "inert": True},
        ]
        signatures = []
        for mode in ("forward", "reverse", "jump", "reload"):
            chapters = [{**chapter, "approach": mode, "direction": mode} for chapter in base]
            result = evaluate_scroll_chapter_state(450, 2000, 1000, 2, chapters)
            signatures.append(result["scene_signature"])
            self.assertNotIn(mode, result["scene_signature"])
        self.assertEqual(len(set(signatures)), 1)

    def test_fast_skip_plays_only_the_final_transition(self):
        result = evaluate_scroll_chapter_state(0, 5000, 1000, 4, [
            {"id": "a", "opacity": 1, "inert": False, "fast_skip_from": 0, "fast_skip_to": 3},
            {"id": "b", "opacity": 0, "inert": True},
            {"id": "c", "opacity": 0, "inert": True},
            {"id": "d", "opacity": 0, "inert": True},
        ])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["played_transitions"], [3])

    def test_scene_weight_and_track_length(self):
        heavy = evaluate_scroll_chapter_state(0, 2000, 1000, 1, [
            {"id": "scene", "opacity": 1, "inert": False, "scene_weight_vh": 2.4, "span": 2},
        ])
        self.assertIn("scene-weight-out-of-band", codes(heavy))
        self.assertEqual(heavy["tracks"][0]["track_vh"], 300)
        self.assertEqual(heavy["cadence"]["dwell_screens"], 1.15)
        self.assertEqual(heavy["cadence"]["move_screens"], 0.85)
        self.assertEqual(heavy["cadence"]["flip_progress"], 0.39)
        self.assertEqual(heavy["cadence"]["track_rule"], "(span + 1) * 100vh")
        for weight in (0.7, 1.8):
            with self.subTest(weight=weight):
                result = evaluate_scroll_chapter_state(0, 2000, 1000, 1, [
                    {"id": "scene", "opacity": 1, "inert": False, "scene_weight_vh": weight},
                ])
                self.assertEqual(result["status"], "pass")

    def test_short_page_and_overscroll_are_clamped(self):
        short = evaluate_scroll_chapter_state(0, 800, 800, 1, [{"id": "only", "opacity": 1, "inert": False}])
        self.assertEqual(short["progress"], 0.0)
        self.assertEqual(short["status"], "pass")
        overscrolled = evaluate_scroll_chapter_state(5000, 3000, 1000, 2, [{"id": "end", "opacity": 1}])
        self.assertEqual(overscrolled["progress"], 1.0)
        self.assertEqual(overscrolled["active_index"], 1)


class PricingAndLandingContractTests(unittest.TestCase):
    def test_valid_pricing_contract_passes(self):
        result = evaluate_pricing_contract(pricing())
        self.assertEqual(result["status"], "pass", result["issues"])
        self.assertEqual(result["plan_count"], 3)
        self.assertEqual(set(result["cta_verbs"]), {"start"})

    def test_fourth_plan_requires_a_documented_exception(self):
        four = [plan("Guide", highlighted=True), plan("Team"), plan("Department"), plan("Agency")]
        bare = evaluate_pricing_contract(pricing(plans=four))
        self.assertEqual(bare["status"], "fail")
        self.assertIn("too-many-plans", codes(bare))
        recorded = evaluate_pricing_contract(pricing(
            plans=four,
            peer_plan_exception="Brief allows a fourth procurement tier for public-sector buyers.",
        ))
        self.assertEqual(recorded["status"], "pass", recorded["issues"])
        self.assertTrue(recorded["exception_accepted"])

    def test_plan_row_counts_stay_inside_three_to_six(self):
        too_many_limits = evaluate_pricing_contract(pricing(plans=[
            plan("Guide", highlighted=True, limits=["a", "b", "c", "d", "e", "f", "g"]),
            plan("Team"),
            plan("Department"),
        ]))
        self.assertIn("limit-row-count", codes(too_many_limits))
        too_few_features = evaluate_pricing_contract(pricing(plans=[
            plan("Guide", highlighted=True, features=["Audit log", "SAML"]),
            plan("Team"),
            plan("Department"),
        ]))
        self.assertIn("feature-row-count", codes(too_few_features))
        edges = evaluate_pricing_contract(pricing(plans=[
            plan("Guide", highlighted=True, limits=["a", "b", "c", "d", "e", "f"], features=["a", "b", "c", "d", "e", "f"]),
            plan("Team"),
            plan("Department"),
        ]))
        self.assertEqual(edges["status"], "pass", edges["issues"])

    def test_plan_ctas_highlight_and_savings_math(self):
        mismatched = evaluate_pricing_contract(pricing(plans=[
            plan("Guide", highlighted=True, cta="Start trial"),
            plan("Team", cta="Contact sales"),
            plan("Department", cta="Start team"),
        ]))
        self.assertIn("cta-verb-mismatch", codes(mismatched))
        same_verb = evaluate_pricing_contract(pricing(plans=[
            plan("Guide", highlighted=True, cta="Start trial"),
            plan("Team", cta="Start team"),
            plan("Department", cta="Start department"),
        ]))
        self.assertEqual(same_verb["status"], "pass", same_verb["issues"])
        none_highlighted = evaluate_pricing_contract(pricing(plans=[plan("Guide"), plan("Team"), plan("Department")]))
        self.assertIn("highlighted-plan-count", codes(none_highlighted))
        two_highlighted = evaluate_pricing_contract(pricing(plans=[
            plan("Guide", highlighted=True),
            plan("Team", highlighted=True),
            plan("Department"),
        ]))
        self.assertIn("highlighted-plan-count", codes(two_highlighted))
        vague_savings = evaluate_pricing_contract(pricing(billing_toggle={
            "monthly": True,
            "annual": True,
            "savings_math": "Annual is cheaper",
        }))
        self.assertIn("missing-savings-math", codes(vague_savings))

    def test_mobile_390_rejects_horizontal_tables(self):
        horizontal = evaluate_pricing_contract(pricing(mobile={
            "width": 390,
            "layout": "horizontal-scroll-table",
            "horizontal_overflow": False,
        }))
        self.assertEqual(horizontal["status"], "fail")
        self.assertIn("mobile-horizontal-scroll", codes(horizontal))
        stacked = evaluate_pricing_contract(pricing(mobile={"width": "390px", "layout": "stacked-cards"}))
        self.assertEqual(stacked["status"], "pass", stacked["issues"])
        overflowing = evaluate_pricing_contract(pricing(mobile={
            "width": 390,
            "layout": "stacked-cards",
            "horizontal_overflow": True,
        }))
        self.assertIn("mobile-horizontal-scroll", codes(overflowing))

    def test_pricing_faq_requires_five_topics(self):
        missing = evaluate_pricing_contract(pricing(faq_topics=[
            "refund policy",
            "cancellation behavior",
            "seat/usage definition",
            "procurement/invoicing",
        ]))
        self.assertEqual(missing["status"], "fail")
        self.assertTrue(any(
            item["code"] == "missing-faq-topic" and "trial terms" in item["message"]
            for item in missing["issues"]
        ))

    def test_campaign_pages_are_noindex_and_evergreen_pages_stay_indexable(self):
        campaign = evaluate_pricing_contract(pricing(offer_kind="time-bound campaign", robots="index,follow"))
        self.assertIn("campaign-missing-noindex", codes(campaign))
        hidden_campaign = evaluate_pricing_contract(pricing(offer_kind="time-bound campaign", robots="noindex"))
        self.assertEqual(hidden_campaign["status"], "pass", hidden_campaign["issues"])
        blocked_evergreen = evaluate_pricing_contract(pricing(offer_kind="evergreen", robots="noindex"))
        self.assertIn("evergreen-not-indexable", codes(blocked_evergreen))


class OriginalityLadderTests(unittest.TestCase):
    def test_eight_word_verbatim_and_unusual_number_are_high_severity(self):
        copy = "Operators reconcile ledger drift before the quarterly close marker 1847"
        result = evaluate_originality_check(
            {"copy": copy, "numbers": ["1847"]},
            {"copy": copy, "numbers": ["1847"]},
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["severity"], "high")
        self.assertIn("verbatim-copy", {item["code"] for item in result["findings"]})
        self.assertIn("unusual-number", {item["code"] for item in result["findings"]})
        self.assertIn(2, result["rungs"])
        self.assertIn(3, result["rungs"])

    def test_seven_word_overlap_is_not_verbatim(self):
        copy = "Operators reconcile ledger drift before the quarterly"
        result = evaluate_originality_check({"copy": copy}, {"copy": copy})
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["findings"], [])

    def test_generic_conventions_are_not_plagiarism(self):
        page = {
            "copy": "Learn more",
            "section_order": ["hero", "faq"],
            "palette": "black-and-white",
            "accent_count": 1,
            "motion": "standard fade",
        }
        result = evaluate_originality_check(page, dict(page))
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["severity"], "none")
        for label in ("Learn more", "hero+FAQ order", "black-and-white palette", "single accent", "standard fade"):
            self.assertIn(label, result["false_positives_ignored"])

    def test_nudged_price_on_copied_structure_fails(self):
        reference = {
            "prices": [49],
            "layout_traits": ["three-tier-cards", "billing-toggle", "limit-rows"],
            "copy": "Operator seat",
        }
        for nudged in (48, 47):
            with self.subTest(nudged=nudged):
                result = evaluate_originality_check({**reference, "prices": [nudged]}, reference)
                self.assertEqual(result["status"], "fail")
                self.assertEqual(result["severity"], "high")
                finding = next(item for item in result["findings"] if item["code"] == "nudged-number-copy-fix")
                self.assertTrue(finding["fix_pattern"])
                self.assertIn("$49", finding["message"])
                self.assertIn(f"${nudged}", finding["message"])
        distant = evaluate_originality_check(
            {
                "prices": [46],
                "layout_traits": ["three-tier-cards", "billing-toggle", "limit-rows"],
                "copy": "Operator seat",
            },
            reference,
        )
        self.assertEqual(distant["status"], "pass")
        self.assertFalse(any(item["code"] == "nudged-number-copy-fix" for item in distant["findings"]))
        different = evaluate_originality_check(
            {
                "prices": [48],
                "layout_traits": ["usage-slider", "single-quote"],
                "copy": "Field crews log hours on site.",
            },
            reference,
        )
        self.assertEqual(different["status"], "pass")

    def test_identical_bytes_are_the_first_rung(self):
        result = evaluate_originality_check(
            {"bytes": "sha256-ledger-hero", "copy": "A calm operator console."},
            {"bytes": "sha256-ledger-hero", "copy": "A field guide to masonry."},
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["severity"], "high")
        self.assertEqual(result["strongest_rung"], 1)
        self.assertIn("identical-bytes", {item["code"] for item in result["findings"]})

    def test_frame_sequence_and_motion_cluster_are_upper_rungs(self):
        frames = ["ledger-mask", "audit-pin", "close-pan", "release-still"]
        sequenced = evaluate_originality_check({"frames": frames}, {"frames": list(frames)})
        self.assertIn("frame-sequence", {item["code"] for item in sequenced["findings"]})
        self.assertIn(4, sequenced["rungs"])
        generic = evaluate_originality_check(
            {"frames": ["hero", "faq", "footer"]},
            {"frames": ["hero", "faq", "footer"]},
        )
        self.assertEqual(generic["findings"], [])
        cluster = evaluate_originality_check(
            {
                "layout_traits": ["split-ledger", "sticky-audit", "asymmetric-close"],
                "motion_traits": ["mask-wipe", "scrub-lag", "chapter-pin"],
            },
            {
                "layout_traits": ["split-ledger", "sticky-audit", "asymmetric-close"],
                "motion_traits": ["mask-wipe", "scrub-lag", "chapter-pin"],
            },
        )
        self.assertEqual(cluster["status"], "fail")
        self.assertIn("multi-trait-cluster", {item["code"] for item in cluster["findings"]})


class DocumentationContractTests(unittest.TestCase):
    def test_motion_and_gsap_docs_state_the_numeric_contract(self):
        motion = norm((SKILLS_ROOT / "codex-frontend-design" / "references" / "motion.md").read_text(encoding="utf-8"))
        gsap = norm((SKILLS_ROOT / "codex-frontend-implementation" / "references" / "gsap-mastery.md").read_text(encoding="utf-8"))
        for phrase in (
            "horizontal & pinned chapter scroll-state contract",
            "progress = scrolly / (scrollheight - innerheight)",
            "1.15",
            "0.85",
            "(span + 1) * 100vh",
            "0.7-1.8",
            "0.39",
            "not `0.50`",
            "inert",
            "scroll-behavior: smooth",
            "fast-skip",
            "identical scene signature",
            "designed still frame",
            "0.01ms",
            "120-220ms",
            "180-320ms",
            "400-800ms",
            "500-760ms",
            "800-1600ms",
            "0.8-1.4",
            "0.035-0.07s",
            "0.08-0.14s",
            "0.06-0.10s",
            "12-24px",
            "24-48px",
            "4-10px",
            "1.03",
            "4deg",
            "16px",
            "5%",
            "82%",
            "20-30%",
            "width",
            "height",
            "devicepixelratio",
            "1/30s",
            "offscreen running animations == 0",
            "lower dpr -> disable post-processing -> freeze shadows -> disable particles -> hide groups -> swap lod -> replace materials",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, motion)
                self.assertIn(phrase, gsap)

    def test_landing_and_pricing_docs_are_linked(self):
        design = (SKILLS_ROOT / "codex-frontend-design" / "SKILL.md").read_text(encoding="utf-8")
        patterns = (SKILLS_ROOT / "codex-frontend-design" / "references" / "patterns.md").read_text(encoding="utf-8")
        landing = norm((SKILLS_ROOT / "codex-frontend-design" / "references" / "landing-page-anatomy.md").read_text(encoding="utf-8"))
        pricing_doc = norm((SKILLS_ROOT / "codex-frontend-design" / "references" / "pricing-architecture.md").read_text(encoding="utf-8"))
        self.assertIn("references/pricing-architecture.md", design)
        self.assertIn("pricing-architecture.md", patterns)
        self.assertTrue((SKILLS_ROOT / "codex-frontend-design" / "references" / "pricing-architecture.md").is_file())
        for phrase in (
            "classic sections",
            "long-form story",
            "minimal conversion",
            "comparison",
            "hero -> benefits -> how it works -> proof -> objections/faq -> final action",
            "source-matched",
            "risk reversal",
            "evergreen",
            "noindex",
            "time-bound",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, landing)
        for phrase in (
            "three tier cards",
            "usage/value slider",
            "two-path split",
            "enterprise last-mile",
            "at most `3`",
            "3-6",
            "390",
            "stacked cards",
            "horizontal-scrolling comparison table",
            "refund policy",
            "trial terms",
            "cancellation behavior",
            "seat/usage definition",
            "procurement/invoicing",
            "savings math",
            "identical action verb",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, pricing_doc)

    def test_originality_imagery_and_craft_docs_state_the_rules(self):
        grammar = (SKILLS_ROOT / "codex-frontend-design" / "references" / "grammar.md").read_text(encoding="utf-8")
        anti_slop = (SKILLS_ROOT / "codex-frontend-design" / "references" / "anti-slop.md").read_text(encoding="utf-8")
        imagery = norm((SKILLS_ROOT / "codex-frontend-design" / "references" / "imagery.md").read_text(encoding="utf-8"))
        craft = norm((SKILLS_ROOT / "codex-frontend-implementation" / "references" / "craft-recipes.md").read_text(encoding="utf-8"))
        for phrase in (
            "Identical bytes/assets",
            "Verbatim copy/claims",
            "Brand names & unusual numbers",
            "Distinctive crop/frame sequence",
            "Multi-trait layout+motion cluster",
            "False-Positive Exclusions",
            "black-and-white",
            "single accent",
            "hero+FAQ",
            "standard fade",
            "Learn more",
            "$49",
            "$47",
            "`distant`",
            "`recognizable`",
            "`close-but-four-elements-changed`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, grammar)
        self.assertIn("12-Point AI Slop & Gimmick Rejection Matrix", anti_slop)
        self.assertIn("grammar.md", anti_slop)
        self.assertIn("$49", anti_slop)
        for phrase in ("1:1", "4:5", "3:4", "16:9", "9:16", "1/3", "30-50%"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, imagery)
        for phrase in (
            "must not compete on the same edge",
            "8px",
            "14px",
            "24px",
            "44px",
            "1px",
            "0.4",
            "150ms",
            "400-600ms",
            "distance traveled",
            "stationary cursor",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, craft)

    def test_visual_gate_links_rubric_and_narrative_qa(self):
        gate = (SKILLS_ROOT / "codex-visual-quality-gate" / "SKILL.md").read_text(encoding="utf-8")
        rubric = norm((SKILLS_ROOT / "codex-visual-quality-gate" / "references" / "anchored-craft-rubric.md").read_text(encoding="utf-8"))
        narrative = norm((SKILLS_ROOT / "codex-visual-quality-gate" / "references" / "narrative-runtime-qa.md").read_text(encoding="utf-8"))
        self.assertIn("references/anchored-craft-rubric.md", gate)
        self.assertIn("references/narrative-runtime-qa.md", gate)
        self.assertIn("evaluate_motion_contract", gate)
        self.assertIn("evaluate_scroll_chapter_state", gate)
        self.assertIn("evaluate_pricing_contract", gate)
        self.assertIn("evaluate_originality_check", gate)
        for phrase in ("minor nits", "below an `8` bar", "7.5", "clipping", "overflow", "contrast", "missing-capture"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rubric)
        for phrase in (
            "404",
            "context loss",
            "200%",
            "url bar",
            "0.39",
            "inert",
            "designed still frame",
            "0.01ms",
            "offscreen running animations == 0",
            "lower dpr -> disable post-processing -> freeze shadows -> disable particles -> hide groups -> swap lod -> replace materials",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, narrative)

    def test_gsap_markdown_links_still_resolve(self):
        guide = SKILLS_ROOT / "codex-frontend-implementation" / "references" / "gsap-mastery.md"
        references = re.findall(r"`([^`]+\.md)`", guide.read_text(encoding="utf-8"))
        self.assertTrue(references)
        for reference in references:
            with self.subTest(reference=reference):
                self.assertTrue((guide.parent / reference).resolve().is_file())

    def test_existing_excellence_phrases_remain(self):
        motion = (SKILLS_ROOT / "codex-frontend-design" / "references" / "motion.md").read_text(encoding="utf-8").lower()
        gsap = (SKILLS_ROOT / "codex-frontend-implementation" / "references" / "gsap-mastery.md").read_text(encoding="utf-8").lower()
        gate = (SKILLS_ROOT / "codex-visual-quality-gate" / "SKILL.md").read_text(encoding="utf-8").lower()
        design = (SKILLS_ROOT / "codex-frontend-design" / "SKILL.md").read_text(encoding="utf-8").lower()
        imagery = (SKILLS_ROOT / "codex-frontend-design" / "references" / "imagery.md").read_text(encoding="utf-8").lower()
        for phrase in (
            "meaningful progression, comparison, spatial relationship, reveal, or transformation",
            "one signature mechanism",
            "quiet section",
            "payoff",
            "utility-heavy",
            "scroll hijacking",
            "native scroll",
            "backward scrolling",
            "browser back/forward",
            "sticky navigation",
            "never moves keyboard focus",
            "reduced motion",
            "static state",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, motion)
        for phrase in (
            "normalized progress",
            "single timeline or progress controller",
            "avoid unrelated scrolltriggers",
            "gsap.matchmedia",
            "context.revert()",
            "reduced-motion",
            "component cleanup",
            "local ownership",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, gsap)
        for phrase in (
            "first-time-user",
            "returning-user",
            "regression",
            "capture key",
            "before and after",
            "first visual anchor",
            "layout contract",
            "invariant",
            "long labels",
            "breakpoint edges",
            "overflow",
            "structural change",
            "intermediate progress",
            "scene entry",
            "scene release",
            "paused, fast, and backward scrolling",
            "reduced-motion static state",
            "mobile/tablet scene treatment",
            "direct jump",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, gate)
        self.assertIn("references/motion.md", design)
        self.assertIn("scroll narrative", design)
        self.assertIn("/codex-frontend", design)
        for phrase in ("materially improves", "available project assets", "not the default", "semantic controls", "focal point", "safe area"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, imagery)


if __name__ == "__main__":
    unittest.main()
