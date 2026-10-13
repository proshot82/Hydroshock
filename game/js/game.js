// Игра: исполняет данные акта (design act*.json ← design/logic/ACT*_LOGIC.md) так же, как
// проверка tools/data/check_logic.py: зоны → глаголы → первое правило с истинным условием →
// реплики слота → эффекты (флаги, тележка, вид, документ, сцена, меню, цепочка, конец акта).
// Ввод BJ2: левая кнопка — действовать (меню действий у предмета), правая — осмотреть;
// предмет из «При себе» — выбрать и щёлкнуть по цели. Советы Предка — GDD §10 (без таймера).

import { ctx, W, H, setCursor } from "./view.js";
import { image, loadImage } from "./assets.js";
import * as audio from "./audio.js";
import * as dialog from "./dialog.js";
import * as reader from "./reader.js";
import { evaluate, first } from "./cond.js";
import { State, save as saveState } from "./state.js";

const C = {
  panel: "rgba(22, 24, 32, 0.94)", brass: "#b8945a", brassHi: "#e0bb72", text: "#ede8db", dim: "#a6a194",
  steel: "#8cb3db", ok: "#59cc66", btn: "#262833", btnHi: "#2f3240",
};
const CURSOR = { look: "act", act: "act", move: "move", zoom: "zoom" };
const HUD = {
  hint: { x: 1640, y: 12, w: 256, h: 52 },
  docs: { x: 1400, y: 12, w: 224, h: 52 },
  menu: { x: 1250, y: 12, w: 134, h: 52 },
  back: { x: 830, y: 1004, w: 260, h: 64 },
};
const INV = { x: 24, y: 76, size: 80, gap: 92 };

let data = null;
let st = null;
let T = {};               // строки интерфейса
let onExit = () => {};
let busy = false;
let frame = null;         // кадр сцены/слота поверх вида: [[слои…], …]
let verbMenu = null;      // {zk, x, y, items:[{verb, label}]}
let choice = null;        // {menu, items:[{id, label, rule}], closable}
let selected = null;      // выбранный предмет
let hover = null;         // {zone, p}
let hoverHud = null;
let showZones = false;
let toast = null;
let pause = null;         // {items}
let docsPanel = null;     // {items}
let endCard = null;
let dryPortrait = false;
let lastPointer = null;
const masks = new Map();  // слой → альфа для попадания
const log = [];           // журнал для автотестов: слоты по порядку

// ------------------------------------------------------------ запуск

export function init(uiTexts, handlers) {
  T = uiTexts;
  onExit = handlers.onExit || onExit;
  dialog.init(data ? data.speakers : {});
}

export async function start(actData, state) {
  data = actData;
  dialog.init(data.speakers || {});
  busy = false; frame = null; verbMenu = null; choice = null; selected = null; pause = null;
  docsPanel = null; endCard = null; toast = null;
  const fresh = !state;
  st = state || new State(data.act, data.start_flags);
  if (!st.view) st.view = Object.keys(data.views)[0];
  preloadAct();
  if (st.ended) { showEnd(); return; }
  if (fresh && data.scenes.open) {
    enterView(st.view, false);
    await runScript(async () => { await runScene("open"); });
  } else {
    enterView(st.view, false);
  }
}

function preloadAct() {
  const names = new Set();
  for (const v of Object.values(data.views)) {
    names.add(v.bg);
    v.layers.forEach((l) => names.add(l.img));
  }
  for (const steps of Object.values(data.scenes)) {
    steps.forEach((s) => s.frames.forEach((f) => Array.isArray(f) && f.forEach((l) => names.add(l.img))));
  }
  Object.values(data.items).forEach((i) => names.add(i.icon));
  // сначала то, что на экране, потом остальное
  const v = data.views[st.view];
  [v.bg, ...v.layers.map((l) => l.img)].forEach((n) => loadImage(n).catch(() => {}));
  names.forEach((n) => loadImage(n).catch(() => {}));
}

// ------------------------------------------------------------ вид и звук

