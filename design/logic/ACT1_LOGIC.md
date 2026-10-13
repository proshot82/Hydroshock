# Акт I «Комплимент от заведения» — логика для движка

Источник данных игры (шаг 2 плана сборки, `docs/BJ3_BUILD_PLAN.md`). Отсюда генератор `tools/data/gen_design.py` собирает `design/act1.json` (руками не править); проверка — `tools/data/check_logic.py` (каждый слот текстов Акта I на своём месте, каждое действие графа — с теми же условиями и последствиями, победа достижима из любого состояния).

Источники: граф `acts/act1/ACT1_graph.json` (ред. 3), условия слотов `docs/BJ3_SLOT_FLAGS.md` (Акт I), ТЗ `texts/act1/BRIEF_ACT1_TEXTS.md` §9, кадры и слои `docs/BJ3_ASSET_SPEC.md` §2–§4, звук §9. При расхождении побеждает граф (шапка SLOT_FLAGS).

## Обозначения

- **Условие:** флаги графа; `¬` — не, `∧` — и, `∨` — или, скобки; `shown(СЛОТ)`, `n(СЛОТ)>=k`; `pos=…` — положение тележки; `probe.n`, `call.n` — счётчики. Пустое условие — всегда.
- **Глагол:** `осмотр` — правая кнопка или «Осмотреть» в меню; `клик` — сразу по щелчку (переходы); иначе — пункт меню действий, подпись `verb_<глагол>` из `texts/ui/UI_TEXTS.md`; `предмет:ИМЯ` — применить предмет из «При себе».
- **Правила одной зоны и глагола** проверяются сверху вниз, срабатывает первое с истинным условием; пункт меню виден, если хоть одно правило глагола истинно.
- **Слот:** id слота текстов; `@группа` — выбрать слот из «Цепочек»; `—` — без реплик.
- **Эффекты** через запятую: `+флаг`, `-флаг`; `pos=…`; `probe+`, `call+`; `вид:ВИД`; `док:DOC.x`; `сцена:ИМЯ`; `меню:ИМЯ`; `цепочка:ИМЯ` (после реплик слота); `звук:ИМЯ`; `музыка:ИМЯ` (на время слота); `кадр:слой+слой…` (картинка на время слота); `акт:N`; `портрет:сухой` (Лапидус без пены — только `OPEN.1_voucher`).
- **Экранный флаг** `scr_…` — состояние экрана, а не сюжета (отодвинутая шторка тележки): ставится и снимается эффектами, как флаг графа, но движок снимает все экранные флаги, когда игрок уходит с вида (решение автора 13.10.2026, «да на все» по Р7). В графе их нет.
- **Музыка в сценах:** `музыка:ИМЯ` в шаге сцены — тема с этого шага до конца сцены или до шага «как вид»; `музыка:стоп` — обрыв музыки и амбиента, миг тишины (0,7 с), потом звуки шага (гидроудар в тишине — решение автора 13.10.2026).
- **Где** у зоны: `x,y,w,h` (несколько через `;`) или `слой ИМЯ` — по непрозрачным пикселям слоя. Зоны-слои лежат поверх прямоугольных; среди равных первой ловит меньшая.

## Виды

| Вид | Тип | Фон | Родитель | Музыка | Амбиент |
|---|---|---|---|---|---|
| W1 | экран | rooms/room_w1 | — | bgm_hotel | amb_room |
| Z01 | зум | zooms/zoom_z01 | W1 | — | — |
| Z02 | зум | zooms/zoom_z02 | W1 | — | — |
| Z03 | зум | zooms/zoom_z03 | W1 | — | — |
| C1 | экран | frames/fr_a1_corridor | W1 | — | — |
| L1 | экран | frames/fr_a1_lift_panel | C1 | — | — |
| W2u | экран | rooms/room_w2_under | — | bgm_hotel | amb_lobby |
| W2s | кадр | frames/fr_a1_under_service | — | bgm_hotel | amb_lobby |

## Слои

Порядок строк — порядок наложения (архитектура → персонажи → предметы → руки → юбка).

