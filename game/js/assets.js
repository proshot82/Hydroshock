// Загрузка ассетов по манифесту сборки (data/manifest.json): картинки — WebP,
// звук — OGG. Картинки грузятся по запросу и кэшируются; экраны, которые
// понадобятся скоро, можно запросить заранее (preload), чтобы смена кадра
// не ждала сети.

let manifest = null;
const images = new Map();   // имя → { img, promise }

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
  return e && e.img.complete && e.img.naturalWidth ? e.img : null;
}

export function loadImage(name) {
  let e = images.get(name);
  if (e) return e.promise;
  const file = manifest && manifest.gfx[name];
  if (!file) return Promise.reject(new Error(`нет в манифесте: ${name}`));
  const img = new Image();
  img.decoding = "async";
  const promise = new Promise((resolve, reject) => {
    img.onload = () => (img.decode ? img.decode().catch(() => {}) : Promise.resolve()).then(() => resolve(img));
    img.onerror = () => reject(new Error(`не загрузилась картинка: ${name}`));
  });
  img.src = "assets/gfx/" + file;
  e = { img, promise };
  images.set(name, e);
  return promise;
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

export function audioUrl(name) {
  const file = manifest && manifest.audio[name];
  return file ? "assets/audio/" + file : null;
}
