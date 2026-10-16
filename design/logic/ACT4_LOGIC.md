# Акт IV «Приёмка» — логика для движка

Источник данных игры (шаг 2 плана сборки, `docs/BJ3_BUILD_PLAN.md`). Отсюда генератор `tools/data/gen_design.py` собирает `design/act4.json` (руками не править); проверка — `tools/data/check_logic.py 4`.

Источники: граф `acts/act4/ACT4_graph.json` (ред. 3), условия слотов `docs/BJ3_SLOT_FLAGS.md` (Акт IV), ТЗ `texts/act4/BRIEF_ACT4_TEXTS.md`, сдача `acts/act4/ACT4_SUBMISSION.md`, кадры и слои `docs/BJ3_ASSET_SPEC.md` §2.6, §2.8, §3 (Z13), §4.2, звук §9, музыка §9.3 и §13. Обозначения — как в логике Актов I–III; новое для Акта IV:

- **Звук на реплике** `звук:имя@N` (в колонке «Звук» сцен — `имя@N`): звук звучит, когда появляется N-я реплика слота. Так у каждого кадра финального монтажа свой звук (спека §9.1: душ, фонтан, барабаны, источник), а шлепки оттиска и скрип пера — на своих титрах.
- **Две музыки в шаге:** `музыка:стоп, музыка:тема` — обрыв, миг тишины, затем новая тема с начала (появление Кухтулху: `bgm_deep` обрывается на титре «Стол приёма в полный рост», затем `bgm_below`, спека §9.3).
- **Конец игры:** `акт:5` после эпилога — карточка «Конец» и «На титул» (строки `the_end`, `to_title`).
- **Уточнено при сборке (на взгляд автора):** (1) выкат тележки к столу приёма (E01, `SEQ.rollout` … `SEQ.wait`) идёт сразу за вступлением, без отдельного щелчка: в первом кадре акта игроку нечего делать, кроме как выехать, а темы совета для этого момента в текстах нет — «Совет предка» сказал бы «Тут всё»; (2) реликвии, найденные наверху после входа в контору, сразу лежат у неё на уступе (слои Z13 при `in_office`), в «При себе» жетон и открытка видны до входа в контору; (3) разговор с Кухтулху в конторе — меню по щелчку на неё, пункт выхода «Закончить разговор» — строка интерфейса `talk_end` (своего слота у неё нет).

## Виды

| Вид | Тип | Фон | Родитель | Музыка | Амбиент |
|---|---|---|---|---|---|
| W5u | экран | rooms/room_w5_under | — | bgm_deep | amb_below |
| W5 | экран | rooms/room_w5 | — | bgm_below | amb_below |
| W6 | экран | rooms/room_w6 | — | bgm_below | amb_below |
| Z13 | зум | zooms/zoom_z13 | W6 | — | — |
| Z12 | зум | zooms/zoom_z12 | W4 | bgm_below | amb_below |
| W4 | экран | rooms/room_w4 | — | bgm_service | amb_hall |
| Z09 | зум | zooms/zoom_z09 | W4 | — | — |
| W3 | экран | rooms/room_w3 | — | bgm_service | amb_laundry |
| Z08 | зум | zooms/zoom_z08 | W3 | — | — |
| W2 | экран | rooms/room_w2 | — | bgm_hotel | amb_lobby |
| Z04 | зум | zooms/zoom_z04 | W2 | — | — |

## Слои

