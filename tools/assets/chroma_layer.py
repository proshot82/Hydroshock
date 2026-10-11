#!/usr/bin/env python3
"""Слой из картинки на мадженте: люди и предметы, которые генератор не может дорисовать в кадр,
не перерисовав фон (ASSET_SPEC §1.2: толпа из-под юбки, 11.10.2026).

  python tools/assets/chroma_layer.py БАЗА.png НА_МАДЖЕНТЕ.png st_ИМЯ [--scale 1.15] [--dx 0] [--dy 0]
      [--floor-y 740] [--shadow 0.45] [--out ПАПКА]

Маджента #FF00FF вырезается (мягкий край по расстоянию до мадженты). --scale — увеличение от
верхнего края по центру кадра (ноги, уходящие за верх кадра, остаются уходящими; ступни опускаются —
так дальние ступни встают перед основанием стойки, а не за ней). --dx/--dy — сдвиг. --floor-y — ниже
этой строки под слоем кладётся мягкая контактная тень (на пол), выше — нет (на стойку и стены тень не
падает). Результат как у cutout.py: <имя>.png (RGBA, обрезан по слою) и запись в cutouts.json папки;
проверочная склейка — work/higgsfield/cutout_preview/<имя>.png.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "gfx" / "cutouts"
PREVIEW = ROOT / "work" / "higgsfield" / "cutout_preview"


def key(im):
    a = np.asarray(im.convert("RGB")).astype(float)
    d = np.sqrt((a[..., 0] - 255) ** 2 + a[..., 1] ** 2 + (a[..., 2] - 255) ** 2)
    alpha = np.clip((d - 60) / 80, 0, 1)
    al = Image.fromarray((alpha * 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    return Image.merge("RGBA", (*im.convert("RGB").split(), al))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("chroma")
    ap.add_argument("name")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--dx", type=int, default=0)
    ap.add_argument("--dy", type=int, default=0)
    ap.add_argument("--floor-y", type=int, default=None)
    ap.add_argument("--shadow", type=float, default=0.45)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    base = Image.open(a.base).convert("RGBA")
    W, H = base.size
    lay = key(Image.open(a.chroma).resize((W, H), Image.LANCZOS))
    if a.scale != 1.0:
        nw, nh = int(W * a.scale), int(H * a.scale)
        big = lay.resize((nw, nh), Image.LANCZOS)
        x0 = (nw - W) // 2
        lay = big.crop((x0, 0, x0 + W, H))
    if a.dx or a.dy:
        moved = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        moved.paste(lay, (a.dx, a.dy))
        lay = moved
    if a.floor_y is not None:
        al = np.asarray(lay.split()[3].filter(ImageFilter.GaussianBlur(14))).astype(float) / 255
        al = np.roll(al, 8, axis=0)
        al[: a.floor_y] = 0
        sh = np.zeros((H, W, 4), dtype="uint8")
        sh[..., 0], sh[..., 1], sh[..., 2] = 40, 30, 25
        sh[..., 3] = (np.clip(al * a.shadow, 0, a.shadow) * 255).astype("uint8")
        shadow = Image.fromarray(sh, "RGBA")
        shadow.alpha_composite(lay)
        lay = shadow
    bbox = lay.split()[3].getbbox()
    out = Path(a.out) if a.out else OUT
    out.mkdir(parents=True, exist_ok=True)
    lay.crop(bbox).save(out / f"{a.name}.png")
    coords_path = out / "cutouts.json"
    coords = json.loads(coords_path.read_text(encoding="utf-8")) if coords_path.exists() else {}
    coords[a.name] = {"base": Path(a.base).name, "x": bbox[0], "y": bbox[1],
                      "w": bbox[2] - bbox[0], "h": bbox[3] - bbox[1]}
    coords_path.write_text(json.dumps(dict(sorted(coords.items())), ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
    PREVIEW.mkdir(parents=True, exist_ok=True)
    prev = base.copy()
    prev.alpha_composite(lay)
    prev.convert("RGB").save(PREVIEW / f"{a.name}.png")
    print(json.dumps({"name": a.name, "bbox": list(bbox)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