| Вид | Слой | Когда |
|---|---|---|
| W1 | st_w1_cistern_open | shown(PROBE.cistern) |
| W1 | st_w1_plunger | plunger_on_panel |
| W1 | st_w1_menu | ¬has_menu_card |
| W1 | st_w1_trolley | pos=room ∧ ¬stars_folded |
| W1 | st_w1_trolley_folded | pos=room ∧ stars_folded |
| W1 | st_w1_juice_empty | pos=room ∧ ¬stars_folded ∧ shown(PROBE.juice) |
| Z01 | st_z01_plunger | plunger_on_panel |
| Z02 | st_z02_voucher_soaked | reception_called |
| Z02 | st_z02_mineral_empty | shown(PROBE.mineral) |
| Z02 | st_z02_kombucha_empty | shown(PROBE.kombucha) |
| Z02 | st_z02_lemonade_empty | shown(PROBE.lemonade) |
| Z02 | st_z02_menu | ¬has_menu_card |
| Z03 | st_z03_juice_empty | shown(PROBE.juice) |
| Z03 | st_z03_stars_folded | stars_folded |
| Z03 | st_z03_skirt_open | scr_skirt_open ∧ ¬stars_folded |
| Z03 | st_z03_skirt_open_folded | scr_skirt_open ∧ stars_folded |
| W2u | st_w2u_crowd | ¬trolley_service_side |
| W2u | ov_skirt |  |
| W2s | ov_skirt |  |

## Зоны

| Вид | Зона | Название | Где | Курсор | Когда | Свойства |
|---|---|---|---|---|---|---|
| W1 | door | Дверь номера | 10,40,220,840 | act |  | плоское |
| W1 | hooks | Крючки | 290,190,90,90 | look |  |  |
| W1 | bed | Кровать | 320,420,690,260 | look |  |  |
| W1 | window | Окно | 640,50,380,350 | look |  | плоское |
| W1 | suitcase | Чемодан | 1050,370,200,140 | look |  |  |
| W1 | desk | Стол и мини-бар | 1250,430,320,360 | zoom |  |  |
| W1 | bucket | Мусорное ведро | 1450,670,100,160 | look |  |  |
| W1 | shower | Душевая | 1640,90,130,590 | zoom |  |  |
| W1 | cistern | Бачок унитаза | 1770,380,90,290 | act |  |  |
| W1 | trolley | Тележка | слой st_w1_trolley | zoom | pos=room ∧ ¬stars_folded |  |
| W1 | trolley_f | Тележка | слой st_w1_trolley_folded | zoom | pos=room ∧ stars_folded |  |
| Z01 | head | Лейка | 480,20,240,110;730,530,90,190 | act |  |  |
| Z01 | dispenser | Дозатор пены | 920,440,120,280;880,780,370,130 | act |  | плоское |
| Z01 | plunger | Вантуз | слой st_z01_plunger | act | plunger_on_panel |  |
| Z01 | ring | Мокрый след | 1150,790,110,110 | look | wet_ring_seen | плоское |
| Z02 | voucher | Путёвка | 350,60,410,280 | look |  | плоское |
| Z02 | phone | Телефон | 1210,0,390,370 | act |  |  |
| Z02 | minibar | Мини-бар | 570,460,650,540 | look |  |  |
| Z02 | mineral | Минералка «Каскадъ» | 680,490,120,330 | act |  |  |
| Z02 | kombucha | Комбуча | 830,496,100,324 | act |  |  |
| Z02 | lemonade | Авторский лимонад | 966,500,94,320 | act |  |  |
| Z02 | menu | Меню мини-бара | слой st_z02_menu | act | ¬has_menu_card | плоское |
| Z03 | pot | Кофейник | 430,30,290,220 | act |  |  |
| Z03 | cup | Чашка | 560,250,220,170 | act |  |  |
| Z03 | juice | Стакан сока | 770,110,100,230 | act |  |  |
| Z03 | cloche | Колпак | 860,70,360,280 | act |  |  |
| Z03 | napkin | Салфетка | 850,370,280,130 | act |  |  |
| Z03 | stars | Звёзды | 300,450,1300,160 | act |  |  |
| Z03 | skirt | Юбка тележки | 280,610,1350,390 | act |  |  |
| Z03 | handle | Тележка | 1480,60,240,400 | act |  |  |
| Z03 | plate | Латунная табличка | 720,600,230,100 | look | scr_skirt_open |  |
| C1 | lift | Служебный лифт | 800,300,190,270 | move |  |  |
| C1 | room | Назад в номер 317 | 1560,60,360,900 | move |  |  |
| L1 | lobby | Кнопка «Вестибюль» | 790,495,220,100 | act |  |  |
| W2u | crowd | Толпа | 300,60,1320,880 | act | ¬trolley_service_side |  |
| W2u | counter | Стойка | 1240,430,280,330 | act |  |  |
| W2u | lobby | Вестибюль за толпой | 1060,80,200,160 | act |  |  |
| W2u | skirt | Юбка тележки | 80,60,220,940;1620,60,220,940 | act |  |  |
| W2u | back | Назад к лифту | 300,960,1320,110 | move |  |  |

