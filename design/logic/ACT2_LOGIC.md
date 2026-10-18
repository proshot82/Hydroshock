# Акт II «Старший по воде» — логика для движка

Источник данных игры (шаг 2 плана сборки, `docs/BJ3_BUILD_PLAN.md`). Отсюда генератор `tools/data/gen_design.py` собирает `design/act2.json` (руками не править); проверка — `tools/data/check_logic.py 2` (каждый слот текстов Акта II на своём месте, каждое действие графа — с теми же условиями и последствиями, конец акта достижим из любого состояния).

Источники: граф `acts/act2/ACT2_graph.json` (ред. 3), условия слотов `docs/BJ3_SLOT_FLAGS.md` (Акт II), ТЗ `texts/act2/BRIEF_ACT2_TEXTS.md` §4 и §9, сдача `acts/act2/ACT2_SUBMISSION.md` (B, D, G, «Изменения 10.2026»), кадры и слои `docs/BJ3_ASSET_SPEC.md` §2–§4, §7, звук §9. При расхождении побеждает граф (шапка SLOT_FLAGS). Обозначения — как в `ACT1_LOGIC.md`; новое для Акта II:

- **Условие `вид=W4`** — игрок сейчас на этом виде (отказ «плёнку тут не к чему приложить» звучит в зале, в других местах — «совмещать не по чему»).
- **Экранные флаги с областью** (раздел «Экранные флаги»): флаг живёт, пока игрок на перечисленных видах. Каскад (`scr_cascade`, Р7 — «да» автора 13.10.2026) включается кнопкой на стойке (Z04), держится, пока игрок у стойки, у экспоната (Z05) и в вестибюле, и гаснет, как только игрок уходит в прачечную, зал или номер. Флаг графа `cascade_on` остаётся навсегда и значит «каскад запускали». Без области флаг снимается при любой смене вида (шторка тележки Акта I).
- **Кадр `вид:Z04+слой`** — вид в его нынешнем состоянии и поверх ещё слои (ящик выдвинут, рука, полосы краски).
- **`планы:ПОЛОЖЕНИЕ`** — три плёнки P05 (`plan_hotel`, `plan_1908`, `plan_soviet`) с подписями по меткам `docs/assets/plans_markers.json`: `рамки` — как легли, `люк` — нарисованный источник на настоящий люк и доворот по номеру 317, `купол`, `подписи`, `фасад` — кривые стопки по ложной опоре. Без `@` — на подсвеченном стекле во весь экран (кадр слота); с `@x,y;x,y;x,y` — на стекле зума Z10 (углы плёнки: верх-лево, верх-право, низ-лево).
- **Заимствованные слоты** — реплики Акта I, которые нужны и здесь: осмотр вантуза и меню (`INV.plunger.look`, `INV.menu.look`, `DOC.menu`), отказы «не тот предмет» (`FB.menu.*`, `FB.generic.*`). Генератор берёт их из `texts/act1/ACT1_TEXTS_FINAL.md`.

## Виды

Музыка (решение автора 14.10.2026): в Акте II вестибюль и номер — `bgm_hotel`; прачечная и зал — `bgm_service` (спека §9.3); внизу лестницы — амбиент низа.

| Вид | Тип | Фон | Родитель | Музыка | Амбиент |
|---|---|---|---|---|---|
| W2 | экран | rooms/room_w2 | — | bgm_hotel | amb_lobby |
| Z04 | зум | zooms/zoom_z04 | W2 | — | — |
| Z05 | экран | zooms/zoom_z05 | — | bgm_hotel | amb_lobby |
| W3 | экран | rooms/room_w3 | — | bgm_service | amb_laundry |
| Z06 | зум | zooms/zoom_z06 | W3 | — | — |
| Z07 | зум | zooms/zoom_z07 | W3 | — | — |
| Z08 | зум | zooms/zoom_z08 | W3 | — | — |
| W4 | экран | rooms/room_w4 | — | bgm_service | amb_hall |
| Z09 | зум | zooms/zoom_z09 | W4 | — | — |
| Z10 | зум | zooms/zoom_z10 | W4 | — | — |
| Z11 | зум | zooms/zoom_z11 | W4 | — | — |
| Z12 | зум | zooms/zoom_z12 | W4 | — | amb_below |
| W1 | экран | rooms/room_w1 | — | bgm_hotel | amb_room |

## Экранные флаги

| Флаг | Виды |
|---|---|
| scr_cascade | W2, Z04, Z05 |

## Слои