function viewMusic(vid) {
  let v = data.views[vid];
  let music = v.music;
  let amb = v.amb;
  while ((!music || !amb) && v.parent) {
    v = data.views[v.parent];
    music = music || v.music;
    amb = amb || v.amb;
  }
  return { music, amb };
}

function enterView(vid, sound = true) {
  if (!data.views[vid]) return;
  const prev = st.view;
  st.view = vid;
  verbMenu = null;
  const m = viewMusic(vid);
  audio.music(m.music || null);
  audio.ambience(m.amb || null);
  if (sound && prev !== vid) {
    const isZoom = data.views[vid].type === "зум";
    const wasZoom = prev && data.views[prev] && data.views[prev].type === "зум";
    audio.sfx(isZoom ? "ui_zoom_in" : wasZoom ? "ui_zoom_out" : "ui_transition");
  }
}

// ------------------------------------------------------------ исполнение

async function runScript(fn) {
  busy = true;
  try {
    await fn();
  } finally {
    busy = false;
    if (data) saveState(st);
  }
}

function changed(before) {
  if (before.flags !== [...st.flags].sort().join(",")) st.hint.lock = false;
}

async function playSlot(slot, opts = {}) {
  if (!slot) return;
  if (slot.startsWith("@")) { await runChain(slot.slice(1)); return; }
  const firstTime = !st.n[slot];
  st.n[slot] = (st.n[slot] || 0) + 1;
  if (firstTime && !slot.startsWith("HINT.")) st.hint.lock = false;   // новый слот снимает блок совета
  log.push(slot);
  const t = data.texts[slot];
  if (!t) return;
  await dialog.say(t.lines, st, { dry: opts.dry || dryPortrait });
}

function applyNow(effects) {
  for (const e of effects) {
    if (e.add) st.flags.add(e.add);
    else if (e.remove) st.flags.delete(e.remove);
    else if (e.pos) st.pos = e.pos;
    else if (e.inc) st.c[e.inc] = (st.c[e.inc] || 0) + 1;
    else if (e.sfx) audio.sfx(e.sfx);
    else if (e.loop) audio.loop(e.loop);
    else if (e.stop) audio.stopLoop(e.stop);
    else if (e.amb) audio.ambience(e.amb);
    else if (e.portrait) dryPortrait = e.portrait === "сухой";
  }
}

async function applyLater(effects) {
  for (const e of effects) {
    if (e.doc) await openDoc(e.doc);
    else if (e.view) enterView(e.view);
    else if (e.scene) await runScene(e.scene);
    else if (e.chain) await runChain(e.chain);
    else if (e.menu) openMenu(e.menu);
    else if (e.act) { st.ended = true; showEnd(); }
  }
}

async function runRule(rule) {
  const before = { flags: [...st.flags].sort().join(",") };
  applyNow(rule.effects);
  const fr = rule.effects.find((e) => e.frame);
  const mus = rule.effects.find((e) => e.music);
  if (fr) frame = fr.frame;
  if (mus) audio.music(mus.music);
  await playSlot(rule.slot);
  if (fr) frame = null;
  if (mus) audio.music(viewMusic(st.view).music);
  await applyLater(rule.effects);
  changed(before);
}

async function runChain(name) {
  const r = first(data.chains[name], st);
  if (!r) return;
  await runRule(r);
}

async function runScene(name) {
  const steps = data.scenes[name] || [];
  for (const step of steps) {
    const before = { flags: [...st.flags].sort().join(",") };
    const frames = step.frames.filter((f) => Array.isArray(f));
    frame = frames.length ? frames : null;
    applyNow(step.sound);
    applyNow(step.effects);
    if (step.effects.some((e) => e.portrait)) {
      await playSlot(step.slot, { dry: true });
      dryPortrait = false;
    } else {
      await playSlot(step.slot);
    }
    await applyLater(step.effects.filter((e) => !e.portrait));
    changed(before);
  }
  frame = null;
}

