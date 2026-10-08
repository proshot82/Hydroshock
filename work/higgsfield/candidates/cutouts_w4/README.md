# Кандидаты: состояния W4 (08.10.2026)

Вырезки поверх принятой `assets/gfx/rooms/room_w4.png`; координаты — `cutouts_candidates.json`.
После приёмки автором: файл → `assets/gfx/cutouts/`, запись — повторным запуском `tools/assets/cutout.py`
(cutouts.json генерируется, руками не править). Кадры-варианты — по job_id из `work/higgsfield/log.jsonl`
(`hf_fetch.py`), принятые — в `work/higgsfield/variants/room_w4__<имя>.png`.

Команды вырезки (база — `assets/gfx/rooms/room_w4.png`, вариант — `work/higgsfield/staging/room_w4__…`):

| Состояние | Вариант (job) | Параметры |
|---|---|---|
| st_w4_mirror_aside | `st_w4_mirror_aside_fix` (04b70ca1…; наклейка «Не трогать — элемент дизайна» врезана из принятого `st_w4_mirror` — `plaque_insert.py`, углы `517.5,563 552,556 554.5,574 520.5,585`) | `--box 425,190,600,650` |
| st_w4_cabin_full | `st_w4_cabin_full2` (f9010a05…) | `--box 222,172,398,708 --thresh 3 --feather 4` |
| st_w4_cabin_empty | `st_w4_cabin_empty2` (fbaeeeb9…) | `--box 222,172,398,708 --thresh 3 --feather 4` |
| st_w4_design | `st_w4_design` (8f2e2218…) | `--box 790,430,1112,580` |
| st_w4_stairs_open | `st_w4_stairs_open` (8263b452…) | `--box 600,265,815,560` |
| st_w4_water_bottle | `st_w4_water_bottle` (3a782e09…) | `--box 1125,430,1180,545 --thresh 14 --open 3 --close 9 --feather 4` |
| st_w4_films | `st_w4_films` (edf6eb4c…) | `--box 950,600,1085,680 --thresh 12 --open 3 --close 15 --feather 6` |
| st_w4_plate | `st_w4_plate` (8be82651…) | `--box 985,280,1085,415` |
| st_w4_tube_photo (А) | `st_w4_tube_photo2` (02366be5…) | `--box 330,780,910,1060 --thresh 18 --close 35` |
| st_w4_tube_photo_b (Б) | `st_w4_tube_photo3` (b07a9554…) | `--box 300,840,620,1065` |

Отклонены мной до показа: первая проба тубуса (генератор передвинул папку), первые пробы кабин
(на банках латиница, в решётке пустой кабины дыра).

`../room_w4_okr_fix.png` — база W4 с исправленной надписью «Осторожно, окрашено» (в принятой — «окращено»):
прямоугольник 945,424–1195,460 из `st_w4_cabin_empty` (0f1f84df…, сдвиг −1 px), растушёвка 3 px, цвет по кольцу.
