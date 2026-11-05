// Draws the Pool LNH icons (own design: two crossed hockey sticks + a puck; no league logos or marks).
// Usage: node tools/make-icons.js pool/static/app
// Writes icon-512.png, icon-192.png, apple-touch-icon.png (mint on graphite, opaque) and badge-96.png
// (white on transparent: Android's small notification icon only uses the transparency, an opaque image = white square).
// Everything stays inside a circle of radius 0.4 around the centre, so round / squircle masks never cut it.
const fs = require('fs'), zlib = require('zlib');

const CRC = new Int32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; return c; });
const crc = (b) => { let c = -1; for (const x of b) c = CRC[(c ^ x) & 255] ^ (c >>> 8); return (c ^ -1) >>> 0; };
function chunk(type, data) {
  const l = Buffer.alloc(4); l.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type), data]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td));
  return Buffer.concat([l, td, c]);
}
function png(N, px) {                       // px(x, y) -> [r, g, b, a] for one sample point in 0..1
  const raw = Buffer.alloc((N * 4 + 1) * N), S = 4;
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      let r = 0, g = 0, b = 0, a = 0;
      for (let i = 0; i < S; i++) for (let j = 0; j < S; j++) {     // 4x4 supersampling, premultiplied
        const c = px((x + (i + .5) / S) / N, (y + (j + .5) / S) / N);
        r += c[0] * c[3]; g += c[1] * c[3]; b += c[2] * c[3]; a += c[3];
      }
      const o = y * (N * 4 + 1) + 1 + x * 4;
      raw[o] = a ? Math.round(r / a) : 0; raw[o + 1] = a ? Math.round(g / a) : 0; raw[o + 2] = a ? Math.round(b / a) : 0;
      raw[o + 3] = Math.round(a / (S * S));
    }
  }
  const ih = Buffer.alloc(13); ih.writeUInt32BE(N, 0); ih.writeUInt32BE(N, 4); ih[8] = 8; ih[9] = 6;   // RGBA
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ih),
    chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}

// distance from point p to segment ab
function seg(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay, t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)));
  return Math.hypot(px - ax - t * dx, py - ay - t * dy);
}
const ell = (x, y, cx, cy, rx, ry) => ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1;

// a stick = shaft from the top of the handle down to the heel, then a blade pointing outward
const STICKS = [
  { shaft: [0.30, 0.20, 0.64, 0.62], blade: [0.64, 0.62, 0.77, 0.63] },   // top-left to bottom-right, blade to the right
  { shaft: [0.70, 0.20, 0.36, 0.62], blade: [0.36, 0.62, 0.23, 0.63] },   // top-right to bottom-left, blade to the left
];
const PUCK = { cx: 0.5, top: 0.71, h: 0.056, rx: 0.13, ry: 0.043 };

function onStick(s, x, y, w) {
  return seg(x, y, ...s.shaft) <= w || seg(x, y, ...s.blade) <= w * 1.15;
}
// what is at (x, y): 'stick', 'gap' (thin space that shows which stick is in front), 'puckTop', 'puckSide' or null
function shape(x, y, w, gap) {
  const P = PUCK;
  if (ell(x, y, P.cx, P.top, P.rx, P.ry)) return 'puckTop';
  if ((Math.abs(x - P.cx) <= P.rx && y >= P.top && y <= P.top + P.h) || ell(x, y, P.cx, P.top + P.h, P.rx, P.ry)) return 'puckSide';
  if (onStick(STICKS[1], x, y, w)) return 'stick';                     // the front stick
  if (seg(x, y, ...STICKS[1].shaft) <= w + gap) return 'gap';
  if (onStick(STICKS[0], x, y, w)) return 'stick';
  return null;
}

const BG = [10, 13, 18, 255], MINT = [43, 227, 166, 255], PTOP = [232, 238, 245, 255], PSIDE = [150, 162, 178, 255];
const color = (x, y) => ({ stick: MINT, puckTop: PTOP, puckSide: PSIDE }[shape(x, y, 0.036, 0.022)] || BG);
const badge = (x, y) => {           // thicker strokes so it still reads at 24 px in the status bar
  const s = shape(x, y, 0.05, 0.03);
  return s && s !== 'gap' ? [255, 255, 255, 255] : [0, 0, 0, 0];
};

const out = process.argv[2] || 'pool/static/app';
fs.writeFileSync(`${out}/icon-512.png`, png(512, color));
fs.writeFileSync(`${out}/icon-192.png`, png(192, color));
fs.writeFileSync(`${out}/apple-touch-icon.png`, png(180, color));
fs.writeFileSync(`${out}/badge-96.png`, png(96, badge));
if (process.argv[3]) {              // optional preview folder: small sizes + the badge on grey
  fs.writeFileSync(`${process.argv[3]}/preview-48.png`, png(48, color));
  fs.writeFileSync(`${process.argv[3]}/preview-badge-grey.png`, png(96, (x, y) => (badge(x, y)[3] ? [255, 255, 255, 255] : [90, 96, 104, 255])));
}
console.log('icons written to', out);