async function openDoc(docId) {
  const d = data.docs[docId];
  if (!d) return;
  if (d.caption && evaluate(d.caption.when, st)) await playSlot(d.caption.slot);
  st.n[docId] = (st.n[docId] || 0) + 1;
  if (!st.docs.includes(docId)) st.docs.push(docId);
  log.push(docId);
  audio.sfx("ui_paper");
  await reader.open(docId, data);
}

function openMenu(name) {
  const items = [];
  for (const it of data.menus[name] || []) {
    const r = first(it.rules, st);
    if (!r) continue;
    const label = it.label.ui ? T[it.label.ui] || it.label.ui : it.label.text;
    items.push({ id: it.id, label, rule: r });
  }
  choice = { menu: name, items, closable: name !== "talk" };
}

// ------------------------------------------------------------ зоны

function visibleZones() {
  const v = data.views[st.view];
  return v.zones.filter((z) => evaluate(z.when, st));
}

function zoneKey(z) {
  return `${st.view}.${z.id}`;
}

function mask(lay) {
  let m = masks.get(lay.img);
  if (m) return m;
  const img = image(lay.img);
  if (!img) return null;
  const c = document.createElement("canvas");
  c.width = img.naturalWidth;
  c.height = img.naturalHeight;
  const g = c.getContext("2d", { willReadFrequently: true });
  g.drawImage(img, 0, 0);
  const px = g.getImageData(0, 0, c.width, c.height).data;
  const a = new Uint8Array(c.width * c.height);
  for (let i = 0; i < a.length; i++) a[i] = px[i * 4 + 3] > 8 ? 1 : 0;
  m = { w: c.width, h: c.height, a, area: a.reduce((s, v) => s + v, 0) };
  masks.set(lay.img, m);
  return m;
}

function hitZone(z, p) {
  if (z.layer) {
    const m = mask(z.layer);
    if (!m) return false;
    const x = Math.floor(p.x - z.layer.x);
    const y = Math.floor(p.y - z.layer.y);
    return x >= 0 && y >= 0 && x < m.w && y < m.h && m.a[y * m.w + x] === 1;
  }
  return z.rects.some(([x, y, w, h]) => p.x >= x && p.x < x + w && p.y >= y && p.y < y + h);
}

function zoneArea(z) {
  if (z.layer) {
    const m = mask(z.layer);
    return m ? m.area : 1e9;
  }
  return z.rects.reduce((s, r) => s + r[2] * r[3], 0);
}

function zoneAt(p) {
  if (!p || frame) return null;
  const hits = visibleZones().filter((z) => hitZone(z, p));
  hits.sort((a, b) => (a.layer ? 0 : 1) - (b.layer ? 0 : 1) || zoneArea(a) - zoneArea(b));
  return hits[0] || null;
}

function verbsOf(zk) {
  const out = [];
  const rules = data.rules[zk] || {};
  for (const [verb, rs] of Object.entries(rules)) {
    if (verb.startsWith("предмет:")) continue;
    const r = first(rs, st);
    if (r) out.push({ verb, rule: r });
  }
  return out;
}

// ------------------------------------------------------------ действия игрока

function act(fn) {
  if (busy) return;
  runScript(fn);
}

function clickZone(z, p) {
  const zk = zoneKey(z);
  if (selected) {
    const item = selected;
    selected = null;
    useItem(item, z);
    return;
  }
  const vs = verbsOf(zk);
  const direct = vs.find((v) => v.verb === "клик");
  if (direct) { act(() => runRule(direct.rule)); return; }
  const look = vs.find((v) => v.verb === "осмотр");
  const others = vs.filter((v) => v.verb !== "осмотр");
  if (!others.length) {
    if (look) act(() => runRule(look.rule));
    return;
  }
  const items = [];
  if (look) items.push({ verb: "осмотр", label: T.verb_look, rule: look.rule });
  others.forEach((v) => items.push({ verb: v.verb, label: T[`verb_${v.verb}`] || v.verb, rule: v.rule }));
  verbMenu = { zk, x: p.x, y: p.y, items, title: z.name };
  audio.sfx("ui_click");
}

