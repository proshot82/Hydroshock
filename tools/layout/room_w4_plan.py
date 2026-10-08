#!/usr/bin/env python3
"""План зала прекраснодушия W4 с камерой (проект на утверждение). Вывод: docs/assets/w4_plan.png"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]
R = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', n)
B = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', n)
im = Image.new('RGB', (1500, 1180), 'white'); d = ImageDraw.Draw(im)
d.text((30, 15), "W4 зал прекраснодушия — план и камера (проект на утверждение)", fill='black', font=B(26))
d.text((30, 52), "север — вверх; зал к западу от вестибюля, служебный коридор — вдоль южной стены (план первого этажа)", fill=(90, 90, 90), font=R(16))
# зал
X0, Y0, X1, Y1 = 200, 110, 1180, 960
d.rectangle((X0, Y0, X1, Y1), fill=(232, 240, 255), outline='black', width=8)
# кайма мозаики
d.rectangle((X0 + 40, Y0 + 40, X1 - 40, Y1 - 40), outline=(40, 140, 150), width=6)
d.text((X0 + 50, Y1 - 110), "мозаика с каймой (улика: та же кайма на фото «Четвергъ»)", fill=(40, 120, 130), font=R(14))
# вестибюль и коридор
d.rectangle((X1, Y0, 1480, Y1), fill=(255, 248, 230), outline='black', width=4)
d.text((X1 + 20, Y0 + 15), "W2 вестибюль", fill='black', font=B(16))
d.rectangle((X0 - 120, Y1, X1 + 300, Y1 + 110), fill=(250, 240, 250), outline='black', width=4)
d.text((X0 - 100, Y1 + 70), "служебный коридор (→ на восток к арке за стойкой)", fill='black', font=R(15))
# парадные двери — восточная стена, северная часть
d.rectangle((X1 - 6, 230, X1 + 6, 370), fill=(255, 248, 230))
d.text((X1 + 15, 210), "парадные двери зала\n(в кадре — справа вдали)\nзаперты на засов,\nперед ними — канат\nна латунных столбиках", fill=(150, 20, 20), font=R(14))
for y in (245, 355):
    d.ellipse((X1 - 70, y - 8, X1 - 54, y + 8), fill=(200, 160, 60), outline='black')
d.line((X1 - 62, 245, X1 - 62, 355), fill=(150, 20, 40), width=4)
# доска почёта и латунная щель — восточная стена ближе к камере
d.rectangle((760, Y0 + 4, 1000, Y0 + 16), fill=(150, 110, 70))
d.text((740, Y0 + 75), "доска почёта (Z09) — северная стена, в кадре в глубине\nсправа от центра: рамки, бежевый прямоугольник,\n«Осторожно, окрашено»; рядом латунная щель", fill='black', font=R(14))
# служебная дверь — южная стена, западная треть (как на плане этажа)
DX0, DX1 = 580, 700
d.rectangle((DX0, Y1 - 6, DX1, Y1 + 6), fill=(232, 240, 255))
d.text((DX0 - 10, Y1 + 15), "служебная дверь зала\n(открывается внутрь)", fill=(0, 60, 160), font=R(14))
# лифт 1908 — западная стена, середина
d.rectangle((X0 - 110, 310, X0, 470), fill=(90, 90, 100), outline='black', width=3)
d.rectangle((X0 - 6, 320, X0 + 6, 460), fill=(200, 160, 60))
d.text((X0 - 190, 480), "шахта лифта 1908\n(вниз, в W5)", fill='black', font=R(14))
d.text((X0 + 20, 350), "решётка лифта + пост «Вниз/Вызов»\n(Z11); латунный порожек в мозаике;\nв начале закрыта зеркалом (состояние)", fill='black', font=R(14))
# лестничная каморка — северо-западный угол, дверь в северной части
d.rectangle((X0, Y0, X0 + 200, Y0 + 170), fill=(225, 225, 225), outline='black', width=5)
d.rectangle((X0 + 60, Y0 + 164, X0 + 150, Y0 + 176), fill=(232, 240, 255))
d.ellipse((X0 + 60, Y0 + 30, X0 + 140, Y0 + 110), outline='black', width=3)
d.ellipse((X0 + 90, Y0 + 60, X0 + 110, Y0 + 80), fill='black')
d.text((X0 + 215, Y0 + 20), "дверь «Служебное помещение» (в кадре — вдали слева)\n→ каморка с винтовой лестницей вниз", fill='black', font=R(14))
# колонны
for cx in (420, 960):
    for cy in (330, 700):
        d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=(180, 200, 205), outline='black', width=3)
d.text((975, 700), "колонны", fill='black', font=R(13))
# стекло над люком и стойка, архивный стол
d.rectangle((600, 430, 780, 560), fill=(200, 235, 245), outline=(40, 120, 160), width=4)
d.ellipse((655, 460, 725, 530), outline='black', width=3)
d.text((600, 400), "стекло над люком (подсвечено)", fill='black', font=R(14))
d.rectangle((800, 470, 820, 520), fill=(200, 160, 60)); d.text((828, 470), "стойка\n«Наследие»\n(бутылка —\nсостояние)", fill='black', font=R(13))
d.rectangle((560, 610, 820, 690), fill=(210, 190, 160), outline='black', width=3)
d.text((570, 625), "архивный стол (Z10):\nтубус, папка, журнал", fill='black', font=R(14))
# камера
cx, cy = 640, 948
d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill='black')
d.multiline_text((720, 880), "камера W4, 1,6 м — в проёме служебной двери, взгляд на север;\nширокий угол ~88° (в кадре: запад — слева, восток — справа)", fill='black', font=B(15))
import math
for ang in (-44, 44):
    a = math.radians(ang); dx, dy = math.sin(a), -math.cos(a)
    t = min(((X0 + 8 - cx) / dx) if dx < 0 else ((X1 - 8 - cx) / dx), (Y0 + 8 - cy) / dy)
    d.line((cx, cy, cx + dx * t, cy + dy * t), fill=(110, 110, 110), width=2)
im.save(ROOT / 'docs' / 'assets' / 'w4_plan.png')
