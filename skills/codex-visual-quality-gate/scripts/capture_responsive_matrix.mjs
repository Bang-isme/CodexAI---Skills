#!/usr/bin/env node
/** Capture responsive routes as overlapped viewport PNGs plus a stitched overview. */
import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import { deflateSync, inflateSync } from "node:zlib";
import { buildCapturePlan, RESPONSIVE_RANGE } from "./responsive_capture_core.mjs";

const MAX_STITCH_BYTES = 320 * 1024 * 1024;

function usage() {
  return `Usage:
  node capture_responsive_matrix.mjs --project-root <path> --manifest <capture-plan.json> [options]

Options:
  --out-dir <relative-path>  Evidence output; defaults to a timestamped .codex/design/reviews folder.
  --wait <ms>                Wait after each scroll stop. Default: 1000.
  --warm-wait <ms>           Wait during the lazy-content warmup scroll. Default: 250.
  --plan-only                Print expected widths and capture targets without launching a browser or writing files.
  --format <json|text>       Output format. Default: json.
  --help                     Show this help.

The script never installs browser or image packages. A Playwright installation and Chromium browser are required to capture.`;
}

function parseArgs(argv) {
  const args = { projectRoot: "", manifest: "", outDir: "", wait: 1000, warmWait: 250, planOnly: false, format: "json" };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--project-root") args.projectRoot = argv[++i] || "";
    else if (arg === "--manifest") args.manifest = argv[++i] || "";
    else if (arg === "--out-dir") args.outDir = argv[++i] || "";
    else if (arg === "--wait") args.wait = Number(argv[++i] || args.wait);
    else if (arg === "--warm-wait") args.warmWait = Number(argv[++i] || args.warmWait);
    else if (arg === "--plan-only") args.planOnly = true;
    else if (arg === "--format") args.format = argv[++i] || "json";
    else if (arg === "--help" || arg === "-h") args.help = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  if (!new Set(["json", "text"]).has(args.format)) throw new Error("--format must be json or text");
  if (!Number.isInteger(args.wait) || args.wait < 0 || !Number.isInteger(args.warmWait) || args.warmWait < 0) {
    throw new Error("wait values must be non-negative integers");
  }
  return args;
}

function confined(root, relative) {
  const absoluteRoot = path.resolve(root);
  const target = path.resolve(absoluteRoot, relative);
  const rel = path.relative(absoluteRoot, target);
  if (rel === ".." || rel.startsWith(`..${path.sep}`) || path.isAbsolute(rel)) {
    throw new Error(`path escapes project root: ${relative}`);
  }
  return target;
}

function safePart(value) {
  return String(value).replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "").slice(0, 80) || "item";
}

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const typeBuffer = Buffer.from(type, "ascii");
  const header = Buffer.alloc(4);
  header.writeUInt32BE(data.length);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])));
  return Buffer.concat([header, typeBuffer, data, crc]);
}

function paeth(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
  return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
}

