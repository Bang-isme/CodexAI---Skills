import assert from "node:assert/strict";
import test from "node:test";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { buildCapturePlan, DEFAULT_VIEWPORTS, expectedResponsiveWidths } from "../codex-visual-quality-gate/scripts/responsive_capture_core.mjs";

const sample = {
  baseUrl: "http://127.0.0.1:3000",
  routes: [{ id: "home", path: "/" }],
  breakpoints: [768, 1024],
  states: [
    { id: "default", routeId: "home", viewportIds: ["all"], actions: [] },
    {
      id: "nav-open",
      routeId: "home",
      viewportIds: ["tablet-portrait", "mobile-portrait"],
      actions: [{ type: "click", selector: "[data-testid=menu-trigger]" }],
    },
  ],
};

test("viewport anchors cover laptop, desktop, wide, tablet orientations, and mobile orientations", () => {
  assert.deepEqual(
    DEFAULT_VIEWPORTS.map(({ id, width, height }) => [id, width, height]),
    [
      ["desktop-laptop", 1280, 800],
      ["desktop-standard", 1440, 900],
      ["desktop-wide", 1920, 1080],
      ["tablet-portrait", 768, 1024],
      ["tablet-landscape", 1024, 768],
      ["mobile-portrait", 390, 844],
      ["mobile-landscape", 844, 390],
    ],
  );
});

test("width sweep includes the full range and each breakpoint edge exactly once", () => {
  const widths = expectedResponsiveWidths([768, 1024]);
  assert.equal(widths[0], 320);
  assert.equal(widths.at(-1), 2560);
  for (const width of [320, 384, 768, 1024, 2560]) assert.ok(widths.includes(width));
  for (const width of [767, 769, 1023, 1025]) assert.ok(widths.includes(width));
  assert.equal(new Set(widths).size, widths.length);
});

test("capture plan covers every route at all anchors and breakpoint boundaries", () => {
  const plan = buildCapturePlan(sample);
  const routeCaptures = plan.targets.filter((target) => target.stateId === "default");
  assert.equal(routeCaptures.length, DEFAULT_VIEWPORTS.length + 6);
  assert.ok(routeCaptures.some((target) => target.viewportId === "width-767" && target.width === 767));
  assert.ok(routeCaptures.some((target) => target.viewportId === "width-1025" && target.width === 1025));
  assert.deepEqual(plan.responsiveWidths, expectedResponsiveWidths([768, 1024]));
});

test("interactive states capture at their declared touch viewports only", () => {
  const plan = buildCapturePlan(sample);
  const stateTargets = plan.targets.filter((target) => target.stateId === "nav-open");
  assert.deepEqual(stateTargets.map(({ viewportId }) => viewportId), ["tablet-portrait", "mobile-portrait"]);
});

test("capture plan rejects routes without a default state", () => {
  assert.throws(
    () => buildCapturePlan({ ...sample, states: sample.states.slice(1) }),
    /route home has no default state/i,
  );
});

test("capture plan rejects invalid breakpoint widths", () => {
  assert.throws(() => buildCapturePlan({ ...sample, breakpoints: [0, 768] }), /breakpoint/i);
});

test("capture plan requires a selector for every interaction action", () => {
  const invalid = {
    ...sample,
    states: [{ id: "default", routeId: "home", actions: [{ type: "waitFor", state: "visible" }] }],
  };
  assert.throws(() => buildCapturePlan(invalid), /needs a selector/i);
});

test("capture plan rejects UX flows that reference routes outside the manifest", () => {
  assert.throws(
    () => buildCapturePlan({ ...sample, flows: [{ id: "checkout", routeIds: ["missing"] }] }),
    /known routeIds/i,
  );
});

test("CLI plan-only reports required anchors and breakpoint-edge captures without a browser", () => {
  const tempRoot = mkdtempSync(path.join(tmpdir(), "codex-vq-plan-"));
  const tempResolved = path.resolve(tempRoot);
  const tempBase = path.resolve(tmpdir()) + path.sep;
  assert.ok(tempResolved.startsWith(tempBase), "temporary fixture path stays inside the OS temp directory");
  try {
    const manifestPath = path.join(tempRoot, "capture-plan.json");
    writeFileSync(manifestPath, JSON.stringify({
      baseUrl: "http://127.0.0.1:3000",
      routes: [{ id: "home", path: "/" }],
      breakpoints: [768],
      states: [{ id: "default", routeId: "home", actions: [] }],
    }));
    const runner = fileURLToPath(new URL("../codex-visual-quality-gate/scripts/capture_responsive_matrix.mjs", import.meta.url));
    const result = spawnSync(process.execPath, [runner, "--project-root", tempRoot, "--manifest", "capture-plan.json", "--plan-only"], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
    const output = JSON.parse(result.stdout);
    assert.equal(output.status, "planned");
    assert.ok(output.targets.some((target) => target.key === "home|default|width-767"));
    assert.ok(output.targets.some((target) => target.key === "home|default|desktop-wide"));
  } finally {
    rmSync(tempRoot, { recursive: true, force: true });
  }
});
