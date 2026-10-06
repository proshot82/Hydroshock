#!/usr/bin/env python3
"""Приёмка портретов: staging → assets/gfx/portraits (ASSET_SPEC §5, §1.8).

Генератор рисует подложку со скруглёнными углами на чёрном поле, отступ поля
у каждого портрета свой. Поэтому: находим подложку (строки и столбцы, где
средняя яркость выше 30), обрезаем по ней, приводим к 512×512 и накладываем
скруглённую маску с радиусом 20 px, как у портретов BJ2. Заливку по тёмному
цвету не используем: контурные линии персонажа связаны с краем и пропадали.

  python tools/assets/accept_portraits.py ИМЯ.png [ИМЯ.png ...]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "work" / "higgsfield" / "staging"
OUT = ROOT / "assets" / "gfx" / "portraits"


RADIUS = 20


def panel_box(a, thr=30):
    lum = a.mean(axis=2)
    rows = np.where(lum.mean(axis=1) > thr)[0]
    cols = np.where(lum.mean(axis=0) > thr)[0]
    return cols[0], rows[0], cols[-1] + 1, rows[-1] + 1


def accept(name):
    im = Image.open(STAGE / name).convert("RGB")
    box = panel_box(np.asarray(im).astype(float))
    im = im.crop(box).resize((512, 512), Image.LANCZOS)
    big = Image.new("L", (2048, 2048), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, 2047, 2047), radius=RADIUS * 4, fill=255)
    out = im.convert("RGBA")
    out.putalpha(big.resize((512, 512), Image.LANCZOS))
    OUT.mkdir(parents=True, exist_ok=True)
    out.save(OUT / name)
    return box


if __name__ == "__main__":
    for n in sys.argv[1:]:
        print(n, "подложка:", accept(n))
