#!/usr/bin/env python3
"""Врезать табличку с надписью (сгенерированную крупным планом и сверенную побуквенно) в кадр по четырём углам.

  python tools/assets/plaque_insert.py КАДР.png ИСТОЧНИК.png X0,Y0,X1,Y1 'x,y x,y x,y x,y' ВЫХОД.png

X0..Y1 — прямоугольник таблички в источнике; четыре точки — углы в кадре (лв, пв, пн, лн).
Яркость и цвет таблички подгоняются к тому, что было на этом месте в кадре (средние по каналам).
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def coeffs(dst, src):
    a = []
    for (x, y), (u, v) in zip(dst, src):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    b = [c for p in src for c in p]
    return np.linalg.solve(np.array(a, float), np.array(b, float)).tolist()


def main(frame, source, box, quad, out):
    fr = Image.open(frame).convert('RGB'); sr = Image.open(source).convert('RGB')
    x0, y0, x1, y1 = map(int, box.split(','))
    q = [tuple(map(float, p.split(','))) for p in quad.split()]
    S = 4  # суперсэмплинг для гладких краёв
    W, H = fr.size
    big = sr.crop((x0, y0, x1, y1))
    w, h = big.size
    src_pts = [(0, 0), (w, 0), (w, h), (0, h)]
    dst_big = [(x * S, y * S) for x, y in q]
    warped = big.transform((W * S, H * S), Image.PERSPECTIVE, coeffs(dst_big, src_pts), Image.BICUBIC)
    mask = Image.new('L', (W * S, H * S), 0); ImageDraw.Draw(mask).polygon(dst_big, fill=255)
    warped = warped.resize((W, H), Image.LANCZOS); mask = mask.resize((W, H), Image.LANCZOS)
    m = np.asarray(mask) > 128
    f = np.asarray(fr, dtype=np.float32); wv = np.asarray(warped, dtype=np.float32)
    gain = f[m].mean(axis=0) / np.maximum(wv[m].mean(axis=0), 1)
    wv = np.clip(wv * gain, 0, 255).astype(np.uint8)
    res = Image.composite(Image.fromarray(wv), fr, mask.filter(ImageFilter.GaussianBlur(0.6)))
    res.save(out)
    print('gain', [round(float(g), 2) for g in gain])


if __name__ == '__main__':
    main(*sys.argv[1:6])