## Действия

| Зона | Глагол | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|---|
| W1.door | осмотр |  | W1.door.look | A12_inspect_room | +room_bare_seen, +knows_bath_day, док:DOC.bathday |
| W1.door | выйти | ¬need_cover ∧ ¬shown(SEQ.peek.1_corridor) | SEQ.peek.1_corridor | — | кадр:frames/fr_a1_corridor, вид:C1 |
| W1.door | выйти | ¬need_cover | — | — | вид:C1 |
| W1.door | выйти | need_cover | W1.door.again | — |  |
| W1.hooks | осмотр |  | W1.hooks | A12_inspect_room | +room_bare_seen |
| W1.bed | осмотр |  | W1.bed | A12_inspect_room | +room_bare_seen |
| W1.window | осмотр |  | W1.window | A12_inspect_room | +room_bare_seen |
| W1.suitcase | осмотр |  | W1.suitcase | A12_inspect_room | +room_bare_seen |
| W1.bucket | осмотр |  | W1.bucket | A12_inspect_room | +room_bare_seen |
| W1.desk | клик |  | — | — | вид:Z02 |
| W1.shower | клик |  | — | — | вид:Z01 |
| W1.trolley | клик |  | — | — | вид:Z03 |
| W1.trolley_f | клик |  | — | — | вид:Z03 |
| W1.cistern | осмотр |  | W1.cistern.look | — |  |
| W1.cistern | облиться | foam_active ∧ ¬foam_class_closed | PROBE.cistern | A02f_probe_cistern | +foam_class_closed, +foam_swollen, +knows_soap_grip, звук:sfx_foam_swell, цепочка:probe_rule |
| W1.cistern | облиться | foam_class_closed | @probe_repeat | — |  |
| C1.lift | клик | ¬shown(SEQ.peek.2_lift) | SEQ.peek.2_lift | — | кадр:frames/fr_a1_lift_panel, вид:L1 |
| C1.lift | клик |  | — | — | вид:L1 |
| C1.room | клик |  | — | — | вид:W1 |
| L1.lobby | клик | ¬need_cover | — | A07_peek_lobby | звук:sfx_lift_down, сцена:peek |
| Z01.head | осмотр |  | Z01.head.look | — |  |
| Z01.head | включить | ¬shown(Z01.head.use) | Z01.head.use | — | звук:sfx_shower_sigh |
| Z01.head | включить | shown(Z01.head.use) | Z01.head.use.repeat | — | звук:sfx_shower_sigh |
| Z01.dispenser | осмотр | plunger_on_panel | Z01.dispenser.look | — |  |
| Z01.dispenser | осмотр | ¬plunger_on_panel | Z01.dispenser.look.full | — | док:DOC.pictograms |
| Z01.dispenser | нажать | | Z01.dispenser.use | — |  |
| Z01.plunger | осмотр |  | Z01.plunger.look | — |  |
| Z01.plunger | потянуть | plunger_on_panel | Z01.plunger.pull | N01a_pull_plunger | +plunger_pull_tried |
| Z01.plunger | подцепить | plunger_on_panel | Z01.plunger.pull | N01b_fingers | +fingers_edge_tried |
| Z01.plunger | нажать_чашку | plunger_on_panel | Z01.plunger.pull | N01c_push | +push_tried |
| Z01.plunger | предмет:menu | plunger_on_panel ∧ ¬foam_class_closed | Z01.plunger.take | N01_free_plunger | +plunger_taken, +wet_ring_seen, +knows_foam_flow, -plunger_on_panel, звук:sfx_plunger_pop |
| Z01.plunger | предмет:menu | plunger_on_panel ∧ foam_class_closed | Z01.plunger.take.after | N01_free_plunger | +plunger_taken, +wet_ring_seen, +knows_foam_flow, -plunger_on_panel, звук:sfx_plunger_pop |
| Z01.ring | осмотр |  | Z01.ring.look | — |  |
| Z02.voucher | осмотр | ¬reception_called | Z02.voucher.look | — | док:DOC.voucher |
| Z02.voucher | осмотр | reception_called | Z02.voucher.look.soaked | — | док:DOC.voucher |
| Z02.voucher | взять |  | Z02.voucher.take | — |  |
| Z02.phone | осмотр |  | Z02.phone.look | — |  |
| Z02.phone | позвонить | ¬reception_called | Z02.phone.call | A03_call_reception | +reception_called, +knows_paper_soaks, звук:sfx_phone_pickup, музыка:mus_hold |
| Z02.phone | позвонить | reception_called | Z02.phone.call.repeat | — | call+, звук:sfx_phone_pickup, музыка:mus_hold |
| Z02.minibar | осмотр |  | Z02.minibar.look | — |  |
| Z02.mineral | осмотр |  | Z02.mineral.look | — |  |
| Z02.mineral | взять | ¬shown(Z02.bottle.take) | Z02.bottle.take | — |  |
| Z02.mineral | взять | shown(Z02.bottle.take) | Z02.bottle.take.repeat | — |  |
| Z02.mineral | облиться | foam_active ∧ ¬foam_class_closed | PROBE.mineral | A02_probe_mineral | +foam_class_closed, +foam_swollen, +knows_soap_grip, звук:sfx_foam_swell, цепочка:probe_rule |
| Z02.mineral | облиться | foam_class_closed | @probe_repeat | — |  |
| Z02.mineral | предмет:plunger |  | Z02.plunger_bottle | — |  |
| Z02.kombucha | осмотр |  | Z02.kombucha.look | — |  |
| Z02.kombucha | взять | ¬shown(Z02.bottle.take) | Z02.bottle.take | — |  |
| Z02.kombucha | взять | shown(Z02.bottle.take) | Z02.bottle.take.repeat | — |  |
| Z02.kombucha | облиться | foam_active ∧ ¬foam_class_closed | PROBE.kombucha | A02b_probe_kombucha | +foam_class_closed, +foam_swollen, +knows_soap_grip, звук:sfx_foam_swell, цепочка:probe_rule |
| Z02.kombucha | облиться | foam_class_closed | @probe_repeat | — |  |
| Z02.kombucha | предмет:plunger |  | Z02.plunger_bottle | — |  |
| Z02.lemonade | осмотр |  | Z02.lemonade.look | — |  |
| Z02.lemonade | взять | ¬shown(Z02.bottle.take) | Z02.bottle.take | — |  |
| Z02.lemonade | взять | shown(Z02.bottle.take) | Z02.bottle.take.repeat | — |  |
| Z02.lemonade | облиться | foam_active ∧ ¬foam_class_closed | PROBE.lemonade | A02c_probe_lemonade | +foam_class_closed, +foam_swollen, +knows_soap_grip, звук:sfx_foam_swell, цепочка:probe_rule |
| Z02.lemonade | облиться | foam_class_closed | @probe_repeat | — |  |
| Z02.lemonade | предмет:plunger |  | Z02.plunger_bottle | — |  |
| Z02.menu | осмотр |  | Z02.menu.look | — |  |
| Z02.menu | взять |  | Z02.menu.take | A11_take_menu_card | +has_menu_card, +knows_assortment, док:DOC.menu |
| Z03.handle | осмотр | ¬stars_folded | Z03.trolley.look | — |  |
| Z03.handle | осмотр | stars_folded | Z03.trolley.look.work | — |  |
| Z03.handle | толкнуть | ¬stars_folded | Z03.trolley.push | — | звук:sfx_trolley_creak, звук:sfx_trolley_jam |
| Z03.handle | толкнуть | stars_folded | Z03.trolley.push.folded | — | звук:sfx_trolley_creak |
| Z03.stars | осмотр | ¬knows_stars_fold | Z03.stars.look | A05_inspect_stars | +knows_stars_fold, +minus_four_stars_said |
| Z03.stars | осмотр | knows_stars_fold ∧ ¬stars_folded | Z03.stars.look.again | — |  |
| Z03.stars | осмотр | stars_folded | Z03.stars.look.folded | — |  |
| Z03.stars | отломать | ¬knows_stars_fold | Z03.stars.pull | — |  |
| Z03.stars | сложить | knows_stars_fold ∧ ¬stars_folded | Z03.stars.fold | A06_fold_stars | +stars_folded, звук:sfx_stars_fold |
| Z03.skirt | осмотр | ¬knows_trolley_chamber | Z03.skirt.look | — |  |
| Z03.skirt | осмотр | knows_trolley_chamber | Z03.skirt.look.after | — |  |
| Z03.skirt | снять_юбку | ¬knows_trolley_chamber | Z03.skirt.use | A04_try_skirt | +knows_trolley_chamber, +plate_revealed, +scr_skirt_open |
| Z03.skirt | снять_юбку | knows_trolley_chamber | Z03.skirt.use.again | — |  |
| Z03.skirt | отодвинуть | knows_trolley_chamber ∧ ¬scr_skirt_open | — | — | +scr_skirt_open |
| Z03.plate | осмотр |  | Z03.plate.look | — | док:DOC.plate |
| Z03.skirt | под_тележку | trolley_at_crowd | — | — | сцена:drive_again |
| Z03.skirt | под_тележку | ¬need_cover | Z03.under.no_peek | — |  |
| Z03.skirt | под_тележку | ¬foam_class_closed | Z03.under.no_wash | — |  |
| Z03.skirt | под_тележку | ¬knows_foam_flow | Z03.under.no_flow | — |  |
| Z03.skirt | под_тележку | ¬reception_called | Z03.under.no_call | — |  |
| Z03.skirt | под_тележку | ¬stars_folded | Z03.under.stars | — |  |
| Z03.skirt | под_тележку | stars_folded ∧ need_cover ∧ reception_called ∧ knows_bath_day ∧ foam_class_closed ∧ knows_foam_flow | — | A08_drive_out | сцена:drive |
| Z03.pot | осмотр |  | Z03.pot.look | A13_inspect_breakfast | +knows_hot_warning |
| Z03.pot | взять |  | Z03.porcelain.take | — |  |
| Z03.pot | облиться | foam_active ∧ ¬foam_class_closed | PROBE.coffee | A02e_probe_coffee | +foam_class_closed, +foam_swollen, +knows_soap_grip, +knows_hot_warning, звук:sfx_foam_swell, цепочка:probe_rule |
| Z03.pot | облиться | foam_class_closed | @probe_repeat | — |  |
| Z03.cup | осмотр |  | Z03.cup.look | — |  |
| Z03.cup | взять |  | Z03.porcelain.take | — |  |
| Z03.cup | облиться | foam_active ∧ ¬foam_class_closed | PROBE.coffee | A02e_probe_coffee | +foam_class_closed, +foam_swollen, +knows_soap_grip, +knows_hot_warning, звук:sfx_foam_swell, цепочка:probe_rule |
| Z03.cup | облиться | foam_class_closed | @probe_repeat | — |  |
| Z03.juice | осмотр |  | Z03.juice.look | — |  |
| Z03.juice | облиться | foam_active ∧ ¬foam_class_closed | PROBE.juice | A02d_probe_juice | +foam_class_closed, +foam_swollen, +knows_soap_grip, звук:sfx_foam_swell, цепочка:probe_rule |
| Z03.juice | облиться | foam_class_closed | @probe_repeat | — |  |
| Z03.cloche | осмотр |  | Z03.cloche.look | — |  |
| Z03.cloche | прикрыться |  | Z03.cloche.use | — |  |
| Z03.napkin | осмотр |  | Z03.napkin.look | — |  |
| Z03.napkin | взять |  | Z03.napkin.use | — |  |
| W2u.crowd | осмотр |  | W2.crowd.look | — |  |
| W2u.crowd | протолкнуться | ¬shown(W2.crowd.push) | W2.crowd.push | — |  |
| W2u.crowd | протолкнуться | shown(W2.crowd.push) | W2.crowd.push.again | — |  |
| W2u.crowd | обратиться |  | — | — | меню:crowd |
| W2u.counter | осмотр |  | W2.board.look | — |  |
| W2u.counter | изольда |  | W2.isolde.look | — |  |
| W2u.lobby | плакат |  | W2.poster.look | — | +poster_seen, +knows_bath_day, док:DOC.bathday |
| W2u.lobby | каскад |  | W2.cascade.look | — | +cascade_dry_seen |
| W2u.skirt | вылезти |  | W2.getout.use | — |  |
| W2u.back | клик | ¬trolley_service_side | W2.lift.use | — | pos=room, вид:W1 |

