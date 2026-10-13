// Титул и настройки.
// Раскладка — спека §10 с поправкой автора 13.10.2026: логотип в (30, 30);
// кнопки 400×72 столбиком с шагом 92 от y = 450, по центру части BJ2 логотипа
// («ЛАТУННЫЙ ЯНЫЧАР» с ятаганом, x 0–660 в файле → центр 30 + 330 = 360;
// римская «II» не в счёт) → x = 160. Плакаты справа (x 900–1880) не перекрыты.
// Вид кнопок и панели настроек — как в BJ2 (src/ui.lua, menu_draw).

import { ctx, W, H, setCursor } from "./view.js";
import { image } from "./assets.js";
import * as audio from "./audio.js";
import * as store from "./store.js";

export const LOGO = { x: 30, y: 30 };
export const LOGO_CENTER_X = 30 + 330;
const BTN = { w: 400, h: 72, gap: 92, y: 450 };
BTN.x = LOGO_CENTER_X - BTN.w / 2;

const C = {
  panel: "rgba(22, 24, 32, 0.92)",
  panelSolid: "#16181f",
  brass: "#b8945a",
  brassHi: "#e0bb72",
  text: "#ede8db",
  dim: "#a6a194",
  ok: "#59cc66",
  btn: "#262833",
  btnHi: "#2f3240",
};

let T = {};                 // строки интерфейса (data/ui.json)
let settings = store.loadSettings();
let mode = "title";         // title | settings
let buttons = [];           // последняя раскладка кнопок: {id, x, y, w, h, enabled}
let hover = null;
let focus = -1;             // кнопка под клавиатурой
let toast = null;           // {text, t0}
let onStart = () => {};
let onSettingsChange = () => {};

export function init(uiTexts, handlers) {
  T = uiTexts;
  onStart = handlers.onStart || onStart;
  onSettingsChange = handlers.onSettings || onSettingsChange;
  onSettingsChange(settings);
  audio.applySettings(settings);
  document.addEventListener("fullscreenchange", () => { /* подпись кнопки сменится в draw */ });
}

export function enter() {
  mode = "title";
  focus = -1;
  audio.music("bgm_title");
}

function fsSupported() {
  const d = document.documentElement;
  return !!(d.requestFullscreen || d.webkitRequestFullscreen);
}

function isFullscreen() {
  return !!(document.fullscreenElement || document.webkitFullscreenElement);
}

function toggleFullscreen() {
  if (isFullscreen()) {
    (document.exitFullscreen || document.webkitExitFullscreen).call(document);
  } else {
    const d = document.documentElement;
    const req = d.requestFullscreen || d.webkitRequestFullscreen;
    const p = req && req.call(d);
    if (p && p.catch) p.catch(() => {});
  }
}

function layoutTitle() {
  const items = [
    { id: "start", t: T.title_start, enabled: true },
    { id: "cont", t: T.title_continue, enabled: store.hasSave() },
    { id: "settings", t: T.title_settings, enabled: true },
    { id: "fullscreen", t: isFullscreen() ? T.title_windowed : T.title_fullscreen, enabled: fsSupported() },
  ];
  return items.map((it, i) => ({ ...it, x: BTN.x, y: BTN.y + i * BTN.gap, w: BTN.w, h: BTN.h }));
}

// Панель настроек — как в BJ2 (600 px, строки через 68, кнопка «Назад» 480×64),
// высота — по числу пунктов, панель — по центру кадра.
const OPTS = ["music", "sound", "fasttext"];
const PANEL = { w: 600, h: 110 + OPTS.length * 68 + 40 + 64 + 44 };
PANEL.x = (W - PANEL.w) / 2;
PANEL.y = Math.round((H - PANEL.h) / 2);

const CONFIRM = { w: 760, h: 300 };
CONFIRM.x = (W - CONFIRM.w) / 2;
CONFIRM.y = 390;

