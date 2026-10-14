#!/usr/bin/env python3
"""Кадр с координатной сеткой — для разметки зон клика по арту.

  python tools/data/grid_view.py КАРТИНКА.png ВЫХОД.png [--step 100] [--scale 0.5]
         [--layers слой1,слой2 ...]   (слои из assets/gfx/cutouts по cutouts.json)

Сетка через --step пикселей мира 1920×1080, подписи координат по краям.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--step", type=int, default=100)
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--layers", default="")
    a = ap.parse_args(argv)
    im = Image.open(a.src).convert("RGBA")
    if a.layers:
        cj = json.loads((ROOT / "assets/gfx/cutouts/cutouts.json").read_text(encoding="utf-8"))
        for name in a.layers.split(","):
            e = cj.get(name, {"x": 0, "y": 0})   # оверлеи юбки — полный кадр, их нет в cutouts.json
            lay = Image.open(ROOT / "assets/gfx/cutouts" / f"{name}.png").convert("RGBA")
            im.alpha_composite(lay, (e["x"], e["y"]))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(str(ROOT / "assets/fonts/PTSans-Bold.ttf"), 22)
    for x in range(0, im.width, a.step):
        d.line((x, 0, x, im.height), fill=(255, 0, 255, 150), width=1 if x % 500 else 3)
        d.text((x + 3, 3), str(x), font=font, fill=(255, 255, 0, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    for y in range(0, im.height, a.step):
        d.line((0, y, im.width, y), fill=(255, 0, 255, 150), width=1 if y % 500 else 3)
        d.text((3, y + 3), str(y), font=font, fill=(255, 255, 0, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    if a.scale != 1:
        im = im.resize((round(im.width * a.scale), round(im.height * a.scale)), Image.LANCZOS)
    im.convert("RGB").save(a.dst)


if __name__ == "__main__":
    main()