## Цепочки

| Группа | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|
| probe_rule | knows_foam_flow | PROBE.rule.known | — |  |
| probe_rule | ¬knows_foam_flow | PROBE.rule.unknown | — |  |
| probe_repeat | probe.n=0 | PROBE.repeat.1 | — | probe+ |
| probe_repeat | probe.n=1 | PROBE.repeat.2 | — | probe+ |
| probe_repeat | probe.n>=2 | PROBE.repeat.3 | — | probe+ |
| talk_open |  | TALK.iz.open | A10_talk_isolde | +shock_report_known, меню:talk |
| act_end |  | END.act1 | — | звук:sfx_pa_chime, акт:2 |

## Сцены

Шаги идут подряд; «Кадр» — картинка шага (`слой+слой…`, первым — фон); «как вид» — текущее состояние вида.

| Сцена | Слот | Кадр | Звук | Эффекты |
|---|---|---|---|---|
| open | OPEN.1_voucher | frames/fr_a1_voucher | музыка:bgm_hotel | портрет:сухой |
| open | OPEN.2_shower | zooms/zoom_z01+st_z01_head_running+st_z01_plunger | петля:sfx_shower_run |  |
| open | OPEN.3_shock | zooms/zoom_z01+st_z01_plunger | музыка:стоп, стоп:sfx_shower_run, sfx_shock_thud |  |
| open | OPEN.4_after | вид:W1 |  |  |
| open | OPEN.5_anc | вид:W1 |  |  |
| peek | SEQ.peek.3_lobby | frames/fr_a1_lobby_peek | sfx_pa_chime, амбиент:amb_lobby | +crowd_seen, +cascade_dry_seen, +poster_seen, +knows_bath_day, +iz_folder_seen |
| peek | SEQ.peek.4_waiter | frames/fr_a1_lobby_waiter | sfx_crowd_part | +knows_waiter_call |
| peek | SEQ.peek.5_back | frames/fr_a1_lift_close |  | +need_cover, вид:W1 |
| drive | SEQ.drive.1_under | frames/fr_a1_under_room |  | pos=door |
| drive | SEQ.drive.2_lift | frames/fr_a1_under_liftdoors+ov_skirt | sfx_trolley_creak | pos=lift |
| drive | SEQ.drive.3_lobby | frames/fr_a1_under_lobby+ov_skirt | sfx_pa_chime, амбиент:amb_lobby | pos=lobby |
| drive | SEQ.drive.4_crowd | rooms/room_w2_under+st_w2u_crowd+ov_skirt |  | +trolley_at_crowd, +plate_revealed, pos=crowd, вид:W2u |
| drive_again | SEQ.drive.again | rooms/room_w2_under+st_w2u_crowd+ov_skirt |  | pos=crowd, вид:W2u |
| shout | SEQ.shout.1 | rooms/room_w2_under+st_w2u_crowd+ov_skirt | sfx_crowd_part |  |
| shout | SEQ.shout.2 | rooms/room_w2_under+st_w2u_parted+ov_skirt |  |  |
| shout | SEQ.shout.3 | rooms/room_w2_under+st_w2u_parted+ov_skirt |  |  |
| shout | SEQ.shout.4 | rooms/room_w2_under+st_w2u_parted+ov_skirt |  | +iz_rule3_seen |
| shout | SEQ.shout.5 | rooms/room_w2_under+st_w2u_parted+st_w2u_gate_open+ov_skirt;frames/fr_a1_under_service+ov_skirt |  | +trolley_service_side, pos=service, вид:W2s, цепочка:talk_open |

