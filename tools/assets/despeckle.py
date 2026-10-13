#!/usr/bin/env python3
"""«Снег» — одиночные тёмные или светлые точки после многократных перегенераций: найти и убрать.

  python tools/assets/despeckle.py report ПАПКА|ФАЙЛ …            — сколько точек на каждой картинке
  python tools/assets/despeckle.py fix ВХОД.png ВЫХОД.png [--thr 38] [--max 6] [--sheet ЛИСТ.png]

Точка — связная группа не больше --max пикселей, которая темнее (или светлее) медианы
окрестности 7×7 больше чем на --thr по яркости, и вокруг которой светлый (тёмный) фон.
Контуры рисунка — длинные связные линии — под это правило не попадают и не трогаются.
Найденные точки заменяются медианой окрестности. --sheet — лист «было / стало» кусками ×3.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

try:
    from scipy import ndimage
except ImportError:  # pragma: no cover
    ndimage = None


def specks(img, thr=38, max_px=6):
    g = np.asarray(img.convert("L"), dtype=np.int16)
    med = np.asarray(img.convert("L").filter(ImageFilter.MedianFilter(7)), dtype=np.int16)
    mask = np.abs(g - med) > thr
    lab, n = ndimage.label(mask)
    if not n:
        return np.zeros_like(mask)
    sizes = ndimage.sum(mask, lab, index=np.arange(1, n + 1))
    small = np.zeros(n + 1, dtype=bool)
    small[1:] = sizes <= max_px
    sel = small[lab]
    # у настоящей точки вокруг почти нет других отклонений (иначе это штрих рисунка)
    ring = ndimage.binary_dilation(sel, iterations=2) & ~sel
    busy = ndimage.uniform_filter((mask & ~sel).astype(np.float32), size=7) > 0.12
    sel &= ~busy
    return sel


def fix(img, sel):
    rgb = img.convert("RGB")
    med = np.asarray(rgb.filter(ImageFilter.MedianFilter(7)))
    a = np.asarray(rgb).copy()
    grow = ndimage.binary_dilation(sel, iterations=1)
    a[grow] = med[grow]
    out = Image.fromarray(a)
    if img.mode == "RGBA":
        out.putalpha(img.getchannel("A"))
    return out


def main(argv=None):
    if ndimage is None:
        sys.exit("нужен scipy")
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["report", "fix"])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--thr", type=int, default=38)
    ap.add_argument("--max", type=int, default=6)
    ap.add_argument("--sheet")
    a = ap.parse_args(argv)
    if a.mode == "report":
        files = []
        for p in a.paths:
            p = Path(p)
            files += sorted(p.glob("*.png")) if p.is_dir() else [p]
        rows = []
        for f in files:
            im = Image.open(f)
            if im.mode == "RGBA":
                continue
            s = specks(im, a.thr, a.max)
            rows.append((int(s.sum()), f))
        for n, f in sorted(rows, reverse=True):
            print(f"{n:7d}  {f}")
        return 0
    src, dst = Path(a.paths[0]), Path(a.paths[1])
    im = Image.open(src)
    s = specks(im, a.thr, a.max)
    out = fix(im, s)
    out.save(dst)
    print(f"{src.name}: точек {int(s.sum())} пикселей → {dst}")
    if a.sheet:
        ys, xs = np.nonzero(s)
        if len(xs):
            # три куска с наибольшей густотой точек
            dens = ndimage.uniform_filter(s.astype(np.float32), size=121)
            crops = []
            d = dens.copy()
            for _ in range(3):
                y, x = np.unravel_index(np.argmax(d), d.shape)
                x0, y0 = max(0, x - 100), max(0, y - 70)
                crops.append((x0, y0, x0 + 200, y0 + 140))
                d[max(0, y - 150):y + 150, max(0, x - 200):x + 200] = 0
            sheet = Image.new("RGB", (1200 + 20, 3 * 420 + 40), "white")
            dr = ImageDraw.Draw(sheet)
            for i, c in enumerate(crops):
                sheet.paste(im.convert("RGB").crop(c).resize((600, 420), Image.NEAREST), (0, 30 + i * 420))
                sheet.paste(out.convert("RGB").crop(c).resize((600, 420), Image.NEAREST), (620, 30 + i * 420))
            dr.text((10, 8), f"{src.name}: было (×3)", fill="black")
            dr.text((630, 8), "стало (×3)", fill="black")
            sheet.save(a.sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
