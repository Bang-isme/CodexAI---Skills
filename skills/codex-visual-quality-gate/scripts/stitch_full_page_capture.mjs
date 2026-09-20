#!/usr/bin/env node
/**
 * provenance: source=MengTo/Skills name=stitched-full-page-capture
 * url=https://github.com/MengTo/Skills
 * date=2026-09-20
 * license=unspecified-in-source
 *
 * Portable capture helper. Prefer Playwright fullPage when Node+Playwright exist.
 * If Playwright is missing, print DEGRADED JSON and exit 2. Does not install packages.
 */
import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";

function usage() {
  console.log(`Usage:
  node stitch_full_page_capture.mjs --url <http(s)://...> --out <file.png>
  node stitch_full_page_capture.mjs --manifest <manifest.json>

Options:
  --viewport <WxH>   Default 1440x1100
  --wait <ms>        Default 500
`);
}

function parseArgs(argv) {
  const args = { url: "", out: "", manifest: "", viewport: "1440x1100", wait: 500 };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") args.help = true;
    else if (arg === "--url") args.url = argv[++i] || "";
    else if (arg === "--out") args.out = argv[++i] || "";
    else if (arg === "--manifest") args.manifest = argv[++i] || "";
    else if (arg === "--viewport") args.viewport = argv[++i] || args.viewport;
    else if (arg === "--wait") args.wait = Number(argv[++i] || args.wait);
    else throw new Error(`Unknown argument: ${arg}`);
  }
  const match = String(args.viewport).match(/^(\d+)x(\d+)$/);
  if (!match) throw new Error(`Invalid --viewport: ${args.viewport}`);
  args.width = Number(match[1]);
  args.height = Number(match[2]);
  return args;
}

function degraded(reason) {
  return { status: "DEGRADED", reason };
}

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch {
    try {
      return await import("@playwright/test");
    } catch {
      return null;
    }
  }
}

async function captureUrl(args) {
  const pw = await loadPlaywright();
  if (!pw?.chromium) {
    return degraded("playwright unavailable; host must supply screenshots");
  }
  const browser = await pw.chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: args.width, height: args.height } });
    await page.goto(args.url, { waitUntil: "networkidle", timeout: 30000 });
    if (args.wait) await page.waitForTimeout(args.wait);
    const out = path.resolve(args.out || "full-page.png");
    await fs.mkdir(path.dirname(out), { recursive: true });
    await page.screenshot({ path: out, fullPage: true });
    return { status: "captured", path: out, engine: "playwright" };
  } finally {
    await browser.close();
  }
}

async function stitchManifest(args) {
  const ffmpeg = process.platform === "win32" ? "ffmpeg.exe" : "ffmpeg";
  const which = spawn(process.platform === "win32" ? "where" : "which", [ffmpeg.replace(".exe", "")]);
  const ok = await new Promise((resolve) => {
    which.on("close", (code) => resolve(code === 0));
  });
  if (!ok) {
    return degraded("ffmpeg unavailable for manifest stitch");
  }
  const raw = JSON.parse(await fs.readFile(args.manifest, "utf8"));
  const items = Array.isArray(raw) ? raw : raw.items || [];
  if (!items.length) return degraded("empty capture manifest");
  return {
    status: "skipped",
    reason: "manifest stitch requires host-supplied viewport frames; prefer --url with Playwright",
    items: items.length,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    process.exit(0);
  }
  let payload;
  if (args.url) payload = await captureUrl(args);
  else if (args.manifest) payload = await stitchManifest(args);
  else {
    usage();
    payload = degraded("missing --url or --manifest");
  }
  console.log(JSON.stringify(payload, null, 2));
  process.exit(payload.status === "captured" ? 0 : 2);
}

main().catch((error) => {
  console.log(JSON.stringify(degraded(String(error.message || error)), null, 2));
  process.exit(2);
});
