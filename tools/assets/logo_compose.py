#!/usr/bin/env python3
"""Логотип титула BJ3 (ASSET_SPEC §10): логотип BJ2 без изменений + строка «ГИДРОУДАР».

  python tools/assets/logo_compose.py BJ2_LOGO.png СТРОКА.png ВЫХОД.png [--height 120] [--gap 40]

BJ2_LOGO — `proshot82/bj2` `assets/gfx/ui/logo_title.png` (1200×420 RGBA), кладётся
сверху байт в байт. СТРОКА — генерация с прозрачным фоном: обрезается по силуэту
(альфа > 8) и масштабируется до высоты --height (Lanczos в предумноженной альфе),
ставится по центру под логотипом с отступом --gap от низа его силуэта. Холст 1200×600 RGBA.
"""
import argparse
import sys

from PIL import Image


def bbox(im):
    return im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("logo")
    ap.add_argument("line")
    ap.add_argument("dst")
    ap.add_argument("--height", type=int, default=120)
    ap.add_argument("--gap", type=int, default=40)
    a = ap.parse_args(argv)
    logo = Image.open(a.logo).convert("RGBA")
    if logo.size != (1200, 420):
        print("логотип BJ2 не 1200×420:", logo.size)
        return 1
    line = Image.open(a.line).convert("RGBA")
    line = line.crop(bbox(line))
    w = round(line.width * a.height / line.height)
    if w > 1180:
        print("строка шире холста:", w)
        return 1
    line = line.convert("RGBa").resize((w, a.height), Image.LANCZOS).convert("RGBA")
    lb = bbox(logo)
    cx = (lb[0] + lb[2]) // 2
    y = lb[3] + a.gap
    if y + a.height > 600:
        print("строка не влезает по высоте:", y + a.height)
        return 1
    out = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
    out.paste(logo, (0, 0))
    out.alpha_composite(line, (cx - w // 2, y))
    out.save(a.dst)
    print(f"{a.dst}: 1200×600, строка {w}×{a.height} в ({cx - w // 2}, {y})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
