#!/usr/bin/env python3
"""Лист-превью для автора: python tools/assets/contact_sheet.py ВЫХОД.png КОЛОНОК подпись=файл ..."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]


def main(argv):
    out, cols, items = argv[0], int(argv[1]), [a.split("=", 1) for a in argv[2:]]
    font = ImageFont.truetype(str(ROOT / "assets/fonts/PTSans-Bold.ttf"), 26)
    ims = [(n, Image.open(f).convert("RGBA")) for n, f in items]
    w = 512 if ims[0][1].width <= ims[0][1].height else 960
    h = round(w * ims[0][1].height / ims[0][1].width)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (w + 16) + 16, rows * (h + 56) + 16), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(ims):
        x, y = 16 + (i % cols) * (w + 16), 16 + (i // cols) * (h + 56)
        bg = Image.new("RGBA", (w, h), (30, 30, 30, 255))
        bg.alpha_composite(im.resize((w, h), Image.LANCZOS))
        sheet.paste(bg.convert("RGB"), (x, y + 36))
        d.text((x, y), n, font=font, fill=(240, 220, 150))
    sheet.save(out)


if __name__ == "__main__":
    main(sys.argv[1:])