function layoutConfirm() {
  return [
    { id: "yes", t: T.yes, x: CONFIRM.x + 80, y: CONFIRM.y + 190, w: 260, h: 72, enabled: true },
    { id: "no", t: T.no, x: CONFIRM.x + CONFIRM.w - 340, y: CONFIRM.y + 190, w: 260, h: 72, enabled: true },
  ];
}

function drawConfirm() {
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.fillRect(0, 0, W, H);
  roundRect(CONFIRM.x, CONFIRM.y, CONFIRM.w, CONFIRM.h, 14);
  ctx.fillStyle = C.panel;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = C.brass;
  ctx.stroke();
  ctx.font = '400 34px "PT Sans"';
  ctx.fillStyle = C.text;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(T.new_game_confirm, W / 2, CONFIRM.y + 100);
  buttons.forEach((b, i) => drawButton(b, hover === b.id || focus === i));
}

function layoutSettings() {
  const top = PANEL.y + 110;
  const rows = OPTS.map((k, i) => ({
    id: "opt_" + k, t: T[k], x: PANEL.x + 60, y: top + i * 68, w: 480, h: 60, enabled: true, toggle: k,
  }));
  rows.push({ id: "back", t: T.back, x: PANEL.x + 60, y: top + OPTS.length * 68 + 40, w: 480, h: 64, enabled: true });
  return rows;
}

function fitFont(text, weight, size, maxW) {
  let s = size;
  ctx.font = `${weight} ${s}px "PT Sans"`;
  while (s > 20 && ctx.measureText(text).width > maxW) {
    s -= 2;
    ctx.font = `${weight} ${s}px "PT Sans"`;
  }
  return s;
}

function roundRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

function drawButton(b, active) {
  roundRect(b.x, b.y, b.w, b.h, 12);
  ctx.fillStyle = active ? C.btnHi : C.panel;
  ctx.fill();
  ctx.lineWidth = active ? 3 : 2;
  ctx.strokeStyle = active ? C.brassHi : C.brass;
  ctx.stroke();
  fitFont(b.t, 700, 44, b.w - 40);
  ctx.fillStyle = b.enabled ? C.text : "rgba(166, 161, 148, 0.55)";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(b.t, b.x + b.w / 2, b.y + b.h / 2 + 2);
}

function drawBackground() {
  const bg = image("ui/bg_title");
  if (bg) ctx.drawImage(bg, 0, 0, W, H);
  const logo = image("ui/logo_title");
  if (logo) ctx.drawImage(logo, LOGO.x, LOGO.y);
}

function drawSettings() {
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.fillRect(0, 0, W, H);
  roundRect(PANEL.x, PANEL.y, PANEL.w, PANEL.h, 14);
  ctx.fillStyle = C.panel;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = C.brass;
  ctx.stroke();
  ctx.font = '700 44px "PT Sans"';
  ctx.fillStyle = C.brassHi;
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.fillText(T.settings, PANEL.x + PANEL.w / 2, PANEL.y + 74);
  buttons.forEach((b, i) => {
    const active = hover === b.id || focus === i;
    if (b.toggle) {
      if (active) {
        roundRect(b.x, b.y, b.w, b.h, 10);
        ctx.fillStyle = "rgba(255, 255, 255, 0.06)";
        ctx.fill();
      }
      ctx.font = '400 34px "PT Sans"';
      ctx.fillStyle = C.text;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(b.t, b.x + 20, b.y + b.h / 2 + 2);
      const on = settings[b.toggle];
      roundRect(b.x + b.w - 60, b.y + 12, 36, 36, 6);
      ctx.lineWidth = 2;
      ctx.strokeStyle = on ? C.ok : C.dim;
      ctx.fillStyle = C.ok;
      if (on) ctx.fill();
      ctx.stroke();
    } else {
      roundRect(b.x, b.y, b.w, b.h, 10);
      ctx.fillStyle = active ? C.btnHi : C.btn;
      ctx.fill();
      ctx.lineWidth = active ? 3 : 2;
      ctx.strokeStyle = active ? C.brassHi : C.brass;
      ctx.stroke();
      ctx.font = '400 34px "PT Sans"';
      ctx.fillStyle = C.text;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(b.t, b.x + b.w / 2, b.y + b.h / 2 + 2);
    }
  });
}

