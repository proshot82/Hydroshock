// Состояние партии и сохранение (GDD §12, handoff §13).
// Переживает сохранение: флаги графов (накопительно), акт, вид, положение тележки,
// счётчики показов слотов и проб/звонков, советы Предка, прочитанные документы.
// Хранилище — браузер; две копии (основная и запасная), как atomic_write + .bak в BJ2.

import * as store from "./store.js";

export const SAVE_VERSION = 1;

export class State {
  constructor(act, startFlags) {
    this.act = act;
    this.flags = new Set(startFlags);
    this.pos = act === 1 ? "room" : null;
    this.n = {};          // показы слотов
    this.c = {};          // счётчики probe, call
    this.view = null;
    this.docs = [];       // прочитанные документы по порядку
    this.hint = { level: {}, lock: false, n: 0 };
    this.ended = false;   // акт закончен (заставка конца)
  }

  shown(slot) {
    return (this.n[slot] || 0) > 0;
  }

  toJSON() {
    return {
      version: SAVE_VERSION, act: this.act, flags: [...this.flags].sort(), pos: this.pos,
      n: this.n, c: this.c, view: this.view, docs: this.docs, hint: this.hint, ended: this.ended,
    };
  }

  static fromJSON(o, knownFlags) {
    if (!o || o.version !== SAVE_VERSION || typeof o.act !== "number") return null;
    const s = new State(o.act, []);
    // вычистка: имена, которых нет в данных этой сборки, не тащим (как sanitize_state в BJ2)
    s.flags = new Set((o.flags || []).filter((f) => knownFlags.has(f)));
    s.pos = typeof o.pos === "string" ? o.pos : null;
    s.n = typeof o.n === "object" && o.n ? { ...o.n } : {};
    s.c = typeof o.c === "object" && o.c ? { ...o.c } : {};
    s.view = typeof o.view === "string" ? o.view : null;
    s.docs = Array.isArray(o.docs) ? o.docs.filter((d) => typeof d === "string") : [];
    s.hint = o.hint && typeof o.hint === "object"
      ? { level: { ...(o.hint.level || {}) }, lock: !!o.hint.lock, n: o.hint.n | 0 }
      : { level: {}, lock: false, n: 0 };
    s.ended = !!o.ended;
    return s;
  }
}

// Записать партию: прежняя основная копия становится запасной.
export function save(state) {
  const prev = store.read("save");
  if (prev) store.write("save.bak", prev);
  return store.write("save", state.toJSON());
}

// Прочитать партию: основная, при порче — запасная. {state, restored} или null.
export function load(knownFlagsByAct) {
  const tryOne = (raw) => {
    if (!raw) return null;
    const flags = knownFlagsByAct(raw.act);
    return flags ? State.fromJSON(raw, flags) : null;
  };
  const main = tryOne(store.read("save"));
  if (main) return { state: main, restored: false };
  const bak = tryOne(store.read("save.bak"));
  if (bak) return { state: bak, restored: true };
  return null;
}

export function clear() {
  store.write("save", null);
  store.write("save.bak", null);
}