| Вид | Слой | Когда |
|---|---|---|
| W5u | st_w5u_tentacles | goods_accepted ∧ ¬lap_out |
| W5u | ov_skirt_dark |  |
| W5 | st_w5_door_office | reported |
| W5 | st_w5_water | water_restored |
| W5 | st_w5_kuh | lap_out ∧ ¬in_office |
| W5 | st_w5_trolley | trolley_reinventoried |
| W5 | st_w5_goods | goods_accepted ∧ ¬payment_sent_alone |
| W5 | st_w5_mark | goods_accepted ∧ payment_sent_alone |
| W6 | st_w6_water | water_restored |
| W6 | st_w6_kuh | ¬marks_exchanged |
| W6 | st_w6_kuh_aside | marks_exchanged |
| W6 | st_w6_seal | ¬marks_exchanged |
| W6 | st_w6_needle_up | water_restored |
| Z13 | st_z13_seal | ¬marks_exchanged |
| Z13 | st_z13_seal_torn | marks_exchanged |
| Z13 | st_z13_needle_up | water_restored |
| Z13 | st_z13_token | relic_r1 ∧ in_office |
| Z13 | st_z13_postcard | relic_r2 ∧ in_office |
| Z13 | st_z13_mug | relic_r3 ∧ in_office |
| Z12 | st_z12_door_open | reported |
| W4 | st_w4_mirror_aside | mirror_removed |
| W4 | st_w4_ramp | ramp_set |
| W4 | st_w4_stairs_open |  |
| W4 | st_w4_design | junk_out |
| W4 | st_w4_films | overlay_by_frame |
| W4 | st_w4_tube_photo | photo_seen |
| W4 | st_w4_plate | name_revealed |
| Z09 | st_z09_plate | name_revealed |
| Z09 | st_z09_flap_open | relic_r1 |
| W3 | st_w3_cabinet_open | relic_r2 |
| Z08 | st_z08_inner_empty | relic_r2 |
| W2 | st_w2_lowdrawer_open | relic_r3 |
| W2 | st_w2_forms1 |  |
| W2 | st_w2_complaints |  |
| W2 | st_w2_iz |  |
| Z04 | st_z04_forms1 |  |
| Z04 | st_z04_lowdrawer_empty | relic_r3 |
| Z04 | st_z04_complaints |  |

## Надписи

| Вид | Где | Текст | Шрифт | Цвет | Угол | Когда |
|---|---|---|---|---|---|---|
| Z09 | 716,330,252,400 | Старший / по воде — / тов. К. | oldb | #2a2118 |  | name_revealed |
| Z13 | 560,590,240,100 | Число · Что подано / Среда (внѣочередной) / кефиръ 1 бут., доложено | old | #3b2a18 |  |  |
| Z13 | 850,590,240,100 | Показанія · Доложилъ · Принялъ / 40 712 | old | #3b2a18 |  |  |

## Зоны