## Меню

Подпись пункта — строка `choice` слота из колонки «Подпись» или ключ `texts/ui/UI_TEXTS.md`. Правила одного пункта — сверху вниз.

| Меню | Пункт | Подпись | Условие | Слот | Граф | Эффекты |
|---|---|---|---|---|---|---|
| crowd | pass | CHOICE.pass | ¬shown(CHOICE.pass) | CHOICE.pass | — |  |
| crowd | pass | CHOICE.pass | shown(CHOICE.pass) | CHOICE.pass.again | — |  |
| crowd | wait | CHOICE.wait |  | CHOICE.wait | — |  |
| crowd | guest | CHOICE.guest |  | CHOICE.guest | — |  |
| crowd | shout | choice_shout | knows_waiter_call | — | A09_shout_hot | сцена:shout |
| talk | clothes | TALK.iz.clothes | ¬shown(TALK.iz.clothes) | TALK.iz.clothes | A10_talk_isolde | меню:talk |
| talk | clothes | TALK.iz.clothes | shown(TALK.iz.clothes) | TALK.iz.again | — | меню:talk |
| talk | guest | TALK.iz.guest | ¬shown(TALK.iz.guest) | TALK.iz.guest | A10_talk_isolde | меню:talk |
| talk | guest | TALK.iz.guest | shown(TALK.iz.guest) | TALK.iz.again | — | меню:talk |
| talk | repair | TALK.iz.repair | ¬shown(TALK.iz.repair) | TALK.iz.repair | A10_talk_isolde | меню:talk |
| talk | repair | TALK.iz.repair | shown(TALK.iz.repair) | TALK.iz.again | — | меню:talk |
| talk | exit | TALK.iz.exit |  | TALK.iz.exit | A10_talk_isolde | +iz_rules_all_shown, +w3_open, +w4_open, цепочка:act_end |

