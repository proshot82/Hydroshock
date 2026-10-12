#!/usr/bin/env python3
"""Схема-раскладка титула ред. 3 (замечание автора 12.10.2026): отель в разрезе, вид с высоты.

  python tools/layout/title_iso_mock.py  →  work/higgsfield/layout/title_iso_mock_1012.png

Кукольный дом в косоугольной (кабинетной) проекции сверху: длинное здание — 3 этажа и подвал —
слегка уходит вниз вправо, глубина идёт вверх вправо. Крыша, фасад и ближний торец сняты:
видны полы, задние стены и перегородки всех этажей. Дальний конец (слева) — 1908 год,
середина — профилакторий, ближний (справа) — отель, цвет плавно перетекает. Под зданием
плита земли в разрезе: камень и карман подземной воды с бирюзовым светом. Одна труба идёт
вертикально от источника в подвале к душевой на верхнем этаже. Верх кадра — небо под логотип.
Цвета плоские: генератор перерисовывает схему в стиле игры, не сдвигая линий.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
W, H = 1920, 1080
EX, EY = (1.0, 0.10), (0.42, -0.28)   # ось длины здания и ось глубины на экране
L, D = 1300, 330                       # длина и глубина здания
FH, BH = 100, 90                       # этаж и подвал
O = (170, 840)                         # экранная точка угла (x=0, y=0, z=0): фасад, дальний конец, земля
INK = (40, 30, 25)


def P(x, y, z):
    return (O[0] + x * EX[0] + y * EY[0], O[1] + x * EX[1] + y * EY[1] - z)


def era(x):
    """1908 (бирюза и белая плитка) → профилакторий (зелёная краска) → отель (бежевый)."""
    stops = [(0.0, (125, 205, 205)), (0.5, (140, 180, 130)), (1.0, (220, 195, 145))]
    t = max(0.0, min(1.0, x / L))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            k = (t - t0) / (t1 - t0)
            return tuple(round(a + (b - a) * k) for a, b in zip(c0, c1))
    return stops[-1][1]


def shade(c, k):
    return tuple(round(v * k) for v in c)


def poly(d, pts, fill, outline=INK, w=3):
    d.polygon([P(*p) for p in pts], fill=fill, outline=outline, width=w)


def storey(d, z, h, rooms):
    n = 26
    for i in range(n):                                    # пол и задняя стена полосами — эпохи перетекают
        x0, x1 = L * i / n, L * (i + 1) / n
        c = era((x0 + x1) / 2)
        poly(d, [(x0, 0, z), (x1, 0, z), (x1, D, z), (x0, D, z)], shade(c, 0.7), outline=None, w=0)
        poly(d, [(x0, D, z), (x1, D, z), (x1, D, z + h), (x0, D, z + h)], c, outline=None, w=0)
    poly(d, [(0, 0, z), (0, D, z), (0, D, z + h), (0, 0, z + h)], shade(era(0), 0.85))   # дальний торец
    for k in range(1, rooms):                             # перегородки комнат
        x = L * k / rooms
        poly(d, [(x, D, z), (x, D * 0.15, z), (x, D * 0.15, z + h), (x, D, z + h)], shade(era(x), 0.9), w=2)
    d.line([P(0, 0, z), P(L, 0, z), P(L, D, z)], fill=INK, width=5)


def main():
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for yy in range(H):                                   # сумеречное небо, верх спокойный
        k = yy / H
        d.line([(0, yy), (W, yy)], fill=(round(120 + 110 * k), round(135 + 70 * k), round(185 - 35 * k)))
    m, dep = 90, 330
    # плита земли: улица сверху, срез спереди, под зданием — камень и вода
    poly(d, [(-m, -m, 0), (L + m, -m, 0), (L + m, D + m, 0), (-m, D + m, 0)], (150, 145, 138))
    poly(d, [(-m, -m, 0), (L + m, -m, 0), (L + m, -m, -dep), (-m, -m, -dep)], (88, 74, 64))
    poly(d, [(L + m, -m, 0), (L + m, D + m, 0), (L + m, D + m, -dep), (L + m, -m, -dep)], (72, 62, 55))
    cx, cy = P(L * 0.45, D * 0.4, -BH - 170)
    for i in range(16):                                   # карман подземной воды
        k = i / 16
        r = 260 * (1 - k)
        d.ellipse((cx - r, cy - r * 0.42, cx + r, cy + r * 0.42),
                  fill=(round(20 + 50 * k), round(60 + 150 * k), round(70 + 140 * k)))
    storey(d, -BH, BH, 5)                                 # подвал
    for f in range(3):
        storey(d, f * FH, FH, 6)
    d.line([P(0, 0, 3 * FH), P(L, 0, 3 * FH), P(L, D, 3 * FH)], fill=INK, width=5)
    d.line([P(0, D, 3 * FH), P(L, D, 3 * FH)], fill=INK, width=5)
    # источник в подвале и труба до душевой на верхнем этаже
    sx, sy = L * 0.45, D * 0.55
    ex, ey = P(sx, sy, -BH)
    d.ellipse((ex - 48, ey - 16, ex + 48, ey + 16), fill=(70, 210, 220), outline=INK, width=3)
    d.line([P(sx, sy, -BH - 150), P(sx, sy, 3 * FH - 10)], fill=(205, 165, 60), width=12)
    tx, ty = P(sx + 40, sy, 2 * FH)
    d.rectangle((tx - 30, ty - 85, tx + 30, ty), outline=(235, 250, 255), width=5)
    out = ROOT / "work/higgsfield/layout/title_iso_mock_1012.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    print(out)


if __name__ == "__main__":
    main()