| Вид | Зона | Название | Где | Курсор | Когда | Свойства |
|---|---|---|---|---|---|---|
| W5u | kuh | Щупальца у стола | слой st_w5u_tentacles | act | goods_accepted ∧ ¬lap_out |  |
| W5u | table | Стол приёма | 1000,0,600,700 | act | ¬lap_out |  |
| W5u | skirt | Шторка тележки | 60,60,240,960;1620,60,240,960 | act | ¬lap_out |  |
| W5 | kuh | Старший по воде | 1015,160,330,330;820,500,700,200 | act | lap_out ∧ ¬reported |  |
| W5 | sign | Табличка «Пріёмный пунктъ» | 895,275,115,80 | look | lap_out ∧ ¬in_office | плоское |
| W5 | sign2 | Табличка «Пріёмный пунктъ» | 1030,270,130,80 | look | ¬lap_out ∨ in_office | плоское |
| W5 | door | Дверь конторы | 1262,235,181,295 | move |  |  |
| W5 | trolley | Тележка | слой st_w5_trolley | look | trolley_reinventoried |  |
| W5 | goods | Груз на столе | слой st_w5_goods | look | goods_accepted ∧ ¬payment_sent_alone | плоское |
| W5 | mark | Отметка на столе | слой st_w5_mark | look | goods_accepted ∧ payment_sent_alone | плоское |
| W6 | kuh | Старший по воде | слой st_w6_kuh | act | ¬marks_exchanged |  |
| W6 | kuh2 | Старший по воде | слой st_w6_kuh_aside | act | marks_exchanged |  |
| W6 | ledge | Уступ с журналом | 380,460,920,160 | zoom |  | плоское |
| W6 | valve | Задвижка и манометр | 1500,260,380,400 | zoom |  |  |
| W6 | stairs | Дверь на лестницу | 690,170,180,280 | move |  |  |
| W6 | back | В приёмный пункт | 0,860,560,220 | move |  |  |
| Z13 | ledger | Журнал старшего по воде | 440,560,740,200 | act |  | плоское |
| Z13 | valve | Маховик задвижки | 1500,380,230,260 | act |  |  |
| Z13 | gauge | Манометр | 1730,240,150,140 | look |  | плоское |
| Z13 | speaker | Динамик громкой связи | 1190,40,190,220 | look |  |  |
| Z13 | files | Папки | 1270,510,340,190;0,490,360,210 | look |  | плоское |
| Z13 | mug | Её кефирная кружка | 360,440,200,190 | act |  |  |
| Z13 | photo | Семейная фотография | 1040,340,220,250 | look |  | плоское |
| Z13 | token | Жетон на уступе | слой st_z13_token | look | relic_r1 ∧ in_office | плоское |
| Z13 | postcard | Открытка на уступе | слой st_z13_postcard | look | relic_r2 ∧ in_office | плоское |
| Z13 | rmug | Кружка Изольды на уступе | слой st_z13_mug | look | relic_r3 ∧ in_office | плоское |
| Z12 | door | Дверь конторы | 860,280,260,390 | move |  |  |
| Z12 | instr | Инструкция 1908 года | 1510,90,300,530 | look |  | плоское |
| Z12 | up | Лестница наверх | 0,180,560,780 | move |  |  |
| W4 | stairs | Служебная лестница вниз | 630,270,160,280 | move |  |  |
| W4 | board | Доска почёта | 880,250,320,170 | zoom |  |  |
| W4 | hatch | Люк под стеклом | 760,600,350,110 | look |  | плоское |
| W4 | design | Куча «дизайна» | слой st_w4_design | look | junk_out |  |
| W4 | back | Назад в коридор | 1360,990,560,90 | move |  |  |
| Z09 | board | Доска почёта | 110,90,1440,770 | look |  | плоское |
| Z09 | chalk | Мел на раме | 150,780,290,80 | look |  | плоское |
| Z09 | slot | Щель «Для жетоновъ» | 1640,590,240,220 | act |  |  |
| W3 | cabinet | Служебный шкаф | 1440,320,170,420 | zoom |  |  |
| W3 | brand | Табличка «Влажное очищение» | 1650,220,180,120 | look |  | плоское |
| W3 | door | Дверь в коридор | 1830,0,90,1080 | move |  |  |
| Z08 | cabinet | Служебный шкаф | 540,20,780,980 | look |  |  |
| Z08 | inner | Внутренняя створка | 830,320,180,210 | act |  | плоское |
| W2 | iz | Изольда Тихоновна | слой st_w2_iz | look |  |  |
| W2 | counter | Стойка | 560,560,1360,520 | zoom |  | плоское |
| W2 | guests | Гости | 380,140,460,360 | look |  |  |
| W2 | corridor | Служебный коридор | 0,40,130,420 | move |  |  |
| Z04 | top | Стойка | 200,0,1300,180 | look |  | плоское |
| Z04 | complaints | Стопка жалоб | слой st_z04_complaints | look |  | плоское |
| Z04 | lowdrawer | Нижний ящик | 0,600,230,460 | act |  |  |

## Действия

