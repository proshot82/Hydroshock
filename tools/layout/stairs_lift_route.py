#!/usr/bin/env python3
"""Схема «лестница и лифт»: разрез и цепочка кадров (по сдаче Акта IV, DS2, и топологии 08.10.2026).

  python tools/layout/stairs_lift_route.py [--z12 ПУТЬ_К_ZOOM_Z12]

Вывод: docs/assets/stairs_lift_route.png. Кадры берутся из assets/gfx и work/higgsfield/variants;
Z12 — из принятого assets/gfx/zooms/zoom_z12.png, а пока его нет — из кандидата (ключ --z12).
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
R = lambda n: ImageFont.truetype(F, n)
B = lambda n: ImageFont.truetype(FB, n)
STAIR = (0, 70, 170)
LIFT = (190, 110, 0)
MARK = (220, 20, 20)
W, H = 1900, 1500

# кадр, подпись, обводки (x0, y0, x1, y1, цвет, номер) в координатах кадра 1920×1080
STAIRS = [
    ('assets/gfx/rooms/room_w4.png', '1. Зал W4: дверь «Служебное\nпомещение» в дальней стене',
     [(600, 250, 800, 560, MARK, '1')]),
    ('work/higgsfield/variants/room_w4__st_w4_stairs_open.png', '2. Дверь открыта: площадка\nс лампочкой, винтовая вниз',
     [(600, 250, 800, 560, MARK, '2')]),
    ('Z12', '3. Низ лестницы (Z12): площадка,\nшесть ступеней вниз, дверь конторы',
     [(0, 180, 470, 1000, STAIR, ''), (860, 100, 1100, 450, MARK, '3')]),
    ('assets/gfx/rooms/room_w6.png', '4. Контора W6 изнутри: справа — эта\nже дверь (ступени вверх), слева — в W5',
     [(1050, 60, 1240, 310, MARK, '3'), (680, 60, 860, 290, MARK, '4')]),
    ('assets/gfx/rooms/room_w5.png', '5. Приёмный пункт W5: дверь конторы\nза столом; слева — кабина лифта',
     [(1240, 190, 1440, 500, MARK, '4'), (30, 50, 390, 700, LIFT, 'Л')]),
]
LIFTR = [
    ('assets/gfx/zooms/zoom_z11.png', 'Л1. Зал W4: решётка лифта 1908,\nпост «Вызов / Вниз» (Z11)',
     [(620, 0, 1270, 1010, LIFT, 'Л')]),
    ('assets/gfx/rooms/room_w5.png', 'Л2. Шахта выходит в W5: та же\nкабина в скале, пост «Вверхъ»',
     [(30, 50, 390, 700, LIFT, 'Л')]),
]


def thumb(path, marks, tw, th, z12):
    p = Path(z12) if path == 'Z12' else ROOT / path
    im = Image.open(p).convert('RGB').resize((tw, th), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    k = tw / 1920
    for x0, y0, x1, y1, col, n in marks:
        d.rounded_rectangle((x0 * k, y0 * k, x1 * k, y1 * k), 8, outline=col, width=4)
        if n:
            d.ellipse((x0 * k - 2, y0 * k - 2, x0 * k + 30, y0 * k + 30), fill=col)
            d.text((x0 * k + 14, y0 * k + 14), n, fill='white', font=B(20), anchor='mm')
    return im


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--z12', default=str(ROOT / 'assets/gfx/zooms/zoom_z12.png'))
    a = ap.parse_args(argv)
    im = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(im)
    d.text((30, 15), 'Куда ведёт винтовая лестница и куда приходит лифт', fill='black', font=B(30))
    d.text((30, 58), 'по сдаче Акта IV (DS2) и топологии отеля 08.10.2026: внизу у лестницы одна дверь — '
           'в контору W6; лифт выходит в приёмный пункт W5; W5 и W6 — соседние, между ними дверь',
           fill=(90, 90, 90), font=R(17))

    # --- разрез (вид сбоку) ---
    d.text((30, 100), 'РАЗРЕЗ (вид сбоку, без масштаба)', fill=(120, 120, 120), font=B(19))
    rock = (232, 222, 205)
    d.rectangle((60, 330, 1840, 760), fill=rock)
    d.text((70, 340), 'скала под отелем', fill=(150, 130, 100), font=R(16))
    # зал W4
    d.rectangle((260, 150, 1380, 330), fill=(232, 240, 255), outline='black', width=3)
    d.text((560, 165), 'W4 зал прекраснодушия (уровень вестибюля)', fill='black', font=B(21))
    d.text((560, 196), 'в кадре W4: лифт — слева у стены, дверь «Служебное помещение» —\n'
           'в дальней стене между лифтом и доской почёта', fill='black', font=R(16))
    # шахта лифта
    d.rectangle((300, 150, 420, 640), fill=(250, 236, 205), outline=LIFT, width=4)
    d.rectangle((318, 220, 402, 320), fill=(205, 170, 90), outline=LIFT, width=2)
    d.text((324, 228), 'кабина', fill='black', font=R(15))
    for y in range(345, 600, 40):
        d.line((360, y, 360, y + 22), fill=LIFT, width=4)
    d.polygon(((345, 605), (375, 605), (360, 630)), fill=LIFT)
    d.text((432, 360), 'шахта лифта 1908\n(Лапидус едет в тележке,\nкак груз)', fill=LIFT, font=B(16))
    # лестничная клетка
    d.rectangle((1380, 150, 1560, 560), fill=(225, 233, 245), outline=STAIR, width=4)
    d.line((1470, 175, 1470, 545), fill=STAIR, width=4)
    for i, y in enumerate(range(180, 540, 30)):
        x0, x1 = (1395, 1545) if i % 2 == 0 else (1545, 1395)
        d.line((x0, y, x1, y + 30), fill=STAIR, width=3)
    d.text((1575, 160), 'дверь «Служебное\nпомещение» → площадка\nс лампочкой →\nвинтовая лестница\nВНИЗ', fill=STAIR, font=B(16))
    d.rectangle((1372, 245, 1388, 325), fill=MARK)
    d.ellipse((1352, 222, 1384, 254), fill=MARK)
    d.text((1368, 238), '1', fill='white', font=B(20), anchor='mm')
    # низ: W5 — W6 — Z12
    y0, y1 = 560, 740
    d.rectangle((260, y0, 700, y1), fill=(220, 240, 238), outline='black', width=3)
    d.text((440, y0 + 10), 'W5 приёмный\nпункт', fill='black', font=B(19))
    d.text((440, y0 + 64), 'стол приёма;\nлифт приходит\nсюда (пост\n«Вверхъ»)', fill='black', font=R(15))
    d.rectangle((780, y0, 1180, y1), fill=(220, 240, 238), outline='black', width=3)
    d.text((795, y0 + 10), 'W6 контора', fill='black', font=B(19))
    d.text((795, y0 + 40), 'грот с трубой и маховиком,\nкаменный уступ с журналом', fill='black', font=R(15))
    d.rectangle((700, 640, 780, 655), fill=MARK)
    d.ellipse((724, 600, 756, 632), fill=MARK)
    d.text((740, 616), '4', fill='white', font=B(20), anchor='mm')
    d.text((690, 665), 'дверь\nW5 ↔ W6', fill='black', font=R(14))
    # ступени вверх от двери конторы к площадке Z12
    d.rectangle((1180, 640, 1196, 735), fill=MARK)
    d.ellipse((1172, 600, 1204, 632), fill=MARK)
    d.text((1188, 616), '3', fill='white', font=B(20), anchor='mm')
    for i in range(6):
        x = 1200 + i * 30
        d.rectangle((x, 735 - (i + 1) * 28, x + 30, 740), fill=(200, 190, 175), outline=(120, 110, 95))
    d.rectangle((1380, 560, 1560, 572), fill=(170, 160, 150))
    d.text((1390, 580), 'площадка Z12\n(низ лестницы)', fill='black', font=B(16))
    d.text((1210, 745), 'шесть ступеней вниз к двери конторы', fill='black', font=R(14))
    d.text((1575, 590), 'здесь кончается\nлестница: других\nдверей нет', fill=STAIR, font=R(15))
    # итог
    d.text((60, 790), 'Лестница и лифт сходятся внизу не в одной точке: лифт привозит в W5, лестница приводит к двери W6. '
           'W5 и W6 соединены дверью.', fill='black', font=B(17))
    d.text((60, 818), 'До доклада Изольды дверь конторы на лестницу заперта (Акт II: стук — тишина); '
           'после доклада открыты обе двери — путь по лестнице сквозной: W4 → Z12 → W6 → W5.', fill='black', font=R(17))

    # --- цепочки кадров ---
    tw, th, gap = 350, 197, 22
    y = 870
    d.text((30, y), 'ПО ЛЕСТНИЦЕ — ногами (человек — да, тележка — нет)', fill=STAIR, font=B(20))
    y += 36
    for i, (p, cap, marks) in enumerate(STAIRS):
        x = 30 + i * (tw + gap)
        im.paste(thumb(p, marks, tw, th, a.z12), (x, y))
        d.multiline_text((x, y + th + 6), cap, fill='black', font=R(15))
        if i < len(STAIRS) - 1:
            d.text((x + tw + 2, y + th // 2 - 16), '→', fill=STAIR, font=B(22))
    y += th + 70
    d.text((30, y), 'НА ЛИФТЕ — грузовом (Лапидус в тележке)', fill=LIFT, font=B(20))
    y += 36
    for i, (p, cap, marks) in enumerate(LIFTR):
        x = 30 + i * (tw + gap)
        im.paste(thumb(p, marks, tw, th, a.z12), (x, y))
        d.multiline_text((x, y + th + 6), cap, fill='black', font=R(15))
        if i == 0:
            d.text((x + tw + 2, y + th // 2 - 16), '→', fill=LIFT, font=B(22))
    d.multiline_text((30 + 2 * (tw + gap) + 20, y + 10),
                     'Красные рамки с номерами — одна и та же дверь на разных кадрах:\n'
                     '1–2 — дверь «Служебное помещение» в зале W4;\n'
                     '3 — дверь конторы: на Z12 снаружи (с площадки), на W6 изнутри (справа, ступени вверх);\n'
                     '4 — дверь между конторой и приёмным пунктом: на W6 слева, на W5 за столом\n'
                     '      (табличка «Контора старшаго по водѣ»).\n'
                     'Рамка «Л» — кабина лифта: наверху в зале W4 (Z11), внизу в W5 слева.\n'
                     'Боковая дверь в W5 справа — кладовая, никуда не ведёт.',
                     fill='black', font=R(16), spacing=6)
    out = ROOT / 'docs' / 'assets' / 'stairs_lift_route.png'
    im.save(out)
    print(out)


if __name__ == '__main__':
    main()
