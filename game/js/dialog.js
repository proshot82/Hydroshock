// Окно реплик — раскладка BJ2 (src/ui.lua, dlg_draw): портрет 268×280 слева внизу (портрет 512 в
// масштабе 0,5), справа панель текста с плашкой имени; текст печатается по 40 знаков в секунду,
// блип — раз в 3 знака. Титр (`cap`) — без портрета и плашки, по центру панели.
// Портрет Лапидуса — файл по пене (спека §5.1): сухой / `_foam` / `_cap`; `lap_clean` — как есть.

import { ctx } from "./view.js";
import { image, loadImage } from "./assets.js";
import * as audio from "./audio.js";

const C = {
  panel: "rgba(22, 24, 32, 0.94)", brass: "#b8945a", steel: "#8cb3db", text: "#ede8db", dim: "#a6a194",
  cap: "#d9d2bf",
};
const CPS = 40;
const BLIP = {
  lap: "blip_lap", anc: "blip_anc", iz: "blip_iz", kuh: "blip_kuh",
  pa: "blip_pa", paiz: "blip_pa", ans: "blip_pa", guest: "blip_guest", guestf: "blip_guest", waiter: "blip_guest",
};
const PORTRAIT_SPEAKERS = new Set(["lap", "iz", "kuh", "anc"]);

let speakers = {};       // id → плашка
let queue = [];
let onLine = null;       // (i) => …: реплика i появилась (звуки «@N» в сценах)
let cur = null;          // {s, e, t, portrait}
let shown = 0;
let t = 0;
let blipAcc = 0;
let doneCb = null;
let fast = false;
let touchHint = false;

export function init(speakerNames) {
  speakers = speakerNames;
}

export function setFast(v) {
  fast = !!v;
}

export function setTouch(v) {
  touchHint = !!v;
}

// Имя файла портрета для реплики; null — без портрета.
export function portraitName(line, st, dry) {
  if (!PORTRAIT_SPEAKERS.has(line.s) || !line.e || line.e === "none") return null;
  if (line.s === "lap" && line.e.startsWith("lap_soap_")) {
    if (dry || !st.flags.has("foam_active")) return `portraits/port_${line.e}`;
    return `portraits/port_${line.e}${st.flags.has("foam_swollen") ? "_cap" : "_foam"}`;
  }
  return `portraits/port_${line.e}`;
}

// Показать реплики; промис разрешается, когда игрок пролистал последнюю.
export function say(lines, st, opts = {}) {
  return new Promise((resolve) => {
    if (!lines || !lines.length) { resolve(); return; }
    queue = lines.map((l, i) => ({ ...l, i, portrait: portraitName(l, st, opts.dry) }));
    queue.forEach((l) => l.portrait && loadImage(l.portrait).catch(() => {}));
    doneCb = resolve;
    onLine = opts.onLine || null;
    next();
  });
}

function next() {
  cur = queue.shift() || null;
  shown = 0; t = 0; blipAcc = 0;
  if (cur && onLine) onLine(cur.i);   // звук кадра монтажа — с его репликой
  if (!cur) {
    const cb = doneCb;
    doneCb = null;
    if (cb) cb();
  }
}

export function active() {
  return cur !== null;
}

export function currentLine() {
  return cur;
}

export function update(dt) {
  if (!cur) return;
  const full = [...cur.t].length;
  if (shown >= full) return;
  if (fast) { shown = full; return; }
  t += dt * CPS;
  const nw = Math.min(full, Math.floor(t));
  if (nw > shown) {
    blipAcc += nw - shown;
    if (blipAcc >= 3) {
      blipAcc = 0;
      const b = BLIP[cur.s];
      if (b) audio.sfx(b, 0.5);
    }
    shown = nw;
  }
}

// Клик по окну: дописать строку целиком или перейти к следующей.
export function click() {
  if (!cur) return false;
  const full = [...cur.t].length;
  if (shown < full) shown = full;
  else next();
  return true;
}

function wrap(text, maxW) {
  const words = text.split(" ");
  const lines = [];
  let line = "";
  for (const w of words) {
    const test = line ? line + " " + w : w;
    if (ctx.measureText(test).width > maxW && line) {
      lines.push(line);
      line = w;
    } else line = test;
  }
  if (line) lines.push(line);
  return lines;
}

function rr(x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

export function draw() {
  if (!cur) return;
  const chars = [...cur.t];
  const text = chars.slice(0, shown).join("");
  const full = shown >= chars.length;
  const px = 24;
  const py = 776;
  const port = cur.portrait ? image(cur.portrait) : null;
  const isCap = cur.s === "cap";
  const withPortrait = !!cur.portrait;
  const tx = withPortrait ? px + 284 : px;
  const tw = withPortrait ? 1580 : 1864;
  const ty = py + 44;
  const th = 236;
  if (withPortrait) {
    rr(px, py, 268, 280, 10);
    ctx.fillStyle = C.panel;
    ctx.fill();
    if (port) ctx.drawImage(port, px + 6, py + 6, 256, 256);
    ctx.lineWidth = 4;
    ctx.strokeStyle = cur.s === "anc" ? C.steel : C.brass;
    rr(px, py, 268, 280, 10);
    ctx.stroke();
  }
  rr(tx, ty, tw, th, 10);
  ctx.fillStyle = C.panel;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = C.brass;
  ctx.stroke();
  // плашка имени
  const name = isCap ? null : speakers[cur.s];
  if (name) {
    ctx.font = '700 26px "PT Sans"';
    const w = ctx.measureText(name).width + 26;
    rr(tx + 14, ty - 18, w, 34, 6);
    ctx.fillStyle = "rgba(13, 15, 23, 0.95)";
    ctx.fill();
    ctx.lineWidth = 3;
    ctx.strokeStyle = cur.s === "anc" ? C.steel : C.brass;
    ctx.stroke();
    ctx.fillStyle = cur.s === "anc" ? C.steel : C.brass;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(name, tx + 27, ty - 1);
  }
  // текст
  ctx.font = isCap ? 'italic 400 34px "PT Sans"' : '400 34px "PT Sans"';
  ctx.fillStyle = isCap ? C.cap : C.text;
  ctx.textBaseline = "alphabetic";
  const fullLines = wrap(cur.t, tw - 52);
  // переносим по полному тексту, чтобы слова не прыгали при печати
  let left = text.length;
  const lh = 44;
  const y0 = ty + 30 + 34;
  fullLines.forEach((ln, k) => {
    const part = ln.slice(0, Math.max(0, left));
    left -= ln.length + 1;
    if (!part) return;
    if (isCap) {
      ctx.textAlign = "center";
      ctx.fillText(part, tx + tw / 2 - (ctx.measureText(ln).width - ctx.measureText(part).width) / 2, y0 + k * lh);
    } else {
      ctx.textAlign = "left";
      ctx.fillText(part, tx + 26, y0 + k * lh);
    }
  });
  ctx.font = '400 24px "PT Sans"';
  ctx.fillStyle = C.dim;
  ctx.textAlign = "right";
  ctx.fillText(full ? (touchHint ? "Коснитесь — дальше" : "Щелчок — дальше") : "…", tx + tw - 26, ty + th - 18);
}

export function contains(p) {
  return !!cur && p && p.y >= 776;
}
