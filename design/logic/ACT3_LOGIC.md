# Акт III «Улучшения номер три» — логика для движка

Источник данных игры (шаг 2 плана сборки, `docs/BJ3_BUILD_PLAN.md`). Отсюда генератор `tools/data/gen_design.py` собирает `design/act3.json` (руками не править); проверка — `tools/data/check_logic.py 3` (каждый слот текстов Акта III на своём месте, каждое действие графа — с теми же условиями и последствиями, конец акта достижим из любого состояния).

Источники: граф `acts/act3/ACT3_graph.json` (ред. 3), условия слотов `docs/BJ3_SLOT_FLAGS.md` (Акт III), ТЗ `texts/act3/BRIEF_ACT3_TEXTS.md`, сдача `acts/act3/ACT3_SUBMISSION.md`, кадры и слои `docs/BJ3_ASSET_SPEC.md` §2.2, §2.5, §3, §4.2, звук §9. При расхождении побеждает граф (шапка SLOT_FLAGS). Обозначения — как в `ACT1_LOGIC.md` и `ACT2_LOGIC.md`; новое для Акта III:

- **Флаги прошлых актов в условиях.** Движок переносит флаги накопительно (GDD §12), поэтому условие может читать и флаг Акта II, которого нет в графе Акта III (`seal_is_mark` — кольцо следа на пломбе, `journal_old_read`). Ставить и снимать можно только флаги своего графа. Проверка начинает со стартовых флагов графа, то есть с худшего случая: всё необязательное в Акте II не сделано.
- **Тележка.** `pos=service` — за стойкой (вестибюль), `pos=hall` — в зале прекраснодушия у стойки «Наследие», `pos=exhibit` — у витрины, `pos=receiving` и `pos=cabin` — внизу и в кабине (только в сценах). Флаг графа `trolley_in_hall` значит «тележку привозили в зал» и не снимается; где тележка сейчас, говорит `pos`. Возить её между стойкой и залом можно сколько угодно (H24, `SEQ.counter.again`).
- **Заимствованные слоты** — реплики Актов I–II в тех же местах: осмотры вестибюля, стойки, витрины, прачечной, доски почёта, архивного стола, двери конторы; разговорные пункты Изольды про витрину, пломбу и табличку; реплики действий, которые граф Акта III повторяет «если не сделано в Акте II» (C17, C18, O10, O11, R1–R3 — шапка Акта III в SLOT_FLAGS).
- **Уточнено при сборке (на взгляд автора):** (1) счёт читается сразу, последней репликой сцены пробного пуска (`Z11.bill.read`): тележка вернулась с почтой, и Лапидус её читает — отдельного щелчка «прочитать» в зуме нет, а повторно счёт открывается из «При себе» (`INV.bill.look`); (2) `W4.lift.search` звучит в зале — в SLOT_FLAGS условие «в прачечной или вестибюле», но реплика говорит «Мозаика с фотографии только здесь, в зале», и слот назван `W4.*`; это осмотр пола у стены лифта, пока лифт не найден; (3) `Z11.board.return` — у кучи «дизайна» в зале (W4), куда доска и выброшена (в SLOT_FLAGS — «в зуме Z11», но кучи из зума не видно); (4) тема совета `down` открыта и после отправки оплаты одной (иначе после C19 совет сказал бы «Тут всё», а ехать ещё надо); (5) меловые «НАШЕ» на посту и «НЕ ТРОГАТЬ» у рубильника — надписи движка (в арте их нет, реплика `Z11.cabin.look` их называет).

## Виды

Музыка — по спеке §9.3: вестибюль `bgm_hotel`, зал и прачечная `bgm_service`; внизу лестницы — амбиент низа; с `SEQ.descent` — `bgm_deep` («чудовище из глубины», до `SEQ.come_out` Акта IV). Первым стоит вид, с которого начинается акт: площадка у двери конторы.

