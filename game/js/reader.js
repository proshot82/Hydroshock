// Читалка документов: носитель 1400×980 (assets/gfx/docs) и текст поверх, по полям
// design/docs/fields.json. Вёрстка — та же, что у пробы приёмки носителей
// (tools/assets/doc_preview.py): один кегль на весь документ, наибольший, при котором текст
// влезает; первая строка — своим шрифтом (заголовок), пустая строка — полуинтервал,
// [оттиск] / [печать отеля] / [отпечатокъ пальца] — картинка оттиска справа.

import { ctx, W, H, uiScale, toWorld } from "./view.js";
import { image, loadImage } from "./assets.js";
import * as plans from "./plans.js";

const MARKS = { "[оттиск]": "docs/stamp_kuh", "[печать отеля]": "docs/stamp_hotel", "[отпечатокъ пальца]": "docs/mark_thumb" };
const DX = (W - 1400) / 2;
const DY = 40;

let cur = null;      // {doc, data, layout}
let doneCb = null;
let touchMode = false;
let hints = {};      // подписи «закрыть» для мыши и пальца (data/ui.json)

// Увеличение пальцем (на телефоне лист мелкий): два касания — крупнее в этой точке / обратно,
// щипок — плавно, палец по увеличенному листу — сдвиг. Мышь: щелчок закрывает, как раньше.
// Мир → экран листа: q' = q·k + o. Лист не уезжает: его края не заходят внутрь своего места.
const ZMAX = 3;
const ZDOUBLE = 1.6;
const TAP2 = 300;    // мс: второе касание
let zoom = { k: 1, ox: 0, oy: 0 };
let pendingTap = null;   // {p, timer}
const fingers = new Map();   // pointerId → точка мира
let pinch = null;            // {d0, k0, ox0, oy0, c0}
let pan = null;              // {p0, ox0, oy0}

export function setHints(ui) {
  hints = { click: ui.close_click, zoom: ui.close_touch_zoom, zoomed: ui.zoomed_touch };
}
export function setTouch(v) {
  touchMode = !!v;
}

function clampZoom() {
  const k = zoom.k;
  const lo = (a, len) => a + len - (a + len) * k;
  const hi = (a) => a - a * k;
  zoom.ox = Math.max(lo(DX, 1400), Math.min(hi(DX), zoom.ox));
  zoom.oy = Math.max(lo(DY, 980), Math.min(hi(DY), zoom.oy));
}

function zoomAt(f, px, py) {
  const k = Math.max(1, Math.min(ZMAX, zoom.k * f));
  const g = k / zoom.k;
  zoom = { k, ox: (zoom.ox - px) * g + px, oy: (zoom.oy - py) * g + py };
  if (zoom.k < 1.04) zoom = { k: 1, ox: 0, oy: 0 };
  clampZoom();
}

function resetZoom() {
  zoom = { k: 1, ox: 0, oy: 0 };
  if (pendingTap) clearTimeout(pendingTap.timer);
  pendingTap = null;
  fingers.clear();
  pinch = null;
  pan = null;
}

// Касание пальцем (game.js): одно — ждём второе; два подряд — увеличить/вернуть; одно без
// второго — закрыть (или вернуть масштаб, если лист увеличен).
export function tap(p) {
  if (!cur || !p) return;
  if (pendingTap && Math.hypot(p.x - pendingTap.p.x, p.y - pendingTap.p.y) < 120) {
    clearTimeout(pendingTap.timer);
    pendingTap = null;
    if (zoom.k > 1) zoom = { k: 1, ox: 0, oy: 0 };
    else zoomAt(ZDOUBLE, p.x, p.y);
    return;
  }
  if (pendingTap) clearTimeout(pendingTap.timer);
  pendingTap = {
    p,
    timer: setTimeout(() => {
      pendingTap = null;
      if (zoom.k > 1) zoom = { k: 1, ox: 0, oy: 0 };
      else close();
    }, TAP2),
  };
}

