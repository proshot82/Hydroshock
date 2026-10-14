// Читалка документов: носитель 1400×980 (assets/gfx/docs) и текст поверх, по полям
// design/docs/fields.json. Вёрстка — та же, что у пробы приёмки носителей
// (tools/assets/doc_preview.py): один кегль на весь документ, наибольший, при котором текст
// влезает; первая строка — своим шрифтом (заголовок), пустая строка — полуинтервал,
// [оттиск] / [печать отеля] / [отпечатокъ пальца] — картинка оттиска справа.

import { ctx, W, H } from "./view.js";
import { image, loadImage } from "./assets.js";

const MARKS = { "[оттиск]": "docs/stamp_kuh", "[печать отеля]": "docs/stamp_hotel", "[отпечатокъ пальца]": "docs/mark_thumb" };
const DX = (W - 1400) / 2;
const DY = 40;

let cur = null;      // {doc, data, layout}
let doneCb = null;

function font(f, size) {
  return `${f[1]} ${size}px "${f[0]}"`;
}

function wrap(line, f, size, width) {
  ctx.font = font(f, size);
  const rows = [];
  let row = "";
  for (const w of line.split(" ")) {
    const t = (row + " " + w).trim();
    if (ctx.measureText(t).width <= width || !row) row = t;
    else { rows.push(row); row = w; }
  }
  rows.push(row);
  return rows;
}

function layout(lines, d, width, size) {
  const rows = [];
  lines.forEach((ln, i) => {
    const head = i === 0 && d.first;
    const f = head ? d.first : d.font;
    const sz = head ? Math.round(size * 1.08) : size;
    const s = ln.trim();
    if (MARKS[s]) { rows.push({ kind: "mark", t: s, h: size * 2.2 }); return; }
    if (!s) { rows.push({ kind: "gap", h: size * 0.5 }); return; }
    for (const r of wrap(ln, f, sz, width)) rows.push({ kind: "text", t: r, f, sz, h: size * 1.28 });
  });
  return { rows, total: rows.reduce((a, r) => a + r.h, 0) };
}

function build(d) {
  const fld = d.field || {};
  const lines = d.lines;
  let parts;
  if (fld.boxes) {
    parts = fld.boxes.map((b, i) => ({ box: b, lines: lines[i] !== undefined ? [lines[i]] : [] }));
  } else if (fld.gap) {
    const cut = lines.findIndex((l) => l.trim() === "[вырезано]");
    const top = cut >= 0 ? lines.slice(0, cut) : lines;
    const bottom = cut >= 0 ? lines.slice(cut + 1) : [];
    const [x0, y0, x1, y1] = fld.box;
    parts = [{ box: [x0, y0, x1, fld.gap[0]], lines: top }, { box: [x0, fld.gap[1], x1, y1], lines: bottom }];
  } else {
    parts = [{ box: fld.box || [100, 100, 1300, 880], lines }];
  }
  let size = fld.max || 84;
  while (size > 10) {
    if (parts.every((p) => !p.lines.length || layout(p.lines, d, p.box[2] - p.box[0], size).total <= p.box[3] - p.box[1])) break;
    size -= 2;
  }
  return parts.map((p) => ({ ...p, ...layout(p.lines, d, p.box[2] - p.box[0], size) }));
}

export function open(docId, data) {
  return new Promise((resolve) => {
    const d = data.docs[docId];
    if (!d) { resolve(); return; }
    loadImage(d.carrier).catch(() => {});
    Object.values(MARKS).forEach((m) => loadImage(m).catch(() => {}));
    cur = { doc: docId, d, parts: null };
    doneCb = resolve;
  });
}

export function active() {
  return cur !== null;
}

export function currentDoc() {
  return cur ? cur.doc : null;
}

export function close() {
  if (!cur) return false;
  cur = null;
  const cb = doneCb;
  doneCb = null;
  if (cb) cb();
  return true;
}

export function draw() {
  if (!cur) return;
  ctx.fillStyle = "rgba(0, 0, 0, 0.72)";
  ctx.fillRect(0, 0, W, H);
  const bg = image(cur.d.carrier);
  if (!bg) return;
  if (!cur.parts) cur.parts = build(cur.d);   // шрифты уже загружены — вёрстку считаем один раз
  ctx.drawImage(bg, DX, DY, 1400, 980);
  const fld = cur.d.field || {};
  const ink = fld.ink ? `rgb(${fld.ink.join(",")})` : "rgb(40, 34, 28)";
  ctx.fillStyle = ink;
  ctx.textBaseline = "top";
  for (const p of cur.parts) {
    const [bx0, by0, bx1, by1] = p.box;
    let y = by0 + (by1 - by0 - p.total) / 2;
    for (const r of p.rows) {
      if (r.kind === "text") {
        ctx.font = font(r.f, r.sz);
        const w = ctx.measureText(r.t).width;
        const x = bx0 + (fld.center ? (bx1 - bx0 - w) / 2 : 0);
        ctx.textAlign = "left";
        ctx.fillText(r.t, DX + x, DY + y);
      } else if (r.kind === "mark") {
        const m = image(MARKS[r.t]);
        if (m) {
          const s = r.h / m.naturalHeight;
          ctx.drawImage(m, DX + bx1 - m.naturalWidth * s - 10, DY + y, m.naturalWidth * s, r.h);
        }
      }
      y += r.h;
    }
  }
  ctx.font = '400 24px "PT Sans"';
  ctx.fillStyle = "#a6a194";
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.fillText("Щелчок — закрыть", W / 2, H - 12);
}