| Вид | Тип | Фон | Родитель | Музыка | Амбиент |
|---|---|---|---|---|---|
| Z12 | зум | zooms/zoom_z12 | W4 | — | amb_below |
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
| W2 | st_w2_forms1 |  |
| W2 | st_w2_complaints |  |
| W2 | st_w2_kefir | kefir_ready ∧ ¬payment_loaded |
| W2 | st_w2_pump_lamp | scr_cascade |
| W2 | st_w2_trolley | pos=service |
| W2 | st_w2_tt_mug | pos=service ∧ relic_r3 ∧ ¬payment_loaded |
| W2 | st_w2_tt_payment | pos=service ∧ payment_loaded |
| W2 | st_w2_iz |  |
| Z04 | st_z04_forms1 |  |
| Z04 | st_z04_pump_lamp | scr_cascade |
| Z04 | st_z04_lowdrawer_empty | relic_r3 |
| Z04 | st_z04_complaints |  |
| Z04 | st_z04_bill_stamped | bill_stamped ∧ ¬payment_loaded |
| Z04 | st_z04_kefir | kefir_ready ∧ ¬payment_loaded |
| Z05 | st_z05_open | vitrine_open |
| Z05 | st_z05_tag | ¬meter_reading_seen |
| Z05 | st_z05_tag_folded | meter_reading_seen |
| Z05 | st_z05_ring | seal_is_mark |
| Z05 | ov_skirt_open |  |
| W3 | st_w3_cabinet_open | relic_r2 |
| Z08 | st_z08_inner_empty | relic_r2 |
| W4 | st_w4_mirror | ¬mirror_removed |
| W4 | st_w4_cabin_full | mirror_removed ∧ ¬junk_out |
| W4 | st_w4_cabin_empty | junk_out ∧ ¬descended_as_staff |
| W4 | st_w4_board_floor | junk_out ∧ ¬ramp_set ∧ ¬ramp_thrown |
| W4 | st_w4_ramp | ramp_set |
| W4 | st_w4_mirror_aside | mirror_removed |
| W4 | st_w4_stairs_open | stairs_open |
| W4 | st_w4_design | junk_out |
| W4 | st_w4_design_board | ramp_thrown ∧ ¬ramp_set |
| W4 | st_w4_films | overlay_by_frame |
| W4 | st_w4_tube_photo | photo_seen |
| W4 | st_w4_plate | name_revealed |
| W4 | st_w4_water_bottle | ¬offering_on_trolley |
| W4 | st_w4_trolley_hall | pos=hall |
| W4 | st_w4_tt_water | pos=hall ∧ offering_on_trolley ∧ ¬test_run_done |
| W4 | st_w4_tt_returned | pos=hall ∧ test_run_done ∧ ¬trolley_back_at_counter |
| W4 | st_w4_tt_payment | pos=hall ∧ payment_in_hall |
| W4 | st_w4_tt_marked | pos=hall ∧ trolley_marked_partial |
| Z09 | st_z09_plate | name_revealed |
| Z09 | st_z09_flap_open | relic_r1 |
| Z10 | st_z10_tube_open |  |
| Z10 | st_z10_photo | photo_seen |
| Z10 | st_z10_bottle | ¬offering_on_trolley |
| Z10 | планы:люк@1216,72;1724,368;884,348 | topology_known |
| Z11 | st_z11_mirror | ¬mirror_removed |
| Z11 | st_z11_mirror_aside | mirror_removed |
| Z11 | st_z11_cabin_full | mirror_removed ∧ ¬junk_out |
| Z11 | st_z11_cabin_empty | junk_out ∧ ¬descended_as_staff |
| Z11 | st_z11_board_floor | junk_out ∧ ¬ramp_set ∧ ¬ramp_thrown |
| Z11 | st_z11_ramp | ramp_set |

## Надписи

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
| Z11 | 425,640,110,40 | НАШЕ | hand | #f4f1e6 | -4 | mirror_removed |
| Z11 | 812,596,150,40 | НЕ ТРОГАТЬ | hand | #f4f1e6 | -3 | junk_out ∧ ¬descended_as_staff |

## Зоны

| Вид | Зона | Название | Где | Курсор | Когда | Свойства |
|---|---|---|---|---|---|---|
| Z12 | door | Дверь конторы | 860,280,260,390 | act |  |  |
| Z12 | notice | Уведомление с пломбой | 950,380,90,130 | act |  | плоское |
| Z12 | instr | Инструкция 1908 года | 1510,90,300,530 | look |  | плоское |
| Z12 | up | Лестница наверх | 0,180,560,780 | move |  |  |
| W2 | iz | Изольда Тихоновна | слой st_w2_iz | act |  |  |
| W2 | trolley | Тележка | слой st_w2_trolley | act | pos=service |  |
| W2 | counter | Стойка | 560,560,1360,520 | zoom |  | плоское |
| W2 | cascade | Фонтан | 1090,280,240,190 | look |  |  |
| W2 | exhibit | Экспонат под витриной | 1320,330,180,170 | look |  |  |
| W2 | guests | Гости | 380,140,460,360 | look |  |  |
| W2 | corridor | Служебный коридор | 0,40,130,420 | move |  |  |
| Z04 | top | Стойка | 200,0,1300,180 | look |  | плоское |
| Z04 | pump | Кнопка фонтана | 1570,860,290,170 | act |  |  |
| Z04 | notice | Уведомление | 770,671,419,298 | look |  | плоское |
| Z04 | regulation | Регламент пуска | 420,400,400,210 | act |  | плоское |
| Z04 | forms1 | Бланк заявки | слой st_z04_forms1 | look |  | плоское |
| Z04 | complaints | Стопка жалоб | слой st_z04_complaints | act |  | плоское |
| Z04 | kefir | Кефир и накладная | слой st_z04_kefir | act | kefir_ready ∧ ¬payment_loaded |  |
| Z04 | bill | Счёт с печатью | слой st_z04_bill_stamped | look | bill_stamped ∧ ¬payment_loaded | плоское |
| Z04 | drawer | Верхний ящик | 0,100,160,400 | act |  |  |
| Z04 | lowdrawer | Нижний ящик | 0,600,230,460 | act |  |  |
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
| Z07 | wall | Декоративная стена | 200,0,1520,900 | act |  | плоское |
| Z08 | cabinet | Служебный шкаф | 540,20,780,980 | look |  |  |
| Z08 | inner | Внутренняя створка | 830,320,180,210 | act |  | плоское |
| W4 | mirror | Зеркало прекраснодушия | слой st_w4_mirror | zoom | ¬mirror_removed |  |
| W4 | lift | Грузовой лифт | 180,30,240,700 | zoom | mirror_removed |  |
| W4 | mirror2 | Зеркало у стены | слой st_w4_mirror_aside | zoom | mirror_removed |  |
| W4 | design | Куча «дизайна» | слой st_w4_design | look | junk_out |  |
| W4 | design_board | Доска «НАШЕ» в куче | слой st_w4_design_board | act | ramp_thrown ∧ ¬ramp_set |  |
| W4 | stairs | Служебная лестница вниз | 630,270,160,280 | move |  |  |
| W4 | board | Доска почёта | 880,250,320,170 | zoom |  |  |
| W4 | hatch | Люк под стеклом | 760,600,350,110 | look |  | плоское |
| W4 | floor | Мозаика у стены лифта | 100,640,640,130 | look | knows_lift_exists ∧ ¬knows_lift_in_hall | плоское |
| W4 | water | Стойка «Наследие» с водой | слой st_w4_water_bottle | zoom | ¬offering_on_trolley |  |
| W4 | trolley | Тележка | слой st_w4_trolley_hall | act | pos=hall |  |
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
| Z10 | photo | Фотография «Четвергъ» | слой st_z10_photo | look | photo_seen | плоское |
| Z10 | glass | Подсвеченное стекло | 880,100,830,560 | look |  | плоское |
| Z10 | water | Вода «Каскадъ» на стойке «Наследие» | слой st_z10_bottle | act | ¬offering_on_trolley |  |
| Z11 | mirror | Зеркало прекраснодушия | слой st_z11_mirror | act | ¬mirror_removed | плоское |
| Z11 | threshold | Латунный порожек | 600,1000,700,80 | look | ¬mirror_removed ∧ knows_lift_exists ∧ ¬knows_door_behind_mirror | плоское |
| Z11 | mirror2 | Зеркало у стены | слой st_z11_mirror_aside | look | mirror_removed |  |
| Z11 | stencil | Трафарет над решёткой | 660,150,520,120 | look | mirror_removed | плоское |
| Z11 | post | Кнопочный пост | 430,370,100,200 | act | mirror_removed |  |
| Z11 | cabin | Кабина лифта | 660,270,520,690 | act | mirror_removed |  |
| Z11 | switch | Рубильник | 830,420,110,180 | act | cabin_seen |  |
| Z11 | board | Доска «НАШЕ» | 850,850,170,90 | act | cabin_seen ∧ ¬junk_out | плоское |
| Z11 | board2 | Доска «НАШЕ» | слой st_z11_board_floor | act | junk_out ∧ ¬ramp_set ∧ ¬ramp_thrown | плоское |