const worldOf = (e) => toWorld(e.clientX, e.clientY, true);

export function touchDown(e, n) {
  fingers.set(e.pointerId, worldOf(e));
  if (n === 2) {
    const [a, b] = [...fingers.values()];
    pinch = { d0: Math.hypot(a.x - b.x, a.y - b.y) || 1, k0: zoom.k, ox0: zoom.ox, oy0: zoom.oy, c0: { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 } };
    pan = null;
    if (pendingTap) { clearTimeout(pendingTap.timer); pendingTap = null; }
  } else if (n === 1 && zoom.k > 1) {
    pan = { p0: worldOf(e), ox0: zoom.ox, oy0: zoom.oy };
  }
}

export function touchMove(e) {
  if (!fingers.has(e.pointerId)) return;
  fingers.set(e.pointerId, worldOf(e));
  if (pinch && fingers.size >= 2) {
    const [a, b] = [...fingers.values()];
    const d = Math.hypot(a.x - b.x, a.y - b.y);
    const c = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    zoom = { k: pinch.k0, ox: pinch.ox0 + (c.x - pinch.c0.x), oy: pinch.oy0 + (c.y - pinch.c0.y) };
    zoomAt(d / pinch.d0, c.x, c.y);
  } else if (pan) {
    const p = worldOf(e);
    zoom.ox = pan.ox0 + (p.x - pan.p0.x);
    zoom.oy = pan.oy0 + (p.y - pan.p0.y);
    clampZoom();
  }
}

export function touchUp(e, n) {
  fingers.delete(e.pointerId);
  if (n < 2) pinch = null;
  if (n === 0) pan = null;
}

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

// Разворот журнала (носитель с корешком, поле `spine`): строки « — » — таблица; первые колонки на левой
// странице, остальные — на правой, через корешок ничего не идёт (разбор автора 16.10.2026).
function buildSpread(d) {
  const fld = d.field;
  const [x0, y0, x1, y1] = fld.box;
  const gut = 36;
  const pages = [[x0, fld.spine - gut], [fld.spine + gut, x1]];
  const head = [];
  const rows = [];
  for (const ln of d.lines) {
    const t = ln.trim();
    if (!t) continue;
    if (t.includes(" — ")) rows.push(t.split(" — ").map((c) => c.trim()));
    else if (!rows.length) head.push(t);
    else rows.push([t]);
  }
  const ncol = Math.max(...rows.map((r) => r.length), 1);
  const left = Math.ceil(ncol / 2);
  const fit = (size) => {
    // ширина колонок пропорциональна самой длинной клетке, страницы делятся поровну между своими
    const cols = [];
    for (let c = 0; c < ncol; c++) {
      const pg = c < left ? 0 : 1;
      ctx.font = font(d.font, size);
      const wmax = Math.max(...rows.map((r, i) => (MARKS[r[c]] ? size * 2.2 : ctx.measureText(r[c] || "").width) * (i === 0 ? 1.08 : 1)));
      cols.push({ pg, need: wmax + size * 0.8 });
    }
    for (const pg of [0, 1]) {
      const mine = cols.filter((c) => c.pg === pg);
      const have = pages[pg][1] - pages[pg][0];
      const need = mine.reduce((a, c) => a + c.need, 0);
      if (need > have) return null;
      let x = pages[pg][0];
      for (const c of mine) { c.x = x; c.w = (c.need / need) * have; x += c.w; }
    }
    const rowH = size * 2.1;
    const headH = head.length * size * 1.5;
    if (headH + rows.length * rowH > y1 - y0) return null;
    return { size, cols, rowH, headH };
  };
  let size = fld.max || 60;
  let L = null;
  while (size > 10 && !(L = fit(size))) size -= 2;
  return { spread: true, head, rows, ...(L || fit(10)), y0 };
}

