# Перенос инфраструктуры BJ2 → BJ3

Источник: `proshot82/bj2`, коммит `1da9c116e97603258abaf45bf7833856cf3624a2` (раунд 27). BJ2 только читается.

Правило (handoff §14 п. 2, §15 п. 1): инструменты копируются, BJ2-данные вычищаются, движок пересобирается под BJ3 не раньше GDD. Смешанные файлы до GDD не переносятся: без данных BJ3 их вычистку нечем проверить, а непроверенный код в репозитории хуже ссылки на коммит.

## Перенесено (этап 1)

| Файл | Правки |
|---|---|
| `src/json.lua` | без изменений |
| `src/touch.lua`, `tools/test_touch.lua` | без изменений; `luajit tools/test_touch.lua` — 24/24 PASS |
| `tools/check_fonts.py` | design/*.json необязательны; обязательный набор `REQUIRED` (ѣ, ъ, і, типографика) проверяется всегда |
| `tools/gen_texts_dump.py` | без изменений; заработает с появлением `design/texts.json` |
| `assets/fonts/` (PT Sans Regular/Bold, Neucha) | без изменений; лицензия OFL |

## Переносится на этапе GDD (с вычисткой BJ2)

Номера строк — по коммиту выше.

| Файл BJ2 | Общая часть | BJ2-содержимое под вычистку |
|---|---|---|
| `src/core/state.lua` | флаги, инвентарь, `need_ok` (`done:`/`item:`/`read:`), сейв-сериализация, солвер | форма СКУД L123-136, стенд вентилей L138-200, L242-251, ветки solve L292-296 |
| `src/ui.lua` (2101 стр.) | диалоги, читалка, инвентарь, цели, подсказки, **unicode-safe сейв** `atomic_write` L791-797 и загрузка с откатом на `.bak` L906-949, меню, ввод | палитра, музыка по комнатам A/B, спикеры lap/anc, глифы, виджеты ПК/СКУД/стенда/щитка, реплики в коде |
| `main.lua`, `conf.lua` | манифест из scene.json, selftest, letterbox, обработчик ошибок | списки аудио, эмоции, имена ассетов, сигналы `BJ2 READY`/`BJ2 FRAME`, identity `BrassJanissary2` |
| `src/scenes.lua` | навигация, катауты `show_on`/`hide_on`, хит-тест | снег, вентили, насосы, `draw_zoom_engine` L340-466 |
| `src/autoplay.lua` | раннер шагов, вотчдог, ops click/tap/hold/save/load/assert | ops формы, стенда, щитка, проверка бейджей по именам |
| `tools/validate_puzzles.py` (GATE1) | граф: ацикличность, достижимость, улики не вслепую | пороги BJ2 (48–52 узла, комнаты A/B, 3 реликвии + корона) — вынести в конфиг под канон V2 |
| `tools/validate_scene.py` (GATE2) | сверка сцены/текстов/ассетов, зоны ≥44 px | виджеты щитка, стенд, спикеры |
| `tools/gates.py` | пиксельные гейты: magenta, контраст WCAG, яркость, силуэты | имена кадров и прямоугольники UI BJ2 |
| `tools/gen_verify_sheets.py` | оверлеи зон на всех видах | рисование щитка; **добавить замер силуэтов в зумах** (§16) |
| `tools/gen_autoplay.py` | навигация L21-111 | маршрут BJ2 (≈670 строк) — переписать по графу BJ3 |
| `tools/fuzz_state.lua`, `trace_solver.lua`, `test_state.lua`, `clue_audit.py` | фаззер, трасса, roundtrip сейва, аудит улик | id узлов BJ2 |
| `tools/test_negatives.py` | каркас `case`/`ap_case`, восстановление по md5 | мутации под данные BJ2 |
| `tools/gen_puzzles.py` | CLI `--pin` / `--new-answers --force` (защита ответов) | граф и ответы BJ2 |
| `tools/build_web.py`, `web/index.html`, `tools/web_smoke.js`, `.github/workflows/web.yml` | веб-сборка love.js, Telegram, сейв в IndexedDB | имена, текст оболочки, координаты кнопок BJ2. В §14 handoff веб не упомянут — переносить только по решению автора |

## Не переносится

`gen_scene.py`, `gen_texts.py`, `gen_walkthrough.py`, `gen_gallery.py`, `gen_video_script.py` (данные и маршруты BJ2 внутри скриптов), разовые ассет-скрипты `gen_garland.py`, `gen_keypad_digits.py`, `gen_r9_cutouts.py`, `gen_r10_assets.py`, `gen_vents_r7.py`, `inspect_art.py`. Генераторы BJ3 пишутся заново по GDD; из `gen_texts.py` полезен счётчик мата L698-712.

## Связь с солвером графа A

`state.lua` BJ2 описывает узлы как `needs/gives/consumes`. Граф A промпта V2 — `requires/adds/removes`. На этапе GDD нужен один конвертер граф A → `puzzles.json`, чтобы GATE1 и `tools/solver/solve_graph.py` проверяли один и тот же граф.