function decodeRgbaPng(buffer) {
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  if (!buffer.subarray(0, 8).equals(signature)) throw new Error("screenshot is not a PNG");
  let offset = 8, width = 0, height = 0, bitDepth = 0, colorType = 0;
  const data = [];
  while (offset + 12 <= buffer.length) {
    const length = buffer.readUInt32BE(offset);
    const type = buffer.toString("ascii", offset + 4, offset + 8);
    const chunk = buffer.subarray(offset + 8, offset + 8 + length);
    if (type === "IHDR") {
      width = chunk.readUInt32BE(0); height = chunk.readUInt32BE(4);
      bitDepth = chunk[8]; colorType = chunk[9];
    } else if (type === "IDAT") data.push(chunk);
    offset += length + 12;
    if (type === "IEND") break;
  }
  if (!width || !height || bitDepth !== 8 || colorType !== 6) {
    throw new Error("PNG stitching requires an 8-bit RGBA screenshot");
  }
  const bytesPerPixel = 4, rowBytes = width * bytesPerPixel;
  const packed = inflateSync(Buffer.concat(data));
  if (packed.length !== (rowBytes + 1) * height) throw new Error("PNG pixel payload dimensions are invalid");
  const pixels = Buffer.alloc(rowBytes * height);
  let packedOffset = 0;
  for (let y = 0; y < height; y++) {
    const filter = packed[packedOffset++], rowOffset = y * rowBytes;
    for (let x = 0; x < rowBytes; x++) {
      const raw = packed[packedOffset++];
      const left = x >= bytesPerPixel ? pixels[rowOffset + x - bytesPerPixel] : 0;
      const up = y > 0 ? pixels[rowOffset + x - rowBytes] : 0;
      const upperLeft = y > 0 && x >= bytesPerPixel ? pixels[rowOffset + x - rowBytes - bytesPerPixel] : 0;
      let predictor;
      if (filter === 0) predictor = 0;
      else if (filter === 1) predictor = left;
      else if (filter === 2) predictor = up;
      else if (filter === 3) predictor = Math.floor((left + up) / 2);
      else if (filter === 4) predictor = paeth(left, up, upperLeft);
      else throw new Error(`unsupported PNG filter: ${filter}`);
      pixels[rowOffset + x] = (raw + predictor) & 0xff;
    }
  }
  return { width, height, pixels };
}

function encodeRgbaPng(width, height, pixels) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  const rowBytes = width * 4;
  const scanlines = Buffer.alloc((rowBytes + 1) * height);
  for (let y = 0; y < height; y++) {
    const dest = y * (rowBytes + 1);
    scanlines[dest] = 0;
    pixels.copy(scanlines, dest + 1, y * rowBytes, (y + 1) * rowBytes);
  }
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  return Buffer.concat([
    signature,
    pngChunk("IHDR", ihdr),
    pngChunk("IDAT", deflateSync(scanlines)),
    pngChunk("IEND", Buffer.alloc(0)),
  ]);
}

export function stitchViewportSlices(slices, width, documentHeight) {
  const outputBytes = width * documentHeight * 4;
  if (outputBytes > MAX_STITCH_BYTES) throw new Error(`stitched image would exceed ${MAX_STITCH_BYTES} bytes`);
  const pixels = Buffer.alloc(outputBytes);
  let coveredEnd = 0;
  let previous = null;
  for (const slice of slices) {
    const decoded = decodeRgbaPng(slice.buffer);
    if (decoded.width !== width || decoded.height !== slice.sourceViewportHeight) throw new Error("viewport slice dimensions mismatch");
    if (slice.coveredStartY !== coveredEnd || slice.coveredEndY <= slice.coveredStartY) throw new Error("viewport slices have a coverage gap");
    if (slice.coveredStartY < slice.sourceScrollY || slice.coveredEndY > slice.sourceScrollY + decoded.height) {
      throw new Error("stitched crop extends outside its source viewport");
    }
    if (previous && slice.sourceScrollY >= previous.sourceScrollY + previous.sourceViewportHeight) {
      throw new Error("viewport source slices do not overlap");
    }
    for (let y = slice.coveredStartY; y < slice.coveredEndY; y++) {
      const sourceY = y - slice.sourceScrollY;
      const sourceStart = sourceY * width * 4;
      decoded.pixels.copy(pixels, y * width * 4, sourceStart, sourceStart + width * 4);
    }
    coveredEnd = slice.coveredEndY;
    previous = slice;
  }
  if (coveredEnd !== documentHeight) throw new Error(`viewport slices cover ${coveredEnd}px; expected ${documentHeight}px`);
  return encodeRgbaPng(width, documentHeight, pixels);
}

async function loadPlaywright(projectRoot) {
  const requireFromProject = createRequire(path.join(projectRoot, "package.json"));
  for (const name of ["playwright", "@playwright/test"]) {
    try {
      const loaded = requireFromProject(name);
      if (loaded?.chromium) return loaded;
    } catch { /* try the next supported package name */ }
  }
  return null;
}

