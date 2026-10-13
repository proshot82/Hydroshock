// Запуск: манифест и строки интерфейса → шрифты и картинки титула (с полосой
// загрузки) → кнопка «Играть» → звук разрешён, титул. Дальше — цикл кадров.

import * as view from "./view.js";
import * as assets from "./assets.js";
import * as audio from "./audio.js";
import * as title from "./title.js";

const shell = document.getElementById("shell");
const status = document.getElementById("status");
const fill = document.getElementById("bar-fill");
const play = document.getElementById("play");

const TITLE_IMAGES = ["ui/bg_title", "ui/logo_title"];
const FONTS = ['400 34px "PT Sans"', '700 44px "PT Sans"'];

let scene = null;   // текущая сцена: пока только титул

function progress(done, total) {
  fill.style.width = `${Math.round((done / Math.max(1, total)) * 100)}%`;
}

function fail(err) {
  console.error(err);
  status.textContent = "Не удалось загрузить игру. Обновите страницу.";
}

async function boot() {
  const m = await assets.loadManifest();
  const ui = await (await fetch("data/ui.json", { cache: "no-cache" })).json();
  title.init(ui, {
    // Шаг 1 сборки: самой игры ещё нет — титул сообщает об этом и остаётся.
    onStart: () => title.showToast("Акт I появится на следующем шаге сборки."),
  });
  await Promise.all(FONTS.map((f) => document.fonts.load(f)));
  await assets.loadImages(TITLE_IMAGES, progress);
  status.textContent = `Сборка ${m.build}`;
  play.disabled = false;
  play.focus();
  console.log("BJ3 READY");
}

function start() {
  audio.unlock();
  audio.preload(["ui_click"]);
  shell.classList.add("hidden");
  scene = title;
  title.enter();
  view.canvas.focus();
  requestAnimationFrame(frame);
}

function frame(now) {
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
  if (e.button !== 0) return;
  audio.unlock();
  if (scene) scene.pointerDown(view.toWorld(e.clientX, e.clientY));
});
view.canvas.addEventListener("contextmenu", (e) => e.preventDefault());
window.addEventListener("keydown", (e) => {
  if (scene && scene.key(e)) e.preventDefault();
});

// Для автотестов (Playwright): раскладка кнопок и настройки в координатах мира.
window.__bj3 = {
  buttons: () => title.getButtons(),
  settings: () => title.getSettings(),
  started: () => scene !== null,
  audio: () => audio.status(),
};

boot().catch(fail);
