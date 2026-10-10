# Кандидаты 10.10.2026: тележка по решению автора (новый Z03 и номер W1)

**Все приняты автором 10.10.2026 и перенесены в `assets/`:**
- «шторка А. остальное принимаю» — `zoom_z03` (job fe15a490), `st_z03_stars_folded` (ccfc9717), `st_z03_skirt_open` (вариант А, шторка вправо, f3e80c9a), `st_z03_juice_empty` (61ea23c9);
- «Вариант на петлях» (лист `work/higgsfield/sheet_1010_w1_trolley.png`) — `st_z03_skirt_open_folded` (986cb9db), `st_w1_trolley` (4bd144de), `st_w1_trolley_folded` (вариант 1 на петлях, 53232ecb; вариант 2 на кольцах 532f1bbe отклонён), `st_w1_juice_empty` (8e0f1de5).

Кадры-варианты — `work/higgsfield/variants/`, записи `accept` — в `work/higgsfield/log.jsonl`. Папка пуста до следующей партии.

Параметры вырезки (для повторения):

| Состояние | База | Вырезка |
|---|---|---|
| `st_z03_skirt_open_folded` | `zoom_z03` | `--box 160,380,1760,1080 --thresh 18 --open 3 --close 41 --align 8 --grow 10 --feather 3` |
| `st_w1_trolley`, `st_w1_trolley_folded` | `room_w1` | `--box 520,500,1240,1050 --thresh 14 --open 3 --close 41 --align 6 --grow 12 --feather 3` |
| `st_w1_juice_empty` | `room_w1 + st_w1_trolley` | `--box 755,525,850,645 --thresh 20 --open 1 --close 9 --align 6 --grow 4 --feather 2 --base-name room_w1.png` |

Отклонены до показа: шторка+звёзды проба 1 (шов по краю юбки); тележка в номере 2 (мелковата), 3 (наезжает на кровать). Прежние `st_w1_*` из `cutouts_0910` (звёзды по углам) удалены как устаревшие.
