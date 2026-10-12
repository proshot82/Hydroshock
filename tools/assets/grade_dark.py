#!/usr/bin/env python3
"""Затемнить кадры «до появления» Кухтулху одинаковой цветокоррекцией (решение автора 12.10.2026:
кадры светлеют только после её полного появления, `SEQ.come_out`).

  python tools/assets/grade_dark.py ВХОД.png ВЫХОД.png [--offset X,Y] [--k 0.32]

Один и тот же расчёт для основы и для её слоёв, поэтому слой после коррекции ложится на
затемнённую основу без шва. Для слоя (RGBA) --offset — его левый верхний угол в кадре
(из cutouts.json): виньетка считается по координатам кадра 1920×1080, а не слоя. Альфа не меняется.

Коррекция: в линейном свете яркость умножается на --k, светлые места (лампы, блики) защищены —
чем ярче пиксель, тем меньше его гасят; тени холодеют (меньше красного, больше синего);
по краям кадра виньетка. --no-protect — без защиты светлого: для оверлея юбки
(ov_skirt_dark), где светлая ткань не лампа и должна погаснуть вместе с кадром.
"""
import argparse

import numpy as np
from PIL import Image

W, H = 1920, 1080


def grade(rgb, ox, oy, k, keep_lights=True):
    s = rgb / 255.0
    lin = s ** 2.2
    lum = 0.2126 * s[..., 0] + 0.7152 * s[..., 1] + 0.0722 * s[..., 2]
    t = np.clip((lum - 0.55) / 0.40, 0, 1)
    protect = t * t * (3 - 2 * t) if keep_lights else np.zeros_like(t)
    f = k + (1 - k) * 0.85 * protect
    out = lin * f[..., None]
    cool = 1 - protect
    out[..., 0] *= 1 - 0.18 * cool
    out[..., 2] *= 1 + 0.12 * cool
    h, w = lum.shape
    yy, xx = np.mgrid[oy:oy + h, ox:ox + w]
    r2 = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    out *= np.clip(1 - 0.30 * r2, 0.45, 1)[..., None]
    return (np.clip(out, 0, 1) ** (1 / 2.2) * 255 + 0.5).astype(np.uint8)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--offset", default="0,0")
    ap.add_argument("--k", type=float, default=0.32)
    ap.add_argument("--no-protect", action="store_true",
                    help="не беречь светлое: для ткани юбки, которая светлая сама по себе, а не лампа")
    a = ap.parse_args(argv)
    ox, oy = map(int, a.offset.split(","))
    im = Image.open(a.src)
    rgba = im.mode == "RGBA"
    arr = np.asarray(im.convert("RGBA" if rgba else "RGB")).astype(float)
    out = grade(arr[..., :3], ox, oy, a.k, keep_lights=not a.no_protect)
    if rgba:
        out = np.dstack([out, arr[..., 3].astype(np.uint8)])
    Image.fromarray(out, "RGBA" if rgba else "RGB").save(a.dst)
    if not rgba:
        print(f"{a.dst}: средняя яркость {np.asarray(Image.fromarray(out).convert('L')).mean() / 2.55:.1f} %")


if __name__ == "__main__":
    main()
