#!/usr/bin/env python3
"""Кусочно-линейно сжать или растянуть части кадра по горизонтали и вертикали — например, сделать
тоньше раму тележки в оверлее юбки (решение автора 12.10.2026: «тоньше»), не перерисовывая его.

  python tools/assets/remap_frame.py ВХОД.png ВЫХОД.png --x 0:0,135:60,377:302,1543:1618,1785:1860,1920:1920 \
      [--y 0:0,95:45,991:1031,1080:1080]

Опорные точки «откуда:куда» в пикселях кадра 1920×1080, по возрастанию; между ними — линейно.
Части, у которых длина отрезка не меняется (стойки, полотнища), только сдвигаются. Альфа (если есть)
переносится вместе с цветом. Выборка — билинейная.
"""
import argparse

import numpy as np
from PIL import Image


def parse(spec, n):
    if not spec:
        return np.array([0, n]), np.array([0, n])
    pts = [tuple(map(float, p.split(":"))) for p in spec.split(",")]
    src, dst = np.array([p[0] for p in pts]), np.array([p[1] for p in pts])
    return src, dst


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--x", default="")
    ap.add_argument("--y", default="")
    a = ap.parse_args(argv)
    im = Image.open(a.src)
    mode = "RGBA" if "A" in im.getbands() else "RGB"
    arr = np.asarray(im.convert(mode)).astype(float)
    h, w = arr.shape[:2]
    xs, xd = parse(a.x, w)
    ys, yd = parse(a.y, h)
    # обратное отображение: для каждого пикселя выхода — откуда брать
    sx = np.interp(np.arange(w) + 0.5, xd, xs) - 0.5
    sy = np.interp(np.arange(h) + 0.5, yd, ys) - 0.5
    x0 = np.clip(np.floor(sx).astype(int), 0, w - 1); x1 = np.clip(x0 + 1, 0, w - 1); fx = np.clip(sx - x0, 0, 1)
    y0 = np.clip(np.floor(sy).astype(int), 0, h - 1); y1 = np.clip(y0 + 1, 0, h - 1); fy = np.clip(sy - y0, 0, 1)
    top = arr[y0][:, x0] * (1 - fx)[None, :, None] + arr[y0][:, x1] * fx[None, :, None]
    bot = arr[y1][:, x0] * (1 - fx)[None, :, None] + arr[y1][:, x1] * fx[None, :, None]
    out = top * (1 - fy)[:, None, None] + bot * fy[:, None, None]
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype("uint8"), mode).save(a.out)
    print(f"{a.out}: x {a.x or '—'}; y {a.y or '—'}")


if __name__ == "__main__":
    main()
