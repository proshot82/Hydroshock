// Запуск: манифест и строки интерфейса → шрифты и картинки титула (с полосой загрузки) →
// кнопка «Играть» (звук разрешён только после нажатия) → титул ⇄ игра. Цикл кадров — здесь.

import * as view from "./view.js";
import * as assets from "./assets.js";
import * as audio from "./audio.js";
import * as title from "./title.js";
import * as game from "./game.js";
import * as dialog from "./dialog.js";
import * as saves from "./state.js";
import * as store from "./store.js";
import * as platform from "./platform.js";
import * as cloud from "./cloud.js";
import * as touch from "./touch.js";

const shell = document.getElementById("shell");
const status = document.getElementById("status");
const fill = document.getElementById("bar-fill");
const play = document.getElementById("play");

const TITLE_IMAGES = ["ui/bg_title", "ui/logo_title"];
const FONTS = ['400 34px "PT Sans"', '700 44px "PT Sans"', '400 34px "Old Standard TT"', '700 34px "Old Standard TT"',
  '400 34px "PT Mono"', '400 34px "Caveat"'];

let scene = null;     // title | game
let manifest = null;
const acts = {};      // загруженные данные актов
let last = 0;

function progress(done, total) {
  fill.style.width = `${Math.round((done / Math.max(1, total)) * 100)}%`;
}

function fail(err) {
  console.error(err);
  status.textContent = "Не удалось загрузить игру. Обновите страницу.";
}

async function actData(n) {
  if (!acts[n]) acts[n] = await (await fetch(`data/act${n}.json`, { cache: "no-cache" })).json();
  return acts[n];
}

// Флаги, которые знает сборка к акту n: накопительно по актам 1..n (GDD §12) — флаг Акта I,
// которого нет в словаре Акта II, при загрузке сейва Акта II не теряется.
function flagsOf(n) {
  if (!acts[n]) return null;
  const s = new Set();
  for (const [k, d] of Object.entries(acts)) if (Number(k) <= n) d.flags.forEach((f) => s.add(f));
  return s;
}

// Конец акта → «Дальше»: следующий акт с тем же состоянием (его готовит game.js).
async function nextAct(n, make) {
  const data = await actData(n);
  scene = game;
  await game.start(data, make(data), { newAct: true });
}

async function startGame(opts = {}) {
  let st = null;
  if (opts.continue) {
    for (const n of manifest.acts || [1]) await actData(n);
    const got = saves.load(flagsOf);
    if (!got) { title.showToast(ui.save_broken); return; }
    st = got.state;
    if (got.restored) title.showToast(ui.save_restored);
  } else {
    saves.clear();
  }
  const n = st ? st.act : (manifest.acts || [1])[0];
  const data = await actData(n);
  scene = game;
  await game.start(data, st);
}

function toTitle() {
  scene = title;
  title.enter();
}

let ui = {};

async function boot() {
  manifest = await assets.loadManifest();
  ui = await (await fetch("data/ui.json", { cache: "no-cache" })).json();
  title.init(ui, {
    onStart: (opts) => startGame(opts).catch(fail),
    onSettings: (s) => dialog.setFast(s.fasttext),
  });
  game.init(ui, {
    onExit: toTitle,
    onNext: { has: (n) => (manifest.acts || [1]).includes(n), start: (n, make) => nextAct(n, make).catch(fail) },
  });
  game.onSettings((k) => (k === "get" ? title.getSettings() : title.toggleSetting(k)));
  // Telegram: его SDK и облачная копия партии — до титула, чтобы «ПРОДОЛЖИТЬ» знал о ней
  await platform.init();
  const synced = await cloud.sync();
  if (cloud.available()) console.log(`облако Telegram: ${synced}`);
  shellTips();
  await Promise.all(FONTS.map((f) => document.fonts.load(f)));
  await assets.loadImages(TITLE_IMAGES, progress);
  if (!store.write("probe", 1)) status.textContent = ui.storage_off;
  else status.textContent = `Сборка ${manifest.build}`;
  play.disabled = false;
  play.focus();
  console.log("BJ3 READY");
}

// Карточка загрузки: как играть на этом устройстве, где хранится сохранение.
function shellTips() {
  const set = (id, t) => { const el = document.getElementById(id); if (el) el.textContent = t || ""; };
  set("tip-input", platform.TOUCH ? ui.tip_touch : ui.tip_mouse);
  set("tip-home", platform.homeScreenTip() ? ui.tip_home_ios : "");
  set("note-save", cloud.available() ? ui.note_save_tg : ui.note_save);
}

function start() {
  platform.onPlay();
  audio.unlock();
  // щелчки интерфейса и «голоса» реплик — сразу: иначе первая реплика стрекочет пачкой, пока они грузятся
  audio.preloadPrefixed(["ui_", "blip_"]);
  shell.classList.add("hidden");
  toTitle();
  view.canvas.focus();
  last = performance.now();
  requestAnimationFrame(frame);
}

