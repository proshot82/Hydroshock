#!/usr/bin/env python3
"""Оверлей юбки тележки из картинки на мадженте (ASSET_SPEC §2.7: ov_skirt, ov_skirt_open).

  python tools/assets/skirt_overlay.py ВХОД.png ВЫХОД.png [--top 0.21] [--side 0.09]

Маджента #FF00FF вырезается в прозрачность (мягкий край, без розовой каймы). Генератор рисует
верхнюю полосу ткани с бахромой толще, чем по спеке, поэтому кадр по вертикали переводится
кусочно: у верхней полосы срезается лишняя ткань сверху (бахрома остаётся в натуральную величину
и кончается на --top высоты кадра), а всё ниже нижнего края бахромы растягивается до низа —
боковые полотнища остаются стоять на полу. Бока не
трогаются; их ширина печатается для сверки со спекой (--side — норма, только для отчёта).
Нижний край бахромы ищется по средней трети ширины кадра. Результат — 1920×1080 RGBA.
"""
import argparse

import numpy as np
from PIL import Image, ImageFilter

W, H = 1920, 1080


def key(rgb):
    a = rgb.astype(float)
    d = np.sqrt((a[..., 0] - 255) ** 2 + a[..., 1] ** 2 + (a[..., 2] - 255) ** 2)
    alpha = np.clip((d - 60) / 80, 0, 1)
    al = Image.fromarray((alpha * 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(
        ImageFilter.GaussianBlur(0.8))
    alpha = np.asarray(al).astype(float) / 255
    # снять розовый налёт с полупрозрачного края: маджента = красный и синий выше зелёного
    spill = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None) * (1 - alpha)
    a[..., 0] -= spill
    a[..., 2] -= spill
    return np.clip(a, 0, 255), alpha


def remap_rows(arr, y_src, y_dst):
    """Строки [y_src - y_dst, y_src) → [0, y_dst) один к одному, [y_src, H) → [y_dst, H)."""
    out_y = np.arange(H, dtype=float)
    src = np.where(out_y < y_dst, out_y + (y_src - y_dst),
                   y_src + (out_y - y_dst) * (H - y_src) / (H - y_dst))
    idx = np.clip(np.round(src).astype(int), 0, H - 1)
    return arr[idx]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--top", type=float, default=0.21)
    ap.add_argument("--side", type=float, default=0.09)
    a = ap.parse_args(argv)
    im = Image.open(a.src).convert("RGB").resize((W, H), Image.LANCZOS)
    rgb, alpha = key(np.asarray(im))
    mid = alpha[:, W // 3: 2 * W // 3]
    rows = np.where((mid > 0.5).any(axis=1))[0]
    hem = int(rows.max()) + 1 if len(rows) else 0
    if hem > H // 2:
        raise SystemExit(f"нижний край бахромы на {hem} px — середина кадра не прозрачная, проверь картинку")
    target = round(a.top * H)
    if hem > target:
        rgb, alpha = remap_rows(rgb, hem, target), remap_rows(alpha, hem, target)
    row = alpha[H // 2]
    left = int(np.argmax(row < 0.5))
    right = W - int(np.argmax(row[::-1] < 0.5))
    out = np.dstack([rgb, alpha * 255]).astype("uint8")
    Image.fromarray(out, "RGBA").save(a.out)
    print(f"{a.out}: бахрома {hem}→{target} px ({target / H:.0%}); бока на середине высоты "
          f"слева {left / W:.1%}, справа {(W - right) / W:.1%} (норма ≈ {a.side:.0%})")


if __name__ == "__main__":
    main()