async function settlePage(page, waitMs) {
  await page.evaluate(async () => {
    if (document.fonts?.ready) await Promise.race([document.fonts.ready, new Promise((resolve) => setTimeout(resolve, 5000))]);
    await Promise.all([...document.images].map((image) => image.decode?.().catch(() => undefined)));
  });
  const brokenImages = await page.evaluate(() => [...document.images]
    .filter((image) => image.complete && image.naturalWidth === 0 && image.currentSrc)
    .map((image) => image.currentSrc));
  if (brokenImages.length) throw new Error(`broken image asset(s): ${brokenImages.join(", ")}`);
  if (waitMs) await page.waitForTimeout(waitMs);
}

async function documentHeight(page) {
  return page.evaluate(() => Math.max(
    document.documentElement?.scrollHeight || 0,
    document.body?.scrollHeight || 0,
  ));
}

async function warmPage(page, viewportHeight, warmWait) {
  const step = Math.max(1, Math.floor(viewportHeight * 0.8));
  let y = 0, previousHeight = 0;
  for (let index = 0; index < 160; index++) {
    const height = await documentHeight(page);
    const maxY = Math.max(0, height - viewportHeight);
    if (y >= maxY && height === previousHeight) break;
    y = Math.min(y + step, maxY);
    await page.evaluate((scrollY) => window.scrollTo(0, scrollY), y);
    await page.waitForTimeout(warmWait);
    previousHeight = Math.max(height, await documentHeight(page));
    if (y >= Math.max(0, previousHeight - viewportHeight)) {
      if (previousHeight === height) break;
      y = Math.max(0, previousHeight - viewportHeight);
    }
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await settlePage(page, warmWait);
}

function listenForErrors(page) {
  const errors = [];
  page.on("pageerror", (error) => errors.push(String(error?.message || error)));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("response", (response) => {
    if (response.status() >= 400) errors.push(`HTTP ${response.status()}: ${response.url()}`);
  });
  page.on("requestfailed", (request) => errors.push(`request failed: ${request.url()} (${request.failure()?.errorText || "unknown"})`));
  return errors;
}

async function openRoute(browser, plan, route, viewport, timeoutMs = 30000) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: 1,
    isMobile: Boolean(viewport.mobile),
    hasTouch: Boolean(viewport.touch),
  });
  const page = await context.newPage();
  const errors = listenForErrors(page);
  const url = new URL(route.path, plan.baseUrl).toString();
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: timeoutMs });
    await settlePage(page, 300);
    await page.addStyleTag({ content: "html, body { scroll-behavior: auto !important; scroll-snap-type: none !important; }" });
    return { context, page, errors, url };
  } catch (error) {
    await context.close();
    throw error;
  }
}

async function applyActions(page, actions, waitMs) {
  for (const action of actions ?? []) {
    const locator = action.selector ? page.locator(action.selector) : null;
    if (action.type === "click") await locator.click({ timeout: 10000 });
    else if (action.type === "fill") await locator.fill(String(action.value ?? ""), { timeout: 10000 });
    else if (action.type === "press") await locator.press(String(action.key ?? "Enter"), { timeout: 10000 });
    else if (action.type === "check") await locator.check({ timeout: 10000 });
    else if (action.type === "uncheck") await locator.uncheck({ timeout: 10000 });
    else if (action.type === "select") await locator.selectOption(String(action.value ?? ""), { timeout: 10000 });
    else if (action.type === "waitFor") await page.locator(action.selector).waitFor({ state: action.state ?? "visible", timeout: 10000 });
    await page.waitForTimeout(waitMs);
  }
}