function lookZone(z) {
  const r = first((data.rules[zoneKey(z)] || {})["осмотр"], st);
  if (r) act(() => runRule(r));
}

function useItem(item, z) {
  const zk = zoneKey(z);
  const r = first((data.rules[zk] || {})[`предмет:${item}`], st);
  if (r) { act(() => runRule(r)); return; }
  const it = data.items[item];
  const miss = z.props.includes("плоское") ? it.miss_flat : it.miss;
  act(() => playSlot(miss));
}

function heldItems() {
  return Object.entries(data.items).filter(([, it]) => evaluate(it.when, st)).map(([id, it]) => ({ id, ...it }));
}

function invSlots() {
  return heldItems().map((it, i) => ({ ...it, x: INV.x + i * INV.gap, y: INV.y, w: INV.size, h: INV.size }));
}

function clickItem(it, button) {
  if (button === 2) {
    selected = null;
    act(async () => {
      await playSlot(it.look);
      applyNow(it.look_effects);
      await applyLater(it.look_effects);
    });
    return;
  }
  if (selected && selected !== it.id) {
    selected = null;
    act(() => runChain("fb_generic"));
    return;
  }
  selected = selected === it.id ? null : it.id;
  audio.sfx("ui_pickup");
}

async function hint() {
  const H_ = data.hints;
  if (!st.hint.n) {
    st.hint.n = 1;
    await playSlot(data.hint_slots.intro);
    return;
  }
  if (st.hint.lock) { await playSlot(data.hint_slots.cooldown); return; }
  const topic = H_.find((h) => evaluate(h.when, st));
  if (!topic) { await playSlot(data.hint_slots.done); return; }
  const lvl = Math.min(3, (st.hint.level[topic.topic] || 0) + 1);
  st.hint.level[topic.topic] = lvl;
  st.hint.n += 1;
  await playSlot(`HINT.${topic.topic}.${lvl}`);
  st.hint.lock = true;
}

function goBack() {
  const v = data.views[st.view];
  if (v.parent) { enterView(v.parent); saveState(st); }
}

function showEnd() {
  endCard = { act: data.act };
  audio.ambience(null);
}

// ------------------------------------------------------------ ввод

function inRect(p, r) {
  return p && p.x >= r.x && p.x < r.x + r.w && p.y >= r.y && p.y < r.y + r.h;
}

function menuRects(items, cx, cy, w = 520, h = 64) {
  const total = items.length * (h + 10) - 10;
  const x = Math.max(20, Math.min(W - w - 20, cx));
  const y = Math.max(80, Math.min(H - total - 20, cy));
  return items.map((it, i) => ({ ...it, x, y: y + i * (h + 10), w, h }));
}

function choiceRects() {
  const w = 1100;
  const h = 76;
  const total = choice.items.length * (h + 12) - 12;
  const x = (W - w) / 2;
  const y = Math.max(120, 700 - total);
  return choice.items.map((it, i) => ({ ...it, x, y: y + i * (h + 12), w, h }));
}

function pauseRects() {
  const items = [
    { id: "resume", label: T.resume },
    { id: "music", label: T.music, toggle: "music" },
    { id: "sound", label: T.sound, toggle: "sound" },
    { id: "fasttext", label: T.fasttext, toggle: "fasttext" },
    { id: "quit", label: T.save_quit },
  ];
  return items.map((it, i) => ({ ...it, x: 660, y: 330 + i * 84, w: 600, h: 70 }));
}

function docsRects() {
  return st.docs.map((d, i) => ({
    doc: d, label: docTitle(d), x: 460, y: 200 + i * 70, w: 1000, h: 60,
  }));
}

function docTitle(d) {
  const lines = (data.docs[d] && data.docs[d].lines) || [];
  const t = (lines.find((l) => l.trim()) || d).trim();
  return t.length > 60 ? t.slice(0, 58) + "…" : t;
}

