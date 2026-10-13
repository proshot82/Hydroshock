// Звук через Web Audio. Браузер разрешает звук только после нажатия игрока,
// поэтому контекст создаётся в unlock(), который вызывается из обработчика
// кнопки «Играть». Музыка — петли со сменой через кроссфейд 1,5 с (как в BJ2),
// эффекты — короткие буферы. Формат: OGG Vorbis, где браузер его не играет
// (старые Safari) — копия в M4A (AAC), её кладёт сборка.

import { getManifest } from "./assets.js";

const FADE = 1.5;          // с, кроссфейд музыки (BJ2)
const MUS_MASTER = 0.85;   // общий множитель музыки (BJ2)

let ac = null;
let musicBus = null;
let sfxBus = null;
let useOgg = true;
const buffers = new Map();  // имя → Promise<AudioBuffer>
let current = null;         // { name, src, gain }
let wanted = null;          // какая музыка должна звучать (даже если выключена)
let settings = { music: true, sound: true };

export function unlock() {
  if (ac) {
    if (ac.state === "suspended") ac.resume();
    return;
  }
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!Ctx) return;
  ac = new Ctx();
  musicBus = ac.createGain();
  sfxBus = ac.createGain();
  musicBus.connect(ac.destination);
  sfxBus.connect(ac.destination);
  const probe = document.createElement("audio");
  useOgg = !!probe.canPlayType && probe.canPlayType('audio/ogg; codecs="vorbis"') !== "";
  applySettings(settings);
  // вкладка в фоне — тишина; вернулась — продолжаем
  document.addEventListener("visibilitychange", () => {
    if (!ac) return;
    if (document.hidden) ac.suspend(); else ac.resume();
  });
}

function url(name) {
  const m = getManifest();
  const e = m && m.audio[name];
  if (!e) return null;
  return "assets/audio/" + (useOgg ? e.ogg : e.m4a || e.ogg);
}

function buffer(name) {
  let p = buffers.get(name);
  if (p) return p;
  const u = url(name);
  if (!ac || !u) return Promise.resolve(null);
  p = fetch(u)
    .then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(r.status))))
    .then((data) => new Promise((res, rej) => ac.decodeAudioData(data, res, rej)))
    .catch((err) => {
      console.warn(`звук ${name} не загрузился:`, err);
      buffers.delete(name);
      return null;
    });
  buffers.set(name, p);
  return p;
}

export function preload(names) {
  names.forEach((n) => buffer(n));
}

export function applySettings(s) {
  settings = { ...settings, ...s };
  if (!ac) return;
  const t = ac.currentTime;
  musicBus.gain.cancelScheduledValues(t);
  musicBus.gain.setTargetAtTime(settings.music ? MUS_MASTER : 0, t, 0.15);
  sfxBus.gain.cancelScheduledValues(t);
  sfxBus.gain.setValueAtTime(settings.sound ? 1 : 0, t);
}

// Сменить фоновую музыку (null — тишина). Та же тема не перезапускается.
export async function music(name) {
  wanted = name;
  if (!ac) return;
  if (current && current.name === name) return;
  const old = current;
  current = null;
  if (old) fadeOut(old);
  if (!name) return;
  const buf = await buffer(name);
  if (!buf || wanted !== name || (current && current.name === name)) return;
  const src = ac.createBufferSource();
  src.buffer = buf;
  src.loop = true;
  const gain = ac.createGain();
  const t = ac.currentTime;
  gain.gain.setValueAtTime(0, t);
  gain.gain.linearRampToValueAtTime(1, t + (old ? FADE : 0.05));
  src.connect(gain).connect(musicBus);
  src.start();
  current = { name, src, gain };
}

function fadeOut(m) {
  const t = ac.currentTime;
  m.gain.gain.cancelScheduledValues(t);
  m.gain.gain.setValueAtTime(m.gain.gain.value, t);
  m.gain.gain.linearRampToValueAtTime(0, t + FADE);
  m.src.stop(t + FADE + 0.05);
}

// Эффект; возвращает Promise, который ждёт загрузки (длительность — из файла).
export async function sfx(name, volume = 1) {
  if (!ac || !settings.sound) return;
  const buf = await buffer(name);
  if (!buf) return;
  const src = ac.createBufferSource();
  src.buffer = buf;
  const gain = ac.createGain();
  gain.gain.value = volume;
  src.connect(gain).connect(sfxBus);
  src.start();
}

export function isUnlocked() {
  return !!ac;
}

// Для автотестов: состояние контекста, что звучит, какой формат выбран.
export function status() {
  return { state: ac ? ac.state : "нет", music: current ? current.name : null, format: useOgg ? "ogg" : "m4a" };
}