async function scanRoute(browser, plan, route, defaultState, waitMs) {
  const viewport = { width: RESPONSIVE_RANGE.maxWidth, height: RESPONSIVE_RANGE.scanHeight };
  const { context, page, errors, url } = await openRoute(browser, plan, route, viewport);
  const samples = [];
  try {
    await applyActions(page, defaultState.actions, waitMs);
    await warmPage(page, viewport.height, Math.min(waitMs, 250));
    for (const width of plan.responsiveWidths) {
      const priorErrorCount = errors.length;
      await page.setViewportSize({ width, height: RESPONSIVE_RANGE.scanHeight });
      await page.waitForTimeout(Math.min(waitMs, 200));
      await settlePage(page, 0);
      const metrics = await page.evaluate(() => {
        const root = document.documentElement;
        const clientWidth = root?.clientWidth || window.innerWidth;
        const scrollWidth = Math.max(root?.scrollWidth || 0, document.body?.scrollWidth || 0);
        const clippedControls = [...document.querySelectorAll('a[href],button,input,select,textarea,[role="button"],[tabindex]:not([tabindex="-1"])')]
          .filter((element) => {
            if (element.closest('[aria-hidden="true"]')) return false;
            const style = getComputedStyle(element);
            if (style.display === "none" || style.visibility === "hidden") return false;
            const rect = element.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0 && (rect.left < -1 || rect.right > clientWidth + 1);
          })
          .slice(0, 30)
          .map((element) => ({ tag: element.tagName.toLowerCase(), id: element.id || "", text: (element.innerText || element.getAttribute("aria-label") || "").trim().slice(0, 80) }));
        return {
          clientWidth,
          scrollWidth,
          contentHeight: Math.max(root?.scrollHeight || 0, document.body?.scrollHeight || 0),
          horizontalOverflow: scrollWidth > clientWidth + 1,
          clippedControls,
        };
      });
      samples.push({ width, ...metrics, consoleErrors: [...new Set(errors.slice(priorErrorCount))] });
    }
    return { routeId: route.id, stateId: "default", path: route.path, widths: samples, errors: [...new Set(errors)], url };
  } finally {
    await context.close();
  }
}

async function captureTarget(browser, plan, target, projectRoot, outRoot, waitMs, warmWait) {
  const route = plan.routes.find((entry) => entry.id === target.routeId);
  const state = plan.states.find((entry) => entry.routeId === target.routeId && entry.id === target.stateId);
  const viewport = {
    id: target.viewportId,
    width: target.width,
    height: target.height,
    deviceScaleFactor: 1,
    mobile: target.mobile,
    touch: target.touch,
  };
  const relativeDir = path.join(
    path.relative(projectRoot, outRoot),
    safePart(route.id), safePart(state.id), safePart(target.viewportId),
  );
  const captureDir = confined(projectRoot, relativeDir);
  await fs.mkdir(captureDir, { recursive: true });
  const { context, page, errors, url } = await openRoute(browser, plan, route, viewport);
  try {
    await warmPage(page, viewport.height, warmWait);
    await applyActions(page, state.actions, waitMs);
    await settlePage(page, waitMs);
    let height = await documentHeight(page);
    const overlap = Math.min(160, Math.max(64, Math.floor(viewport.height * 0.15)));
    let coveredEnd = 0, requestedY = 0, previousScrollY = null;
    const segments = [], decodedSlices = [];
    for (let index = 0; index < 200; index++) {
      await page.evaluate((scrollY) => window.scrollTo(0, scrollY), requestedY);
      await page.waitForTimeout(waitMs);
      await settlePage(page, 0);
      const actualScrollY = Math.round(await page.evaluate(() => window.scrollY));
      height = Math.max(height, await documentHeight(page));
      if (actualScrollY > coveredEnd) throw new Error(`scroll jumped over uncovered content at y=${coveredEnd}`);
      const endY = Math.min(height, actualScrollY + viewport.height);
      if (endY <= coveredEnd) {
        if (coveredEnd >= height) break;
        requestedY = Math.min(Math.max(actualScrollY + 1, coveredEnd - overlap), Math.max(0, height - viewport.height));
        if (requestedY <= actualScrollY && previousScrollY === actualScrollY) throw new Error("capture could not advance through the page");
        previousScrollY = actualScrollY;
        continue;
      }
      const segmentFile = path.join(captureDir, `slice-${String(segments.length + 1).padStart(3, "0")}.png`);
      const buffer = await page.screenshot({ path: segmentFile, type: "png", animations: "disabled" });
      const segment = {
        path: path.relative(projectRoot, segmentFile).split(path.sep).join("/"),
        sourceScrollY: actualScrollY,
        sourceViewportHeight: viewport.height,
        coveredStartY: coveredEnd,
        coveredEndY: endY,
        image: { width: viewport.width, height: viewport.height },
      };
      segments.push(segment);
      decodedSlices.push({ buffer, ...segment, sourceViewportHeight: viewport.height });
      coveredEnd = endY;
      previousScrollY = actualScrollY;
      height = Math.max(height, await documentHeight(page));
      if (coveredEnd >= height) break;
      requestedY = Math.max(0, coveredEnd - overlap);
    }
    if (coveredEnd !== height) throw new Error(`capture covered ${coveredEnd}px of ${height}px`);
    const stitchedFile = path.join(captureDir, "stitched.png");
    const stitched = stitchViewportSlices(decodedSlices, viewport.width, height);
    await fs.writeFile(stitchedFile, stitched);
    return {
      key: target.key,
      routeId: route.id,
      stateId: state.id,
      viewportId: target.viewportId,
      viewport: { width: viewport.width, height: viewport.height, deviceScaleFactor: 1 },
      url,
      status: "captured",
      documentHeight: height,
      stitchedPath: path.relative(projectRoot, stitchedFile).split(path.sep).join("/"),
      stitchedImage: { width: viewport.width, height },
      segments,
      errors: [...new Set(errors)],
    };
  } finally {
    await context.close();
  }
}

