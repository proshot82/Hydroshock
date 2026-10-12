#!/usr/bin/env python3
"""Превью титульного экрана: фон + логотип + кнопки меню там, где их нарисует движок.

  python tools/assets/title_preview.py ФОН.png ЛОГОТИП.png ПРЕВЬЮ.png
         [--logo-x 40 --logo-y 30 --logo-w 860] [--btn-x 270 --btn-y 470 --btn-gap 92]
         [--keep X0,Y0,X1,Y1]

Логотип масштабируется до ширины --logo-w (предумноженная альфа). Четыре кнопки 400×72 —
столбиком от (--btn-x, --btn-y). --keep — прямоугольник, который нельзя перекрывать
(например, плакаты); скрипт печатает, задевают ли его логотип и кнопки.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("bg")
    ap.add_argument("logo")
    ap.add_argument("dst")
    ap.add_argument("--logo-x", type=int, default=40)
    ap.add_argument("--logo-y", type=int, default=30)
    ap.add_argument("--logo-w", type=int, default=860)
    ap.add_argument("--btn-x", type=int, default=270)
    ap.add_argument("--btn-y", type=int, default=470)
    ap.add_argument("--btn-gap", type=int, default=92)
    ap.add_argument("--keep")
    a = ap.parse_args(argv)
    bg = Image.open(a.bg).convert("RGBA")
    lg = Image.open(a.logo).convert("RGBA")
    lg = lg.crop(lg.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
    h = round(lg.height * a.logo_w / lg.width)
    lg = lg.convert("RGBa").resize((a.logo_w, h), Image.LANCZOS).convert("RGBA")
    bg.alpha_composite(lg, (a.logo_x, a.logo_y))
    boxes = [("логотип", (a.logo_x, a.logo_y, a.logo_x + a.logo_w, a.logo_y + h))]
    d = ImageDraw.Draw(bg)
    font = ImageFont.truetype(str(ROOT / "assets/fonts/PTSans-Bold.ttf"), 34)
    for i, t in enumerate(["Начать", "Продолжить", "Настройки", "Выход"]):
        x, y = a.btn_x, a.btn_y + i * a.btn_gap
        d.rounded_rectangle((x, y, x + 400, y + 72), 12, fill=(34, 34, 42, 235), outline=(200, 160, 80), width=2)
        d.text((x + 200, y + 36), t, font=font, fill=(235, 225, 200), anchor="mm")
        boxes.append((f"кнопка «{t}»", (x, y, x + 400, y + 72)))
    bg.convert("RGB").save(a.dst)
    print(f"{a.dst}: логотип {a.logo_w}×{h} в ({a.logo_x}, {a.logo_y}); кнопки от ({a.btn_x}, {a.btn_y})")
    if a.keep:
        k = [int(v) for v in a.keep.split(",")]
        hit = [n for n, b in boxes if b[0] < k[2] and b[2] > k[0] and b[1] < k[3] and b[3] > k[1]]
        print("перекрытий нет" if not hit else "перекрывают: " + ", ".join(hit))
        return 1 if hit else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
