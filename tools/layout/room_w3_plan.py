#!/usr/bin/env python3
"""План прачечной W3 с камерой (проект на утверждение). Вывод: docs/assets/w3_plan.png"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]
R = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', n)
B = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', n)
im = Image.new('RGB', (1500, 1000), 'white'); d = ImageDraw.Draw(im)
d.text((30, 15), "W3 прачечная — план и камера (утверждено автором 08.10.2026)", fill='black', font=B(26))
d.text((30, 52), "север — вверх; прачечная к югу от служебного коридора (план первого этажа)", fill=(90, 90, 90), font=R(16))
# коридор
d.rectangle((60, 100, 1440, 200), fill=(250, 240, 250), outline='black', width=6)
d.text((80, 110), "служебный коридор (← зал на западе, → арка к стойке на востоке)", fill='black', font=R(16))
# комната
d.rectangle((260, 200, 1240, 920), fill=(232, 245, 240), outline='black', width=8)
d.rectangle((640, 194, 760, 206), fill=(232, 245, 240))
d.text((600, 215), "дверь «Прачечная»\n(открывается внутрь)", fill=(0, 120, 60), font=R(15))
# барабаны вдоль восточной стены (в кадре — слева: камера смотрит на юг)
for i in range(4):
    y = 300 + i * 120
    d.ellipse((1100, y, 1220, y + 100), fill=(200, 205, 210), outline='black', width=3)
d.text((1050, 230), "4 барабана (Z06),\nтабло над ними", fill='black', font=R(15))
d.text((930, 425), "одежда Лапидуса →\nза стеклом", fill=(150, 40, 40), font=R(14))
# стол и баки в центре
d.rectangle((620, 520, 880, 620), fill=(210, 190, 160), outline='black', width=3); d.text((630, 625), "сортировочный стол", fill='black', font=R(15))
d.ellipse((640, 420, 710, 490), fill=(170, 200, 220), outline='black', width=3); d.ellipse((790, 420, 860, 490), fill=(170, 200, 220), outline='black', width=3)
d.text((650, 395), "баки с водой", fill='black', font=R(14))
# декоративная стена вдоль южной стены
d.rectangle((560, 885, 1000, 915), fill=(235, 220, 190), outline='black', width=2)
d.text((560, 845), "«декоративная стена» (Z07): обшитый\nарочный проём, табличка «Декоративная стена»", fill='black', font=R(14))
# шкаф в юго-западном углу (в кадре — справа)
d.rectangle((275, 800, 370, 905), fill=(150, 160, 150), outline='black', width=3); d.text((275, 770), "советский шкаф (Z08)", fill='black', font=R(14))
# табличка «Влажное очищение» на западной стене (в кадре — справа)
d.rectangle((260, 420, 272, 520), fill=(200, 160, 60)); d.text((282, 430), "табличка\n«Влажное очищение»", fill=(120, 80, 0), font=R(14))
# камера
cx, cy = 700, 260
d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill='black'); d.multiline_text((cx - 330, cy + 30), "камера W3, 1,6 м — у двери, взгляд на юг\n(в кадре: восток — слева, запад — справа)", fill='black', font=B(15))
d.line((cx, cy, 270, 900), fill=(110, 110, 110), width=2); d.line((cx, cy, 1235, 860), fill=(110, 110, 110), width=2)
im.save(ROOT / 'docs' / 'assets' / 'w3_plan.png')
