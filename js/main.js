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
const actLoads = {};  // идущие загрузки: акт → Promise (заблаговременная и настоящая не дублируются)
let last = 0;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function progress(done, total) {
  fill.style.width = `${Math.round((done / Math.max(1, total)) * 100)}%`;
}

// Игра не загрузилась. До «Играть» сообщение — на карточке загрузки; после неё карточка скрыта,
// поэтому на титуле оно идёт плашкой, иначе игрок не увидел бы ничего.
function fail(err) {
  console.error(err);
  const msg = "Не удалось загрузить игру. Обновите страницу.";
  status.textContent = msg;
  if (scene === title) title.showToast(msg, 8);
}

// Данные акта. Не загрузились — следующий вызов пробует снова (сбой в памяти не остаётся).
function actData(n) {
  if (acts[n]) return Promise.resolve(acts[n]);
  if (!actLoads[n]) {
    actLoads[n] = fetch(`data/act${n}.json`, { cache: "no-cache" })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`акт ${n}: ответ сервера ${r.status}`))))
      .then((d) => { acts[n] = d; return d; })
      .finally(() => { delete actLoads[n]; });
  }
  return actLoads[n];
}

// Следующий акт — заранее, пока идёт текущий: переход между актами не должен зависеть от сети в
// ту самую секунду (на телефоне она пропадает). Не вышло — не беда, на переходе загрузим снова.
function prefetchAct(n) {
  if ((manifest.acts || [1]).includes(n)) actData(n).catch(() => {});
}

// Флаги, которые знает сборка к акту n: накопительно по актам 1..n (GDD §12) — флаг Акта I,
// которого нет в словаре Акта II, при загрузке сейва Акта II не теряется.
function flagsOf(n) {
  if (!acts[n]) return null;
  const s = new Set();
  for (const [k, d] of Object.entries(acts)) if (Number(k) <= n) d.flags.forEach((f) => s.add(f));
  return s;
}

// Конец акта → следующий акт с тем же состоянием (его готовит game.js). Данные не загрузились —
// пробуем снова сами, сколько понадобится: игрок на чёрном экране перехода видит строку «ждём
// сеть» (game.transitStalled), а не вечную темноту. Сохранение уже записано: закрыть игру можно.
async function nextAct(n, make) {
  let data = null;
  for (let wait = 1500; !data; wait = Math.min(wait * 2, 12000)) {
    try {
      data = await actData(n);
    } catch (e) {
      console.warn(`акт ${n} не загрузился, повтор через ${wait} мс:`, e);
      game.transitStalled(true);
      await sleep(wait);
    }
  }
  scene = game;
  prefetchAct(n + 1);
  await game.start(data, make(data), { newAct: true });
}

async function startGame(opts = {}) {
  let st = null;
  if (opts.continue) {
    // нужны акты до сохранённого включительно (флаги копятся по актам); остальные — по ходу игры
    const upto = Math.max(1, ...["save", "save.bak"].map((k) => {
      const raw = store.read(k);
      return raw && typeof raw.act === "number" ? raw.act : 1;
    }));
    for (const n of manifest.acts || [1]) if (n <= upto) await actData(n);
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
  prefetchAct(n + 1);
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

// Следующий кадр заказывается первым: ошибка в одном кадре не должна останавливать игру навсегда
// (без этого экран замирал бы на последнем кадре до перезагрузки страницы). Ошибка пишется в
// консоль один раз на каждое новое сообщение — её ловят дымовой тест и автопрохождение.
let frameError = null;
function frame(now) {
  requestAnimationFrame(frame);
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  try {
    touch.update(dt);
    if (scene && scene.update) scene.update(dt);
    view.begin();
    try {
      if (scene) scene.draw(now);
    } finally {
      view.end();   // область отсечения кадра снимается и после ошибки, иначе они копятся
    }
    drawRing();
    // «назад» Telegram и браузера — как Esc, пока в игре есть куда возвращаться
    const inGame = scene === game;
    platform.setInGame(inGame);
    platform.setBack(inGame && game.canEscape(), () => { if (scene === game) game.escape(); });
  } catch (e) {
    if (String(e) !== frameError) {
      frameError = String(e);
      console.error("ошибка кадра:", e);
    }
  }
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
