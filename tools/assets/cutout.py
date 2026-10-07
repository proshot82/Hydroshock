#!/usr/bin/env python3
"""Вырезать состояние из кадра-варианта поверх принятой базы (ASSET_SPEC §1.2).

  python tools/assets/cutout.py БАЗА.png ВАРИАНТ.png st_ИМЯ \
      --box X0,Y0,X1,Y1 [--keep X0,Y0,X1,Y1 ...] [--thresh 38] [--close 25] [--feather 10]

Маска — где вариант заметно отличается от базы, только внутри --box (область элемента);
дыры внутри маски заливаются, мелкий шум убирается, края растушёвываются. Области --keep
всегда берутся из базы (вывески, которые генератор сдвинул или исказил). Цвет варианта
подгоняется к базе по кольцу вокруг маски (сдвиг средних по каналам).

Результат: assets/gfx/cutouts/<имя>.png — RGBA, обрезан по маске; координаты левого
верхнего угла — assets/gfx/cutouts/cutouts.json (генерируется, руками не править);
проверочная склейка «база + вырезка» и маска — work/higgsfield/cutout_preview/.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "gfx" / "cutouts"
PREVIEW = ROOT / "work" / "higgsfield" / "cutout_preview"


def rect(s):
    v = [int(x) for x in s.split(",")]
    if len(v) != 4 or v[0] >= v[2] or v[1] >= v[3]:
        raise argparse.ArgumentTypeError("ожидается X0,Y0,X1,Y1 с X0<X1, Y0<Y1: " + s)
    return v


def morph(mask, size, grow):
    """Расширение (grow=True) или сужение маски квадратом size, через фильтры PIL."""
    f = ImageFilter.MaxFilter if grow else ImageFilter.MinFilter
    while size > 1:                       # большие окна — повтором малых, PIL так быстрее
        step = min(size, 9) | 1
        mask = mask.filter(f(step))
        size -= step - 1
    return mask


def fill_holes(mask, box):
    """Залить замкнутые дыры: всё, что не достижимо заливкой от рамки box, — внутри."""
    x0, y0, x1, y1 = box
    sub = mask.crop(box)
    pad = Image.new("L", (sub.width + 2, sub.height + 2), 0)
    pad.paste(sub, (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 128)
    a = np.array(pad)[1:-1, 1:-1]
    a = np.where(a == 128, 0, 255).astype(np.uint8)
    out = mask.copy()
    out.paste(Image.fromarray(a), (x0, y0))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("variant")
    ap.add_argument("name")
    ap.add_argument("--box", type=rect, required=True)
    ap.add_argument("--keep", type=rect, action="append", default=[])
    ap.add_argument("--thresh", type=int, default=38)
    ap.add_argument("--close", type=int, default=25)
    ap.add_argument("--open", type=int, default=7)
    ap.add_argument("--feather", type=int, default=10)
    a = ap.parse_args(argv)

    base = Image.open(a.base).convert("RGB")
    var = Image.open(a.variant).convert("RGB")
    if base.size != var.size:
        sys.exit(f"размеры не совпадают: {base.size} и {var.size}")

    b = np.asarray(base.filter(ImageFilter.GaussianBlur(2)), dtype=np.int16)
    v = np.asarray(var.filter(ImageFilter.GaussianBlur(2)), dtype=np.int16)
    diff = np.abs(b - v).max(axis=2)
    m = np.zeros(diff.shape, np.uint8)
    x0, y0, x1, y1 = a.box
    m[y0:y1, x0:x1] = (diff[y0:y1, x0:x1] > a.thresh) * 255
    mask = Image.fromarray(m)
    mask = morph(morph(mask, a.open, False), a.open, True)        # убрать шум
    mask = morph(morph(mask, a.close, True), a.close, False)      # срастить фигуру
    mask = fill_holes(mask, a.box)
    d = ImageDraw.Draw(mask)
    for k in a.keep:
        d.rectangle(k, fill=0)
    hard = np.asarray(mask) > 127
    if not hard.any():
        sys.exit("маска пуста — поднимите чувствительность (--thresh ниже) или проверьте --box")

    # Цвет: сдвиг средних варианта к базе по кольцу шириной ~12 px вокруг маски.
    ring = (np.asarray(morph(mask, 25, True)) > 127) & ~hard
    vb = np.asarray(var, dtype=np.float32)
    bb = np.asarray(base, dtype=np.float32)
    shift = bb[ring].mean(axis=0) - vb[ring].mean(axis=0) if ring.any() else np.zeros(3)
    matched = np.clip(vb + shift, 0, 255).astype(np.uint8)

    alpha = mask.filter(ImageFilter.GaussianBlur(a.feather / 2))
    rgba = Image.fromarray(matched).convert("RGBA")
    rgba.putalpha(alpha)
    bbox = alpha.point(lambda p: 255 if p > 2 else 0).getbbox()
    cut = rgba.crop(bbox)

    OUT.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)
    cut.save(OUT / f"{a.name}.png")
    coords_path = OUT / "cutouts.json"
    coords = json.loads(coords_path.read_text(encoding="utf-8")) if coords_path.exists() else {}
    coords[a.name] = {"base": Path(a.base).name, "x": bbox[0], "y": bbox[1],
                      "w": cut.width, "h": cut.height}
    coords_path.write_text(json.dumps(dict(sorted(coords.items())), ensure_ascii=False, indent=1)
                           + "\n", encoding="utf-8")
    comp = base.convert("RGBA")
    comp.alpha_composite(cut, (bbox[0], bbox[1]))
    comp.convert("RGB").save(PREVIEW / f"{a.name}.png")
    alpha.save(PREVIEW / f"{a.name}__mask.png")
    print(json.dumps({"name": a.name, "bbox": bbox, "shift": [round(float(s), 1) for s in shift],
                      "area_pct": round(100 * hard.mean(), 1)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
