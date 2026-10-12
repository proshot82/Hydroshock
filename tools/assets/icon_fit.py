#!/usr/bin/env python3
"""Иконка предмета из прозрачной генерации: обрезка по силуэту и вписывание (ASSET_SPEC §6).

  python tools/assets/icon_fit.py ВХОД.png ВЫХОД.png [--size 128] [--fill 0.88]

Силуэт — пиксели с альфой > 8. Длинная сторона силуэта занимает --fill поля
(спека: 80–90 %), предмет по центру. Масштаб — Lanczos в предумноженной альфе
(без светлой каймы по краю); почти непрозрачное (альфа ≥ 250) доводится до 255.
Печатает долю поля, которую занял предмет.
"""
import argparse
import sys

from PIL import Image


def fit_icon(im, size=128, fill=0.88):
    im = im.convert("RGBA")
    a = im.getchannel("A").point(lambda v: 255 if v > 8 else 0)
    box = a.getbbox()
    if not box:
        raise ValueError("пустой силуэт")
    obj = im.crop(box)
    w, h = obj.size
    s = fill * size / max(w, h)
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    obj = obj.convert("RGBa").resize((nw, nh), Image.LANCZOS).convert("RGBA")
    al = obj.getchannel("A").point(lambda v: 255 if v >= 250 else v)
    obj.putalpha(al)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(obj, ((size - nw) // 2, (size - nh) // 2))
    return out, (nw / size, nh / size)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--size", type=int, default=128)
    ap.add_argument("--fill", type=float, default=0.88)
    a = ap.parse_args(argv)
    out, (fw, fh) = fit_icon(Image.open(a.src), a.size, a.fill)
    out.save(a.dst)
    print(f"{a.dst}: {a.size}x{a.size}, предмет {fw:.0%} × {fh:.0%} поля")
    return 0


if __name__ == "__main__":
    sys.exit(main())
