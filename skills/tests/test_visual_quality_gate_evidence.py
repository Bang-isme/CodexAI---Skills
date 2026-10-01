from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "codex-visual-quality-gate" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from visual_quality_gate import (  # noqa: E402
    DEFAULT_VIEWPORTS,
    expected_responsive_widths,
    build_report,
    scan_file,
    validate_capture_evidence,
)


def write_png(path: Path, width: int, height: int) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    row = b"\x00" + (b"\x00\x00\x00\xff" * width)
    pixels = zlib.compress(row * height)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", pixels)
        + chunk(b"IEND", b"")
    )


def complete_manifest(project: Path) -> dict:
    route_id = "home"
    breakpoint = 768
    widths = expected_responsive_widths([breakpoint])
    captures = [
        make_capture(project, route_id, v["id"], v["width"], v["height"])
        for v in DEFAULT_VIEWPORTS
    ]
    for width in (breakpoint - 1, breakpoint, breakpoint + 1):
        captures.append(make_capture(project, route_id, f"width-{width}", width, 900))

    scan_widths = [
        {
            "width": width,
            "clientWidth": width,
            "scrollWidth": width,
            "horizontalOverflow": False,
            "clippedControls": [],
            "consoleErrors": [],
        }
        for width in widths
    ]
    return {
        "schemaVersion": 1,
        "status": "captured",
        "provenance": {"appRevision": "fixture", "references": []},
        "routes": [{"id": route_id, "path": "/"}],
        "states": [{"id": "default", "routeId": route_id, "viewportIds": [v["id"] for v in DEFAULT_VIEWPORTS]}],
        "flows": [{"id": "primary-task", "routeIds": [route_id], "summary": "Complete the page's primary task."}],
        "breakpoints": [breakpoint],
        "breakpointSources": ["fixture.css: 768px"],
        "responsiveScan": {
            "minWidth": 320,
            "maxWidth": 2560,
            "step": 64,
            "routes": [{"routeId": route_id, "stateId": "default", "widths": scan_widths}],
        },
        "captures": captures,
        "visualReview": {
            "status": "complete",
            "reviewer": "fixture-reviewer",
            "summary": "Every required fixture image was inspected.",
            "checkedCaptureKeys": [c["key"] for c in captures],
            "findings": [],
        },
        "functionalReview": {
            "status": "complete",
            "checkedFlowIds": ["primary-task"],
            "checkedRouteStateKeys": [f"{route_id}|default"],
            "mainFlowStatus": "pass",
            "accessibilityStatus": "pass",
            "findings": [],
        },
        "errors": [],
    }


