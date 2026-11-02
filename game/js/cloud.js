// Сохранение в облаке Telegram (CloudStorage, Bot API 6.9+): только внутри Telegram. Главная
// копия партии — по-прежнему в браузере (state.js, основная и запасная); облако — зеркало, чтобы
// игра продолжалась с другого телефона или с компьютера, а потеря данных встроенного браузера
// Telegram не стирала прогресс.
//
// Ограничения облака: значение — до 4096 знаков, ключи — латиница, цифры, «_» и «-». Партия
// режется на куски по CHUNK знаков. Пишем по очереди в две ячейки (a/b): сначала куски в
// свободную, потом заголовок {t, slot, n} — оборванная запись оставляет целой прежнюю копию.
// t — время сохранения (мс); при запуске побеждает более поздняя копия, облачная или местная.

import { telegram, tgAt } from "./platform.js";
import * as store from "./store.js";

const CHUNK = 4000;
const META = "bj3_meta";
const DELAY = 1500;       // мс: сохранения подряд (каждое действие) сливаются в одну запись

let timer = null;
let pending = null;       // {t, save}
let writing = false;

function cs() {
  const tg = telegram();
  return tg && tgAt("6.9") && tg.CloudStorage ? tg.CloudStorage : null;
}

export function available() {
  return !!cs();
}

const call = (fn) => new Promise((resolve) => {
  try { fn((err, v) => resolve(err ? null : v)); } catch (e) { resolve(null); }
});

async function readMeta(c) {
  const raw = await call((cb) => c.getItem(META, cb));
  try { return raw ? JSON.parse(raw) : null; } catch (e) { return null; }
}

async function readCloud(c) {
  const meta = await readMeta(c);
  if (!meta || !meta.t) return null;
  if (!meta.n) return { t: meta.t, save: null };   // новая игра: облачная партия стёрта
  const keys = Array.from({ length: meta.n }, (_, i) => `bj3_${meta.slot}_${i}`);
  const vals = await call((cb) => c.getItems(keys, cb));
  if (!vals) return null;
  try {
    return { t: meta.t, save: JSON.parse(keys.map((k) => vals[k] || "").join("")) };
  } catch (e) {
    return null;
  }
}

async function writeCloud(c, rec) {
  const old = await readMeta(c);
  const slot = old && old.slot === "a" ? "b" : "a";
  const text = rec.save == null ? "" : JSON.stringify(rec.save);
  const n = text ? Math.ceil(text.length / CHUNK) : 0;
  for (let i = 0; i < n; i++) {
    const ok = await call((cb) => c.setItem(`bj3_${slot}_${i}`, text.slice(i * CHUNK, (i + 1) * CHUNK), cb));
    if (!ok) return false;
  }
  return !!(await call((cb) => c.setItem(META, JSON.stringify({ t: rec.t, slot, n }), cb)));
}

async function flush() {
  timer = null;
  const c = cs();
  if (!c || !pending || writing) return;
  const rec = pending;
  pending = null;
  writing = true;
  const ok = await writeCloud(c, rec);
  writing = false;
  if (!ok) console.warn("облако Telegram: сохранение не записалось");
  if (pending) schedule();
}

function schedule(now = false) {
  if (timer) clearTimeout(timer);
  timer = setTimeout(flush, now ? 0 : DELAY);
}

// state.js: партия записана (save == null — стёрта новой игрой).
export function push(t, save) {
  if (!cs()) return;
  pending = { t, save };
  schedule();
}

// Вкладку свернули или Telegram закрывают — пишем сразу, не дожидаясь паузы.
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden" && pending) schedule(true);
});

// При запуске: облачная копия новее местной — она становится местной (прежняя местная —
// запасной); местная новее — отправляется в облако. Не дольше TIMEOUT мс.
export async function sync(timeout = 4000) {
  const c = cs();
  if (!c) return "нет облака";
  const cloud = await Promise.race([readCloud(c), new Promise((r) => setTimeout(() => r("timeout"), timeout))]);
  if (cloud === "timeout") return "облако не ответило";
  const localT = store.read("save.t") || 0;
  const local = store.read("save");
  if (cloud && cloud.t > localT) {
    if (local) store.write("save.bak", local);
    store.write("save", cloud.save);
    if (cloud.save == null) store.write("save.bak", null);
    store.write("save.t", cloud.t);
    return "взято из облака";
  }
  if (localT && (!cloud || localT > cloud.t)) {
    pending = { t: localT, save: local };
    schedule(true);
    return "отправлено в облако";
  }
  return "совпадает";
}
