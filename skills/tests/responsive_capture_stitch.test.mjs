import assert from "node:assert/strict";
import test from "node:test";
import { deflateSync, inflateSync } from "node:zlib";
import { stitchViewportSlices } from "../codex-visual-quality-gate/scripts/capture_responsive_matrix.mjs";

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const kind = Buffer.from(type, "ascii");
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const checksum = Buffer.alloc(4);
  checksum.writeUInt32BE(crc32(Buffer.concat([kind, data])));
  return Buffer.concat([length, kind, data, checksum]);
}

function pngFromRows(rows) {
  const width = rows[0].length / 4;
  const height = rows.length;
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  const scanlines = Buffer.concat(rows.map((row) => Buffer.concat([Buffer.from([0]), row])));
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(scanlines)),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

function readPngRows(buffer) {
  let offset = 8, width = 0, height = 0;
  const idat = [];
  while (offset + 12 <= buffer.length) {
    const length = buffer.readUInt32BE(offset);
    const type = buffer.toString("ascii", offset + 4, offset + 8);
    const data = buffer.subarray(offset + 8, offset + 8 + length);
    if (type === "IHDR") {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
    }
    if (type === "IDAT") idat.push(data);
    offset += length + 12;
    if (type === "IEND") break;
  }
  const packed = inflateSync(Buffer.concat(idat));
  const stride = 1 + width * 4;
  assert.ok(Array.from({ length: height }, (_, row) => packed[row * stride] === 0).every(Boolean));
  return Array.from({ length: height }, (_, row) => [...packed.subarray(row * stride + 1, (row + 1) * stride)]);
}

const rgbaRow = (red) => Buffer.from([red, 0, 0, 255, red, 0, 0, 255]);

test("stitch retains every document row with overlapping source viewports", () => {
  const first = pngFromRows([10, 20, 30, 40].map(rgbaRow));
  const second = pngFromRows([30, 40, 50, 60].map(rgbaRow));
  const stitched = stitchViewportSlices([
    { buffer: first, sourceScrollY: 0, sourceViewportHeight: 4, coveredStartY: 0, coveredEndY: 3 },
    { buffer: second, sourceScrollY: 2, sourceViewportHeight: 4, coveredStartY: 3, coveredEndY: 6 },
  ], 2, 6);

  assert.deepEqual(readPngRows(stitched).map((row) => row[0]), [10, 20, 30, 40, 50, 60]);
});

test("stitch rejects a gap rather than returning an incomplete long page", () => {
  const source = pngFromRows([10, 20, 30, 40].map(rgbaRow));
  assert.throws(
    () => stitchViewportSlices([
      { buffer: source, sourceScrollY: 0, sourceViewportHeight: 4, coveredStartY: 0, coveredEndY: 2 },
      { buffer: source, sourceScrollY: 0, sourceViewportHeight: 4, coveredStartY: 3, coveredEndY: 4 },
    ], 2, 4),
    /coverage gap/i,
  );
});
