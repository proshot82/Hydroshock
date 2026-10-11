#!/usr/bin/env python3
"""Вклеить перерисованный участок (правка увеличенной вырезки) обратно в кадр базы.

  python tools/assets/patch_region.py БАЗА.png СЫРОЙ_КАДР.png X0,Y0,X1,Y1 ВЫХОД.png [--wide] [--ring N]

Участок X0,Y0–X1,Y1 базы вырезался, увеличивался (×3–×4) и правился генератором. Генератор отдаёт
кадр своей пропорции (обрезка по центру или растяжение) и чуть другого масштаба — подбираются
способ подгонки, масштаб 0,97–1,03 и сдвиг ±8 px по медиане разницы с базой. --wide — масштаб
0,93–1,07 и сдвиг ±16 px (участок правился дважды и «уплыл»). --ring N — сравнивать только
полосу шириной N px по краю участка: если в середине переставлены предметы (стопка бумаг
сдвинута), середина сбивает подгонку, а край участка остался как на базе. ВЫХОД — кадр-вариант
1920×1080 (база с вклеенным участком) для tools/assets/cutout.py.
"""
import argparse

import numpy as np
from PIL import Image


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("raw")
    ap.add_argument("box")
    ap.add_argument("out")
    ap.add_argument("--wide", action="store_true")
    ap.add_argument("--ring", type=int, default=0)
    a = ap.parse_args(argv)
    base = Image.open(a.base).convert("RGB")
    raw = Image.open(a.raw).convert("RGB")
    x0, y0, x1, y1 = map(int, a.box.split(","))
    scales = [round(0.93 + 0.01 * i, 2) for i in range(15)] if a.wide else [0.97, 0.98, 0.99, 1.0, 1.01, 1.02, 1.03]
    sh = 16 if a.wide else 8
    w, h = x1 - x0, y1 - y0
    B = np.asarray(base, float)

    # варианты: сырой кадр растянут целиком в участок, либо обрезан по центру по большей стороне
    rw, rh = raw.size
    cands = {"stretch": raw}
    if rw / rh > w / h:
        nw = round(rh * w / h)
        cands["cropx"] = raw.crop(((rw - nw) // 2, 0, (rw - nw) // 2 + nw, rh))
    else:
        nh = round(rw * h / w)
        cands["cropy"] = raw.crop((0, (rh - nh) // 2, rw, (rh - nh) // 2 + nh))

    def score(p, X, Y):
        pw, ph = p.shape[1], p.shape[0]
        if X < 0 or Y < 0 or X + pw > B.shape[1] or Y + ph > B.shape[0]:
            return None
        d = np.abs(B[Y:Y + ph, X:X + pw] - p).max(2)
        m = np.zeros(d.shape, bool)
        m[10:-10, 10:-10] = True
        if a.ring:
            m[10 + a.ring:-10 - a.ring, 10 + a.ring:-10 - a.ring] = False
        return float(np.median(d[m]))

    best = None
    for name, im in cands.items():
        for s in scales:
            pw, ph = round(w * s), round(h * s)
            p = np.asarray(im.resize((pw, ph), Image.LANCZOS), float)
            cx, cy = x0 + (w - pw) // 2, y0 + (h - ph) // 2
            for dx in range(-sh, sh + 1, 2):
                for dy in range(-sh, sh + 1, 2):
                    d = score(p, cx + dx, cy + dy)
                    if d is not None and (best is None or d < best[0]):
                        best = (d, name, s, cx + dx, cy + dy)
    d, name, s, X, Y = best
    pw, ph = round(w * s), round(h * s)
    p = np.asarray(cands[name].resize((pw, ph), Image.LANCZOS), float)
    for ddx in (-1, 0, 1):          # доуточнить сдвиг по 1 px
        for ddy in (-1, 0, 1):
            dd = score(p, X + ddx, Y + ddy)
            if dd is not None and dd < d:
                d, best = dd, (dd, name, s, X + ddx, Y + ddy)
    d, name, s, X, Y = best
    out = base.copy()
    out.paste(Image.fromarray(p.astype("uint8")), (X, Y))
    out.save(a.out)
    print(name, "scale", s, "at", X, Y, pw, ph, "median", round(d, 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
