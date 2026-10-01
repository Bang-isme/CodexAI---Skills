import assert from "node:assert/strict";
import test from "node:test";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const skillsRoot = path.resolve(testDir, "..");
const helper = path.join(skillsRoot, "codex-visual-quality-gate", "scripts", "capture_responsive_matrix.mjs");

async function playwrightAvailable() {
  for (const packageName of ["playwright", "@playwright/test"]) {
    try {
      const pw = await import(packageName);
      const browser = await pw.chromium.launch({ headless: true });
      await browser.close();
      return true;
    } catch { /* check next package or treat Chromium as unavailable */ }
  }
  return false;
}

const canCapture = await playwrightAvailable();
const browserSkipReason = canCapture ? false : "Playwright with Chromium is not available in this environment";

test("browser capture warms lazy content, stitches sticky-page slices, captures interaction state, and reports broken assets", {
  skip: browserSkipReason,
  timeout: 240_000,
}, async () => {
  const sections = Array.from({ length: 12 }, (_, index) => `
    <section class="panel" data-lazy="${index}">
      <h2>Section ${index + 1}</h2>
      <div class="lazy" aria-live="polite">Loading section…</div>
    </section>`).join("\n");
  const longPage = `<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      @font-face { font-family: MissingFixtureFont; src: url('/missing-font.woff2'); }
      body { margin: 0; font-family: MissingFixtureFont, sans-serif; }
      header { position: sticky; top: 0; z-index: 2; background: white; border-bottom: 1px solid #999; padding: 16px; }
      .panel { min-height: 420px; padding: 24px; border-bottom: 1px solid #aaa; }
      #menu { display: none; }
      #menu[data-open="true"] { display: block; }
    </style></head><body>
      <header><button id="menu-toggle" aria-expanded="false" aria-controls="menu">Menu</button><nav id="menu" data-open="false">Open navigation</nav></header>
      <main>${sections}</main>
      <script>
        document.querySelector('#menu-toggle').addEventListener('click', () => {
          const menu = document.querySelector('#menu');
          const open = menu.dataset.open !== 'true';
          menu.dataset.open = String(open);
          document.querySelector('#menu-toggle').setAttribute('aria-expanded', String(open));
        });
        const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.querySelector('.lazy').innerHTML = '<p>Lazy content hydrated for section ' + (Number(entry.target.dataset.lazy) + 1) + '</p>';
          observer.unobserve(entry.target);
        }), { rootMargin: '200px' });
        document.querySelectorAll('[data-lazy]').forEach((section) => observer.observe(section));
      </script>
    </body></html>`;
  const brokenPage = `<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>@font-face { font-family: Broken; src: url('/missing-font.woff2'); } body { font-family: Broken, sans-serif; }</style>
    </head><body><h1>Broken assets</h1><img src="/missing-image.png" alt="Broken fixture image"></body></html>`;

  const server = createServer((request, response) => {
    if (request.url === "/long") {
      response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
      response.end(longPage);
    } else if (request.url === "/broken") {
      response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
      response.end(brokenPage);
    } else {
      response.writeHead(404, { "content-type": "text/plain" });
      response.end("fixture asset missing");
    }
  });

  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  const tempRoot = mkdtempSync(path.join(testDir, ".responsive-e2e-"));
  const tempResolved = path.resolve(tempRoot);
  assert.ok(tempResolved.startsWith(`${path.resolve(testDir)}${path.sep}`), "fixture output stays inside its dedicated temp directory");
  try {
    const manifestPath = path.join(tempRoot, "capture-plan.json");
    writeFileSync(manifestPath, JSON.stringify({
      baseUrl: `http://127.0.0.1:${address.port}`,
      routes: [{ id: "long", path: "/long" }, { id: "broken", path: "/broken" }],
      breakpoints: [],
      states: [
        { id: "default", routeId: "long", actions: [] },
        { id: "menu-open", routeId: "long", viewportIds: ["mobile-portrait"], actions: [{ type: "click", selector: "#menu-toggle" }] },
        { id: "default", routeId: "broken", actions: [] },
      ],
      flows: [
        { id: "long-page-task", routeIds: ["long"], summary: "Scroll through a long page and open its menu." },
        { id: "broken-assets", routeIds: ["broken"], summary: "Report required asset load failures." },
      ],
      provenance: { appRevision: "browser-fixture", references: ["inline test fixture"] },
    }));

    const result = spawnSync(process.execPath, [
      helper,
      "--project-root", skillsRoot,
      "--manifest", path.relative(skillsRoot, manifestPath),
      "--out-dir", path.relative(skillsRoot, path.join(tempRoot, "output")),
      "--wait", "100",
      "--warm-wait", "50",
    ], { encoding: "utf8", timeout: 240_000, maxBuffer: 20 * 1024 * 1024 });
    assert.equal(result.status, 1, result.stderr || result.stdout.slice(-2000));
    const output = JSON.parse(result.stdout);
    assert.equal(output.status, "fail", "broken image/font evidence must fail the capture run");
    assert.ok(output.errors.some((error) => /broken image|HTTP 404/i.test(error)));

    const captureManifest = JSON.parse(readFileSync(path.join(tempRoot, "output", "capture-manifest.json"), "utf8"));
    const longCaptures = captureManifest.captures.filter((capture) => capture.routeId === "long" && capture.status === "captured");
    assert.equal(longCaptures.length, 8, "seven anchors plus the declared menu state are captured");
    const longDesktop = longCaptures.find((capture) => capture.key === "long|default|desktop-laptop");
    assert.ok(longDesktop.documentHeight > 3000, "lazy content was activated before measuring page height");
    assert.ok(longDesktop.segments.length > 1, "long page is captured as multiple viewport slices");
    assert.equal(longDesktop.segments.at(-1).coveredEndY, longDesktop.documentHeight, "last slice reaches the document end");
    assert.ok(longCaptures.some((capture) => capture.key === "long|menu-open|mobile-portrait"));
    assert.ok(captureManifest.captures.some((capture) => capture.routeId === "broken" && capture.status === "failed"));
  } finally {
    await new Promise((resolve) => server.close(resolve));
    rmSync(tempRoot, { recursive: true, force: true });
  }
});
