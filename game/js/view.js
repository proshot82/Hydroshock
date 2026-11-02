// Холст игры: мир 1920×1080 вписывается в окно любого размера с чёрными полями
// (letterbox, как в BJ2 main.lua). Буфер холста — в настоящих пикселях экрана
// (с учётом devicePixelRatio), поэтому картинка чёткая и на ретине.
//
// Размер холста меряется в каждом кадре, а не по событию resize: встроенный браузер iOS
// (WKWebView — в нём Telegram открывает игру на iPhone) в resize отдаёт неверный размер, верный
// приходит позже без события (WebKit 170595; урок BJ2 №8, р.27).
//
// Кадр «лёжа» (BJ2 р.26): на сенсорном экране, который держат вертикально, мир рисуется
// повёрнутым на 90° по часовой во всю длинную сторону — игрок поворачивает телефон влево и
// играет горизонтально, даже если поворот экрана в телефоне заблокирован. Экран ↔ мир — только
// через toWorld / toScreen.
//
// Крупный интерфейс (uiScale): на маленьком экране кнопки, «При себе», окно реплик и меню
// растут, чтобы текст реплик был не мельче READ_PX настоящих точек экрана, а кнопки — по пальцу.
// На компьютере и планшете множитель 1 — всё как раньше.

export const W = 1920;
export const H = 1080;

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d", { alpha: false });

let scale = 1;
let ox = 0;
let oy = 0;
let dpr = 1;
let rot = false;       // кадр «лёжа»
let cw = 1;            // буфер холста, настоящие пиксели
let ch = 1;
let touchDevice = false;
let ui = 1;

const BODY_PX = 34;    // кегль текста реплик в мире
const READ_PX = 15.5;  // не мельче — точек экрана (CSS px)
const UI_MAX = 1.5;

export function setTouchDevice(v) {
  touchDevice = !!v;
}

export function rotated() {
  return rot;
}

export function resize() {
  dpr = Math.min(window.devicePixelRatio || 1, 3);
  cw = Math.max(1, Math.round(canvas.clientWidth * dpr));
  ch = Math.max(1, Math.round(canvas.clientHeight * dpr));
  if (canvas.width !== cw || canvas.height !== ch) {
    canvas.width = cw;
    canvas.height = ch;
  }
  rot = touchDevice && ch > cw;
  const lw = rot ? ch : cw;   // стороны кадра «как видит игрок»
  const lh = rot ? cw : ch;
  scale = Math.min(lw / W, lh / H);
  ox = Math.floor((lw - W * scale) / 2);
  oy = Math.floor((lh - H * scale) / 2);
  const cssPerWorld = scale / dpr;
  ui = Math.max(1, Math.min(UI_MAX, READ_PX / (BODY_PX * cssPerWorld)));
}

// Множитель интерфейса для этого кадра (1 — компьютер; на телефоне до 1,5).
export function uiScale() {
  return ui;
}

// Поворот «лёжа»: точка кадра (lx, ly) → точка буфера холста.
function base() {
  if (rot) return [0, scale, -scale, 0, cw - oy, ox];   // 90° по часовой
  return [scale, 0, 0, scale, ox, oy];
}

// Начало кадра: чистим поля и переходим в координаты мира.
export function begin() {
  resize();
  ctx.save();   // область отсечения ниже — только на этот кадр (end() её снимает), иначе отсечения копятся
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.setTransform(...base());
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
  ctx.globalAlpha = 1;
  // мир не вылезает на поля
  ctx.beginPath();
  ctx.rect(0, 0, W, H);
  ctx.clip();
}

export function end() {
  ctx.restore();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

// Точка окна (CSS-пиксели события мыши/пальца) → точка мира; null — на полях (raw — без отсечки,
// для щипка, который может начаться и на полях).
export function toWorld(clientX, clientY, raw = false) {
  const r = canvas.getBoundingClientRect();
  let bx = (clientX - r.left) * dpr;   // пиксели буфера
  let by = (clientY - r.top) * dpr;
  if (rot) [bx, by] = [by, cw - bx];   // обратно из «лёжа»
  const x = (bx - ox) / scale;
  const y = (by - oy) / scale;
  if (!raw && (x < 0 || y < 0 || x >= W || y >= H)) return null;
  return { x, y };
}

// Точка мира → точка окна (CSS-пиксели) — для автотестов.
export function toScreen(x, y) {
  const r = canvas.getBoundingClientRect();
  let bx = ox + x * scale;
  let by = oy + y * scale;
  if (rot) [bx, by] = [cw - by, bx];
  return { x: r.left + bx / dpr, y: r.top + by / dpr };
}

// Длина в мире → точки экрана (CSS px): сколько займёт на экране.
export function worldToCss(len) {
  return (len * scale) / dpr;
}

// Рисование поверх мира в точках окна (кольцо долгого касания): fn(ctx, k), k — CSS px → буфер.
export function overlay(fn) {
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  fn(ctx, dpr, canvas.getBoundingClientRect());
  ctx.restore();
}

export function setCursor(name) {
  if (touchDevice) return;
  const css = CURSORS[name] || CURSORS.normal;
  if (canvas.style.cursor !== css) canvas.style.cursor = css;
}

// Курсоры BJ2 (assets/gfx/cursors, 64×64) с горячими точками из BJ2 main.lua.
const CURSORS = {
  normal: 'url("assets/gfx/cursors/cursor_normal.png") 14 6, default',
  act: 'url("assets/gfx/cursors/cursor_act.png") 20 10, pointer',
  move: 'url("assets/gfx/cursors/cursor_move.png") 14 6, pointer',
  zoom: 'url("assets/gfx/cursors/cursor_zoom.png") 22 22, zoom-in',
};

export { canvas, ctx };