function drawToast(now) {
  if (!toast) return;
  const age = (now - toast.t0) / 1000;
  if (age > 3.5) { toast = null; return; }
  const a = age > 3 ? 1 - (age - 3) / 0.5 : 1;
  ctx.globalAlpha = a;
  ctx.font = '400 32px "PT Sans"';
  const w = ctx.measureText(toast.text).width + 60;
  const x = W / 2 - w / 2;
  const y = H - 130;
  roundRect(x, y, w, 64, 12);
  ctx.fillStyle = C.panel;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = C.brass;
  ctx.stroke();
  ctx.fillStyle = C.text;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(toast.text, W / 2, y + 34);
  ctx.globalAlpha = 1;
}

export function showToast(text) {
  toast = { text, t0: performance.now() };
}

export function draw(now) {
  drawBackground();
  if (mode === "title") {
    buttons = layoutTitle();
    buttons.forEach((b, i) => drawButton(b, b.enabled && (hover === b.id || focus === i)));
  } else if (mode === "confirm") {
    buttons = layoutConfirm();
    drawConfirm();
  } else {
    buttons = layoutSettings();
    drawSettings();
  }
  drawToast(now);
}

function hit(p) {
  if (!p) return null;
  return buttons.find((b) => p.x >= b.x && p.x < b.x + b.w && p.y >= b.y && p.y < b.y + b.h) || null;
}

export function pointerMove(p) {
  const b = hit(p);
  hover = b && b.enabled ? b.id : null;
  if (hover) focus = -1;
  setCursor(hover ? "act" : "normal");
}

export function pointerDown(p) {
  const b = hit(p);
  if (!b || !b.enabled) return false;
  activate(b);
  return true;
}

function activate(b) {
  audio.sfx("ui_click");
  switch (b.id) {
    case "start":
      if (store.hasSave()) { mode = "confirm"; focus = -1; hover = null; }
      else onStart();
      break;
    case "yes":
      mode = "title";
      onStart({ fresh: true });
      break;
    case "no":
      mode = "title";
      focus = -1;
      hover = null;
      break;
    case "cont":
      onStart({ continue: true });
      break;
    case "settings":
      mode = "settings";
      focus = -1;
      hover = null;
      break;
    case "fullscreen":
      toggleFullscreen();
      break;
    case "back":
      mode = "title";
      focus = -1;
      hover = null;
      break;
    default:
      if (b.toggle) toggleSetting(b.toggle);
  }
}

export function key(e) {
  const list = buttons.filter((b) => b.enabled);
  if (!list.length) return false;
  const idx = focus >= 0 ? list.indexOf(buttons[focus]) : -1;
  const move = (d) => {
    const n = (idx + d + list.length) % list.length;
    focus = buttons.indexOf(list[n]);
    hover = null;
  };
  switch (e.key) {
    case "ArrowDown": case "Tab":
      move(e.shiftKey && e.key === "Tab" ? -1 : 1);
      return true;
    case "ArrowUp":
      move(-1);
      return true;
    case "Enter": case " ":
      if (focus >= 0 && buttons[focus] && buttons[focus].enabled) activate(buttons[focus]);
      return true;
    case "Escape":
      if (mode === "settings" || mode === "confirm") { mode = "title"; focus = -1; return true; }
      return false;
    default:
      return false;
  }
}

export function toggleSetting(k) {
  settings = { ...settings, [k]: !settings[k] };
  store.saveSettings(settings);
  audio.applySettings(settings);
  onSettingsChange(settings);
  return settings;
}

export function getButtons() {
  return buttons.map((b) => ({ id: b.id, x: b.x, y: b.y, w: b.w, h: b.h, enabled: b.enabled, t: b.t }));
}

export function getSettings() {
  return { ...settings };
}