| Вид | Слой | Когда |
|---|---|---|
| W2 | st_w2_cascade_on | scr_cascade |
| W2 | st_w2_vitrine_open | vitrine_open |
| W2 | st_w2_lowdrawer_open | relic_r3 |
| W2 | st_w2_forms3 | ¬requests_stapled |
| W2 | st_w2_forms1 | requests_stapled |
| W2 | st_w2_folder | ¬counter_notice_read |
| W2 | st_w2_map | ¬has_hotel_map |
| W2 | st_w2_pump_lamp | scr_cascade |
| W2 | st_w2_trolley | pos=service |
| W2 | st_w2_tt_key | pos=service ∧ has_stairs_key ∧ ¬stairs_open |
| W2 | st_w2_tt_mug | pos=service ∧ relic_r3 |
| W2 | st_w2_iz |  |
| Z04 | st_z04_forms3 | ¬requests_stapled |
| Z04 | st_z04_forms1 | requests_stapled |
| Z04 | st_z04_folder | ¬counter_notice_read |
| Z04 | st_z04_map | ¬has_hotel_map |
| Z04 | st_z04_pump_lamp | scr_cascade |
| Z04 | st_z04_lowdrawer_empty | relic_r3 |
| Z05 | st_z05_open | vitrine_open |
| Z05 | st_z05_tag | ¬meter_reading_seen |
| Z05 | st_z05_tag_folded | meter_reading_seen |
| Z05 | st_z05_ring | seal_is_mark |
| Z05 | ov_skirt_open |  |
| W3 | st_w3_cabinet_open | relic_r2 |
| Z08 | st_z08_inner_empty | relic_r2 |
| W4 | st_w4_mirror |  |
| W4 | st_w4_stairs_open | stairs_open |
| W4 | st_w4_films | overlay_by_frame |
| W4 | st_w4_tube_photo | photo_seen |
| W4 | st_w4_plate | name_revealed |
| Z09 | st_z09_plate | name_revealed |
| Z09 | st_z09_flap_open | relic_r1 |
| Z10 | st_z10_tube_open | shown(Z10.tube.open) ∨ photo_seen |
| Z10 | st_z10_photo | photo_seen |
| Z10 | планы:рамки@1216,72;1724,368;884,348 | overlay_by_frame ∧ ¬topology_known |
| Z10 | планы:люк@1216,72;1724,368;884,348 | topology_known |
| Z11 | st_z11_mirror |  |
| W1 | st_w1_cistern_open | shown(PROBE.cistern) |
| W1 | st_w1_trolley_folded | pos=room |
| W1 | st_w1_juice_empty | pos=room ∧ shown(PROBE.juice) |

## Надписи

Текст движка на чистых полях арта (спека §3: табличка постамента, бирка, табло — «поле под текст движка»; разбор автора 16.10.2026: «нет ни подписи на постаменте, ни цифр», «табло стиралок пустые»). `Где` — x,y,w,h; ` / ` — новая строка; кегль подбирается по полю; `Угол` — градусы по часовой.

| Вид | Где | Текст | Шрифт | Цвет | Угол | Когда |
|---|---|---|---|---|---|---|
| Z05 | 668,488,200,50 | Контрольный счётчикъ водолечебницы «Каскадъ», 1908 / Экспонат. Не трогать | old | #2d241a |  |  |
| Z05 | 724,152,92,44 | ЭКСПОНАТ № 1 / Коллекция наследия | sansb | #2a2a2a |  | ¬meter_reading_seen |
| Z06 | 372,60,390,80 | 0:47 / НЕТ ПОДАЧИ ВОДЫ | mono | #7cf29a |  |  |
| Z06 | 1158,60,390,80 | 0:47 / НЕТ ПОДАЧИ ВОДЫ | mono | #7cf29a |  |  |
| W3 | 82,157,150,46 | 0:47 | mono | #7cf29a | 24 |  |
| W3 | 365,276,82,32 | 0:47 | mono | #7cf29a | 26 |  |
| W3 | 510,338,54,24 | 0:47 | mono | #7cf29a | 30 |  |
| W3 | 604,373,34,18 | 0:47 | mono | #7cf29a | 30 |  |
| Z09 | 716,330,252,400 | Старший / по воде — / тов. К. | oldb | #2a2118 |  | name_revealed |

## Зоны