export function pointerMove(p) {
  lastPointer = p;
  hoverHud = null;
  hover = null;
  if (!data || endCard || pause || docsPanel || reader.active() || dialog.active() || busy) {
    setCursor(p && (endCard || pause || docsPanel || reader.active() || dialog.active()) ? "act" : "normal");
    return;
  }
  if (choice || verbMenu) { setCursor("act"); return; }
  for (const [k, r] of Object.entries(HUD)) {
    if (k === "back" && !data.views[st.view].parent) continue;
    if (inRect(p, r)) { hoverHud = k; setCursor("act"); return; }
  }
  if (invSlots().some((s) => inRect(p, s))) { setCursor("act"); return; }
  const z = zoneAt(p);
  if (z) hover = { zone: z, p };
  setCursor(z ? CURSOR[z.cursor] || "act" : "normal");
}

export function pointerDown(p, button = 0) {
  if (!data || !p) return false;
  if (endCard) {
    if (inRect(p, END_BTN)) { audio.sfx("ui_click"); onExit(); }
    return true;
  }
  if (pause) {
    const b = pauseRects().find((r) => inRect(p, r));
    if (!b) return true;
    audio.sfx("ui_click");
    if (b.id === "resume") pause = null;
    else if (b.id === "quit") { pause = null; saveState(st); onExit(); }
    else onSettingToggle(b.toggle);
    return true;
  }
  if (docsPanel) {
    const b = docsRects().find((r) => inRect(p, r));
    docsPanel = null;
    if (b) act(async () => { audio.sfx("ui_paper"); await reader.open(b.doc, data); });
    return true;
  }
  if (reader.active()) { reader.close(); return true; }
  if (dialog.active()) { dialog.click(); return true; }
  if (busy) return true;
  if (choice) {
    const b = choiceRects().find((r) => inRect(p, r));
    if (b) {
      choice = null;
      audio.sfx("ui_click");
      act(() => runRule(b.rule));
    } else if (choice.closable) choice = null;
    return true;
  }
  if (verbMenu) {
    const b = menuRects(verbMenu.items, verbMenu.x, verbMenu.y).find((r) => inRect(p, r));
    verbMenu = null;
    if (b && button === 0) act(() => runRule(b.rule));
    return true;
  }
  if (button === 0 && inRect(p, HUD.hint)) { audio.sfx("ui_click"); act(hint); return true; }
  if (button === 0 && inRect(p, HUD.docs)) { audio.sfx("ui_click"); docsPanel = { open: true }; return true; }
  if (button === 0 && inRect(p, HUD.menu)) { audio.sfx("ui_click"); pause = { open: true }; return true; }
  if (data.views[st.view].parent && inRect(p, HUD.back)) { goBack(); return true; }
  const slot = invSlots().find((s) => inRect(p, s));
  if (slot) { clickItem(slot, button); return true; }
  const z = zoneAt(p);
  if (!z) {
    if (selected) selected = null;
    else if (button === 2) goBack();
    return true;
  }
  if (button === 2) {
    if (selected) { selected = null; return true; }
    lookZone(z);
  } else clickZone(z, p);
  return true;
}

let settingsHook = () => {};
export function onSettings(fn) {
  settingsHook = fn;
}
function onSettingToggle(k) {
  settingsHook(k);
}

export function key(e) {
  if (!data) return false;
  if (e.key === " " && !dialog.active() && !reader.active()) { showZones = !showZones; return true; }
  if (e.key === "Escape") {
    if (reader.active()) { reader.close(); return true; }
    if (docsPanel) { docsPanel = null; return true; }
    if (pause) { pause = null; return true; }
    if (verbMenu) { verbMenu = null; return true; }
    if (choice && choice.closable) { choice = null; return true; }
    if (selected) { selected = null; return true; }
    if (dialog.active() || busy || endCard) return true;
    if (data.views[st.view].parent) { goBack(); return true; }
    pause = { open: true };
    return true;
  }
  if ((e.key === "Enter" || e.key === " ") && dialog.active()) { dialog.click(); return true; }
  return false;
}