## Действия

| Зона | Глагол | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|---|
| Z12.door | осмотр |  | Z12.door.look | — | док:DOC.notice_door |
| Z12.door | постучать | payment_in_hall | Z12.door.payment | O07_walk_down | +door_still_closed, звук:sfx_knock |
| Z12.door | постучать |  | Z12.door.knock.again | — | звук:sfx_knock |
| Z12.door | открыть |  | Z12.door.use | — |  |
| Z12.notice | осмотр |  | — | — | док:DOC.notice_door |
| Z12.notice | сорвать |  | Z12.seal.tear | — |  |
| Z12.instr | осмотр | knows_receiving_point ∧ ¬instr1908_read | Z12.instr.read | C01_read_order | +instr1908_read, +knows_order_trolley, док:DOC.instr1908 |
| Z12.instr | осмотр |  | — | — | док:DOC.instr1908 |
| Z12.up | клик |  | — | — | вид:W4 |
| W2.iz | клик |  | TALK.iz.after | — | меню:talk |
| W2.trolley | в_зал_с_тележкой | payment_loaded ∧ ¬iz_reported_pa | — | C15_leave_counter | сцена:report |
| W2.trolley | в_зал_с_тележкой | knows_order_trolley ∧ ¬trolley_in_hall | SEQ.trolley.hall | C02_trolley_stairs | +trolley_in_hall, pos=hall, звук:sfx_trolley_creak, кадр:вид:W4, вид:W4 |
| W2.trolley | в_зал_с_тележкой | trolley_in_hall ∧ ¬shown(SEQ.counter.again) | SEQ.counter.again | — | pos=hall, звук:sfx_trolley_creak, кадр:вид:W4, вид:W4 |
| W2.trolley | в_зал_с_тележкой | trolley_in_hall | — | — | pos=hall, звук:sfx_trolley_creak, вид:W4 |
| W2.trolley | подкатить | kefir_ready ∧ invoice_ready ∧ invoice_filled ∧ trolley_back_at_counter ∧ ¬payment_loaded | SEQ.load | C14_load_payment | +payment_loaded, кадр:zooms/cu_z04_kefir_hands |
| W2.trolley | к_экспонату | ¬payment_loaded | SEQ.exhibit.go | — | pos=exhibit, звук:sfx_trolley_creak, кадр:frames/fr_a2_under_exhibit+ov_skirt, вид:Z05 |
| W2.trolley | вылезти |  | W2.getout | — |  |
| W2.counter | клик |  | — | — | вид:Z04 |
| W2.cascade | осмотр |  | W2.cascade.look | — |  |
| W2.exhibit | осмотр |  | W2.exhibit.look | — | док:DOC.exhibit |
| W2.exhibit | подойти |  | SEQ.exhibit.nocover | — |  |
| W2.guests | осмотр |  | W2.guests | — |  |
| W2.corridor | в_прачечную |  | — | — | вид:W3 |
| W2.corridor | в_зал |  | — | — | вид:W4 |
| Z04.top | осмотр |  | Z04.look | — |  |
| Z04.pump | осмотр |  | Z04.pump.look | — |  |
| Z04.pump | нажать_кнопку | ¬cascade_on | Z04.pump.use | C17_vitrine_readings | +cascade_on, +scr_cascade, звук:sfx_pump_dry |
| Z04.pump | нажать_кнопку | cascade_on | Z04.pump.use.repeat | — | +scr_cascade, звук:sfx_pump_dry |
| Z04.notice | осмотр |  | — | — | док:DOC.notice_counter |
| Z04.regulation | осмотр | ¬regulation_cut_seen | Z04.regulation.look | O11_read_regulation | +regulation_cut_seen, док:DOC.regulation |
| Z04.regulation | осмотр |  | — | — | док:DOC.regulation |
| Z04.regulation | снять_регламент |  | Z04.regulation.take | — |  |
| Z04.forms1 | осмотр |  | Z04.forms.look.stapled | — |  |
| Z04.complaints | осмотр | bill_read ∧ ¬knows_mp_habit | Z04.stamp.watch | C12_watch_stamp | +knows_mp_habit, звук:sfx_stamp, кадр:вид:Z04+st_z04_iz_hand, док:DOC.complaint |
| Z04.complaints | осмотр |  | — | — | док:DOC.complaint |
| Z04.complaints | предмет:bill | knows_secret_payer ∧ ¬bill_stamped | — | C13_bill_under_stamp | сцена:payment |
| Z04.kefir | осмотр |  | — | — | док:DOC.invoice |
| Z04.kefir | взять |  | Z04.kefir.take | O06_take_bottle | +grip_refused_bottle, звук:sfx_bottle_catch |
| Z04.kefir | взять_через_салфетку |  | Z04.kefir.napkin | — |  |
| Z04.kefir | взять_накладную |  | Z04.invoice.take | — | док:DOC.invoice |
| Z04.bill | осмотр |  | — | — | док:DOC.bill |
| Z04.drawer | осмотр |  | Z04.drawer.look | — |  |
| Z04.drawer | нажать_ящик |  | Z04.drawer.open | — | звук:sfx_drawer_click |
| Z04.lowdrawer | осмотр |  | Z04.drawer.look | — |  |
| Z04.lowdrawer | нажать_ящик | ¬relic_r3 | Z04.lowdrawer.open | R3_mug | +relic_r3, звук:sfx_drawer_click, звук:sting_relic, кадр:вид:Z04+st_z04_lowdrawer_mug |
| Z04.lowdrawer | нажать_ящик | relic_r3 | Z04.lowdrawer.again | — |  |
| Z05.vitrine | осмотр | ¬vitrine_open | Z05.vitrine.look | — |  |
| Z05.vitrine | осмотр | vitrine_open | Z05.meter.look | — |  |
| Z05.vitrine | поддеть | ¬vitrine_open | Z05.vitrine.pry | — |  |
| Z05.vitrine | разбить | ¬vitrine_open | Z05.vitrine.smash | — |  |
| Z05.vitrine | нажать_стекло | ¬vitrine_open ∧ scr_cascade | Z05.vitrine.push | C17_vitrine_readings | +vitrine_open, +meter_seal_seen, звук:sfx_latch_click, звук:sting_solved, кадр:zooms/zoom_z05+st_z05_tag+st_z05_palm+ov_skirt_open;zooms/zoom_z05+st_z05_open+st_z05_tag+ov_skirt_open |
| Z05.vitrine | нажать_стекло | ¬vitrine_open | Z05.vitrine.push.seen | — | кадр:zooms/zoom_z05+st_z05_tag+st_z05_palm+ov_skirt_open |
| Z05.vitrine | предмет:plunger | ¬vitrine_open | Z05.vitrine.plunger | — |  |
| Z05.tag | осмотр |  | Z05.meter.look | — |  |
| Z05.tag | отогнуть |  | Z05.tag.fold | C17_vitrine_readings | +meter_reading_seen, звук:sfx_tag_fold, кадр:zooms/zoom_z05+st_z05_open+st_z05_tag_folded+ov_skirt_open, док:DOC.tag |
| Z05.seal | осмотр |  | Z05.meter.look | — |  |
| Z05.seal | стереть |  | Z05.seal.wipe | — |  |
| Z05.guests | осмотр |  | W2.guests | — |  |
| Z05.skirt | вылезти |  | W2.getout | — |  |
| Z05.back | клик |  | SEQ.exhibit.back | — | pos=service, звук:sfx_trolley_creak, кадр:вид:W2, вид:W2 |
| W3.drums | клик |  | — | — | вид:Z06 |
| W3.tanks | облиться |  | Z06.tank.probe | — | probe+, звук:sfx_foam_swell |
| W3.wall | клик |  | — | — | вид:Z07 |
| W3.cabinet | клик |  | — | — | вид:Z08 |
| W3.brand | осмотр |  | W3.brand.look | — |  |
| W3.door | в_вестибюль |  | — | — | вид:W2, цепочка:pa_more |
| W3.door | в_зал |  | — | — | вид:W4 |
| Z06.panels | осмотр |  | Z06.drums.look | — |  |
| Z06.drums | осмотр |  | Z06.drums.look | — |  |
| Z06.drums | запустить |  | Z06.drum.restart | — | звук:sfx_drum_beep, кадр:вид:Z06+st_z06_blink |
| Z07.wall | осмотр |  | Z07.cladding.look | — |  |
| Z07.wall | открыть_панель |  | Z07.cladding.use | — |  |
| Z08.cabinet | осмотр |  | Z08.cabinet.look | — |  |
| Z08.inner | осмотр |  | Z08.cabinet.look | — |  |
| Z08.inner | открыть | ¬relic_r2 | Z08.cabinet.open | R2_postcard | +relic_r2, звук:sting_relic, кадр:zooms/zoom_z08+st_z08_inner_postcard, док:DOC.postcard |
| Z08.inner | открыть | relic_r2 | Z08.cabinet.again | — |  |
| W4.mirror | клик |  | — | — | вид:Z11 |
| W4.lift | клик |  | — | — | вид:Z11 |
| W4.mirror2 | клик |  | — | — | вид:Z11 |
| W4.design | осмотр |  | W4.design.look | — | док:DOC.sticker |
| W4.design_board | осмотр |  | Z11.board.look | — |  |
| W4.design_board | достать_доску |  | Z11.board.return | — | -ramp_thrown |
| W4.stairs | клик |  | — | — | вид:Z12 |
| W4.board | клик |  | — | — | вид:Z09 |
| W4.hatch | осмотр |  | W4.hatch.look | — |  |
| W4.floor | осмотр |  | W4.lift.search | — |  |
| W4.water | клик |  | — | — | вид:Z10 |
| W4.trolley | осмотр | trolley_marked_partial | — | — | док:DOC.partial_mark |
| W4.trolley | осмотр | test_run_done ∧ ¬bill_stamped | — | — | док:DOC.note |
| W4.trolley | спустить_тележку | ¬knows_lift_exists | W4.stairs.trolley | C02_trolley_stairs | +knows_lift_exists, pos=stairs, звук:sfx_trolley_jam, кадр:вид:W4+st_w4_trolley_stairs, цепочка:back_hall |
| W4.trolley | спустить_тележку |  | W4.stairs.carry | — |  |
| W4.trolley | за_стойку | bill_read ∧ ¬trolley_back_at_counter | SEQ.bill.counter | C11_trolley_counter | +trolley_back_at_counter, pos=service, звук:sfx_trolley_creak, кадр:вид:W2, вид:W2 |
| W4.trolley | за_стойку |  | — | — | pos=service, звук:sfx_trolley_creak, вид:W2, цепочка:counter_again |
| W4.table | клик |  | — | — | вид:Z10 |
| W4.back | в_вестибюль |  | — | — | вид:W2, цепочка:pa_more |
| W4.back | в_прачечную |  | — | — | вид:W3 |
| Z09.board | осмотр |  | Z09.board.look | C18_board_plate | +knows_plate_under_paint, +knows_paint_fresh, +paint_act_read, +chalk_sample_seen, док:DOC.paint_act |
| Z09.paint | осмотр | name_revealed | Z09.plate.look | — | док:DOC.plate_k |
| Z09.paint | осмотр |  | Z09.board.look | C18_board_plate | +knows_plate_under_paint, +knows_paint_fresh, +paint_act_read, +chalk_sample_seen, док:DOC.paint_act |
| Z09.paint | тереть | knows_plate_under_paint ∧ ¬name_revealed | Z09.paint.rub | — | звук:sfx_soap_smear |
| Z09.paint | предмет:menu | knows_plate_under_paint ∧ knows_paint_fresh ∧ ¬name_revealed | Z09.paint.scrape | C18_board_plate | +name_revealed, +board_restored, +menu_smeared, звук:sfx_paint_scrape, звук:sting_solved, кадр:вид:Z09+st_z09_stripes;вид:Z09+st_z09_stripes;вид:Z09, док:DOC.plate_k |
| Z09.paint | предмет:plunger | ¬name_revealed | Z09.paint.plunger | — |  |
| Z09.paint | предмет:token | ¬name_revealed | Z09.paint.token | — |  |
| Z09.act | осмотр |  | — | — | док:DOC.paint_act |
| Z09.chalk | осмотр |  | Z09.chalk.look | — |  |
| Z09.slot | осмотр |  | Z09.slot.look | — |  |
| Z09.slot | нажать_заслонку | ¬relic_r1 | Z09.slot.use | R1_token | +relic_r1, звук:sfx_token_drop, звук:sting_relic, док:DOC.token |
| Z10.table | осмотр |  | Z10.table.look | — |  |
| Z10.tube | осмотр |  | — | — | док:DOC.map_1908 |
| Z10.tube | взять |  | FB.paper.act3 | — |  |
| Z10.folder | осмотр |  | — | — | док:DOC.map_soviet |
| Z10.papers | осмотр |  | Z10.table.look | — |  |
| Z10.papers | читать_распоряжение |  | — | — | док:DOC.layoff |
| Z10.papers | читать_памятку | ¬memo_soviet_read | Z10.memo.read | O10_read_memo | +memo_soviet_read, док:DOC.memo |
| Z10.papers | читать_памятку |  | — | — | док:DOC.memo |
| Z10.papers | унести |  | Z10.paper.take | — |  |
| Z10.journal | осмотр |  | — | — | док:DOC.journal |
| Z10.journal | взять |  | FB.paper.act3 | — |  |
| Z10.photo | осмотр | knows_lift_exists ∧ ¬knows_lift_in_hall | Z10.photo.again | C03_photo_floor | +knows_lift_in_hall, док:DOC.photo |
| Z10.photo | осмотр |  | — | — | док:DOC.photo |
| Z10.glass | осмотр | topology_known | Z10.films.look | — | кадр:планы:люк |
| Z10.glass | осмотр |  | W4.hatch.look | — |  |
| Z10.water | осмотр |  | Z10.water.look | — | док:DOC.water_stand |
| Z10.water | взять |  | Z10.water.carry | — |  |
| Z10.water | облиться |  | Z10.water.head | — | probe+, звук:sfx_foam_swell |
| Z10.water | на_тележку | knows_order_trolley ∧ pos=hall | Z10.water.offer | C08_offering | +offering_on_trolley |
| Z11.mirror | осмотр | knows_door_behind_mirror | Z11.mirror.look.again | — |  |
| Z11.mirror | осмотр | knows_lift_exists | Z11.threshold.look | C04_threshold | +knows_door_behind_mirror, +knows_lift_in_hall, +mirror_seen |
| Z11.mirror | осмотр |  | Z11.mirror.look | — |  |
| Z11.mirror | снять_зеркало | ¬knows_door_behind_mirror | Z11.mirror.use | — |  |
| Z11.mirror | нажать_зеркало | knows_door_behind_mirror | Z11.mirror.press | O01_mirror_hands | +mirror_tried |
| Z11.mirror | потянуть_зеркало | knows_door_behind_mirror | Z11.mirror.pull | O01_mirror_hands | +mirror_tried |
| Z11.mirror | разбить_зеркало |  | Z11.mirror.smash | — |  |
| Z11.mirror | отклеить |  | Z11.sticker.peel | — |  |
| Z11.mirror | предмет:menu |  | Z11.mirror.menu | — |  |
| Z11.mirror | предмет:menu_p |  | Z11.mirror.menu | — |  |
| Z11.mirror | предмет:plunger | knows_lift_in_hall ∧ knows_door_behind_mirror ∧ knows_soap_grip | — | C05_plunger_mirror | сцена:mirror |
| Z11.threshold | осмотр |  | Z11.threshold.look | C04_threshold | +knows_door_behind_mirror, +knows_lift_in_hall, +mirror_seen |
| Z11.mirror2 | осмотр |  | Z11.mirror.after | — |  |
| Z11.stencil | осмотр |  | Z11.gate.look | — | док:DOC.stencil, док:DOC.post |
| Z11.post | осмотр |  | Z11.gate.look | — | док:DOC.stencil, док:DOC.post |
| Z11.post | ждать_воду | test_run_done ∧ ¬payment_delivered | Z11.wait.water | — |  |
| Z11.cabin | осмотр | ¬cabin_seen | Z11.cabin.look | C06_inspect_cabin | +cabin_seen, +chalk_seen, док:DOC.sticker, док:DOC.chalk |
| Z11.cabin | осмотр | ¬junk_out | — | — | док:DOC.sticker |
| Z11.cabin | открыть_решётку | ¬cabin_seen | Z11.cabin.look | C06_inspect_cabin | +cabin_seen, +chalk_seen, док:DOC.sticker, док:DOC.chalk |
| Z11.cabin | банки | cabin_seen ∧ ¬junk_out | Z11.cabin.paint | — | док:DOC.paint_can |
| Z11.cabin | вынести_дизайн | cabin_seen ∧ chalk_seen ∧ ¬junk_out | — | C07_clear_junk | сцена:clear |
| Z11.cabin | искать_кнопку | cabin_seen | Z11.cabin.button | — |  |
| Z11.cabin | вкатить_тележку | pos=hall ∧ cabin_seen ∧ ¬junk_out | Z11.cabin.trolley.full | — |  |
| Z11.cabin | вкатить_тележку | pos=hall ∧ junk_out ∧ ¬ramp_set | Z11.cabin.trolley.step | — | звук:sfx_wheel_bump, кадр:вид:Z11+st_z11_trolley_stuck |
| Z11.cabin | отправить_тележку | pos=hall ∧ ramp_set ∧ payment_in_hall | — | C19_send_alone | -payment_in_hall, сцена:send_alone |
| Z11.cabin | отправить_тележку | pos=hall ∧ ramp_set ∧ offering_on_trolley ∧ ¬test_run_done | — | C09_test_run | сцена:test |
| Z11.cabin | отправить_тележку | pos=hall ∧ ramp_set ∧ ¬offering_on_trolley ∧ ¬test_run_done | Z11.lift.empty | — |  |
| Z11.cabin | встать_в_кабину | payment_in_hall ∧ cabin_free | Z11.ride.standing | O08_ride_standing | +people_ban_read |
| Z11.cabin | встать_в_кабину | ¬payment_in_hall ∧ ¬trolley_marked_partial | Z11.lift.ride.early | — |  |
| Z11.cabin | под_тележку | pos=hall ∧ ramp_set ∧ payment_in_hall ∧ iz_reported_pa | — | C16_ride_as_staff | сцена:ride |
| Z11.cabin | под_тележку | pos=hall ∧ ramp_set ∧ trolley_marked_partial ∧ iz_reported_pa | — | C16b_ride_after_send | сцена:ride_after |
| Z11.switch | осмотр |  | — | — | док:DOC.chalk |
| Z11.switch | повернуть_рубильник |  | Z11.switch.use | O03_touch_switch | +switch_tried, звук:sfx_switch, кадр:вид:Z11+st_z11_lamp_off;вид:Z11+st_z11_lamp_off;вид:Z11 |
| Z11.switch | стереть_мел | chalk_seen | Z11.chalk.wipe | — |  |
| Z11.board | осмотр |  | Z11.board.look | — |  |
| Z11.board2 | осмотр |  | Z11.board.look | — |  |
| Z11.board2 | положить_трапом |  | Z11.ramp.set | C07b_set_ramp | +cabin_free, +ramp_set, звук:sfx_board_lay, кадр:вид:Z11 |
| Z11.board2 | выбросить |  | Z11.board.throw | O12_throw_ramp | +ramp_thrown |