| Вид | Зона | Название | Где | Курсор | Когда | Свойства |
|---|---|---|---|---|---|---|
| W2 | iz | Изольда Тихоновна | слой st_w2_iz | act |  |  |
| W2 | trolley | Тележка | слой st_w2_trolley | act | pos=service |  |
| W2 | counter | Стойка | 560,560,1360,520 | zoom |  | плоское |
| W2 | cascade | Фонтан | 1090,280,240,190 | look |  |  |
| W2 | exhibit | Экспонат под витриной | 1320,330,180,170 | look |  |  |
| W2 | guests | Гости | 380,140,460,360 | look |  |  |
| W2 | corridor | Служебный коридор | 0,40,130,420 | move |  |  |
| Z04 | top | Стойка | 200,0,1300,180 | look |  | плоское |
| Z04 | pump | Кнопка фонтана | 1570,860,290,170 | act |  |  |
| Z04 | folder | Папка | слой st_z04_folder | act | ¬counter_notice_read | плоское |
| Z04 | notice | Уведомление | 770,671,419,298 | look | counter_notice_read | плоское |
| Z04 | map | Карта отеля в подставке | слой st_z04_map | act | ¬has_hotel_map |  |
| Z04 | regulation | Регламент пуска | 420,400,400,210 | act |  | плоское |
| Z04 | forms | Бланки заявок | слой st_z04_forms3 | look | ¬requests_stapled | плоское |
| Z04 | forms1 | Бланк заявки | слой st_z04_forms1 | look | requests_stapled | плоское |
| Z04 | drawer | Верхний ящик | 40,280,330,280 | act |  |  |
| Z04 | lowdrawer | Нижний ящик | 40,570,330,340 | act |  |  |
| Z05 | vitrine | Витрина | 460,0,660,430 | act |  | плоское |
| Z05 | tag | Бирка «Экспонат № 1» | 690,120,180,140 | act | vitrine_open ∧ ¬meter_reading_seen | плоское |
| Z05 | seal | Пломба | 650,260,120,110 | act | vitrine_open |  |
| Z05 | guests | Гости у таблички | 1420,0,300,920 | look |  |  |
| Z05 | skirt | Юбка тележки | 0,80,230,920 | act |  |  |
| Z05 | back | Назад за стойку | 1730,80,190,920 | move |  |  |
| W3 | drums | Барабаны | 0,0,660,1000 | zoom |  |  |
| W3 | tanks | Баки с водой | 680,460,320,220 | act |  |  |
| W3 | wall | Декоративная стена | 800,90,560,360 | zoom |  | плоское |
| W3 | cabinet | Служебный шкаф | 1440,320,170,420 | zoom |  |  |
| W3 | brand | Табличка «Влажное очищение» | 1650,220,180,120 | look |  | плоское |
| W3 | door | Дверь в коридор | 1830,0,90,1080 | move |  |  |
| Z06 | panels | Табло | 330,30,470,130;1120,30,440,130 | look |  | плоское |
| Z06 | drums | Барабаны | 190,0,1540,1000 | act |  |  |
| Z06 | hatch | Люк с одеждой | 350,280,460,500 | act |  |  |
| Z07 | wall | Декоративная стена | 200,0,1520,900 | act |  | плоское |
| Z08 | cabinet | Служебный шкаф | 540,20,780,980 | look |  |  |
| Z08 | inner | Внутренняя створка | 830,320,180,210 | act |  | плоское |
| W4 | mirror | Зеркало прекраснодушия | слой st_w4_mirror | zoom |  |  |
| W4 | stairs | Дверь «Служебное помещение» | 630,270,160,280 | act |  |  |
| W4 | board | Доска почёта | 880,250,320,170 | zoom |  |  |
| W4 | hatch | Люк под стеклом | 760,600,350,110 | look |  | плоское |
| W4 | table | Архивный стол | 240,780,1100,230 | zoom |  |  |
| W4 | back | Назад в коридор | 1360,990,560,90 | move |  |  |
| Z09 | board | Доска почёта | 110,90,1440,770 | look |  | плоское |
| Z09 | paint | Бежевый прямоугольник | 650,270,380,550 | act |  | плоское |
| Z09 | act | Акт малярной приёмки | 940,390,80,170 | look |  | плоское |
| Z09 | chalk | Мел на раме | 150,780,290,80 | look |  | плоское |
| Z09 | slot | Щель «Для жетоновъ» | 1640,590,240,220 | act |  |  |
| Z10 | table | Архивный стол | 0,320,1160,760 | look |  | плоское |
| Z10 | tube | Тубус | 0,380,390,250 | act |  |  |
| Z10 | folder | Папка профилактория | 140,530,350,220 | look |  | плоское |
| Z10 | papers | Распоряжения | 400,610,330,330 | act |  | плоское |
| Z10 | journal | Журнал | 690,690,340,340 | act |  | плоское |
| Z10 | photo | Фотография | слой st_z10_photo | look | photo_seen | плоское |
| Z10 | glass | Подсвеченное стекло | 880,100,830,560 | act |  | плоское |
| Z10 | hatch | Люк под стеклом | 1150,360,320,240 | act |  | плоское |
| Z11 | mirror | Зеркало прекраснодушия | слой st_z11_mirror | act |  | плоское |
| Z12 | door | Дверь конторы | 860,280,260,390 | act |  |  |
| Z12 | notice | Уведомление с пломбой | 950,380,90,130 | act |  | плоское |
| Z12 | instr | Инструкция 1908 года | 1510,90,300,530 | look |  | плоское |
| Z12 | up | Лестница наверх | 0,180,560,780 | move |  |  |
| W1 | shower | Душевая | 1640,90,130,590 | look |  |  |
| W1 | trolley | В тележке — за стойку | слой st_w1_trolley_folded | act | pos=room | выход |

## Действия