export function update(dt) {
  dialog.update(dt);
}

// ------------------------------------------------------------ отрисовка

function rr(x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

function drawLayers(layers) {
  for (const l of layers) {
    const img = image(l.img);
    if (img) ctx.drawImage(img, l.x, l.y);
  }
}

function drawWorld() {
  if (frame) {
    const cur = dialog.currentLine();
    const idx = Math.min(cur ? cur.i : 0, frame.length - 1);
    drawLayers(frame[idx]);
    return;
  }
  const v = data.views[st.view];
  const bg = image(v.bg);
  if (!bg) {
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, W, H);
    ctx.font = '400 30px "PT Sans"';
    ctx.fillStyle = C.dim;
    ctx.textAlign = "center";
    ctx.fillText(T.loading || "Загрузка…", W / 2, H / 2);
    return;
  }
  ctx.drawImage(bg, 0, 0, W, H);
  drawLayers(v.layers.filter((l) => evaluate(l.when, st)));
  if (showZones) {
    ctx.lineWidth = 4;
    for (const z of visibleZones()) {
      ctx.strokeStyle = "rgba(255, 220, 120, 0.9)";
      ctx.fillStyle = "rgba(255, 220, 120, 0.18)";
      if (z.layer) {
        const m = mask(z.layer);
        if (m) {
          ctx.strokeRect(z.layer.x, z.layer.y, z.layer.w || m.w, z.layer.h || m.h);
        }
      } else z.rects.forEach(([x, y, w, h]) => { ctx.fillRect(x, y, w, h); ctx.strokeRect(x, y, w, h); });
    }
  }
}

function button(r, label, active, opts = {}) {
  rr(r.x, r.y, r.w, r.h, 10);
  ctx.fillStyle = active ? C.btnHi : opts.fill || C.panel;
  ctx.fill();
  ctx.lineWidth = active ? 3 : 2;
  ctx.strokeStyle = opts.stroke || (active ? C.brassHi : C.brass);
  ctx.stroke();
  ctx.font = opts.font || '700 26px "PT Sans"';
  ctx.fillStyle = opts.color || C.text;
  ctx.textAlign = opts.align || "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label, opts.align === "left" ? r.x + 24 : r.x + r.w / 2, r.y + r.h / 2 + 1);
}

function drawHud() {
  const quiet = busy || dialog.active() || reader.active() || frame;
  if (frame || endCard) return;
  // «При себе»
  const slots = invSlots();
  ctx.font = '700 24px "PT Sans"';
  const label = (data.texts["UI.inventory"] && data.texts["UI.inventory"].lines[0] && data.texts["UI.inventory"].lines[0].t) || "ПРИ СЕБЕ";
  rr(INV.x, 16, ctx.measureText(label).width + 28, 48, 8);
  ctx.fillStyle = C.panel;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = C.brass;
  ctx.stroke();
  ctx.fillStyle = C.brassHi;
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillText(label, INV.x + 14, 41);
  for (const s of slots) {
    rr(s.x, s.y, s.w, s.h, 8);
    ctx.fillStyle = C.panel;
    ctx.fill();
    ctx.lineWidth = selected === s.id ? 4 : 2;
    ctx.strokeStyle = selected === s.id ? C.ok : C.brass;
    ctx.stroke();
    const ic = image(s.icon);
    if (ic) ctx.drawImage(ic, s.x + 6, s.y + 6, s.w - 12, s.h - 12);
  }
  if (quiet) return;
  button(HUD.hint, T.hint_btn, hoverHud === "hint", { stroke: hoverHud === "hint" ? "#b8d4f0" : C.steel, color: "#d6e6f5" });
  button(HUD.docs, T.docs_btn, hoverHud === "docs");
  button(HUD.menu, "МЕНЮ", hoverHud === "menu");
  if (data.views[st.view].parent) button(HUD.back, T.back.toUpperCase(), hoverHud === "back", { font: '700 30px "PT Sans"' });
}