| Зона | Глагол | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|---|
| W5u.kuh | поздороваться |  | TALK.kuh.under | O01_report_from_under | +under_refused |
| W5u.kuh | высунуть_руку |  | W5.hand | O01_report_from_under | +under_refused |
| W5u.kuh | подтолкнуть_груз |  | W5.push_goods | — |  |
| W5u.table | осмотр |  | W5.push_goods | — |  |
| W5u.table | ждать |  | W5.wait_more | — |  |
| W5u.skirt | вылезти | kuh_wants_hello | — | E02_come_out | сцена:come_out |
| W5u.skirt | обернуться_юбкой |  | W5.cover.skirt | O02_cover_up | +cover_tried |
| W5u.skirt | прикрыться_картой | has_hotel_map | W5.cover.map | O02_cover_up | +cover_tried |
| W5u.skirt | прикрыться_меню | has_menu_card | W5.cover.menu | O02_cover_up | +cover_tried |
| W5u.skirt | прикрыться_салфеткой | breakfast_on_trolley | W5.cover.napkin | O02_cover_up | +cover_tried |
| W5.kuh | доложиться |  | — | E03_report | сцена:report |
| W5.sign | осмотр |  | W5.sign.read | — | док:DOC.reception_sign |
| W5.sign2 | осмотр |  | W5.sign.read | — | док:DOC.reception_sign |
| W5.door | клик | in_office | — | — | вид:W6 |
| W5.door | клик | reported | — | E04_enter_office | сцена:office |
| W5.door | клик |  | W5.door.early | — |  |
| W5.trolley | осмотр |  | — | — | док:DOC.plate_mark |
| W5.goods | осмотр |  | — | — | док:DOC.note_fixed |
| W5.mark | осмотр |  | — | — | док:DOC.partial_mark |
| W6.kuh | клик |  | — | — | меню:kuh |
| W6.kuh2 | клик |  | — | — | меню:kuh |
| W6.ledge | клик |  | — | — | вид:Z13 |
| W6.valve | клик |  | — | — | вид:Z13 |
| W6.stairs | клик | ¬shown(SEQ.upstairs) | SEQ.upstairs | — | вид:Z12 |
| W6.stairs | клик |  | — | — | вид:Z12 |
| W6.back | клик |  | — | — | вид:W5 |
| Z13.ledger | осмотр |  | Z13.ledger.look | — | док:DOC.ledger |
| Z13.ledger | расписаться_ручкой | ¬marks_exchanged | Z13.ledger.pen | O04_pen | +pen_slipped, звук:sfx_pen_roll |
| Z13.ledger | расписаться_пальцем | ¬marks_exchanged | Z13.ledger.thumb | O05_thumb | +thumb_smeared, звук:sfx_soap_smear |
| Z13.ledger | предмет:plunger | ¬marks_exchanged | — | E05_plunger_mark | сцена:mark |
| Z13.valve | осмотр | ¬marks_exchanged | Z13.valve.look | — | док:DOC.seal_tag |
| Z13.valve | повернуть_маховик | ¬marks_exchanged | Z13.valve.sealed | O06_valve_sealed | +valve_refused |
| Z13.valve | повернуть_маховик | ¬water_restored | — | E06_open_valve | сцена:finale |
| Z13.gauge | осмотр | ¬marks_exchanged | Z13.valve.look | — | док:DOC.seal_tag |
| Z13.speaker | осмотр |  | Z13.speaker.look | — |  |
| Z13.files | осмотр |  | Z13.files.look | — |  |
| Z13.mug | осмотр |  | Z13.mug.look | — |  |
| Z13.mug | облиться |  | FB.kefir.head | — |  |
| Z13.photo | осмотр |  | Z13.photo.look | O03_look_photo | +family_photo_seen, док:DOC.photo_family |
| Z13.token | осмотр |  | Z13.relics.look | — |  |
| Z13.postcard | осмотр |  | Z13.relics.look | — |  |
| Z13.rmug | осмотр |  | Z13.relics.look | — |  |
| Z12.door | клик |  | — | — | вид:W6 |
| Z12.instr | осмотр |  | — | — | док:DOC.instr1908 |
| Z12.up | клик |  | — | — | вид:W4 |
| W4.stairs | клик |  | — | — | вид:Z12 |
| W4.board | клик |  | — | — | вид:Z09 |
| W4.hatch | осмотр |  | W4.hatch.look | — |  |
| W4.design | осмотр |  | W4.design.look | — | док:DOC.sticker |
| W4.back | в_вестибюль |  | — | — | вид:W2 |
| W4.back | в_прачечную |  | — | — | вид:W3 |
| Z09.board | осмотр |  | — | — | док:DOC.paint_act |
| Z09.chalk | осмотр |  | Z09.chalk.look | — |  |
| Z09.slot | осмотр |  | Z09.slot.look | — |  |
| Z09.slot | нажать_заслонку | ¬relic_r1 | Z09.token.act4 | R1_token | +relic_r1, звук:sfx_token_drop, звук:sting_relic, док:DOC.token |
| W3.cabinet | клик |  | — | — | вид:Z08 |
| W3.brand | осмотр |  | W3.brand.look | — |  |
| W3.door | в_вестибюль |  | — | — | вид:W2 |
| W3.door | в_зал |  | — | — | вид:W4 |
| Z08.cabinet | осмотр |  | Z08.cabinet.look | — |  |
| Z08.inner | открыть | ¬relic_r2 | Z08.postcard.act4 | R2_postcard | +relic_r2, звук:sting_relic, кадр:zooms/zoom_z08+st_z08_inner_postcard, док:DOC.postcard |
| Z08.inner | открыть | relic_r2 | Z08.cabinet.again | — |  |
| W2.iz | осмотр |  | TALK.iz.after | — |  |
| W2.counter | клик |  | — | — | вид:Z04 |
| W2.guests | осмотр |  | W2.guests | — |  |
| W2.corridor | в_прачечную |  | — | — | вид:W3 |
| W2.corridor | в_зал |  | — | — | вид:W4 |
| Z04.top | осмотр |  | Z04.look | — |  |
| Z04.complaints | осмотр |  | — | — | док:DOC.complaint |
| Z04.lowdrawer | нажать_ящик | ¬relic_r3 | Z04.mug.act4 | R3_mug | +relic_r3, звук:sfx_drawer_click, звук:sfx_stamp, звук:sting_relic, кадр:вид:Z04+st_z04_lowdrawer_mug |
| Z04.lowdrawer | нажать_ящик | relic_r3 | Z04.lowdrawer.again | — |  |