function nowId() {
  return new Date().toISOString().replaceAll(":", "-").replaceAll(".", "-");
}

async function writeReport(file, report) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, `${JSON.stringify(report, null, 2)}\n`, "utf8");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }
  if (!args.projectRoot || !args.manifest) throw new Error("--project-root and --manifest are required");
  const projectRoot = path.resolve(args.projectRoot);
  const inputFile = confined(projectRoot, args.manifest);
  const input = JSON.parse(await fs.readFile(inputFile, "utf8"));
  const plan = buildCapturePlan(input);
  if (args.planOnly) {
    const result = {
      status: "planned",
      responsiveScan: { ...RESPONSIVE_RANGE, widths: plan.responsiveWidths, routeIds: plan.routes.map((route) => route.id) },
      flows: plan.flows,
      breakpoints: plan.breakpoints,
      viewports: plan.viewports,
      targets: plan.targets,
    };
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  const defaultOut = path.join(".codex", "design", "reviews", "responsive", nowId());
  const outRoot = confined(projectRoot, args.outDir || defaultOut);
  await fs.mkdir(outRoot, { recursive: true });
  const reportFile = path.join(outRoot, "capture-manifest.json");
  const degradedBase = {
    schemaVersion: 1,
    status: "DEGRADED",
    reason: "",
    baseUrl: plan.baseUrl,
    routes: plan.routes,
    states: plan.states,
    flows: plan.flows,
    breakpoints: plan.breakpoints,
    breakpointSources: input.breakpointSources ?? [],
    provenance: {
      ...(input.provenance && typeof input.provenance === "object" ? input.provenance : {}),
      captureRunner: "codex-visual-quality-gate/scripts/capture_responsive_matrix.mjs",
      capturedAt: new Date().toISOString(),
    },
    responsiveScan: { ...RESPONSIVE_RANGE, routes: [] },
    captures: [],
    visualReview: { status: "pending", checkedCaptureKeys: [], findings: [] },
    functionalReview: { status: "pending", checkedFlowIds: [], checkedRouteStateKeys: [], mainFlowStatus: "pending", accessibilityStatus: "pending", findings: [] },
    errors: [],
  };
  const playwright = await loadPlaywright(projectRoot);
  if (!playwright?.chromium) {
    degradedBase.reason = "Playwright is not installed in the project; no browser screenshots were captured";
    degradedBase.runtime = { playwright: "unavailable", browser: "unavailable" };
    await writeReport(reportFile, degradedBase);
    console.log(JSON.stringify({ ...degradedBase, reportPath: path.relative(projectRoot, reportFile).split(path.sep).join("/") }, null, 2));
    process.exitCode = 2;
    return;
  }

  let browser;
  try {
    browser = await playwright.chromium.launch({ headless: true });
  } catch (error) {
    degradedBase.reason = `Chromium could not launch: ${error?.message || error}`;
    degradedBase.runtime = { playwright: "available", browser: "unavailable" };
    await writeReport(reportFile, degradedBase);
    console.log(JSON.stringify({ ...degradedBase, reportPath: path.relative(projectRoot, reportFile).split(path.sep).join("/") }, null, 2));
    process.exitCode = 2;
    return;
  }
  const browserVersion = browser.version();

  const responsiveRoutes = [], captures = [], errors = [];
  for (const route of plan.routes) {
    const defaultState = plan.states.find((state) => state.routeId === route.id && state.id === "default");
    let scanned;
    try {
      scanned = await scanRoute(browser, plan, route, defaultState, args.wait);
      responsiveRoutes.push(scanned);
      for (const sample of scanned.widths) {
        if (sample.horizontalOverflow || sample.consoleErrors.length || sample.clippedControls?.length) {
          const viewportId = `width-${sample.width}`;
          const key = `${route.id}|default|${viewportId}`;
          if (!plan.targets.some((target) => target.key === key)) {
            plan.targets.push({
              key, routeId: route.id, path: route.path, stateId: "default", viewportId,
              width: sample.width, height: RESPONSIVE_RANGE.scanHeight, deviceScaleFactor: 1, mobile: false, touch: false,
              actions: defaultState.actions ?? [],
            });
          }
        }
        errors.push(...sample.consoleErrors.map((message) => `${route.id}@${sample.width}px: ${message}`));
      }
      errors.push(...(scanned.errors ?? []).map((message) => `${route.id}: ${message}`));
    } catch (error) {
      const message = String(error?.stack || error);
      errors.push(`${route.id} responsive scan: ${message}`);
      responsiveRoutes.push({ routeId: route.id, stateId: "default", path: route.path, widths: [], errors: [message] });
    }
  }
  for (const target of plan.targets) {
    try {
      const capture = await captureTarget(browser, plan, target, projectRoot, outRoot, args.wait, args.warmWait);
      captures.push(capture);
      errors.push(...capture.errors.map((message) => `${capture.key}: ${message}`));
    } catch (error) {
      const message = String(error?.stack || error);
      captures.push({
        key: target.key,
        routeId: target.routeId,
        stateId: target.stateId,
        viewportId: target.viewportId,
        viewport: { width: target.width, height: target.height, deviceScaleFactor: 1 },
        status: "failed",
        error: message,
        segments: [],
      });
      errors.push(`${target.key}: ${message}`);
    }
  }
  await browser.close();

  const report = {
    schemaVersion: 1,
    status: errors.length ? "fail" : "captured",
    baseUrl: plan.baseUrl,
    routes: plan.routes,
    states: plan.states,
    flows: plan.flows,
    breakpoints: plan.breakpoints,
    breakpointSources: input.breakpointSources ?? [],
    provenance: {
      ...(input.provenance && typeof input.provenance === "object" ? input.provenance : {}),
      captureRunner: "codex-visual-quality-gate/scripts/capture_responsive_matrix.mjs",
      capturedAt: new Date().toISOString(),
      browser: browserVersion,
    },
    responsiveScan: { ...RESPONSIVE_RANGE, routes: responsiveRoutes },
    captures,
    visualReview: { status: "pending", checkedCaptureKeys: [], findings: [] },
    functionalReview: { status: "pending", checkedFlowIds: [], checkedRouteStateKeys: [], mainFlowStatus: "pending", accessibilityStatus: "pending", findings: [] },
    errors,
    notes: [
      "Viewport dimensions are CSS pixels at deviceScaleFactor 1; these are browser emulations, not physical-device certification.",
      "Inspect every stitched overview together with its original viewport slices; fixed or sticky UI can repeat in the stitched overview.",
    ],
  };
  await writeReport(reportFile, report);
  console.log(JSON.stringify({ ...report, reportPath: path.relative(projectRoot, reportFile).split(path.sep).join("/") }, null, 2));
  if (report.status !== "captured") process.exitCode = 1;
}

const directRun = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (directRun) main().catch((error) => {
  console.error(JSON.stringify({ status: "error", message: String(error?.stack || error) }, null, 2));
  process.exitCode = 1;
});
