// Сенсорный ввод — распознаватель жестов касания, перенос src/touch.lua из BJ2 (р.25).
// Правой кнопки, наведения и клавиатуры у пальца нет, поэтому жест переводится в щелчки игры:
//   короткое касание                   → левый щелчок, на отпускании;
//   удержание HOLD с без сдвига        → правый щелчок (осмотр, «назад», описание предмета) —
//                                        сразу по истечении, пока палец ещё на экране
//                                        (как меню по долгому нажатию на телефоне);
//   палец уехал дальше SLOP            → жест отменён, щелчков нет.
// Щелчок уходит в точку, где палец КОСНУЛСЯ экрана. Мышь сюда не попадает (main.js разбирает
// pointerType): у мыши щелчок на нажатии, без задержек.
//
// Модуль — чистый JS без браузера: его гоняет юнит-тест tools/web/test_touch.mjs под node.

export const HOLD = 0.45;       // с: удержание, которое считается правым щелчком
export const SLOP = 18;         // точек экрана: сдвиг дальше — уже не касание и не удержание
export const RING_DELAY = 0.2;  // с: кольцо не мигает на обычном касании
export const RING_R = 30;       // точек экрана: радиус кольца — шире подушечки пальца

let gest = null;                // {x, y, t, done, fired}
let emit = () => {};

// fn(x, y, button): точка окна и кнопка игры (0 — левая, 2 — правая)
export function init(fn) {
  emit = fn;
}

function far(g, x, y) {
  const dx = x - g.x;
  const dy = y - g.y;
  return dx * dx + dy * dy > SLOP * SLOP;
}

export function pressed(x, y) {
  gest = { x, y, t: 0, done: false, fired: false };
}

export function moved(x, y) {
  const g = gest;
  if (g && !g.done && far(g, x, y)) g.done = true;
}

export function released(x, y) {
  const g = gest;
  gest = null;
  if (!g || g.done) return;
  // палец уехал, а событий сдвига не было (их может и не быть) — тоже не касание
  if (far(g, x, y)) return;
  emit(g.x, g.y, 0);
}

// Второй палец, системный жест, уход со страницы — жест отменён без щелчков.
export function cancel() {
  gest = null;
}

export function active() {
  return gest !== null;
}

export function update(dt) {
  const g = gest;
  if (!g || g.done) return;
  g.t += dt;
  if (g.t >= HOLD) {
    g.done = true;
    g.fired = true;
    emit(g.x, g.y, 2);
  }
}

// Кольцо удержания: {x, y, p} — точка окна и доля 0..1, либо null. После срабатывания кольцо
// замкнуто, пока палец на экране: игрок видит, что удержание засчитано; отменённый сдвигом жест
// кольца не рисует.
export function ring() {
  const g = gest;
  if (!g) return null;
  if (g.fired) return { x: g.x, y: g.y, p: 1 };
  if (g.done || g.t < RING_DELAY) return null;
  return { x: g.x, y: g.y, p: Math.min(1, (g.t - RING_DELAY) / (HOLD - RING_DELAY)) };
}
