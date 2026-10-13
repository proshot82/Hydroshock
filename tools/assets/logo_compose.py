#!/usr/bin/env python3
"""Логотип титула BJ3 (ASSET_SPEC §10): логотип BJ2 без изменений + строка «ГИДРОУДАР»
[+ римская «II» из труб справа от названия — замечание автора 12.10.2026].

  python tools/assets/logo_compose.py BJ2_LOGO.png СТРОКА.png ВЫХОД.png [--height 120] [--gap 40]
         [--numeral II.png --numeral-height 300 --numeral-top 40 --numeral-gap 30 --center all]

BJ2_LOGO — `proshot82/bj2` `assets/gfx/ui/logo_title.png` (1200×420 RGBA), кладётся
слева сверху байт в байт. Принятый `assets/gfx/ui/logo_title.png` BJ3 — склейка с «II»,
уменьшенная до 840×376 (12.10.2026); строка «ГИДРОУДАР» в нём по центру части BJ2
(поправка автора 13.10.2026, спека §10) — при повторной склейке брать --center logo. СТРОКА и «II» — генерации с прозрачным фоном: обрезаются по
силуэту (альфа > 8) и масштабируются до заданной высоты (Lanczos в предумноженной альфе).
«II» ставится справа от силуэта логотипа на --numeral-gap, верх — на --numeral-top;
холст расширяется вправо (высота 600). Строка — под логотипом с отступом --gap,
по центру логотипа BJ2 (--center logo) или всего холста (--center all).
"""
import argparse
import sys

from PIL import Image


def bbox(im):
    return im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()


def fit_h(im, h):
    im = im.crop(bbox(im))
    w = round(im.width * h / im.height)
    return im.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("logo")
    ap.add_argument("line")
    ap.add_argument("dst")
    ap.add_argument("--height", type=int, default=120)
    ap.add_argument("--gap", type=int, default=40)
    ap.add_argument("--numeral")
    ap.add_argument("--numeral-height", type=int, default=300)
    ap.add_argument("--numeral-top", type=int, default=40)
    ap.add_argument("--numeral-gap", type=int, default=30)
    ap.add_argument("--center", choices=["logo", "all"], default="logo")
    a = ap.parse_args(argv)
    logo = Image.open(a.logo).convert("RGBA")
    if logo.size != (1200, 420):
        print("логотип BJ2 не 1200×420:", logo.size)
        return 1
    lb = bbox(logo)
    W, num, nx = 1200, None, 0
    if a.numeral:
        num = fit_h(Image.open(a.numeral).convert("RGBA"), a.numeral_height)
        nx = lb[2] + a.numeral_gap
        W = max(W, nx + num.width + lb[0])           # справа такое же поле, как слева
    line = fit_h(Image.open(a.line).convert("RGBA"), a.height)
    if line.width > W - 20:
        print("строка шире холста:", line.width)
        return 1
    cx = (lb[0] + lb[2]) // 2 if a.center == "logo" else W // 2
    y = lb[3] + a.gap
    if y + a.height > 600:
        print("строка не влезает по высоте:", y + a.height)
        return 1
    out = Image.new("RGBA", (W, 600), (0, 0, 0, 0))
    out.paste(logo, (0, 0))
    if num is not None:
        out.alpha_composite(num, (nx, a.numeral_top))
    out.alpha_composite(line, (cx - line.width // 2, y))
    out.save(a.dst)
    msg = f"{a.dst}: {W}×600, строка {line.width}×{a.height} в ({cx - line.width // 2}, {y})"
    if num is not None:
        msg += f", «II» {num.width}×{num.height} в ({nx}, {a.numeral_top})"
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