| Зона | Глагол | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|---|
| W2.iz | клик | iz_admits_facts | TALK.iz.after | — | меню:talk |
| W2.iz | клик |  | TALK.iz.open | — | меню:talk |
| W2.trolley | к_экспонату |  | SEQ.exhibit.go | — | pos=exhibit, звук:sfx_trolley_creak, кадр:frames/fr_a2_under_exhibit+ov_skirt, вид:Z05 |
| W2.trolley | в_номер |  | SEQ.w1.return | — | pos=room, звук:sfx_trolley_creak, кадр:frames/fr_a1_under_lobby+ov_skirt, вид:W1 |
| W2.counter | клик |  | — | — | вид:Z04 |
| W2.cascade | осмотр |  | W2.cascade.look | — |  |
| W2.exhibit | осмотр |  | W2.exhibit.look | — | док:DOC.exhibit |
| W2.exhibit | подойти |  | SEQ.exhibit.nocover | — |  |
| W2.guests | осмотр |  | W2.guests | — |  |
| W2.corridor | в_прачечную |  | — | — | вид:W3, цепочка:w3_enter |
| W2.corridor | в_зал |  | — | — | вид:W4, цепочка:w4_enter |
| Z04.top | осмотр |  | Z04.look | — |  |
| Z04.pump | осмотр |  | Z04.pump.look | — |  |
| Z04.pump | нажать_кнопку | ¬cascade_on | Z04.pump.use | B01_pump_cascade | +cascade_on, +scr_cascade, звук:sfx_pump_dry |
| Z04.pump | нажать_кнопку | cascade_on | Z04.pump.use.repeat | — | +scr_cascade, звук:sfx_pump_dry |
| Z04.folder | осмотр |  | Z04.folder.look | — |  |
| Z04.folder | поднять |  | Z04.folder.take | — | звук:sfx_folder_slap |
| Z04.notice | осмотр |  | — | — | док:DOC.notice_counter |
| Z04.map | осмотр |  | Z04.map.look | — |  |
| Z04.map | взять |  | Z04.map.take | B04_take_hotel_map | +has_hotel_map, звук:ui_pickup, док:DOC.map_hotel |
| Z04.regulation | осмотр |  | Z04.regulation.look | B22_read_regulation | +regulation_cut_seen, док:DOC.regulation |
| Z04.regulation | снять_регламент |  | Z04.regulation.take | — |  |
| Z04.forms | осмотр |  | Z04.forms.look | — |  |
| Z04.forms1 | осмотр |  | Z04.forms.look.stapled | — |  |
| Z04.drawer | осмотр |  | Z04.drawer.look | — |  |
| Z04.drawer | нажать_ящик | knows_push_latch | Z04.drawer.open | — | звук:sfx_drawer_click |
| Z04.drawer | взять_кефир | kefir_in_drawer_seen | Z04.kefir.take | — |  |
| Z04.lowdrawer | осмотр |  | Z04.drawer.look | — |  |
| Z04.lowdrawer | нажать_ящик | knows_push_latch ∧ ¬relic_r3 | Z04.lowdrawer.open | R3_mug | +relic_r3, звук:sfx_drawer_click, звук:sting_relic, кадр:вид:Z04+st_z04_lowdrawer_mug |
| Z04.lowdrawer | нажать_ящик | relic_r3 | Z04.lowdrawer.again | — |  |
| Z05.vitrine | осмотр | ¬vitrine_open | Z05.vitrine.look | — |  |
| Z05.vitrine | осмотр | vitrine_open | Z05.meter.look | — |  |
| Z05.vitrine | поддеть | ¬vitrine_open | Z05.vitrine.pry | — |  |
| Z05.vitrine | разбить | ¬vitrine_open | Z05.vitrine.smash | — |  |
| Z05.vitrine | нажать_стекло | ¬vitrine_open ∧ scr_cascade | Z05.vitrine.push | B08_open_vitrine | +vitrine_open, +meter_seal_seen, звук:sfx_latch_click, звук:sting_solved, кадр:zooms/zoom_z05+st_z05_tag+st_z05_palm+ov_skirt_open;zooms/zoom_z05+st_z05_open+st_z05_tag+ov_skirt_open |
| Z05.vitrine | нажать_стекло | ¬vitrine_open | Z05.vitrine.push.seen | — | кадр:zooms/zoom_z05+st_z05_tag+st_z05_palm+ov_skirt_open |
| Z05.vitrine | предмет:plunger | ¬vitrine_open | Z05.vitrine.plunger | — |  |
| Z05.tag | осмотр |  | Z05.meter.look | — |  |
| Z05.tag | отогнуть |  | Z05.tag.fold | B08_open_vitrine | +meter_reading_seen, звук:sfx_tag_fold, кадр:zooms/zoom_z05+st_z05_open+st_z05_tag_folded+ov_skirt_open, док:DOC.tag |
| Z05.seal | осмотр |  | Z05.meter.look | — |  |
| Z05.seal | стереть |  | Z05.seal.wipe | — |  |
| Z05.seal | предмет:plunger | ¬journal_old_read | Z05.seal.plunger.early | B09_compare_plunger | +seal_is_mark, звук:sfx_plunger_press |
| Z05.seal | предмет:plunger |  | Z05.seal.plunger | B09_compare_plunger | +seal_is_mark, звук:sfx_plunger_press |
| Z05.guests | осмотр |  | W2.guests | — |  |
| Z05.skirt | вылезти |  | W2.getout | — |  |
| Z05.back | клик |  | SEQ.exhibit.back | — | pos=service, звук:sfx_trolley_creak, кадр:вид:W2, вид:W2 |
| W3.drums | клик |  | — | — | вид:Z06 |
| W3.tanks | облиться |  | Z06.tank.probe | — | probe+, звук:sfx_foam_swell |
| W3.wall | клик |  | — | — | вид:Z07 |
| W3.cabinet | клик |  | — | — | вид:Z08 |
| W3.brand | осмотр |  | W3.brand.look | — |  |
| W3.door | в_вестибюль |  | — | — | вид:W2, цепочка:pa_more |
| W3.door | в_зал |  | — | — | вид:W4, цепочка:w4_enter |
| Z06.panels | осмотр | ¬drums_same_time | Z06.drums.look | B02_inspect_drums | +drums_same_time, +clothes_locked_seen |
| Z06.panels | осмотр |  | Z06.drums.look | — |  |
| Z06.drums | осмотр | ¬drums_same_time | Z06.drums.look | B02_inspect_drums | +drums_same_time, +clothes_locked_seen |
| Z06.drums | осмотр |  | Z06.drums.look | — |  |
| Z06.drums | запустить |  | Z06.drum.restart | — | звук:sfx_drum_beep, кадр:вид:Z06+st_z06_blink |
| Z06.hatch | осмотр | ¬drums_same_time | Z06.drums.look | B02_inspect_drums | +drums_same_time, +clothes_locked_seen |
| Z06.hatch | осмотр |  | Z06.drums.look | — |  |
| Z06.hatch | открыть_люк | ¬shown(Z06.hatch.open) | Z06.hatch.open | — | +clothes_locked_seen |
| Z06.hatch | открыть_люк |  | Z06.hatch.open.repeat | — |  |
| Z07.wall | осмотр |  | Z07.cladding.look | B24_inspect_cladding | +cladding_seen |
| Z07.wall | открыть_панель |  | Z07.cladding.use | — |  |
| Z08.cabinet | осмотр |  | Z08.cabinet.look | — |  |
| Z08.inner | осмотр |  | Z08.cabinet.look | — |  |
| Z08.inner | открыть | ¬relic_r2 | Z08.cabinet.open | R2_postcard | +relic_r2, звук:sting_relic, кадр:zooms/zoom_z08+st_z08_inner_postcard, док:DOC.postcard |
| Z08.inner | открыть | relic_r2 | Z08.cabinet.again | — |  |
| W4.mirror | клик |  | — | — | вид:Z11 |
| W4.stairs | клик | stairs_open | — | — | вид:Z12 |
| W4.stairs | осмотр | stairs_open | — | — | вид:Z12 |
| W4.stairs | осмотр |  | W4.stairs.look | — |  |
| W4.stairs | открыть | ¬has_stairs_key | W4.stairs.locked | — |  |
| W4.stairs | открыть | ¬topology_known | W4.stairs.no_plan | — |  |
| W4.stairs | открыть | has_stairs_key ∧ topology_known ∧ iz_admits_facts ∧ ¬stairs_open | — | B15_descend | сцена:stairs |
| W4.stairs | предмет:key | ¬topology_known | W4.stairs.no_plan | — |  |
| W4.stairs | предмет:key | topology_known ∧ iz_admits_facts | — | B15_descend | сцена:stairs |
| W4.board | клик |  | — | — | вид:Z09 |
| W4.hatch | осмотр |  | W4.hatch.look | — |  |
| W4.hatch | предмет:map | ¬overlay_by_frame | Z10.films.lay | B05_lay_films | +overlay_by_frame, +knows_map_lies, +photo_seen, кадр:планы:рамки, вид:Z10 |
| W4.table | клик |  | — | — | вид:Z10 |
| W4.back | в_вестибюль |  | — | — | вид:W2, цепочка:pa_more |
| W4.back | в_прачечную |  | — | — | вид:W3, цепочка:w3_enter |
| Z09.board | осмотр |  | Z09.board.look | B11_inspect_board | +knows_plate_under_paint, +knows_paint_fresh, +paint_act_read, +chalk_sample_seen, док:DOC.paint_act |
| Z09.paint | осмотр | name_revealed | Z09.plate.look | — | док:DOC.plate_k |
| Z09.paint | осмотр |  | Z09.board.look | B11_inspect_board | +knows_plate_under_paint, +knows_paint_fresh, +paint_act_read, +chalk_sample_seen, док:DOC.paint_act |
| Z09.paint | тереть | knows_plate_under_paint ∧ ¬name_revealed | Z09.paint.rub | — | звук:sfx_soap_smear |
| Z09.paint | предмет:menu | knows_plate_under_paint ∧ knows_paint_fresh ∧ ¬name_revealed | Z09.paint.scrape | B12_scrape_plate | +name_revealed, +board_restored, +menu_smeared, звук:sfx_paint_scrape, звук:sting_solved, кадр:вид:Z09+st_z09_stripes;вид:Z09+st_z09_stripes;вид:Z09, док:DOC.plate_k |
| Z09.paint | предмет:plunger | ¬name_revealed | Z09.paint.plunger | — |  |
| Z09.paint | предмет:token | ¬name_revealed | Z09.paint.token | — |  |
| Z09.act | осмотр | ¬paint_act_read | Z09.board.look | B11_inspect_board | +knows_plate_under_paint, +knows_paint_fresh, +paint_act_read, +chalk_sample_seen, док:DOC.paint_act |
| Z09.act | осмотр |  | — | — | док:DOC.paint_act |
| Z09.chalk | осмотр | ¬chalk_sample_seen | Z09.board.look | B11_inspect_board | +knows_plate_under_paint, +knows_paint_fresh, +paint_act_read, +chalk_sample_seen, док:DOC.paint_act |
| Z09.chalk | осмотр |  | Z09.chalk.look | — |  |
| Z09.slot | осмотр |  | Z09.slot.look | — |  |
| Z09.slot | нажать_заслонку | ¬relic_r1 | Z09.slot.use | R1_token | +relic_r1, звук:sfx_token_drop, звук:sting_relic, док:DOC.token |
| Z10.table | осмотр |  | Z10.table.look | — |  |
| Z10.table | предмет:map |  | Z10.films.elsewhere | — |  |
| Z10.tube | осмотр | ¬shown(Z10.tube.open) | Z10.tube.open | — | +photo_seen, док:DOC.map_1908, док:DOC.photo |
| Z10.tube | осмотр |  | — | — | док:DOC.map_1908 |
| Z10.tube | взять |  | FB.paper.1 | — |  |
| Z10.folder | осмотр |  | Z10.folder.open | — | док:DOC.map_soviet |
| Z10.folder | предмет:map |  | Z10.films.elsewhere | — |  |
| Z10.papers | осмотр |  | Z10.table.look | — |  |
| Z10.papers | читать_распоряжение | ¬layoff_read | Z10.layoff.read | B13_read_layoff | +layoff_read, док:DOC.layoff |
| Z10.papers | читать_распоряжение |  | — | — | док:DOC.layoff |
| Z10.papers | читать_памятку | ¬memo_soviet_read | Z10.memo.read | B21_read_soviet_memo | +memo_soviet_read, док:DOC.memo |
| Z10.papers | читать_памятку |  | — | — | док:DOC.memo |
| Z10.papers | унести |  | Z10.paper.take | — |  |
| Z10.papers | предмет:map |  | Z10.films.elsewhere | — |  |
| Z10.journal | осмотр | ¬journal_old_read | Z10.journal.read | B07_read_old_journal | +journal_old_read, док:DOC.journal |
| Z10.journal | осмотр |  | — | — | док:DOC.journal |
| Z10.journal | взять |  | FB.paper.1 | — |  |
| Z10.journal | предмет:map |  | Z10.films.elsewhere | — |  |
| Z10.photo | осмотр |  | — | — | док:DOC.photo |
| Z10.glass | осмотр | topology_known | Z10.films.look | — | кадр:планы:люк |
| Z10.glass | осмотр | overlay_by_frame | — | — | кадр:планы:рамки |
| Z10.glass | осмотр |  | W4.hatch.look | — |  |
| Z10.glass | по_куполу | overlay_by_frame ∧ ¬topology_known | Z10.films.dome | — | кадр:планы:купол |
| Z10.glass | по_подписям | overlay_by_frame ∧ ¬topology_known | Z10.films.labels | — | кадр:планы:подписи |
| Z10.glass | по_фасаду | overlay_by_frame ∧ ¬topology_known | Z10.films.facade | — | кадр:планы:фасад |
| Z10.glass | предмет:map | ¬overlay_by_frame | Z10.films.lay | B05_lay_films | +overlay_by_frame, +knows_map_lies, +photo_seen, кадр:планы:рамки |
| Z10.hatch | осмотр | topology_known | Z10.films.look | — | кадр:планы:люк |
| Z10.hatch | осмотр |  | W4.hatch.look | — |  |
| Z10.hatch | совместить_с_люком | overlay_by_frame ∧ knows_map_lies ∧ ¬topology_known | Z10.films.align | B06_align_source | +topology_known, +knows_receiving_point, +knows_office_by_source, +knows_counter_on_line, +knows_service_stairs, звук:sting_solved, кадр:планы:рамки;планы:люк |
| Z10.hatch | предмет:map | ¬overlay_by_frame | Z10.films.lay | B05_lay_films | +overlay_by_frame, +knows_map_lies, +photo_seen, кадр:планы:рамки |
| Z11.mirror | осмотр |  | Z11.mirror.look | B23_inspect_mirror | +mirror_seen |
| Z11.mirror | снять_зеркало |  | Z11.mirror.use | — |  |
| Z12.door | осмотр |  | Z12.door.look | B15_descend | +office_notice_read, док:DOC.notice_door, цепочка:act_end |
| Z12.door | постучать |  | Z12.door.knock | — | звук:sfx_knock, цепочка:act_end |
| Z12.door | открыть |  | Z12.door.use | — |  |
| Z12.notice | осмотр |  | Z12.door.look | B15_descend | +office_notice_read, док:DOC.notice_door, цепочка:act_end |
| Z12.notice | сорвать |  | Z12.seal.tear | — |  |
| Z12.instr | осмотр |  | Z12.instr.look | — | док:DOC.instr1908 |
| Z12.up | клик |  | — | — | вид:W4 |
| W1.shower | осмотр |  | W1.shower.act2 | — |  |
| W1.trolley | под_тележку |  | — | — | pos=service, звук:sfx_trolley_creak, вид:W2 |

