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

function flagsOf(n) {
  const d = acts[n];
  return d ? new Set(d.flags) : null;
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
  game.init(ui, { onExit: toTitle });
  game.onSettings((k) => (k === "get" ? title.getSettings() : title.toggleSetting(k)));
  await Promise.all(FONTS.map((f) => document.fonts.load(f)));
  await assets.loadImages(TITLE_IMAGES, progress);
  if (!store.write("probe", 1)) status.textContent = ui.storage_off;
  else status.textContent = `Сборка ${manifest.build}`;
  play.disabled = false;
  play.focus();
  console.log("BJ3 READY");
}

function start() {
  audio.unlock();
  audio.preload(["ui_click"]);
  shell.classList.add("hidden");
  toTitle();
  view.canvas.focus();
  last = performance.now();
  requestAnimationFrame(frame);
}

function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  if (scene && scene.update) scene.update(dt);
  view.begin();
  if (scene) scene.draw(now);
  view.end();
  requestAnimationFrame(frame);
}

play.addEventListener("click", start);

view.canvas.tabIndex = 0;
view.canvas.addEventListener("pointermove", (e) => {
  if (scene) scene.pointerMove(view.toWorld(e.clientX, e.clientY));
});
view.canvas.addEventListener("pointerdown", (e) => {
  if (e.button !== 0 && e.button !== 2) return;
  audio.unlock();
  if (scene) scene.pointerDown(view.toWorld(e.clientX, e.clientY), e.button);
});
view.canvas.addEventListener("contextmenu", (e) => e.preventDefault());
window.addEventListener("keydown", (e) => {
  if (scene && scene.key(e)) e.preventDefault();
});

// Для автотестов (Playwright): раскладка и состояние в координатах мира 1920×1080.
window.__bj3 = {
  buttons: () => title.getButtons(),
  settings: () => title.getSettings(),
  started: () => scene !== null,
  scene: () => (scene === game ? "game" : scene === title ? "title" : null),
  audio: () => audio.status(),
  game: () => game.debug(),
};

boot().catch(fail);
