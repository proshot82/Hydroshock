// Хранилище браузера. Любое обращение может бросить исключение (приватное окно,
// запрет сайтов, переполнение) — тогда игра работает без него, а не падает.
// Сохранение партии появится на шаге ядра: две копии (основная и запасная),
// как atomic_write + .bak в BJ2.

const PREFIX = "bj3.";

export function read(key, fallback = null) {
  try {
    const raw = window.localStorage.getItem(PREFIX + key);
    return raw == null ? fallback : JSON.parse(raw);
  } catch (e) {
    return fallback;
  }
}

export function write(key, value) {
  try {
    window.localStorage.setItem(PREFIX + key, JSON.stringify(value));
    return true;
  } catch (e) {
    return false;
  }
}

export function hasSave() {
  return read("save") != null || read("save.bak") != null;
}

const DEFAULT_SETTINGS = { music: true, sound: true, fasttext: false };

export function loadSettings() {
  return { ...DEFAULT_SETTINGS, ...(read("settings") || {}) };
}

export function saveSettings(s) {
  return write("settings", s);
}