function drawHover() {
  if (!hover || busy || verbMenu || choice || dialog.active()) return;
  const text = hover.zone.name;
  ctx.font = '700 28px "PT Sans"';
  const w = ctx.measureText(text).width + 28;
  const x = Math.min(W - w - 10, hover.p.x + 28);
  const y = Math.min(H - 60, hover.p.y + 30);
  rr(x, y, w, 46, 8);
  ctx.fillStyle = "rgba(13, 15, 23, 0.9)";
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = C.brass;
  ctx.stroke();
  ctx.fillStyle = C.text;
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillText(text, x + 14, y + 24);
}

function drawVerbMenu() {
  if (!verbMenu) return;
  const rects = menuRects(verbMenu.items, verbMenu.x, verbMenu.y);
  const p = lastPointer;
  ctx.font = '700 26px "PT Sans"';
  const t = verbMenu.title;
  const r0 = rects[0];
  ctx.fillStyle = C.brassHi;
  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";
  ctx.lineWidth = 6;
  ctx.strokeStyle = "rgba(0,0,0,0.85)";
  ctx.strokeText(t, r0.x + 6, r0.y - 12);
  ctx.fillText(t, r0.x + 6, r0.y - 12);
  rects.forEach((r) => button(r, r.label, inRect(p, r), { align: "left", font: '400 30px "PT Sans"' }));
}

function drawChoice() {
  if (!choice) return;
  ctx.fillStyle = "rgba(0, 0, 0, 0.45)";
  ctx.fillRect(0, 0, W, H);
  choiceRects().forEach((r) => button(r, r.label, inRect(lastPointer, r), { align: "left", font: '400 32px "PT Sans"' }));
}

function drawPause() {
  if (!pause) return;
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.fillRect(0, 0, W, H);
  rr(620, 220, 680, 560, 14);
  ctx.fillStyle = C.panel;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = C.brass;
  ctx.stroke();
  ctx.font = '700 44px "PT Sans"';
  ctx.fillStyle = C.brassHi;
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.fillText(T.pause, W / 2, 290);
  const s = settingsHook("get") || {};
  for (const r of pauseRects()) {
    const lab = r.toggle ? `${r.label}: ${s[r.toggle] ? "да" : "нет"}` : r.label;
    button(r, lab, inRect(lastPointer, r), { font: '400 32px "PT Sans"' });
  }
}

function drawDocs() {
  if (!docsPanel) return;
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.fillRect(0, 0, W, H);
  rr(420, 100, 1080, 880, 14);
  ctx.fillStyle = C.panel;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = C.brass;
  ctx.stroke();
  ctx.font = '700 40px "PT Sans"';
  ctx.fillStyle = C.brassHi;
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.fillText(T.docs_title, W / 2, 165);
  const rs = docsRects();
  if (!rs.length) {
    ctx.font = '400 30px "PT Sans"';
    ctx.fillStyle = C.dim;
    ctx.fillText(T.docs_empty, W / 2, 300);
  }
  rs.forEach((r) => button(r, r.label, inRect(lastPointer, r), { align: "left", font: '400 28px "PT Sans"' }));
}

const END_BTN = { x: 760, y: 700, w: 400, h: 72 };

function drawEnd() {
  if (!endCard) return;
  ctx.fillStyle = "#0b0c10";
  ctx.fillRect(0, 0, W, H);
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.font = '700 60px "PT Sans"';
  ctx.fillStyle = C.brassHi;
  ctx.fillText(T[`act_${endCard.act}`] || "", W / 2, 360);
  ctx.font = '400 36px "PT Sans"';
  ctx.fillStyle = C.text;
  ctx.fillText(`Конец акта ${data.roman}.`, W / 2, 450);
  ctx.fillStyle = C.dim;
  const nextT = T[`act_${endCard.act + 1}`];
  if (nextT) ctx.fillText(`${nextT} — в следующей сборке.`, W / 2, 510);
  button(END_BTN, T.to_title, inRect(lastPointer, END_BTN), { font: '700 34px "PT Sans"' });
}

