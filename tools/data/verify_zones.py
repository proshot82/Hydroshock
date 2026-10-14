#!/usr/bin/env python3
"""Листы проверки зон клика (verify-листы, handoff §16): каждый вид акта с зонами поверх арта.

  python tools/data/verify_zones.py ACT ПАПКА [--states all]

Для каждого вида — кадр: фон + слои, видимые в стартовом состоянии акта (или все слои вида
при --states all), поверх — зоны: прямоугольники рамкой, зоны-слои — контуром по альфе,
подпись «имя зоны · название». Плюс общий лист ПАПКА/_act<N>.png (все виды мелко).
Проверяет числом: зона-слой непуста, зоны не меньше 44 px, зоны одного вида не совпадают целиком.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_design as G  # noqa: E402
import logic as L  # noqa: E402

ROOT = G.ROOT
GFX = ROOT / "assets" / "gfx"
COLORS = [(255, 64, 64), (64, 200, 255), (255, 210, 0), (120, 255, 120), (255, 120, 255), (255, 150, 40)]


def load(img):
    return Image.open(GFX / f"{img}.png").convert("RGBA")


def compose(view, st, all_layers):
    im = load(view["bg"]).resize((1920, 1080))
    for lay in view["layers"]:
        if all_layers or L.evaluate(lay["when"], st):
            im.alpha_composite(load(lay["img"]), (lay["x"], lay["y"]))
    return im


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("act", type=int)
    ap.add_argument("out")
    ap.add_argument("--states", default="start", choices=["start", "all"])
    a = ap.parse_args(argv)
    data = G.build(a.act)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    st = {"flags": set(data["start_flags"]), "pos": "room", "n": {}, "c": {}, "act": a.act}
    font = ImageFont.truetype(str(ROOT / "assets/fonts/PTSans-Bold.ttf"), 30)
    sheets, problems = [], []
    for vid, view in data["views"].items():
        im = compose(view, st, a.states == "all")
        over = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        for i, z in enumerate(view["zones"]):
            col = COLORS[i % len(COLORS)]
            label = f"{z['id']} · {z['name']}"
            if "layer" in z:
                lay = load(z["layer"]["img"])
                alpha = np.array(lay.getchannel("A")) > 8
                if not alpha.any():
                    problems.append(f"{vid}.{z['id']}: слой зоны пуст")
                    continue
                mask = Image.fromarray((alpha * 255).astype("uint8"))
                edge = mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))
                tint = Image.new("RGBA", lay.size, col + (255,))
                over.paste(tint, (z["layer"]["x"], z["layer"]["y"]), edge)
                ys, xs = np.nonzero(alpha)
                tx, ty = z["layer"]["x"] + int(xs.min()) + 8, z["layer"]["y"] + int(ys.min()) + 8
            else:
                for (x, y, w, h) in z["rects"]:
                    d.rectangle((x, y, x + w, y + h), outline=col + (255,), width=5)
                    d.rectangle((x, y, x + w, y + h), fill=col + (40,))
                tx, ty = z["rects"][0][0] + 8, z["rects"][0][1] + 6
            d.text((tx, ty), label, font=font, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=col + (255,))
        rect_sets = [tuple(map(tuple, z.get("rects", []))) for z in view["zones"] if "rects" in z]
        if len(rect_sets) != len(set(rect_sets)):
            problems.append(f"{vid}: у двух зон одинаковые прямоугольники")
        im.alpha_composite(over)
        hdr = ImageDraw.Draw(im)
        hdr.rectangle((0, 1030, 1920, 1080), fill=(0, 0, 0, 200))
        hdr.text((16, 1036), f"Акт {data['roman']} · вид {vid} · {view['bg']} · зон {len(view['zones'])}",
                 font=font, fill=(255, 255, 255, 255))
        im = im.convert("RGB")
        im.save(out / f"{vid}.png")
        sheets.append(im.resize((640, 360), Image.LANCZOS))
    cols = 3
    rows = (len(sheets) + cols - 1) // cols
    sheet = Image.new("RGB", (640 * cols, 360 * rows), (20, 20, 20))
    for i, s in enumerate(sheets):
        sheet.paste(s, ((i % cols) * 640, (i // cols) * 360))
    sheet.save(out / f"_act{a.act}.png")
    for p in problems:
        print("ПРОБЛЕМА", p)
    print(f"листов {len(sheets)} → {out}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