## Цепочки

| Группа | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|
| rollout | payment_sent_alone | — | E01_roll_out | сцена:rollout_empty |
| rollout |  | — | E01_roll_out | сцена:rollout |
| epilogue | relic_r1 ∧ relic_r2 ∧ relic_r3 | EPI.3 | — | кадр:frames/fr_epi_laundry;frames/fr_epi_bath17;frames/fr_epi_bath17;zooms/zoom_z13+st_z13_seal_torn+st_z13_needle_up+st_z13_postcard+st_z13_mug, док:DOC.menu_new, акт:5 |
| epilogue | relic_r1 ∧ relic_r2 | EPI.2 | — | кадр:frames/fr_epi_laundry;frames/fr_epi_minibar;zooms/zoom_z13+st_z13_seal_torn+st_z13_needle_up+st_z13_token+st_z13_postcard+st_z13_spot_mug, док:DOC.menu_new, акт:5 |
| epilogue | relic_r1 ∧ relic_r3 | EPI.2 | — | кадр:frames/fr_epi_laundry;frames/fr_epi_minibar;zooms/zoom_z13+st_z13_seal_torn+st_z13_needle_up+st_z13_token+st_z13_mug+st_z13_spot_postcard, док:DOC.menu_new, акт:5 |
| epilogue | relic_r2 ∧ relic_r3 | EPI.2 | — | кадр:frames/fr_epi_laundry;frames/fr_epi_minibar;zooms/zoom_z13+st_z13_seal_torn+st_z13_needle_up+st_z13_postcard+st_z13_mug+st_z13_spot_token, док:DOC.menu_new, акт:5 |
| epilogue | relic_r1 | EPI.1 | — | кадр:frames/fr_epi_laundry;frames/fr_epi_minibar;zooms/zoom_z13+st_z13_seal_torn+st_z13_needle_up+st_z13_token, док:DOC.menu_new, акт:5 |
| epilogue | relic_r2 | EPI.1 | — | кадр:frames/fr_epi_laundry;frames/fr_epi_minibar;zooms/zoom_z13+st_z13_seal_torn+st_z13_needle_up+st_z13_postcard, док:DOC.menu_new, акт:5 |
| epilogue | relic_r3 | EPI.1 | — | кадр:frames/fr_epi_laundry;frames/fr_epi_minibar;zooms/zoom_z13+st_z13_seal_torn+st_z13_needle_up+st_z13_mug, док:DOC.menu_new, акт:5 |
| epilogue |  | EPI.0 | — | кадр:frames/fr_epi_laundry;frames/fr_epi_minibar, док:DOC.menu_new, акт:5 |

## Сцены

Шаги идут подряд; «Кадр» — картинка шага (`;` — следующая картинка с очередной реплики); «вид:W5» — вид в его текущем состоянии (флаги шага уже стоят). Кадры до `SEQ.come_out` — тёмные (решение автора 12.10.2026, «сначала чудовище, потом бухгалтерша»).

