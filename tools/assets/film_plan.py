#!/usr/bin/env python3
"""План на плёнке: рисунок тушью на белом → прозрачная плёнка 1400×980 RGBA (ASSET_SPEC §7.1).

  python tools/assets/film_plan.py РИСУНОК.png ВЫХОД.png --film hotel|1908|soviet [--src-width 1470]

Рисунок — перерисовка подложки tools/layout/plans_layout.py (3:2, плёнка 1400 px по центру),
поэтому сначала по центру срезается 1400×980. Линии становятся краской плёнки: альфа — от темноты
линии (белое — прозрачно), цвет — сама тушь рисунка, чуть насыщеннее. Под линиями — сама плёнка:
  hotel  — прозрачный пластиковый вкладыш: еле заметный холодный тон, скруглённые углы, блик по краю;
  1908   — восковка: тёплая полупрозрачная бумага с лёгкой неровностью, края чуть темнее;
  soviet — лекционная плёнка: прозрачная, серо-зелёная кайма и два отверстия под кольца сверху.
"""
import argparse

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1400, 980
FILM = {
    'hotel': dict(tint=(226, 234, 246), a=0.07, edge=(150, 170, 200), edge_a=0.45, radius=34),
    '1908': dict(tint=(238, 226, 196), a=0.52, edge=(170, 140, 95), edge_a=0.55, radius=6),
    'soviet': dict(tint=(222, 234, 226), a=0.10, edge=(90, 130, 105), edge_a=0.55, radius=14),
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out')
    ap.add_argument('--film', required=True, choices=FILM)
    a = ap.parse_args(argv)
    f = FILM[a.film]
    im = Image.open(a.src).convert('RGB')
    if im.size != (W, H):
        x0 = (im.width - W) // 2
        im = im.crop((x0, 0, x0 + W, H))
    rgb = np.asarray(im).astype(float)
    lum = rgb.mean(axis=2)
    ink_a = np.clip((242 - lum) / 170, 0, 1)
    # цвет линии: тушь рисунка, без белёсого ореола
    ink_rgb = np.clip(rgb - (255 - rgb) * 0.25, 0, 255)
    # плёнка
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((2, 2, W - 3, H - 3), radius=f['radius'], fill=255)
    if a.film == 'soviet':
        for cx in (W // 2 - 260, W // 2 + 260):
            ImageDraw.Draw(mask).ellipse((cx - 16, 28, cx + 16, 60), fill=0)
    film = np.asarray(mask).astype(float) / 255
    base_a = np.full((H, W), f['a'])
    if a.film == '1908':
        rng = np.random.default_rng(1908)
        noise = Image.fromarray((rng.random((H // 8, W // 8)) * 255).astype('uint8')).resize((W, H), Image.BICUBIC)
        base_a = base_a + (np.asarray(noise.filter(ImageFilter.GaussianBlur(6))).astype(float) / 255 - 0.5) * 0.12
    # край плёнки: кайма в несколько пикселей
    edge = np.asarray(mask.filter(ImageFilter.MinFilter(9))).astype(float) / 255
    rim = np.clip(film - edge, 0, 1)
    if a.film == 'soviet':
        holes = Image.new('L', (W, H), 0)
        for cx in (W // 2 - 260, W // 2 + 260):
            ImageDraw.Draw(holes).ellipse((cx - 20, 24, cx + 20, 64), outline=255, width=4)
        rim = np.maximum(rim, np.asarray(holes).astype(float) / 255)
    tint = np.array(f['tint'], float)
    edge_c = np.array(f['edge'], float)
    # слои: плёнка → кайма → линии (обычное наложение «поверх»)
    out_a = base_a * film
    out_rgb = np.broadcast_to(tint, (H, W, 3)).copy()
    ra = rim * f['edge_a']
    out_rgb = (out_rgb * (out_a * (1 - ra))[..., None] + edge_c * ra[..., None])
    out_a = out_a * (1 - ra) + ra
    out_rgb = np.where(out_a[..., None] > 0, out_rgb / np.maximum(out_a, 1e-6)[..., None], tint)
    la = ink_a * film
    new_a = la + out_a * (1 - la)
    out_rgb = (ink_rgb * la[..., None] + out_rgb * (out_a * (1 - la))[..., None]) / np.maximum(new_a, 1e-6)[..., None]
    res = np.dstack([np.clip(out_rgb, 0, 255), np.clip(new_a * 255, 0, 255)]).astype('uint8')
    Image.fromarray(res, 'RGBA').save(a.out)
    print(f'{a.out}: плёнка {a.film}, линии {int((ink_a > 0.3).sum())} px')


if __name__ == '__main__':
    main()