function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  touch.update(dt);
  if (scene && scene.update) scene.update(dt);
  view.begin();
  if (scene) scene.draw(now);
  view.end();
  drawRing();
  // «назад» Telegram и браузера — как Esc, пока в игре есть куда возвращаться
  const inGame = scene === game;
  platform.setInGame(inGame);
  platform.setBack(inGame && game.canEscape(), () => { if (scene === game) game.escape(); });
  requestAnimationFrame(frame);
}

// Кольцо долгого касания (BJ2 р.25): растёт вокруг пальца, после срабатывания замкнуто.
function drawRing() {
  const r = touch.ring();
  if (!r) return;
  view.overlay((g, k, box) => {
    const x = (r.x - box.left) * k;
    const y = (r.y - box.top) * k;
    const R = touch.RING_R * k;
    g.lineWidth = 4 * k;
    g.strokeStyle = "rgba(0, 0, 0, 0.45)";
    g.beginPath();
    g.arc(x, y, R, 0, Math.PI * 2);
    g.stroke();
    g.strokeStyle = "rgba(224, 187, 114, 0.95)";   // латунь интерфейса
    g.beginPath();
    g.arc(x, y, R, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * r.p);
    g.stroke();
  });
}

play.addEventListener("click", start);

view.canvas.tabIndex = 0;

// Ввод. Мышь — как прежде: щелчок на нажатии, правая кнопка — осмотр и «назад». Палец (и перо) —
// через распознаватель жестов touch.js: касание — левый щелчок на отпускании, удержание — правый.
// Сенсорный режим включается первым касанием и выключается движением мыши: на ноутбуке с
// сенсорным экраном работают оба способа, подписи («Щелчок» / «Коснитесь») — по последнему.
let touchMode = platform.TOUCH;
function setTouchMode(v) {
  touchMode = v;
  view.setTouchDevice(platform.TOUCH || v);
  game.setTouch(v);
  dialog.setTouch(v);
}
setTouchMode(platform.TOUCH);

function tap(x, y, button) {
  if (!scene) return;
  audio.unlock();
  const p = view.toWorld(x, y);
  if (button === 2) platform.haptic();
  if (scene.pointerMove) scene.pointerMove(p);
  scene.pointerDown(p, button);
  // у пальца нет наведения: подсветка того, что было под ним, не должна застывать
  if (scene.pointerMove) scene.pointerMove(null);
}
touch.init(tap);

const fingers = new Set();
const isTouch = (e) => e.pointerType === "touch" || e.pointerType === "pen";

view.canvas.addEventListener("pointermove", (e) => {
  if (isTouch(e)) {
    if (fingers.size === 1) touch.moved(e.clientX, e.clientY);
    if (scene && scene.touchMove) scene.touchMove(e);
    return;
  }
  if (touchMode) setTouchMode(false);
  if (scene) scene.pointerMove(view.toWorld(e.clientX, e.clientY));
});
view.canvas.addEventListener("pointerdown", (e) => {
  if (isTouch(e)) {
    e.preventDefault();
    if (!touchMode) setTouchMode(true);
    fingers.add(e.pointerId);
    try { view.canvas.setPointerCapture(e.pointerId); } catch (err) { /* без захвата */ }
    // второй палец — щипок (увеличение бумаг), не касание
    if (fingers.size === 1) touch.pressed(e.clientX, e.clientY);
    else touch.cancel();
    if (scene && scene.touchDown) scene.touchDown(e, fingers.size);
    return;
  }
  if (e.button !== 0 && e.button !== 2) return;
  audio.unlock();
  if (scene) scene.pointerDown(view.toWorld(e.clientX, e.clientY), e.button);
});
function fingerUp(e, cancelled) {
  if (!isTouch(e)) return;
  const was = fingers.size;
  fingers.delete(e.pointerId);
  if (scene && scene.touchUp) scene.touchUp(e, fingers.size);
  if (was === 1 && !cancelled) touch.released(e.clientX, e.clientY);
  else touch.cancel();
}
view.canvas.addEventListener("pointerup", (e) => fingerUp(e, false));
view.canvas.addEventListener("pointercancel", (e) => fingerUp(e, true));
view.canvas.addEventListener("contextmenu", (e) => e.preventDefault());
window.addEventListener("keydown", (e) => {
  if (scene && scene.key(e)) e.preventDefault();
});

// Для автотестов (Playwright): раскладка и состояние в координатах мира 1920×1080.
window.__bj3 = {
  toScreen: (x, y) => view.toScreen(x, y),
  rotated: () => view.rotated(),
  uiScale: () => view.uiScale(),
  touchMode: () => touchMode,
  platform: () => ({ touch: platform.TOUCH, ios: platform.IOS, standalone: platform.STANDALONE, telegram: !!platform.telegram(), cloud: cloud.available() }),
  buttons: () => title.getButtons(),
  settings: () => title.getSettings(),
  started: () => scene !== null,
  scene: () => (scene === game ? "game" : scene === title ? "title" : null),
  audio: () => audio.status(),
  game: () => game.debug(),
};

boot().catch(fail);