## Цепочки

| Группа | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|
| b00 |  | — | B00_opening_demo | +cascade_demo_seen, +cascade_pump_dry |
| w3_enter | ¬shown(W3.enter) | W3.enter | — |  |
| w3_enter |  | — | — |  |
| w4_enter | ¬shown(W4.enter) | W4.enter | — |  |
| w4_enter |  | — | — |  |
| pa_more | ¬shown(W2.pa.more) | W2.pa.more | — | звук:sfx_pa_chime |
| pa_more |  | — | — |  |
| act_end | shown(Z12.door.look) ∧ shown(Z12.door.knock) | END.act2 | B15_descend | +midpoint_known, звук:sfx_pa_chime, акт:3 |
| act_end |  | — | — |  |

## Сцены

Шаги идут подряд; «Кадр» — картинка шага (`слой+слой…`, первым — фон; `;` — следующая картинка с очередной реплики); «вид:W2» — вид в его текущем состоянии.

| Сцена | Слот | Кадр | Звук | Эффекты |
|---|---|---|---|---|
| open | OPEN.counter | вид:W2 | музыка:bgm_hotel, амбиент:amb_lobby | pos=service |
| open | OPEN.demo | вид:W2;вид:W2;вид:W2+st_w2_cascade_on+st_w2_pump_lamp;вид:W2+st_w2_cascade_on+st_w2_pump_lamp;вид:W2+st_w2_cascade_on+st_w2_pump_lamp;вид:W2 | sfx_pump_dry | цепочка:b00 |
| open | OPEN.requests | zooms/cu_z04_forms | sfx_phone_ring |  |
| open | OPEN.pa | вид:W2 | sfx_pa_chime |  |
| open | OPEN.pa.board | вид:W2 |  |  |
| open | OPEN.anc | вид:W2 |  |  |
| cause | TALK.req.open | вид:W2 |  |  |
| cause | TALK.req.cut | zooms/cu_z04_forms;zooms/cu_z04_forms;zooms/cu_z04_forms;zooms/cu_z04_forms;zooms/cu_z04_forms+st_cu_z04_forms_stapled;zooms/cu_z04_forms+st_cu_z04_forms_stapled;вид:Z04+st_z04_drawer_kefir;вид:Z04+st_z04_drawer_kefir | sfx_stamp, sting_solved | +knows_supply_cut, +requests_stapled, +knows_push_latch, +kefir_in_drawer_seen, +knows_iz_stamp_mp |
| duty | TALK.iz.duty | вид:W2 |  | +iz_admits_facts, +knows_supplier_exists, +knows_thursday_plumber, +knows_handover_gap, +knows_chalk_author |
| duty | TALK.iz.folder | zooms/cu_z04_folder |  | +counter_notice_read, док:DOC.notice_counter |
| duty | TALK.iz.ladder | вид:W2 |  | +iz_stepladder_minimized |
| duty | TALK.iz.key | zooms/cu_z04_key | sting_solved | +has_stairs_key |
| stairs | SEQ.stairs.open | вид:W4 | sfx_key_door | +stairs_open |
| stairs | Z12.enter | zooms/zoom_z12 | амбиент:amb_below | +knows_stairs_narrow, вид:Z12 |

