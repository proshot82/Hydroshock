#!/usr/bin/env python3
"""Проба загадки P05 на настоящих плёнках: подсвеченное стекло + три плана с подписями движка.

  python tools/assets/plans_preview.py ПАПКА_С_НОСИТЕЛЯМИ ВЫХОД.png

Берёт paper_lightbox.png и plan_hotel/1908/soviet.png из папки, метки — из
docs/assets/plans_markers.json (tools/layout/plans_layout.py), подписи — шрифтами §7.2
(отель — PT Sans, 1908 — Old Standard TT, профилакторий — PT Mono). Три кадра: каждая плёнка
отдельно (как в читалке), стопка по рамкам (источник в трёх местах) и стопка по люку
(источник на одной точке, номер 317 доворачивает — одна вертикаль).
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / 'assets' / 'fonts'
FONT = {'hotel': 'PTSans-Regular.ttf', '1908': 'OldStandard-Regular.ttf', 'soviet': 'PTMono-Regular.ttf'}
INK = {'hotel': (28, 52, 120), '1908': (110, 64, 30), 'soviet': (30, 110, 60)}
HATCH = (700, 860)


def labelled(folder, name, data):
    film = Image.open(Path(folder) / f'plan_{name}.png').convert('RGBA')
    d = ImageDraw.Draw(film)
    font = ImageFont.truetype(str(FONTS / FONT[name]), 26)
    for key, m in data['markers'].items():
        if not m['label']:
            continue
        x, y = m['x'], m['y']
        w = font.getlength(m['label'])
        side = m.get('side', 'r')
        if side == 'a':
            tx, ty = x - w / 2, y - 50
        elif side == 'bl':
            tx, ty = x - w + 14, y + 18
        elif side in ('b', 'b2'):
            tx, ty = x - w / 2, y + (18 if side == 'b' else 56)
        else:
            tx, ty = (x + 20 if side == 'r' and x + 20 + w < 1390 else x - 20 - w), y - 16
        d.text((tx, ty), m['label'], font=font, fill=INK[name] + (255,))
    return film


def main(folder, out):
    data = json.loads((ROOT / 'docs' / 'assets' / 'plans_markers.json').read_text(encoding='utf-8'))
    box = Image.open(Path(folder) / 'paper_lightbox.png').convert('RGBA')
    films = {n: labelled(folder, n, data[f'plan_{n}']) for n in ('hotel', '1908', 'soviet')}
    frames = []
    for n, f in films.items():
        im = box.copy()
        im.alpha_composite(f)
        frames.append((f'plan_{n}: отдельно, как в читалке', im))
    stack = box.copy()
    for f in films.values():
        stack.alpha_composite(f)
    frames.append(('по рамкам: источник в трёх местах', stack))
    al = box.copy()
    for n, f in films.items():
        sx, sy = data[f'plan_{n}']['source']
        rot = f.rotate(data[f'plan_{n}']['angle_deg'], center=(sx, sy), resample=Image.BICUBIC,
                       translate=(HATCH[0] - sx, HATCH[1] - sy))
        al.alpha_composite(rot)
    d = ImageDraw.Draw(al)
    d.line((HATCH[0], 0, HATCH[0], 980), fill=(220, 0, 0, 120), width=1)
    frames.append(('по люку и номеру 317: одна вертикаль', al))
    tw, th = 933, 653
    sheet = Image.new('RGB', (tw * 2 + 30, (th + 40) * 3 + 10), 'white')
    ds = ImageDraw.Draw(sheet)
    lab = ImageFont.truetype(str(FONTS / 'PTSans-Bold.ttf'), 24)
    for i, (t, im) in enumerate(frames):
        x, y = 10 + (i % 2) * (tw + 10), 10 + (i // 2) * (th + 40)
        ds.text((x, y), t, font=lab, fill='black')
        sheet.paste(im.convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 32))
    sheet.save(out)
    print(out)


if __name__ == '__main__':
    main(*sys.argv[1:3])