function drawSelected() {
  if (!selected || !lastPointer) return;
  const it = data.items[selected];
  const ic = it && image(it.icon);
  if (ic) {
    ctx.globalAlpha = 0.9;
    ctx.drawImage(ic, lastPointer.x + 14, lastPointer.y + 14, 72, 72);
    ctx.globalAlpha = 1;
  }
}

export function draw() {
  if (!data) return;
  if (endCard) { drawEnd(); return; }
  drawWorld();
  drawHud();
  drawHover();
  drawVerbMenu();
  drawChoice();
  dialog.draw();
  reader.draw();
  drawDocs();
  drawPause();
  drawSelected();
}

// ------------------------------------------------------------ для автотестов (Playwright)

export function debug() {
  if (!data) return null;
  return {
    act: data.act, view: st.view, busy, ended: !!endCard, frame: !!frame, pos: st.pos,
    flags: [...st.flags].sort(), dialog: dialog.active() ? dialog.currentLine() : null,
    reader: reader.currentDoc(), choice: choice ? choice.items.map((i) => ({ id: i.id, label: i.label })) : null,
    verbs: verbMenu ? verbMenu.items.map((i) => i.verb) : null, selected,
    zones: frame ? [] : visibleZones().map((z) => ({ id: z.id, name: z.name, at: clickPoint(z) })),
    items: invSlots().map((s) => ({ id: s.id, at: [s.x + s.w / 2, s.y + s.h / 2] })),
    menuItems: verbMenu ? menuRects(verbMenu.items, verbMenu.x, verbMenu.y).map((r) => ({ verb: r.verb, at: [r.x + r.w / 2, r.y + r.h / 2] }))
      : choice ? choiceRects().map((r) => ({ id: r.id, at: [r.x + r.w / 2, r.y + r.h / 2] })) : null,
    hud: { hint: center(HUD.hint), docs: center(HUD.docs), back: center(HUD.back), end: center(END_BTN) },
    log: log.slice(),
    n: { ...st.n }, hint: { ...st.hint },
  };
}

function center(r) {
  return [r.x + r.w / 2, r.y + r.h / 2];
}

// Точка, где щелчок действительно попадает в зону (её не перекрывает зона поверх): от центра
// зоны по спирали. null — зону перекрыли целиком (такую зону автопрохождение считает ошибкой).
function clickPoint(z) {
  const boxes = z.layer ? [[z.layer.x, z.layer.y, z.layer.w || 1, z.layer.h || 1]] : z.rects;
  for (const [x, y, w, h] of boxes) {
    const cx = x + w / 2;
    const cy = y + h / 2;
    for (let r = 0; r <= Math.max(w, h) / 2; r += 6) {
      for (let a = 0; a < 16; a++) {
        const p = { x: cx + Math.cos((a / 16) * 2 * Math.PI) * r, y: cy + Math.sin((a / 16) * 2 * Math.PI) * r };
        if (p.x < x || p.y < y || p.x >= x + w || p.y >= y + h) continue;
        if (zoneAt(p) === z) return [Math.round(p.x), Math.round(p.y)];
        if (r === 0) break;
      }
    }
  }
  return null;
}

// точка внутри зоны-слоя: ближайший к центру непрозрачный пиксель
function layerPoint(lay) {
  const m = mask(lay);
  if (!m) return [lay.x + 10, lay.y + 10];
  const cx = Math.floor(m.w / 2);
  const cy = Math.floor(m.h / 2);
  for (let r = 0; r < Math.max(m.w, m.h); r += 4) {
    for (let dy = -r; dy <= r; dy += 4) {
      for (let dx = -r; dx <= r; dx += 4) {
        const x = cx + dx;
        const y = cy + dy;
        if (x >= 0 && y >= 0 && x < m.w && y < m.h && m.a[y * m.w + x]) return [lay.x + x, lay.y + y];
      }
    }
  }
  return [lay.x, lay.y];
}
