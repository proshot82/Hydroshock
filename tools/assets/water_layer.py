#!/usr/bin/env python3
"""Слой «вода прибывает» (st_w5_water, st_w6_water): только вода, пена и струи, без шва по рамке.

  python tools/assets/water_layer.py БАЗА.png ВАРИАНТ.png st_ИМЯ --out ПАПКА \
      [--keep X0,Y0,X1,Y1 ...] [--min-area 15000] [--minus st_СЛОЙ ...]

cutout.py режет по разнице внутри прямоугольника; для воды это не годится: генератор при правке
слегка перерисовывает весь кадр, и в маску попадают скалы и мебель. Здесь маска — разница с базой
только в зоне бирюзовой воды (база или вариант, с запасом 7 px) плюс новые светлые струи и пена
рядом с водой; острова меньше --min-area px выбрасываются. --keep — прямоугольники из базы
(без нужды не ставить: прямоугольник в воде даёт видимую ступеньку). --minus — вычесть альфу
слоёв, которые при этом флаге всегда на экране и стоят в воде (Кухтулху у стеллажа в W6,
тележка в W5): вода не закрывает щупальца и колёса при любом порядке слоёв. Слой ищется сначала
в --out, потом в assets/gfx/cutouts/. Координаты пишутся в cutouts.json папки --out.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
CUT = ROOT / "assets" / "gfx" / "cutouts"


def rect(s):
    return tuple(int(v) for v in s.split(","))


def water(im):
    h, s, v = [np.asarray(c, float) for c in im.convert("HSV").split()]
    return (h > 105) & (h < 145) & (s > 70) & (v > 60), (s < 60) & (v > 200)   # бирюза, белая пена


def drop_islands(m, min_area):
    """Убрать связные куски меньше min_area px (считается по маске ×1/4)."""
    sm = m.filter(ImageFilter.MaxFilter(9)).resize((m.width // 4, m.height // 4))
    sm = sm.point(lambda t: 255 if t else 0)
    a = np.asarray(sm)
    seen = np.zeros(a.shape, bool)
    drop = np.zeros(a.shape, bool)
    for y, x in zip(*np.nonzero(a == 255)):
        if seen[y, x]:
            continue
        t = sm.copy()
        ImageDraw.floodfill(t, (int(x), int(y)), 100)
        comp = np.asarray(t) == 100
        seen |= comp
        if comp.sum() * 16 < min_area:
            drop |= comp
    d = Image.fromarray((drop * 255).astype("uint8")).resize(m.size).filter(ImageFilter.MaxFilter(9))
    return ImageChops.subtract(m, d)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("variant")
    ap.add_argument("name")
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep", type=rect, action="append", default=[])
    ap.add_argument("--min-area", type=int, default=4000)
    ap.add_argument("--minus", action="append", default=[])
    a = ap.parse_args(argv)
    out = Path(a.out)
    base = Image.open(a.base).convert("RGB")
    var = Image.open(a.variant).convert("RGB")
    cb, fb = water(base)
    cv, fv = water(var)
    d = np.abs(np.asarray(base, float) - np.asarray(var, float)).max(2)
    zone = np.asarray(Image.fromarray(((cb | cv) * 255).astype("uint8")).filter(ImageFilter.MaxFilter(15))) > 0
    near = np.asarray(Image.fromarray((zone * 255).astype("uint8")).filter(ImageFilter.MaxFilter(61))) > 0
    m = (zone & (d > 16)) | (fv & ~fb & near & (d > 30))
    for x0, y0, x1, y1 in a.keep:
        m[y0:y1, x0:x1] = False
    M = Image.fromarray((m * 255).astype("uint8"))
    M = drop_islands(M, a.min_area)
    M = M.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    M = M.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.MinFilter(15))
    M = M.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2.5))
    arr = np.asarray(M).copy()
    for x0, y0, x1, y1 in a.keep:
        arr[y0:y1, x0:x1] = 0
    M = Image.fromarray(arr)
    cj = out / "cutouts.json"
    coords = json.loads(cj.read_text(encoding="utf-8")) if cj.exists() else {}
    full = json.loads((CUT / "cutouts.json").read_text(encoding="utf-8"))
    for n in a.minus:
        src, e = (out / f"{n}.png", coords[n]) if (out / f"{n}.png").exists() else (CUT / f"{n}.png", full[n])
        k = Image.new("L", base.size, 0)
        k.paste(Image.open(src).getchannel("A"), (e["x"], e["y"]))
        M = ImageChops.multiply(M, ImageChops.invert(k))
    bb = M.point(lambda t: 255 if t > 8 else 0).getbbox()
    layer = var.convert("RGBA")
    layer.putalpha(M)
    layer.crop(bb).save(out / f"{a.name}.png")
    coords[a.name] = {"base": Path(a.base).name, "x": bb[0], "y": bb[1], "w": bb[2] - bb[0], "h": bb[3] - bb[1]}
    cj.write_text(json.dumps({k: {f: v[f] for f in ("base", "x", "y", "w", "h")} for k, v in sorted(coords.items())}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"name": a.name, "bbox": list(bb), "area_pct": round(100 * (np.asarray(M) > 8).mean(), 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
