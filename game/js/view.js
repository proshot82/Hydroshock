// Холст игры: мир 1920×1080 вписывается в окно любого размера с чёрными полями
// (letterbox, как в BJ2 main.lua). Буфер холста — в настоящих пикселях экрана
// (с учётом devicePixelRatio), поэтому картинка чёткая и на ретине.

export const W = 1920;
export const H = 1080;

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d", { alpha: false });

let scale = 1;
let ox = 0;
let oy = 0;
let dpr = 1;

export function resize() {
  dpr = Math.min(window.devicePixelRatio || 1, 3);
  const cw = Math.max(1, Math.round(canvas.clientWidth * dpr));
  const ch = Math.max(1, Math.round(canvas.clientHeight * dpr));
  if (canvas.width !== cw || canvas.height !== ch) {
    canvas.width = cw;
    canvas.height = ch;
  }
  scale = Math.min(cw / W, ch / H);
  ox = Math.floor((cw - W * scale) / 2);
  oy = Math.floor((ch - H * scale) / 2);
}

// Начало кадра: чистим поля и переходим в координаты мира.
export function begin() {
  resize();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.setTransform(scale, 0, 0, scale, ox, oy);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
  ctx.globalAlpha = 1;
  // мир не вылезает на поля
  ctx.beginPath();
  ctx.rect(0, 0, W, H);
  ctx.clip();
}

export function end() {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

// Точка окна (CSS-пиксели события мыши/пальца) → точка мира; null — на полях.
export function toWorld(clientX, clientY) {
  const r = canvas.getBoundingClientRect();
  const x = ((clientX - r.left) * dpr - ox) / scale;
  const y = ((clientY - r.top) * dpr - oy) / scale;
  if (x < 0 || y < 0 || x >= W || y >= H) return null;
  return { x, y };
}

export function setCursor(name) {
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