## Цепочки

| Группа | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|
| pa_more | junk_out ∧ n(W2.pa.more)<2 | W2.pa.more | — | звук:sfx_pa_chime |
| pa_more |  | — | — |  |
| back_hall |  | — | — | pos=hall |
| counter_again | ¬shown(SEQ.counter.again) | SEQ.counter.again | — |  |
| counter_again |  | — | — |  |
| plate_line | board_restored | Z11.bill.plate.done | — |  |
| plate_line |  | Z11.bill.plate.todo | — |  |
| bill_look |  | INV.bill.look | — | док:DOC.bill, цепочка:plate_line |
| read_bill |  | Z11.bill.read | C10_read_bill | +kuh_note_read, +bill_read, +knows_kuh_name, +knows_debt_balance, +knows_secret_payer, +lowest_point, кадр:zooms/zoom_z11+st_z11_mirror_aside+st_z11_cabin_empty+st_z11_ramp+st_z11_trolley_returned, док:DOC.bill, цепочка:plate_line |

## Сцены

Шаги идут подряд; «Кадр» — картинка шага (`слой+слой…`, первым — фон; `;` — следующая картинка с очередной реплики); «вид:W2» — вид в его текущем состоянии (флаги шага уже стоят).

| Сцена | Слот | Кадр | Звук | Эффекты |
|---|---|---|---|---|
| open | OPEN.door | zooms/zoom_z12 | амбиент:amb_below | pos=service, вид:Z12 |
| open | OPEN.pa | zooms/zoom_z12 | sfx_pa_chime |  |
| open | OPEN.anc | zooms/zoom_z12 |  |  |
| mirror | Z11.mirror.plunger | zooms/zoom_z11+st_z11_mirror;zooms/zoom_z11+st_z11_mirror+st_z11_hand_plunger;вид:Z11 | sfx_suction_glass | +mirror_removed, +lift_gate_seen |
| mirror | PA.mirror | вид:Z11 | sfx_pa_chime |  |
| clear | Z11.cabin.clear | вид:Z11 |  | +junk_out |
| clear | PA.cabin | вид:Z11 | sfx_pa_chime |  |
| test | SEQ.test.send | zooms/zoom_z11+st_z11_mirror_aside+st_z11_cabin_empty+st_z11_ramp+st_z11_trolley_water+st_z11_finger_down;zooms/zoom_z11+st_z11_mirror_aside | sfx_grille_shut, sfx_lift_down | pos=receiving |
| test | SEQ.test.call | zooms/zoom_z11+st_z11_mirror_aside+st_z11_finger_call;zooms/zoom_z11+st_z11_mirror_aside+st_z11_cabin_empty+st_z11_ramp+st_z11_trolley_returned | sfx_lift_up | +test_run_done, +has_bill, +breakfast_stamped, pos=hall, док:DOC.note, док:DOC.tray_stamp |
| test | — | zooms/zoom_z11+st_z11_mirror_aside+st_z11_cabin_empty+st_z11_ramp+st_z11_trolley_returned |  | цепочка:read_bill |
| payment | Z04.bill.under | вид:Z04+st_z04_bill_mp+st_z04_iz_hand;вид:Z04 | sfx_stamp | +bill_stamped |
| payment | TALK.iz.confess | вид:Z04 |  | +iz_confessed, +knows_payer_iz |
| payment | SEQ.iz.payment | вид:Z04+st_z04_drawer_kefir;вид:Z04 | sfx_drawer_click, sfx_stamp | +iz_sees_lapidus, +kefir_ready, +invoice_ready, док:DOC.invoice |
| report | SEQ.report | rooms/room_w2+st_w2_forms1+st_w2_complaints+st_w2_iz_mic+st_w2_trolley+st_w2_tt_payment;rooms/room_w2+st_w2_forms1+st_w2_complaints+st_w2_iz_mic+st_w2_trolley+st_w2_tt_payment;frames/fr_a3_lobby_hush+ov_skirt;frames/fr_a3_lobby_hush+ov_skirt | sfx_pa_chime, sfx_lobby_hush | +iz_reported_pa, +payment_in_hall, pos=hall, вид:W4 |
| send_alone | SEQ.send.alone | zooms/zoom_z11+st_z11_mirror_aside+st_z11_cabin_empty+st_z11_ramp+st_z11_finger_down;zooms/zoom_z11+st_z11_mirror_aside+st_z11_cabin_empty+st_z11_ramp+st_z11_trolley_marked | sfx_lift_down, sfx_lift_up | +payment_delivered, +payment_sent_alone, +trolley_marked_partial, pos=hall, док:DOC.partial_mark |
| ride | SEQ.ride | frames/fr_a3_ride_under | sfx_grille_shut | +descended_as_staff, +lap_hides_again, +goods_on_trolley, pos=cabin |
| ride | SEQ.descent | frames/fr_a3_dark;frames/fr_a3_under_arrive+ov_skirt_dark | музыка:bgm_deep, sfx_descent | +payment_delivered, +in_receiving_point, pos=receiving |
| ride | END.act3 | frames/fr_a3_under_arrive+ov_skirt_dark | sfx_wet_steps | акт:4 |
| ride_after | Z11.ride.after.send | вид:Z11;frames/fr_a3_ride_under;frames/fr_a3_ride_under | sfx_grille_shut | +descended_as_staff, +lap_hides_again, pos=cabin |
| ride_after | SEQ.descent | frames/fr_a3_dark;frames/fr_a3_under_arrive+ov_skirt_dark | музыка:bgm_deep, sfx_descent | +in_receiving_point, pos=receiving |
| ride_after | END.act3 | frames/fr_a3_under_arrive+ov_skirt_dark | sfx_wet_steps | акт:4 |

