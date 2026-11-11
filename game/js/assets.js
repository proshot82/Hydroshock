// Загрузка ассетов по манифесту сборки (data/manifest.json): картинки — WebP,
// звук — OGG. Картинки грузятся по запросу и кэшируются; экраны, которые
// понадобятся скоро, можно запросить заранее (preload), чтобы смена кадра
// не ждала сети.

let manifest = null;
const images = new Map();   // имя → { img, promise, used }
// Сколько картинок держать в памяти: распакованный кадр 1920×1080 — около 8 МБ, а за игру их
// сотни. Сверх предела выбрасываются те, к которым дольше всего не обращались (их перезагрузят
// из кэша браузера, если понадобятся снова). Без предела память браузера растёт до гигабайтов,
// и через несколько минут игра начинает тормозить.
const KEEP = 48;
// Картинка не загрузилась (сеть пропала, сервер ответил ошибкой) — пробуем снова, но не чаще, чем
// раз в RETRY_MS: отрисовка просит недостающую картинку в каждом кадре.
const RETRY_MS = 3000;
const pinned = new Set(["ui/bg_title", "ui/logo_title"]);

export async function loadManifest() {
  const r = await fetch("data/manifest.json", { cache: "no-cache" });
  if (!r.ok) throw new Error(`манифест: ${r.status}`);
  manifest = await r.json();
  return manifest;
}

export function getManifest() {
  return manifest;
}

// Имя в игре — путь ассета без расширения: "ui/bg_title", "rooms/room_w1".
export function image(name) {
  const e = images.get(name);
  if (!e) return null;
  e.used = performance.now();
  return e.img.complete && e.img.naturalWidth ? e.img : null;
}

function evict() {
  if (images.size <= KEEP) return;
  const old = [...images.entries()].filter(([n, e]) => !pinned.has(n) && e.img.complete)
    .sort((a, b) => a[1].used - b[1].used);
  for (const [n, e] of old.slice(0, images.size - KEEP)) {
    e.img.onload = e.img.onerror = null;
    e.img.src = "";            // отпустить распакованную картинку
    images.delete(n);
  }
}

export function loadImage(name) {
  let e = images.get(name);
  if (e && !(e.failed && performance.now() - e.failed > RETRY_MS)) return e.promise;
  const file = manifest && manifest.gfx[name];
  if (!file) return Promise.reject(new Error(`нет в манифесте: ${name}`));
  const img = new Image();
  img.decoding = "async";
  e = { img, promise: null, used: performance.now(), failed: 0 };
  const entry = e;
  e.promise = new Promise((resolve, reject) => {
    img.onload = () => resolve(img);
    img.onerror = () => {
      entry.failed = performance.now();
      reject(new Error(`не загрузилась картинка: ${name}`));
    };
  });
  img.src = "assets/gfx/" + file;
  images.set(name, e);
  evict();
  return e.promise;
}

// Загрузка пачки с прогрессом: onProgress(готово, всего).
export async function loadImages(names, onProgress) {
  let done = 0;
  onProgress && onProgress(0, names.length);
  await Promise.all(names.map((n) => loadImage(n).then(() => {
    done += 1;
    onProgress && onProgress(done, names.length);
  })));
}