## Меню

Подпись пункта — строка `choice` слота из колонки «Подпись» или ключ `texts/ui/UI_TEXTS.md`. Правила одного пункта — сверху вниз. Разговор не закрыть, пока не выбран «Закончить разговор».

| Меню | Пункт | Подпись | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|---|---|
| talk | cause | choice_cause | ¬drums_same_time | TALK.req.early | — | меню:talk |
| talk | cause | choice_cause | knows_supply_cut | TALK.req.again | — | меню:talk |
| talk | cause | choice_cause |  | — | B03_merge_requests | сцена:cause, меню:talk |
| talk | duty | TALK.iz.duty | layoff_read ∧ requests_stapled ∧ ¬iz_admits_facts | — | B14_present_model | сцена:duty, меню:talk |
| talk | vitrine | TALK.iz.vitrine |  | TALK.iz.vitrine | — | меню:talk |
| talk | stairs | TALK.iz.stairs | ¬has_stairs_key | TALK.iz.stairs | — | меню:talk |
| talk | seal | TALK.iz.seal | meter_seal_seen | TALK.iz.seal | — | меню:talk |
| talk | plate | TALK.iz.plate | name_revealed | TALK.iz.plate | — | меню:talk |
| talk | signature | TALK.iz.signature | paint_act_read ∧ ¬shown(TALK.iz.signature) | TALK.iz.signature | B20_accuse_signature | +iz_defends_seen, меню:talk |
| talk | signature | TALK.iz.signature | shown(TALK.iz.signature) | TALK.iz.signature.again | — | меню:talk |
| talk | kefir | TALK.iz.kefir | kefir_in_drawer_seen | TALK.iz.kefir | — | меню:talk |
| talk | exit | TALK.iz.exit |  | TALK.iz.exit | — |  |

