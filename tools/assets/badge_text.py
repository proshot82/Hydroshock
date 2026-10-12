#!/usr/bin/env python3
"""Переписать мелкую надпись на табличке в кадре, когда генератор ошибся в буквах
(ASSET_SPEC §1.5: побуквенная сверка; бейдж Изольды — «И. Т. Итьева», решение автора 07.10.2026).

  python tools/assets/badge_text.py КАДР.png ВЫХОД.png --box X0,Y0,X1,Y1 --text "И. Т. Итьева"

--box — поле таблички внутри рамки (без рамки). Поле заливается цветом самой таблички
(медиана светлой половины пикселей поля, с лёгким переходом сверху вниз, как в кадре), надпись
рисуется в 8 раз крупнее шрифтом PT Sans Bold, сжимается по ширине до поля и уменьшается
Lanczos — так она мягкая, как нарисованная. Цвет букв — тёмный тон из того же поля.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / "assets" / "fonts" / "PTSans-Bold.ttf"
K = 8


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--box", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--fill", type=float, default=0.86, help="доля высоты поля под буквы")
    a = ap.parse_args(argv)
    x0, y0, x1, y1 = (int(v) for v in a.box.split(","))
    im = Image.open(a.src).convert("RGB")
    field = np.asarray(im.crop((x0, y0, x1, y1))).astype(float)
    lum = field.mean(axis=2)
    light = field[lum >= np.median(lum)]
    dark = field[lum <= np.percentile(lum, 10)]
    paper, ink = np.median(light, axis=0), np.median(dark, axis=0)
    w, h = x1 - x0, y1 - y0
    # фон поля: цвет таблички, сверху на 6 % светлее, снизу на 6 % темнее
    grad = np.linspace(1.06, 0.94, h)[:, None, None]
    bg = np.clip(paper[None, None, :] * grad * np.ones((h, w, 1)), 0, 255)
    big = Image.new("L", (w * K, h * K), 0)
    font = ImageFont.truetype(str(FONT), int(h * K * a.fill))
    l, t, r, b = font.getbbox(a.text)
    txt = Image.new("L", (r - l + 4, b - t + 4), 0)
    ImageDraw.Draw(txt).text((2 - l, 2 - t), a.text, font=font, fill=255)
    tw = min(txt.width, int(w * K * 0.94))
    th = min(txt.height, int(h * K * a.fill))
    txt = txt.resize((tw, th), Image.LANCZOS)
    big.paste(txt, ((w * K - tw) // 2, (h * K - th) // 2))
    mask = np.asarray(big.resize((w, h), Image.LANCZOS)).astype(float)[..., None] / 255
    out = bg * (1 - mask) + ink[None, None, :] * mask
    im.paste(Image.fromarray(out.astype("uint8")), (x0, y0))
    im.save(a.out)
    print(f"{a.out}: поле {w}×{h} px, бумага {paper.astype(int).tolist()}, чернила {ink.astype(int).tolist()}")


if __name__ == "__main__":
    main()
