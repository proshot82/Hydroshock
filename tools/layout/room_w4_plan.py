#!/usr/bin/env python3
"""План зала прекраснодушия W4 с камерой (ред. 2: без окон в стенах, лестница за северной стеной). Вывод: docs/assets/w4_plan.png"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]
R = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', n)
B = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', n)
im = Image.new('RGB', (1500, 1360), 'white'); d = ImageDraw.Draw(im)
d.text((30, 15), "W4 зал прекраснодушия — план и камера (ред. 2, на утверждение)", fill='black', font=B(26))
d.text((30, 52), "север — вверх; зал к западу от вестибюля, служебный коридор — вдоль южной стены (план первого этажа)", fill=(90, 90, 90), font=R(16))
d.text((30, 76), "окон в стенах зала нет: он внутри здания, свет — сверху, через стеклянный фонарь в потолке (1908)", fill=(150, 20, 20), font=B(16))
OY = 180
X0, Y0, X1, Y1 = 200, 110 + OY, 1180, 960 + OY
# помещения отеля за северной и западной стенами (вне игры)
d.rectangle((X0 - 150, 110, X1, Y0), fill=(240, 240, 240), outline='black', width=4)
d.text((X0 + 330, 130), "другие помещения отеля (вне игры)", fill=(120, 120, 120), font=R(15))
d.rectangle((40, Y0, X0, Y1), fill=(240, 240, 240), outline='black', width=4)
# зал
d.rectangle((X0, Y0, X1, Y1), fill=(232, 240, 255), outline='black', width=8)
# фонарь верхнего света
d.rectangle((420, Y0 + 230, 960, Y0 + 560), outline=(200, 160, 60), width=3)
d.text((440, Y0 + 538), "стеклянный фонарь в потолке (над серединой зала)", fill=(150, 110, 30), font=R(13))
# кайма мозаики
d.rectangle((X0 + 40, Y0 + 40, X1 - 40, Y1 - 40), outline=(40, 140, 150), width=6)
d.text((X0 + 50, Y1 - 110), "мозаика с каймой (улика: та же кайма на фото «Четвергъ»)", fill=(40, 120, 130), font=R(14))
# вестибюль и коридор
d.rectangle((X1, Y0, 1480, Y1), fill=(255, 248, 230), outline='black', width=4)
d.text((X1 + 20, Y0 + 15), "W2 вестибюль", fill='black', font=B(16))
d.rectangle((X0 - 160, Y1, X1 + 300, Y1 + 110), fill=(250, 240, 250), outline='black', width=4)
d.text((X0 - 140, Y1 + 70), "служебный коридор (→ на восток к арке за стойкой)", fill='black', font=R(15))
# парадные двери — восточная стена, северная часть
d.rectangle((X1 - 6, 230 + OY, X1 + 6, 370 + OY), fill=(255, 248, 230))
d.text((X1 + 15, 210 + OY), "парадные двери зала\n(в кадре — справа вдали)\nзаперты на засов,\nперед ними — канат\nна латунных столбиках", fill=(150, 20, 20), font=R(14))
for y in (245 + OY, 355 + OY):
    d.ellipse((X1 - 70, y - 8, X1 - 54, y + 8), fill=(200, 160, 60), outline='black')
d.line((X1 - 62, 245 + OY, X1 - 62, 355 + OY), fill=(150, 20, 40), width=4)
# доска почёта — северная стена, правее центра
d.rectangle((760, Y0 + 4, 1000, Y0 + 16), fill=(150, 110, 70))
d.text((740, Y0 + 75), "доска почёта (Z09) — северная стена, в кадре в глубине\nсправа от центра: рамки, бежевый прямоугольник,\n«Осторожно, окрашено»; рядом латунная щель", fill='black', font=R(14))
# служебная дверь — южная стена (как на плане этажа)
DX0, DX1 = 580, 700
d.rectangle((DX0, Y1 - 6, DX1, Y1 + 6), fill=(232, 240, 255))
d.text((DX0 - 10, Y1 + 15), "служебная дверь зала\n(открывается внутрь)", fill=(0, 60, 160), font=R(14))
# лифт 1908 — западная стена
d.rectangle((X0 - 110, 310 + OY, X0, 470 + OY), fill=(90, 90, 100), outline='black', width=3)
d.rectangle((X0 - 6, 320 + OY, X0 + 6, 460 + OY), fill=(200, 160, 60))
d.text((50, 480 + OY), "шахта лифта 1908\n(вниз, в W5)", fill='black', font=R(14))
d.text((X0 + 20, 350 + OY), "решётка лифта + пост «Вниз/Вызов»\n(Z11); латунный порожек в мозаике;\nв начале закрыта зеркалом (состояние)", fill='black', font=R(14))
# лестничная клетка — за северной стеной, дверь в северной стене (левая часть)
SX0, SX1 = 300, 520
d.rectangle((SX0, Y0 - 150, SX1, Y0), fill=(225, 225, 225), outline='black', width=5)
d.ellipse((SX0 + 70, Y0 - 125, SX0 + 150, Y0 - 45), outline='black', width=3)
d.ellipse((SX0 + 100, Y0 - 95, SX0 + 120, Y0 - 75), fill='black')
d.text((SX0 + 160, Y0 - 120), "лестничная клетка:\nвинтовая лестница\nвниз", fill='black', font=R(13))
d.rectangle((SX0 + 60, Y0 - 6, SX0 + 160, Y0 + 6), fill=(232, 240, 255))
d.text((X0 + 20, Y0 + 20), "дверь «Служебное помещение» в северной стене (в кадре — вдали слева),\nглухая стена вокруг, за ней — лестничная клетка", fill='black', font=R(14))
# колонны
for cx in (420, 960):
    for cy in (330 + OY, 700 + OY):
        d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=(180, 200, 205), outline='black', width=3)
d.text((975, 700 + OY), "колонны", fill='black', font=R(13))
# стекло над люком и стойка, архивный стол
d.rectangle((600, 430 + OY, 780, 560 + OY), fill=(200, 235, 245), outline=(40, 120, 160), width=4)
d.ellipse((655, 460 + OY, 725, 530 + OY), outline='black', width=3)
d.text((600, 400 + OY), "стекло над люком (подсвечено)", fill='black', font=R(14))
d.rectangle((800, 470 + OY, 820, 520 + OY), fill=(200, 160, 60)); d.text((828, 470 + OY), "стойка\n«Наследие»\n(бутылка —\nсостояние)", fill='black', font=R(13))
d.rectangle((560, 610 + OY, 820, 690 + OY), fill=(210, 190, 160), outline='black', width=3)
d.text((570, 625 + OY), "архивный стол (Z10):\nтубус, папка, журнал", fill='black', font=R(14))
# камера
cx, cy = 640, 948 + OY
d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill='black')
d.multiline_text((720, 880 + OY), "камера W4, 1,6 м — в проёме служебной двери, взгляд на север;\nширокий угол ~88° (в кадре: запад — слева, восток — справа)", fill='black', font=B(15))
for ang in (-44, 44):
    a = math.radians(ang); dx, dy = math.sin(a), -math.cos(a)
    t = min(((X0 + 8 - cx) / dx) if dx < 0 else ((X1 - 8 - cx) / dx), (Y0 + 8 - cy) / dy)
    d.line((cx, cy, cx + dx * t, cy + dy * t), fill=(110, 110, 110), width=2)
im.save(ROOT / 'docs' / 'assets' / 'w4_plan.png')
