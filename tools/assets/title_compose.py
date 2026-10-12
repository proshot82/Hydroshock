#!/usr/bin/env python3
"""Фон титула ред. 3 (замечание автора 12.10.2026): небо + отель в разрезе, склейка.

  python tools/assets/title_compose.py НЕБО.png РАЗРЕЗ.png ВЫХОД.png [--width 1180] [--bottom 0]
         [--preview ПРЕВЬЮ.png --logo LOGO.png --logo-scale 0.8 --buttons left|center]

НЕБО — генерация 16:9, доводится до 1920×1080 (кадрирование по центру, Lanczos).
РАЗРЕЗ — генерация с прозрачным фоном: обрезается по силуэту (альфа > 8), масштабируется
до ширины --width в предумноженной альфе и ставится центром на --cx, низом на --bottom px от
нижнего края кадра (отрицательное — уходит за край). ВЫХОД — 1920×1080 RGB.
--preview дополнительно рисует, как экран будет выглядеть в игре: логотип сверху над разрезом
(в масштабе --logo-scale) и четыре кнопки меню — столбиком посередине, как в BJ2, или слева.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hf_fetch import fit  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def scaled(im, w=None, k=None):
    im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
    if k is None:
        k = w / im.width
    size = (round(im.width * k), round(im.height * k))
    return im.convert("RGBa").resize(size, Image.LANCZOS).convert("RGBA")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("sky")
    ap.add_argument("cut")
    ap.add_argument("dst")
    ap.add_argument("--width", type=int, default=1180)
    ap.add_argument("--bottom", type=int, default=0)
    ap.add_argument("--cx", type=int, default=960, help="центр разреза и логотипа по x")
    ap.add_argument("--preview")
    ap.add_argument("--logo")
    ap.add_argument("--logo-scale", type=float, default=0.8)
    ap.add_argument("--logo-top", type=int, default=20)
    ap.add_argument("--buttons", choices=["left", "center"], default="left")
    a = ap.parse_args(argv)
    bg = fit(Image.open(a.sky).convert("RGB"), 1920, 1080).convert("RGBA")
    cut = scaled(Image.open(a.cut).convert("RGBA"), w=a.width)
    x, y = a.cx - cut.width // 2, 1080 - a.bottom - cut.height
    bg.alpha_composite(cut, (x, y))
    out = bg.convert("RGB")
    out.save(a.dst)
    lum = round(ImageStat.Stat(out.convert("L")).mean[0] / 2.55, 1)
    print(f"{a.dst}: разрез {cut.width}×{cut.height} в ({x}, {y}), яркость {lum} %")
    if a.preview:
        pv = out.convert("RGBA")
        if a.logo:
            lg = scaled(Image.open(a.logo).convert("RGBA"), k=a.logo_scale)
            pv.alpha_composite(lg, (a.cx - lg.width // 2, a.logo_top))
            print(f"логотип {lg.width}×{lg.height}, низ на {a.logo_top + lg.height}")
        d = ImageDraw.Draw(pv)
        font = ImageFont.truetype(str(ROOT / "assets/fonts/PTSans-Bold.ttf"), 34)
        for i, t in enumerate(["Начать", "Продолжить", "Настройки", "Выход"]):
            bx, by = (60, 560 + i * 92) if a.buttons == "left" else (760, 640 + i * 92)
            d.rounded_rectangle((bx, by, bx + 400, by + 72), 12, fill=(34, 34, 42, 235),
                                outline=(200, 160, 80), width=2)
            d.text((bx + 200, by + 36), t, font=font, fill=(235, 225, 200), anchor="mm")
        pv.convert("RGB").save(a.preview)
    return 0


if __name__ == "__main__":
    sys.exit(main())