function drawSpread(sp, d, ink) {
  ctx.textBaseline = "middle";
  ctx.textAlign = "left";
  let y = DY + sp.y0;
  sp.head.forEach((t, i) => {
    ctx.font = font(i === 0 && d.first ? d.first : d.font, Math.round(sp.size * (i === 0 ? 1.15 : 1)));
    ctx.fillStyle = ink;
    ctx.fillText(t, DX + sp.cols[0].x, y + sp.size * 0.7);
    y += sp.size * 1.5;
  });
  sp.rows.forEach((r, i) => {
    r.forEach((cell, c) => {
      const col = sp.cols[c];
      if (!col) return;
      if (MARKS[cell]) {
        const m = image(MARKS[cell]);
        if (m) {
          const h = sp.rowH * 0.9;
          const w = (m.naturalWidth / m.naturalHeight) * h;
          ctx.drawImage(m, DX + col.x, y + (sp.rowH - h) / 2, w, h);
        }
        return;
      }
      ctx.font = font(i === 0 && d.first ? d.first : d.font, sp.size);
      ctx.fillStyle = ink;
      ctx.fillText(cell, DX + col.x, y + sp.rowH / 2);
    });
    y += sp.rowH;
  });
}

export function open(docId, data) {
  return new Promise((resolve) => {
    const d = data.docs[docId];
    if (!d) { resolve(); return; }
    loadImage(d.carrier).catch(() => {});
    if (d.plan) loadImage(d.plan.img).catch(() => {});
    Object.values(MARKS).forEach((m) => loadImage(m).catch(() => {}));
    cur = { doc: docId, d, parts: null, spread: null };
    resetZoom();
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
  resetZoom();
  const cb = doneCb;
  doneCb = null;
  if (cb) cb();
  return true;
}

// План на подсвеченном стекле (DOC.map_*): плёнка с подписями по меткам, заголовок — первая строка.
function drawPlan(bg) {
  const d = cur.d;
  ctx.drawImage(bg, DX, DY, 1400, 980);
  const c = plans.render([d.plan]);
  if (c) ctx.drawImage(c, DX, DY);
  const title = (d.lines.find((l) => l.trim()) || "").trim();
  ctx.font = `700 34px "${d.plan.font[0]}"`;
  ctx.fillStyle = d.plan.ink;
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillText(title, DX + 40, DY + 30);
  hintClose();
}

function hintClose() {
  ctx.restore();   // подпись — вне увеличения (draw() начал его)
  const u = uiScale();
  ctx.font = `400 ${Math.round(24 * u)}px "PT Sans"`;
  ctx.fillStyle = "#a6a194";
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  const t = !touchMode ? hints.click || "Щелчок — закрыть"
    : zoom.k > 1 ? hints.zoomed || "Коснитесь — уменьшить" : hints.zoom || "Коснитесь — закрыть · два касания — крупнее";
  // подпись на подложке: при увеличении лист заходит под неё
  const w = ctx.measureText(t).width + 30 * u;
  ctx.fillStyle = "rgba(0, 0, 0, 0.72)";
  ctx.fillRect((W - w) / 2, H - 40 * u, w, 40 * u);
  ctx.fillStyle = "#a6a194";
  ctx.fillText(t, W / 2, H - 12 * u);
}

export function draw() {
  if (!cur) return;
  ctx.fillStyle = "rgba(0, 0, 0, 0.72)";
  ctx.fillRect(0, 0, W, H);
  const bg = image(cur.d.carrier);
  if (!bg) return;
  ctx.save();   // увеличение листа; снимает hintClose()
  ctx.transform(zoom.k, 0, 0, zoom.k, zoom.ox, zoom.oy);
  if (cur.d.plan) { drawPlan(bg); return; }
  if (cur.d.field && cur.d.field.spine) {
    if (!cur.spread) cur.spread = buildSpread(cur.d);
    ctx.drawImage(bg, DX, DY, 1400, 980);
    const f = cur.d.field;
    drawSpread(cur.spread, cur.d, f.ink ? `rgb(${f.ink.join(",")})` : "rgb(40, 34, 28)");
    hintClose();
    return;
  }
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
  hintClose();
}