def make_capture(project: Path, route_id: str, viewport_id: str, width: int, height: int) -> dict:
    key = f"{route_id}|default|{viewport_id}"
    base = Path(".codex/design/reviews/responsive") / route_id / viewport_id
    slice_path = base / "slice-01.png"
    full_path = base / "stitched.png"
    write_png(project / slice_path, width, height)
    write_png(project / full_path, width, 1200)
    overlap = min(100, max(1, height // 8))
    step = max(1, height - overlap)
    scroll_positions = [0]
    while scroll_positions[-1] + height < 1200:
        next_y = min(scroll_positions[-1] + step, max(0, 1200 - height))
        if next_y <= scroll_positions[-1]:
            break
        scroll_positions.append(next_y)
    segments = []
    covered_end = 0
    for scroll_y in scroll_positions:
        end_y = min(1200, scroll_y + height)
        segments.append(
            {
                "path": slice_path.as_posix(),
                "sourceScrollY": scroll_y,
                "sourceViewportHeight": height,
                "coveredStartY": covered_end,
                "coveredEndY": end_y,
                "image": {"width": width, "height": height},
            }
        )
        covered_end = end_y
    return {
        "key": key,
        "routeId": route_id,
        "stateId": "default",
        "viewportId": viewport_id,
        "viewport": {"width": width, "height": height, "deviceScaleFactor": 1},
        "status": "captured",
        "documentHeight": 1200,
        "stitchedPath": full_path.as_posix(),
        "stitchedImage": {"width": width, "height": 1200},
        "segments": segments,
    }


def save_manifest(project: Path, manifest: dict) -> Path:
    path = project / ".codex/design/reviews/responsive/capture-manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


class VisualQualityGateEvidenceTests(unittest.TestCase):
    def in_project(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name)

    def test_responsive_widths_include_full_sweep_and_breakpoint_edges(self):
        widths = expected_responsive_widths([768, 1024])

        self.assertEqual(widths[0], 320)
        self.assertEqual(widths[-1], 2560)
        self.assertTrue(set(range(320, 2561, 64)).issubset(widths))
        self.assertTrue({767, 768, 769, 1023, 1024, 1025}.issubset(widths))
        self.assertEqual(widths, sorted(set(widths)))

    def test_complete_capture_manifest_passes(self):
        project = self.in_project()
        path = save_manifest(project, complete_manifest(project))

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["route_count"], 1)
        self.assertEqual(report["flow_count"], 1)
        self.assertEqual(report["capture_count"], len(DEFAULT_VIEWPORTS) + 3)
        self.assertEqual(report["responsive_width_count"], len(expected_responsive_widths([768])))

    def test_missing_capture_manifest_is_degraded(self):
        report = validate_capture_evidence(self.in_project(), None)

        self.assertEqual(report["status"], "DEGRADED")
        self.assertIn("manifest", report["reason"].lower())

    def test_top_level_visual_gate_cannot_pass_without_capture_manifest(self):
        report = build_report(self.in_project(), [], apply=False, max_rounds=2)

        self.assertEqual(report["status"], "DEGRADED")
        self.assertEqual(report["capture_evidence"]["status"], "DEGRADED")

    def test_missing_route_viewport_capture_fails(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["captures"].pop(0)
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("capture" in issue.lower() for issue in report["issues"]))

    def test_segment_gap_fails_even_when_stitched_image_exists(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["captures"][0]["segments"][1]["coveredStartY"] = 810
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("gap" in issue.lower() or "coverage" in issue.lower() for issue in report["issues"]))

    def test_missing_width_sample_fails(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["responsiveScan"]["routes"][0]["widths"].pop()
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("width" in issue.lower() for issue in report["issues"]))

    def test_breakpoint_without_a_source_reference_is_degraded(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["breakpointSources"] = []
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "DEGRADED")
        self.assertTrue(any("breakpoint" in issue.lower() and "source" in issue.lower() for issue in report["issues"]))

    def test_horizontal_overflow_fails_responsive_gate(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["responsiveScan"]["routes"][0]["widths"][3]["horizontalOverflow"] = True
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("overflow" in issue.lower() for issue in report["issues"]))

    def test_off_viewport_control_signal_requires_a_capture_at_that_width(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["responsiveScan"]["routes"][0]["widths"][0]["clippedControls"] = [
            {"tag": "button", "id": "next-step", "text": "Continue"}
        ]
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("missing capture home|default|width-320" in issue for issue in report["issues"]))

    def test_incomplete_visual_review_is_degraded(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["visualReview"]["checkedCaptureKeys"].pop()
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "DEGRADED")
        self.assertTrue(any("review" in issue.lower() for issue in report["issues"]))

    def test_degraded_capture_runtime_stays_degraded_without_fake_missing_capture_failures(self):
        project = self.in_project()
        manifest = {
            "schemaVersion": 1,
            "status": "DEGRADED",
            "reason": "Playwright unavailable",
            "routes": [{"id": "home", "path": "/"}],
            "captures": [],
        }
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "DEGRADED")
        self.assertIn("Playwright", report["reason"])

    def test_unresolved_p1_review_finding_fails_with_capture_evidence(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["visualReview"]["findings"] = [{
            "captureKey": manifest["captures"][0]["key"],
            "routeId": "home",
            "stateId": "default",
            "viewportId": "desktop-laptop",
            "description": "Primary action is clipped.",
            "severity": "P1",
            "blocking": True,
            "resolution": {"status": "open"},
        }]
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("unresolved" in issue.lower() for issue in report["issues"]))

    def test_missing_accessibility_review_is_degraded(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["functionalReview"]["accessibilityStatus"] = "pending"
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "DEGRADED")
        self.assertTrue(any("accessibility" in issue.lower() for issue in report["issues"]))

    def test_fixed_p1_review_finding_does_not_block_when_cited(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["visualReview"]["findings"] = [{
            "captureKey": manifest["captures"][0]["key"],
            "routeId": "home",
            "stateId": "default",
            "viewportId": "desktop-laptop",
            "description": "Primary action was clipped before the fix.",
            "severity": "P1",
            "blocking": True,
            "resolution": {"status": "fixed", "note": "Reflowed the actions below the heading."},
        }]
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "pass")

    def test_capture_path_cannot_escape_project_root(self):
        project = self.in_project()
        manifest = complete_manifest(project)
        manifest["captures"][0]["stitchedPath"] = "../../outside.png"
        path = save_manifest(project, manifest)

        report = validate_capture_evidence(project, path)

        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("escape" in issue.lower() or "confine" in issue.lower() for issue in report["issues"]))

    def test_style_pattern_matches_are_review_prompts_not_automatic_defects(self):
        project = self.in_project()
        source = project / "Page.tsx"
        source.write_text(
            '<button className="primary">Save</button>\n'
            '<button className="primary">Publish</button>\n'
            'linear-gradient(90deg, blue, purple) card card card card card card',
            encoding="utf-8",
        )
        findings = []

        scan_file(source, project, findings)

        self.assertTrue(findings)
        self.assertTrue(all(not finding["blocking"] for finding in findings))
        self.assertTrue(all(finding["severity"] == "warning" for finding in findings))


if __name__ == "__main__":
    unittest.main()
