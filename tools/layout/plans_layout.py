#!/usr/bin/env python3
"""Три плана на плёнках (ASSET_SPEC §7.1, загадка P05 Акта II): точная раскладка меток.

  python tools/layout/plans_layout.py

Каждый план — разрез здания (вид сбоку), как его нарисовала своя эпоха: отель (карта для гостей,
симметричный фасад и купол, которого нет), водолечебница 1908 года (восковка), профилакторий
(лекционная плёнка). Здание у всех одно: точки заданы в общих «мировых» координатах — от источника
(0, 0) вверх, номер 317 — на 640 px прямо над источником. Каждая плёнка рисует здание со своим
сдвигом и наклоном, поэтому:
  * сложенные по рамкам (как листы в пачке) — контуры похожи, а источник в трёх разных местах;
  * каждая плёнка, положенная нарисованным источником на люк и довёрнутая по номеру 317, ложится
    в одно: источник → контора → … → номер 317 на одной вертикали; три имени зала — друг на друге;
    «Техническое помещение» отеля — ровно на «Конторе старшаго по водѣ»; купол уезжает в сторону.

Вывод:
  docs/assets/plans_markers.json — метки каждой плёнки в пикселях плёнки 1400×980 (их подписывает
      движок текстом DOC.map_*), источник и номер 317, угол плёнки; движок по ним совмещает;
  docs/assets/plans_alignment.png — проверка: стопка по рамкам и стопка по люку;
  work/higgsfield/layout/plan_<эпоха>_mock.png — подложка для генератора (3:2, плёнка по центру).
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
W, H = 1400, 980          # плёнка
MW = 1470                 # подложка 3:2 для генератора: плёнка по центру, по 35 px полей
L = 640                   # от источника до номера 317

# мировые точки: (dx, вверх) от источника
WORLD = {
    'source': (0, 0),
    'office': (0, 150),          # контора старшего по воде / «Техническое помещение»
    'reception': (-265, 150),    # приёмный пункт
    'stairs': (180, 240),        # служебная лестница (между низом и залом)
    'service_door': (190, 330),  # дверь «Служебное помещение» наверху лестницы
    'hall': (-220, 330),         # зал: водолечения / оздоровления / прекраснодушия
    'mirror': (-385, 330),       # «Зеркало прекраснодушия» (за ним лифт — на планах лифта нет)
    'laundry': (330, 330),       # прачечная / «Декоративная стена»
    'room317': (0, L),           # ванная № 17 / палата 317 / номер 317
}

FILMS = {
    'hotel': dict(S=(830, 880), angle=0.0, ink=(28, 52, 120),
                  labels={'hall': ('Зал прекраснодушия', 'b2'), 'mirror': ('Зеркало прекраснодушия', 'b'),
                          'laundry': ('Декоративная стена', 'bl'), 'service_door': ('Служебное помещение', 'b2'),
                          'office': 'Техническое помещение', 'room317': 'Номер 317', 'dome': 'Купол',
                          'source': None},
                  dome=(680, 118), facade=(110, 1250)),
    '1908': dict(S=(600, 860), angle=5.0, ink=(110, 64, 30),
                 labels={'hall': 'Залъ водолѣченія', 'reception': 'Пріёмный пунктъ',
                         'office': 'Контора старшаго по водѣ', 'stairs': 'Лѣстница служебная',
                         'room317': 'Ванная № 17', 'source': 'Источникъ'}),
    'soviet': dict(S=(880, 900), angle=-4.0, ink=(30, 110, 60),
                   labels={'hall': 'Зал оздоровления', 'laundry': 'Прачечная', 'room317': 'Палата 317',
                           'stairs': 'Лестница служебная', 'reception': 'Приёмный пункт',
                           'source': 'Источник'}),
}


def to_film(f, dx, up):
    a = math.radians(f['angle'])
    x, y = dx, -up
    return (f['S'][0] + x * math.cos(a) - y * math.sin(a), f['S'][1] + x * math.sin(a) + y * math.cos(a))


def poly(f, pts):
    return [to_film(f, *p) for p in pts]


def rect(f, x0, u0, x1, u1):
    return poly(f, [(x0, u0), (x1, u0), (x1, u1), (x0, u1), (x0, u0)])


def draw_plan(name, f, d, ox=0, width=3):
    ink = f['ink']
    line = lambda pts, w=width: d.line([(x + ox, y) for x, y in pts], fill=ink, width=w, joint='curve')
    # этажи и комнаты (одно здание на всех плёнках)
    if name == 'hotel':
        x0, x1 = f['facade']; c = (x0 + x1) / 2
        # «лицом к гостю»: симметричный фасад, купол по центру, колонны
        d.rectangle((x0 + ox, 150, x1 + ox, 900), outline=ink, width=width)
        for k in range(1, 4):
            d.line((x0 + ox, 150 + k * 190, x1 + ox, 150 + k * 190), fill=ink, width=2)
        for xx in range(int(x0) + 60, int(x1), 110):
            d.rectangle((xx + ox, 190, xx + 34 + ox, 250), outline=ink, width=2)
            d.rectangle((xx + ox, 380, xx + 34 + ox, 440), outline=ink, width=2)
        d.arc((c - 150 + ox, 30, c + 150 + ox, 270), 180, 360, fill=ink, width=width)
        d.line((c + ox, 30, c + ox, 0), fill=ink, width=2)
        for xx in (x0 + 20, x1 - 40):
            d.rectangle((xx + ox, 560, xx + 20 + ox, 900), outline=ink, width=2)
    else:
        line(rect(f, -420, 90, 420, 720))                         # контур
        for u in (270, 410, 560):
            line(poly(f, [(-420, u), (420, u)]), 2)               # перекрытия
        line(rect(f, -420, 90, -110, 210), 2)                      # приёмный пункт
        line(rect(f, -90, 90, 120, 210), 2)                        # контора
        steps = [(140 + 12 * i, 90 + 30 * i) for i in range(7)]
        line(poly(f, [p for s in steps for p in (s, (s[0] + 12, s[1]))]), 2)   # лестница
        line(rect(f, -60, 580, 60, 700), 2)                        # номер 317
        line(poly(f, [(0, 35), (0, 580)]), 4)                      # труба
        for xx in range(-380, 380, 120):
            line(rect(f, xx, 450, xx + 60, 520), 1)
            line(rect(f, xx, 600, xx + 60, 680), 1) if abs(xx) > 90 else None
        if name == '1908':                                         # ванные по кругу в зале
            cx, cu = -220, 330
            for k in range(8):
                a = 2 * math.pi * k / 8
                px, pu = cx + 95 * math.cos(a), cu + 40 * math.sin(a)
                line(rect(f, px - 14, pu - 8, px + 14, pu + 8), 1)
    # источник
    sx, sy = to_film(f, 0, 0)
    d.ellipse((sx - 60 + ox, sy - 32, sx + 60 + ox, sy + 32), outline=ink, width=width)
    for k in (-12, 4):
        d.arc((sx - 40 + ox, sy + k - 6, sx + ox, sy + k + 6), 0, 180, fill=ink, width=2)
        d.arc((sx + ox, sy + k - 6, sx + 40 + ox, sy + k + 6), 180, 360, fill=ink, width=2)


def markers(name, f):
    """Метки плёнки. Подпись ставит движок: side — с какой стороны от метки (r — справа, l — слева,
    a — над меткой, b — под ней, b2 — под ней вторым рядом, bl — под ней, концом к метке; по умолчанию справа, а если не влезает в плёнку — слева)."""
    out = {}
    for key, label in f['labels'].items():
        label, side = label if isinstance(label, tuple) else (label, 'r')
        if key == 'dome':
            x, y = f['dome']
        else:
            x, y = to_film(f, *WORLD[key])
        assert 40 < x < W - 40 and 40 < y < H - 40, (name, key, x, y)
        out[key] = {'x': round(x), 'y': round(y), 'label': label, 'side': side}
    return out


def mark(d, x, y, ink, ox=0, r=13):
    d.ellipse((x - r + ox, y - r, x + r + ox, y + r), outline=ink, width=3)
    d.ellipse((x - 3 + ox, y - 3, x + 3 + ox, y + 3), fill=ink)


def main():
    data = {}
    lay = ROOT / 'work' / 'higgsfield' / 'layout'
    lay.mkdir(parents=True, exist_ok=True)
    for name, f in FILMS.items():
        m = markers(name, f)
        sx, sy = to_film(f, 0, 0)
        rx, ry = to_film(f, 0, L)
        data[f'plan_{name}'] = {'size': [W, H], 'source': [round(sx, 1), round(sy, 1)],
                                'room317': [round(rx, 1), round(ry, 1)], 'angle_deg': f['angle'],
                                'markers': m}
        im = Image.new('RGB', (MW, H), 'white')
        d = ImageDraw.Draw(im)
        ox = (MW - W) // 2
        draw_plan(name, f, d, ox)
        for v in m.values():
            mark(d, v['x'], v['y'], f['ink'], ox)
        im.save(lay / f'plan_{name}_mock.png')
    (ROOT / 'docs' / 'assets' / 'plans_markers.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    # проверка: по рамкам и по люку
    font = ImageFont.truetype(F, 18); fb = ImageFont.truetype(FB, 24)
    sheet = Image.new('RGB', (2 * W + 60, H + 90), 'white')
    ds = ImageDraw.Draw(sheet)
    ds.text((20, 15), 'Стопка по рамкам: источник в трёх местах', font=fb, fill='black')
    ds.text((W + 40, 15), 'Стопка по люку (источник + номер 317): одна вертикаль', font=fb, fill='black')
    for k, (name, f) in enumerate(FILMS.items()):
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        draw_plan(name, f, dl, 0, 2)
        for v in data[f'plan_{name}']['markers'].values():
            mark(dl, v['x'], v['y'], f['ink'])
        sheet.paste(layer, (20, 60), layer)
        # совмещение: источник → (700, 860), поворот на −angle
        sx, sy = data[f'plan_{name}']['source']
        rot = layer.rotate(f['angle'], center=(sx, sy), resample=Image.BICUBIC,
                           translate=(700 - sx, 860 - sy))
        sheet.paste(rot, (W + 40, 60), rot)
    ds.line((W + 40 + 700, 60, W + 40 + 700, 60 + H), fill=(200, 0, 0), width=1)
    ds.text((W + 50, H + 60), 'красная линия — вертикаль через люк; синий — отель, коричневый — 1908, зелёный — профилакторий',
            font=font, fill=(90, 90, 90))
    sheet.save(ROOT / 'docs' / 'assets' / 'plans_alignment.png')
    print(json.dumps({k: (v['source'], v['room317']) for k, v in data.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