## Меню

Подпись пункта — строка `choice` слота из колонки «Подпись» или ключ `texts/ui/UI_TEXTS.md`. Правила одного пункта — сверху вниз. Разговор не закрыть, пока не выбран «Закончить разговор».

| Меню | Пункт | Подпись | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|---|---|
| talk | invoice | TALK.iz.invoice | bill_stamped ∧ ¬meter_reading_seen ∧ ¬invoice_filled | TALK.iz.invoice.noreading | — | меню:talk |
| talk | invoice | TALK.iz.invoice | bill_stamped ∧ ¬board_restored ∧ ¬invoice_filled | TALK.iz.invoice.noplate | — | меню:talk |
| talk | invoice | TALK.iz.invoice | bill_stamped ∧ ¬invoice_filled | TALK.iz.invoice | C13b_report_for_invoice | +invoice_filled, звук:sfx_stamp, док:DOC.invoice, меню:talk |
| talk | bill | TALK.iz.bill | bill_read ∧ ¬bill_stamped | TALK.iz.bill | O05_bill_direct | +iz_forwards_bill, меню:talk |
| talk | stamp | TALK.iz.stamp | bill_read ∧ ¬bill_stamped | TALK.iz.stamp | — | меню:talk |
| talk | accuse | TALK.iz.accuse | knows_secret_payer ∧ ¬iz_confessed | TALK.iz.accuse | — | меню:talk |
| talk | carry | TALK.iz.carry | kefir_ready ∧ ¬payment_loaded | TALK.iz.carry | — | меню:talk |
| talk | kefir | TALK.iz.kefir | knows_order_trolley ∧ ¬kefir_ready | TALK.iz.kefir | O04_ask_kefir | +iz_kefir_refused, меню:talk |
| talk | mirror | TALK.iz.mirror | knows_door_behind_mirror | TALK.iz.mirror | O02_ask_mirror | +iz_mirror_design, меню:talk |
| talk | vitrine | TALK.iz.vitrine | ¬vitrine_open | TALK.iz.vitrine | — | меню:talk |
| talk | seal | TALK.iz.seal | meter_seal_seen | TALK.iz.seal | — | меню:talk |
| talk | plate | TALK.iz.plate | name_revealed | TALK.iz.plate | — | меню:talk |
| talk | exit | TALK.iz.exit |  | TALK.iz.exit | — |  |