## Подсказки

Порядок строк — приоритет тем (SLOT_FLAGS, Акт I: по кратчайшему пути A11 → N01 → A10; `skirt` — последней).

| Тема | Открыта, когда |
|---|---|
| plunger | plunger_on_panel |
| foam | foam_active ∧ ¬foam_class_closed |
| call | ¬reception_called |
| stars | ¬stars_folded |
| peek | ¬need_cover |
| drive | stars_folded ∧ need_cover ∧ reception_called ∧ knows_bath_day ∧ foam_class_closed ∧ knows_foam_flow ∧ ¬trolley_at_crowd |
| crowd | trolley_at_crowd ∧ ¬trolley_service_side |
| skirt | ¬knows_trolley_chamber ∧ ¬trolley_at_crowd |

## Предметы

| Предмет | Иконка | При себе, когда | Осмотр | Эффекты осмотра | Мимо (неплоское) | Мимо (плоское) |
|---|---|---|---|---|---|---|
| plunger | icons/ic_plunger | plunger_taken | INV.plunger.look |  | FB.plunger.1 | FB.plunger.2 |
| menu | icons/ic_menu | has_menu_card | INV.menu.look | док:DOC.menu | @fb_menu | @fb_menu |

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
| DOC.voucher | docs/paper_union | reception_called → DOC.voucher.soaked |
| DOC.menu | docs/paper_laminated |  |
| DOC.pictograms | docs/panel_pictograms |  |
| DOC.bathday | docs/paper_hotel |  |
| DOC.plate | docs/plate_brass |  |

## Прочее

| Слот | Где звучит |
|---|---|
| UI.inventory | подпись кнопки «При себе» |
| HINT.intro | первое нажатие «Совет предка» |
| HINT.cooldown | совет уже дан, после него не было действия |
| HINT.done | открытых тем нет |