| Сцена | Слот | Кадр | Звук | Эффекты |
|---|---|---|---|---|
| open | OPEN.arrive | frames/fr_a3_under_arrive+ov_skirt_dark | музыка:bgm_deep, амбиент:amb_below | pos=receiving |
| open | OPEN.steps | frames/fr_a3_under_arrive+st_fr_a3_under_arrive_tentacles+ov_skirt_dark | sfx_wet_steps |  |
| open | OPEN.anc | frames/fr_a3_under_arrive+st_fr_a3_under_arrive_tentacles+ov_skirt_dark |  | цепочка:rollout |
| rollout | SEQ.rollout | rooms/room_w5_under+st_w5u_reach+ov_skirt_dark | sfx_trolley_creak | pos=reception |
| rollout | SEQ.goods | rooms/room_w5_under+st_w5u_tentacles+ov_skirt_dark | sfx_wet_stamp@4 | +goods_accepted |
| rollout | SEQ.debt | rooms/room_w5_under+st_w5u_tentacles+ov_skirt_dark |  |  |
| rollout | SEQ.note_fix | rooms/room_w5_under+st_w5u_tentacles+ov_skirt_dark | sfx_pen_scratch@2, sfx_wet_stamp@2 | док:DOC.note_fixed |
| rollout | SEQ.trolley_return | rooms/room_w5_under+st_w5u_tentacles+ov_skirt_dark | sfx_wet_stamp@4 | +trolley_reinventoried, док:DOC.plate_mark |
| rollout | SEQ.wait | rooms/room_w5_under+st_w5u_tentacles+ov_skirt_dark |  | +kuh_wants_hello, вид:W5u |
| rollout_empty | SEQ.rollout.empty | rooms/room_w5_under+st_w5u_reach+ov_skirt_dark | sfx_trolley_creak | pos=reception |
| rollout_empty | SEQ.goods.prior | rooms/room_w5_under+st_w5u_tentacles+ov_skirt_dark | sfx_wet_stamp@3 | +goods_accepted |
| rollout_empty | SEQ.debt | rooms/room_w5_under+st_w5u_tentacles+ov_skirt_dark |  |  |
| rollout_empty | SEQ.trolley_return | rooms/room_w5_under+st_w5u_tentacles+ov_skirt_dark | sfx_wet_stamp@4 | +trolley_reinventoried, док:DOC.plate_mark |
| rollout_empty | SEQ.wait | rooms/room_w5_under+st_w5u_tentacles+ov_skirt_dark |  | +kuh_wants_hello, вид:W5u |
| come_out | SEQ.come_out | вид:W5 | музыка:стоп, музыка:bgm_below, sfx_pen_scratch@4 | +lap_out, вид:W5 |
| report | SEQ.hello | вид:W5 |  |  |
| report | SEQ.report_line | вид:W5 | sfx_pen_scratch@5, sfx_wet_stamp@5 | +reported |
| report | SEQ.doors | вид:W5 | sfx_door_clicks |  |
| office | SEQ.office | вид:W6 |  | +in_office, вид:W6 |
| mark | Z13.plunger.mark | zooms/zoom_z13+st_z13_seal+st_z13_hand_plunger;zooms/zoom_z13+st_z13_seal+st_z13_hand_plunger;zooms/zoom_z13+st_z13_seal;zooms/zoom_z13+st_z13_seal+st_z13_tentacle;zooms/zoom_z13+st_z13_seal_torn;zooms/zoom_z13+st_z13_seal_torn | sfx_plunger_press@1, sfx_wet_stamp@4, sfx_seal_tear@5 | +marks_exchanged, док:DOC.ledger |
| finale | Z13.valve.turn | zooms/zoom_z13+st_z13_seal_torn+st_z13_hand_wheel;zooms/zoom_z13+st_z13_seal_torn+st_z13_hand_wheel;zooms/zoom_z13+st_z13_seal_torn+st_z13_hand_wheel+st_z13_needle_up;вид:Z13 | sfx_valve_turn@2, sfx_building_exhale@3, sting_water@4 | +water_restored |
| finale | PA.final | вид:Z13 | sfx_pa_chime, sfx_pa_drown@2 |  |
| finale | SEQ.finale | zooms/zoom_z01+st_z01_head_running;frames/fr_a4_cascade_duck;frames/fr_a4_cascade_duck;zooms/zoom_z06+st_z06_spin;rooms/room_w4+st_w4_mirror_aside+st_w4_stairs_open+st_w4_design+st_w4_films+st_w4_tube_photo+st_w4_plate+st_w4_source_water | музыка:bgm_epilogue, sfx_fin_shower@1, sfx_fin_cascade@2, sfx_drums_turn@4, sfx_fin_spring@5 | цепочка:epilogue |