## Подсказки

Порядок строк — приоритет тем (SLOT_FLAGS, Акт III: по кратчайшему пути C01 → C16). Уточнено при сборке: тема `down` открыта и после отправки оплаты одной (`trolley_marked_partial`) — ехать докладчиком ещё надо.

| Тема | Открыта, когда |
|---|---|
| order | ¬instr1908_read |
| lift | instr1908_read ∧ ¬knows_lift_exists |
| where | knows_lift_exists ∧ ¬(knows_lift_in_hall ∧ knows_door_behind_mirror) |
| mirror | knows_lift_in_hall ∧ knows_door_behind_mirror ∧ ¬mirror_removed |
| cabin | mirror_removed ∧ ¬junk_out |
| ramp | junk_out ∧ ¬ramp_set |
| test | cabin_free ∧ ¬test_run_done |
| payer | bill_read ∧ ¬bill_stamped |
| plate | bill_read ∧ ¬board_restored |
| reading | bill_stamped ∧ ¬meter_reading_seen |
| invoice | bill_stamped ∧ meter_reading_seen ∧ board_restored ∧ ¬invoice_filled |
| load | invoice_filled ∧ ¬payment_loaded |
| down | (payment_in_hall ∨ trolley_marked_partial) ∧ ¬in_receiving_point |

