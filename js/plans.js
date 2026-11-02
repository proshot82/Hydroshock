// Плёнки P05 (Акт II): три плана здания на подсвеченном стекле, подписи — по меткам
// docs/assets/plans_markers.json (собирает tools/data/gen_design.py). Тот же расчёт, что у пробы
// приёмки tools/assets/plans_preview.py: плёнка сдвигается на tx, ty и поворачивается на rot
// градусов против часовой вокруг точки cx, cy; подпись — справа от метки (или как задано side).

import { image } from "./assets.js";

const SIZE = { w: 1400, h: 980 };
const FONT_PX = 26;
const cache = new Map();

function labelAt(g, lab) {
  const w = g.measureText(lab.t).width;
  const { x, y } = lab;
  switch (lab.side) {
    case "a": return [x - w / 2, y - 50];
    case "bl": return [x - w + 14, y + 18];
    case "b": return [x - w / 2, y + 18];
    case "b2": return [x - w / 2, y + 56];
    default: return x + 20 + w < 1390 ? [x + 20, y - 16] : [x - 20 - w, y - 16];
  }
}

// Холст 1400×980 со стопкой плёнок; null, пока картинки не загружены.
export function render(films) {
  const key = JSON.stringify(films.map((f) => [f.img, f.tx, f.ty, f.rot]));
  if (cache.has(key)) return cache.get(key);
  const imgs = films.map((f) => image(f.img));
  if (imgs.some((i) => !i)) return null;
  const c = document.createElement("canvas");
  c.width = SIZE.w;
  c.height = SIZE.h;
  const g = c.getContext("2d");
  films.forEach((f, i) => {
    g.save();
    g.translate(f.cx + f.tx, f.cy + f.ty);
    g.rotate((-f.rot * Math.PI) / 180);
    g.translate(-f.cx, -f.cy);
    g.drawImage(imgs[i], 0, 0);
    g.font = `${f.font[1]} ${FONT_PX}px "${f.font[0]}"`;
    g.fillStyle = f.ink;
    g.textBaseline = "top";
    g.textAlign = "left";
    for (const lab of f.labels) {
      const [tx, ty] = labelAt(g, lab);
      g.fillText(lab.t, tx, ty);
    }
    g.restore();
  });
  cache.set(key, c);
  return c;
}

// Слой «планы:…» на экране: на стекле во весь экран (box) или на стекле зума (onto — три угла).
export function draw(ctx, lay) {
  const c = render(lay.plans);
  if (lay.box) {
    const box = image(lay.box);
    if (box) ctx.drawImage(box, lay.x, lay.y, SIZE.w, SIZE.h);
    if (c) ctx.drawImage(c, lay.x, lay.y);
    return;
  }
  if (!c || !lay.onto) return;
  const [p0, p1, p2] = lay.onto;
  ctx.save();
  ctx.transform((p1[0] - p0[0]) / SIZE.w, (p1[1] - p0[1]) / SIZE.w,
    (p2[0] - p0[0]) / SIZE.h, (p2[1] - p0[1]) / SIZE.h, p0[0], p0[1]);
  ctx.globalAlpha = 0.9;
  ctx.drawImage(c, 0, 0);
  ctx.restore();
}

// Картинки, которые нужны слою (для предзагрузки).
export function images(lay) {
  return [...(lay.box ? [lay.box] : []), ...lay.plans.map((f) => f.img)];
}
