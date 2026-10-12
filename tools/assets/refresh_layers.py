#!/usr/bin/env python3
"""Очистить слои экрана от кусков старой основы после правки основы участком (ASSET_SPEC §1.2).

  python tools/assets/refresh_layers.py СТАРАЯ_ОСНОВА.png НОВАЯ_ОСНОВА.png ПАПКА_СЛОЁВ ВЫХОД \
      [--only st_a,st_b] [--diff 30] [--same 40]

Слой вырезан из кадра-варианта со своим краем фона: если основу потом поправили (переодели толпу),
в краях слоя остаются кусочки старой основы — на новой основе они видны пятнами (синий лоскут
старых джинсов рядом со стопкой бланков). Здесь у каждого слоя этой основы (по cutouts.json папки)
там, где основа изменилась (разница > --diff), гасится альфа пикселей, почти совпадающих со старой
основой (разница < --same): это не предмет слоя, а его фон. Предмет, отличный от старой основы,
остаётся. Слои, которым нечего чистить, не пишутся. ВЫХОД — папка для исправленных слоёв (кандидаты);
cutouts.json туда пишется с теми же координатами.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("layers")
    ap.add_argument("out")
    ap.add_argument("--only", default="")
    ap.add_argument("--diff", type=int, default=30)
    ap.add_argument("--same", type=int, default=40)
    a = ap.parse_args(argv)
    old = np.asarray(Image.open(a.old).convert("RGB")).astype(int)
    new = np.asarray(Image.open(a.new).convert("RGB")).astype(int)
    changed = np.abs(old - new).max(2) > a.diff
    changed = np.asarray(Image.fromarray(changed.astype("uint8") * 255).filter(ImageFilter.MaxFilter(5))) > 0
    src = Path(a.layers)
    coords = json.loads((src / "cutouts.json").read_text(encoding="utf-8"))
    only = set(filter(None, a.only.split(",")))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    out_json = out / "cutouts.json"
    out_coords = json.loads(out_json.read_text(encoding="utf-8")) if out_json.exists() else {}
    base_name = Path(a.old).name
    for name, v in sorted(coords.items()):
        if v["base"] != base_name or (only and name not in only):
            continue
        x, y, w, h = v["x"], v["y"], v["w"], v["h"]
        lay = np.asarray(Image.open(src / f"{name}.png").convert("RGBA")).astype(int)
        ch = changed[y:y + h, x:x + w]
        stale = ch & (lay[..., 3] > 0) & (np.abs(lay[..., :3] - old[y:y + h, x:x + w]).max(2) < a.same)
        if not stale.any():
            continue
        # мягкий край: гасим с растушёвкой 2 px, чтобы не было рваной кромки
        m = Image.fromarray((stale * 255).astype("uint8")).filter(ImageFilter.MaxFilter(3)).filter(
            ImageFilter.GaussianBlur(1.5))
        keep = 1 - np.asarray(m).astype(float) / 255
        lay[..., 3] = (lay[..., 3] * keep).astype(int)
        Image.fromarray(lay.astype("uint8"), "RGBA").save(out / f"{name}.png")
        out_coords[name] = v
        print(f"{name}: погашено {int(stale.sum())} px старой основы")
    out_json.write_text(json.dumps(dict(sorted(out_coords.items())), ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")


if __name__ == "__main__":
    main()