## Предметы

| Предмет | Иконка | При себе, когда | Осмотр | Эффекты осмотра | Мимо (неплоское) | Мимо (плоское) |
|---|---|---|---|---|---|---|
| plunger | icons/ic_plunger | plunger_taken | INV.plunger.act3 |  | FB.plunger.act3 | FB.plunger.act3 |
| menu | icons/ic_menu | has_menu_card ∧ ¬menu_smeared | INV.menu.look | док:DOC.menu | @fb_menu | @fb_menu |
| menu_p | icons/ic_menu_painted | menu_smeared | INV.menu.painted |  | @fb_menu | @fb_menu |
| bill | icons/ic_bill | has_bill ∧ ¬bill_stamped | @bill_look |  | FB.bill.1 | FB.bill.1 |
| token | icons/ic_token | relic_r1 | INV.token.look | док:DOC.token | @fb_generic | @fb_generic |
| postcard | icons/ic_postcard | relic_r2 | INV.postcard.look | док:DOC.postcard | @fb_generic | @fb_generic |

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
| DOC.notice_counter | docs/paper_kuh |  |
| DOC.notice_door | docs/paper_kuh |  |
| DOC.instr1908 | docs/paper_1908 |  |
| DOC.exhibit | docs/plaque_museum |  |
| DOC.tag | docs/tag_exhibit |  |
| DOC.journal | docs/page_ledger |  |
| DOC.paint_act | docs/paper_office |  |
| DOC.layoff | docs/paper_hotel |  |
| DOC.plate_k | docs/plate_enamel |  |
| DOC.regulation | docs/paper_regulation |  |
| DOC.memo | docs/paper_soviet |  |
| DOC.map_1908 | docs/paper_lightbox+docs/plan_1908 |  |
| DOC.map_soviet | docs/paper_lightbox+docs/plan_soviet |  |
| DOC.photo | docs/photo_thursday |  |
| DOC.postcard | docs/card_postcard |  |
| DOC.token | docs/token_big |  |
| DOC.menu | docs/paper_laminated |  |
| DOC.stencil | docs/panel_steel |  |
| DOC.sticker | docs/label_sticker |  |
| DOC.chalk | docs/box_switch |  |
| DOC.post | docs/panel_post |  |
| DOC.paint_can | docs/label_can |  |
| DOC.water_stand | docs/card_tent |  |
| DOC.note | docs/paper_note |  |
| DOC.bill | docs/paper_kuh |  |
| DOC.tray_stamp | docs/tray_porcelain |  |
| DOC.complaint | docs/paper_office |  |
| DOC.invoice | docs/paper_office |  |
| DOC.partial_mark | docs/paper_kuh |  |

## Прочее

| Слот | Где звучит |
|---|---|
| UI.inventory | подпись кнопки «При себе» (из Акта I) |
| HINT.intro | первое нажатие «Совет предка» (из Акта I) |
| HINT.cooldown | совет уже дан, после него не было действия (из Акта I) |
| HINT.done | открытых тем нет |
