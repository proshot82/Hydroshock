#!/usr/bin/env python3
"""Слой-прямоугольник: участок кадра-варианта целиком, с мягким краем по фону.

  python tools/assets/rect_layer.py БАЗА.png ВАРИАНТ.png st_ИМЯ --box X0,Y0,X1,Y1 --out ПАПКА [--feather 14]

Для состояний, где генератор переставил предметы внутри участка (стопку бумаг сдвинули, чтобы
положить вещь): маска по разнице с базой там рваная — старые и новые края стопки, островки
перерисованной фактуры. Здесь слой — весь прямоугольник --box варианта (вклеенного
tools/assets/patch_region.py, края участка совпадают с базой), прозрачность спадает к краю
на --feather px. Прямоугольник ставить так, чтобы его край шёл по однородному фону (камень,
скала), а не через предмет. --cut — вырезать из прямоугольника углы (в координатах кадра), где
рядом стоит то, что меняется другими слоями (маховик с пломбой, рамка фото). Координаты — в cutouts.json папки --out.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("variant")
    ap.add_argument("name")
    ap.add_argument("--box", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--feather", type=int, default=14)
    ap.add_argument("--cut", action="append", default=[])
    a = ap.parse_args(argv)
    x0, y0, x1, y1 = map(int, a.box.split(","))
    var = Image.open(a.variant).convert("RGBA").crop((x0, y0, x1, y1))
    f = a.feather
    m = Image.new("L", var.size, 0)
    d = ImageDraw.Draw(m)
    bw, bh = Image.open(a.base).size        # у края кадра растушёвки нет: там слой встык с рамкой экрана
    d.rectangle((-3 * f if x0 == 0 else f, -3 * f if y0 == 0 else f,
                 var.width - 1 + (3 * f if x1 == bw else -f), var.height - 1 + (3 * f if y1 == bh else -f)), fill=255)
    for c in a.cut:
        cx0, cy0, cx1, cy1 = map(int, c.split(","))
        d.rectangle((cx0 - x0 - f, cy0 - y0 - f, cx1 - x0 + f, cy1 - y0 + f), fill=0)
    m = m.filter(ImageFilter.GaussianBlur(f / 2))
    if x0 == 0 or y0 == 0 or x1 == bw or y1 == bh:      # размытие у края кадра не должно гасить альфу
        pad = Image.new("L", (var.width + 6 * f, var.height + 6 * f), 0)
        pd = ImageDraw.Draw(pad)
        pd.rectangle((0 if x0 == 0 else 3 * f + f, 0 if y0 == 0 else 3 * f + f,
                      pad.width if x1 == bw else 3 * f + var.width - 1 - f, pad.height if y1 == bh else 3 * f + var.height - 1 - f), fill=255)
        for c in a.cut:
            cx0, cy0, cx1, cy1 = map(int, c.split(","))
            pd.rectangle((cx0 - x0 + 2 * f, cy0 - y0 + 2 * f, cx1 - x0 + 4 * f, cy1 - y0 + 4 * f), fill=0)
        m = pad.filter(ImageFilter.GaussianBlur(f / 2)).crop((3 * f, 3 * f, 3 * f + var.width, 3 * f + var.height))
    var.putalpha(m)
    out = Path(a.out)
    var.save(out / f"{a.name}.png")
    cj = out / "cutouts.json"
    coords = json.loads(cj.read_text(encoding="utf-8")) if cj.exists() else {}
    coords[a.name] = {"base": Path(a.base).name, "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}
    cj.write_text(json.dumps(dict(sorted(coords.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"name": a.name, "box": [x0, y0, x1, y1]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