## Подсказки

Порядок строк — приоритет тем (SLOT_FLAGS, Акт II: по кратчайшему пути B00 → B15; необязательные — после обязательных). Уточнено при сборке (на решение автора): тема `witness` открыта, как только заявки сшиты, — третья ступень сама велит прочитать распоряжение (в SLOT_FLAGS было ещё условие «распоряжение прочитано», и тогда, пока оно не прочитано, совет молчал бы); тема `down` держится до конца акта, а не до открытия двери (внизу ещё нужно осмотреть дверь и постучать).

| Тема | Открыта, когда |
|---|---|
| check | ¬drums_same_time |
| cause | cascade_pump_dry ∧ drums_same_time ∧ ¬knows_supply_cut |
| map | ¬overlay_by_frame |
| align | overlay_by_frame ∧ ¬topology_known |
| witness | requests_stapled ∧ ¬iz_admits_facts |
| down | has_stairs_key ∧ ¬midpoint_known |
| vitrine | cascade_demo_seen ∧ ¬vitrine_open |
| seal | vitrine_open ∧ ¬seal_is_mark |
| paint | knows_plate_under_paint ∧ ¬name_revealed |
| journal | ¬journal_old_read |

## Предметы

| Предмет | Иконка | При себе, когда | Осмотр | Эффекты осмотра | Мимо (неплоское) | Мимо (плоское) |
|---|---|---|---|---|---|---|
| plunger | icons/ic_plunger | plunger_taken | INV.plunger.look |  | FB.plunger.act2 | FB.plunger.act2 |
| menu | icons/ic_menu | has_menu_card ∧ ¬menu_smeared | INV.menu.look | док:DOC.menu | @fb_menu | @fb_menu |
| menu_p | icons/ic_menu_painted | menu_smeared | INV.menu.painted |  | @fb_menu | @fb_menu |
| map | icons/ic_map | has_hotel_map ∧ ¬overlay_by_frame | INV.map.look | док:DOC.map_hotel | @fb_films | @fb_films |
| key | icons/ic_key | has_stairs_key ∧ ¬stairs_open | INV.key.look |  | FB.key.1 | FB.key.1 |
| token | icons/ic_token | relic_r1 | INV.token.look | док:DOC.token | @fb_generic | @fb_generic |
| postcard | icons/ic_postcard | relic_r2 | INV.postcard.look | док:DOC.postcard | @fb_generic | @fb_generic |