## Меню

| Меню | Пункт | Подпись | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|---|---|
| kuh | photo | TALK.kuh.photo | family_photo_seen | TALK.kuh.photo | — | меню:kuh |
| kuh | plate | TALK.kuh.plate |  | TALK.kuh.plate | — | меню:kuh |
| kuh | kefir | TALK.kuh.kefir |  | TALK.kuh.kefir | — | меню:kuh |
| kuh | exit | talk_end |  | — | — |  |

## Подсказки

Порядок строк — приоритет тем (SLOT_FLAGS, Акт IV).

| Тема | Открыта, когда |
|---|---|
| out | kuh_wants_hello ∧ ¬lap_out |
| hello | lap_out ∧ ¬reported |
| office | reported ∧ ¬in_office |
| mark | in_office ∧ ¬marks_exchanged |
| valve | marks_exchanged ∧ ¬water_restored |

## Предметы

| Предмет | Иконка | При себе, когда | Осмотр | Эффекты осмотра | Мимо (неплоское) | Мимо (плоское) |
|---|---|---|---|---|---|---|
| plunger | icons/ic_plunger | plunger_taken | INV.plunger.act4 |  | FB.plunger.act4 | FB.plunger.act4 |
| menu_p | icons/ic_menu_painted | menu_smeared | INV.menu.painted |  | @fb_menu | @fb_menu |
| token | icons/ic_token | relic_r1 ∧ ¬in_office | INV.token.look | док:DOC.token | @fb_generic | @fb_generic |
| postcard | icons/ic_postcard | relic_r2 ∧ ¬in_office | INV.postcard.look | док:DOC.postcard | @fb_generic | @fb_generic |

Предмет на предмет в «При себе» без своего правила — `@fb_generic`.

| Группа | Условие | Слот | Эффекты |
|---|---|---|---|
| fb_menu | ¬shown(FB.menu.1) | FB.menu.1 |  |
| fb_menu | shown(FB.menu.1) | FB.menu.2 |  |
| fb_generic | n(FB.generic.1)=0 | FB.generic.1 |  |
| fb_generic | n(FB.generic.1)>=1 ∧ n(FB.generic.2)=0 | FB.generic.2 |  |
| fb_generic | n(FB.generic.2)>=1 | FB.generic.3 |  |

## Документы

| Документ | Носитель | Подпись при условии |
|---|---|---|
| DOC.reception_sign | docs/plate_enamel |  |
| DOC.note_fixed | docs/paper_note |  |
| DOC.plate_mark | docs/plate_brass |  |
| DOC.ledger | docs/page_ledger |  |
| DOC.seal_tag | docs/tag_seal |  |
| DOC.photo_family | docs/photo_family |  |
| DOC.menu_new | docs/paper_laminated |  |
| DOC.partial_mark | docs/paper_kuh |  |
| DOC.instr1908 | docs/paper_1908 |  |
| DOC.token | docs/token_big |  |
| DOC.postcard | docs/card_postcard |  |
| DOC.paint_act | docs/paper_office |  |
| DOC.sticker | docs/label_sticker |  |
| DOC.complaint | docs/paper_office |  |
| DOC.menu | docs/paper_laminated |  |

## Прочее

| Слот | Где звучит |
|---|---|
| UI.inventory | подпись кнопки «При себе» (из Акта I) |
| HINT.intro | первое нажатие «Совет предка» (из Акта I) |
| HINT.cooldown | совет уже дан, после него не было действия (из Акта I) |
| HINT.done | открытых тем нет |