Предмет на предмет в «При себе» без своего правила — `@fb_generic`.

| Группа | Условие | Слот | Эффекты |
|---|---|---|---|
| fb_menu | ¬shown(FB.menu.1) | FB.menu.1 |  |
| fb_menu | shown(FB.menu.1) | FB.menu.2 |  |
| fb_films | (вид=W4 ∨ вид=Z10) ∧ ¬shown(FB.films.1) | FB.films.1 |  |
| fb_films | вид=W4 ∨ вид=Z10 | FB.films.2 |  |
| fb_films |  | Z10.films.elsewhere |  |
| fb_generic | n(FB.generic.1)=0 | FB.generic.1 |  |
| fb_generic | n(FB.generic.1)>=1 ∧ n(FB.generic.2)=0 | FB.generic.2 |  |
| fb_generic | n(FB.generic.2)>=1 | FB.generic.3 |  |

## Документы

| Документ | Носитель | Подпись при условии |
|---|---|---|
| DOC.notice_counter | docs/paper_kuh |  |
| DOC.notice_door | docs/paper_kuh |  |
| DOC.exhibit | docs/plaque_museum |  |
| DOC.tag | docs/tag_exhibit |  |
| DOC.journal | docs/page_ledger |  |
| DOC.paint_act | docs/paper_office |  |
| DOC.layoff | docs/paper_hotel |  |
| DOC.plate_k | docs/plate_enamel |  |
| DOC.regulation | docs/paper_regulation |  |
| DOC.memo | docs/paper_soviet |  |
| DOC.instr1908 | docs/paper_1908 |  |
| DOC.map_hotel | docs/paper_lightbox+docs/plan_hotel |  |
| DOC.map_1908 | docs/paper_lightbox+docs/plan_1908 |  |
| DOC.map_soviet | docs/paper_lightbox+docs/plan_soviet |  |
| DOC.photo | docs/photo_thursday |  |
| DOC.postcard | docs/card_postcard |  |
| DOC.token | docs/token_big |  |
| DOC.menu | docs/paper_laminated |  |

## Прочее

| Слот | Где звучит |
|---|---|
| UI.inventory | подпись кнопки «При себе» (из Акта I) |
| HINT.intro | первое нажатие «Совет предка» (из Акта I) |
| HINT.cooldown | совет уже дан, после него не было действия (из Акта I) |
| HINT.done | открытых тем нет |
