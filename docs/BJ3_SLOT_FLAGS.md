# Слоты текстов → флаги графов

**Что это.** Условие «Когда» каждого слота текстов (ТЗ актов, §9) записано флагами графов `acts/act*/ACT*_graph.json`, а не прозой. Это ответ на находку ревью R-11 (решение автора 06.10.2026). Источник условий — ТЗ актов, графы и сдачи; при расхождении побеждает граф.

**Как читать.** Строка таблицы: слот → условие показа → действие графа, которое слот озвучивает (или «—», если слот не меняет состояние) → что слот ставит (флаги графа, счётчики из §0). Проверка: `python tools/texts/check_slot_flags.py` сверяет, что каждый слот ТЗ есть в таблице ровно один раз, а каждый флаг и действие существуют в графе акта или в §0.

**Обозначения.** `∧` — и, `∨` — или, `¬` — не. `room:W1` — игрок на экране W1; `zoom:Z03` — открыт зум Z03. `shown(SLOT)` — слот уже звучал; `n(SLOT)` — сколько раз. Слоты одной группы с номерами (`.1`, `.2`, `.3`) выбираются счётчиком показов группы. Переходы в документ записаны как `→ DOC.x`. Слоты кадров одной последовательности (`SEQ.*`) идут подряд без условий между ними.

## 0. Флаги и счётчики вне графов (движок и тексты)

Графы фиксируют смыслы; показ реплик требует ещё немного состояния. Эти имена не входят в `flags_glossary` и не участвуют в солвере; их хранит движок, они переживают сохранение (handoff §13).

| Имя | Что это | Где меняется |
|---|---|---|
| `room`, `zoom` | текущий экран и открытый зум | навигация |
| `n(SLOT)` | счётчик показов слота; `shown(SLOT)` = `n(SLOT) > 0` | при каждом показе |
| `hint.lock` | совет Предка только что дан; снимается любым действием игрока, которое меняет флаг графа или открывает новый слот. Таймера нет (DESIGN_BIBLE §16 п. 10, решение автора 06.10.2026) | кнопка «Совет предка» / любое действие |
| `hint.level(тема)` | ступень подсказки по теме, 0–3; каждое нажатие при открытой теме даёт ступень `level+1` и поднимает счётчик; на ступени 3 повторяется третья | кнопка «Совет предка» |
| `hint.n` | сколько раз нажата кнопка за игру (для `HINT.intro`) | кнопка |
| приоритет тем | когда открыто несколько тем, первой идёт тема, чьё обязательное действие стоит раньше на кратчайшем пути солвера (решение автора 06.10.2026); порядок указан в начале каждого акта | — |
| `probe.n` | число повторных проб жидкостью после закрытия класса (`PROBE.repeat.*`) | пробы |
| `call.n` | число звонков на стойку после первого | телефон |
| `trolley.pos` | положение тележки: `room`, `door`, `lift`, `lobby`, `crowd`, `service`, `exhibit`, `stairs`, `hall`, `cabin`, `receiving`, `office` | кадры `SEQ.*` |
| `combo(a, b)` | попытка применить предмет `a` к объекту `b`; для фидбеков `FB.*` — любое сочетание, не описанное отдельным слотом | инвентарь |
| `relics` | число найденных реликвий = `relic_r1 + relic_r2 + relic_r3` (0–3); выбирает эпилог | граф |
| `menu:` | пункт меню выбран в слоте выбора (`CHOICE.*`, `TALK.*`) | меню |

## Акт I «Комплимент от заведения»

Граф: `acts/act1/ACT1_graph.json`, 18 действий, старт — `shock_done`, `foam_active`, `voucher_read`, `plunger_on_panel`, `trolley_present`, `breakfast_on_trolley`, `bathday_done`, `iz_formal`.

Приоритет тем Предка (по кратчайшему пути A01 → A10): `plunger` → `foam` → `call` → `skirt` → `stars` → `peek` → `drive` → `crowd`.

| Слот | Когда (флагами) | Действие графа | Ставит |
|---|---|---|---|
| `OPEN.1_voucher` | старт игры, до `voucher_read` | — (виньетка) | `voucher_read` |
| `OPEN.2_shower` | после `OPEN.1_voucher`, до `shock_done` | — | `foam_active` |
| `OPEN.3_shock` | после `OPEN.2_shower` | — | `shock_done` |
| `OPEN.4_after` | сразу после `OPEN.3_shock`; управление переходит к игроку | — | — |
| `OPEN.5_anc` | один раз после `OPEN.4_after` (по желанию реализации; если не показан — Предок представится в `HINT.intro`) | — | — |
| `W1.hooks` | `room:W1`, крючки | A12_inspect_room (часть) | `room_bare_seen` |
| `W1.bed` | `room:W1`, кровать | A12_inspect_room (часть) | `room_bare_seen` |
| `W1.window` | `room:W1`, окно | A12_inspect_room (часть) | `room_bare_seen` |
| `W1.suitcase` | `room:W1`, чемодан | A12_inspect_room (часть) | `room_bare_seen` |
| `W1.bucket` | `room:W1`, ведро | A12_inspect_room (часть) | `room_bare_seen` |
| `W1.door.look` | `room:W1`, дверь | A12_inspect_room (часть) → `DOC.bathday` | `room_bare_seen`, `knows_bath_day` |
| `W1.door.again` | `room:W1`, выйти без тележки ∧ `need_cover` | — | — |
| `W1.cistern.look` | `room:W1`, бачок в санузле | — | — |
| `Z01.head.look` | `zoom:Z01` | — | — |
| `Z01.head.use` | `zoom:Z01` ∧ ¬`shown(Z01.head.use)` | — (D1) | — |
| `Z01.head.use.repeat` | `zoom:Z01` ∧ `shown(Z01.head.use)` | — | — |
| `Z01.dispenser.look` | `zoom:Z01` ∧ `plunger_on_panel` | — | — |
| `Z01.dispenser.look.full` | `zoom:Z01` ∧ `plunger_taken` | — → `DOC.pictograms` | — |
| `Z01.dispenser.use` | `zoom:Z01` | — | — |
| `Z01.plunger.look` | `zoom:Z01` ∧ `plunger_on_panel` | — | — |
| `Z01.plunger.take` | `zoom:Z01` ∧ `plunger_on_panel` ∧ ¬`foam_class_closed` | A01_take_plunger | `plunger_taken`, `wet_ring_seen`, `knows_foam_flow`; снимает `plunger_on_panel` |
| `Z01.plunger.take.after` | `zoom:Z01` ∧ `plunger_on_panel` ∧ `foam_class_closed` | A01_take_plunger | то же |
| `Z01.ring.look` | `zoom:Z01` ∧ `wet_ring_seen` | — | — |
| `Z02.voucher.look` | `zoom:Z02` ∧ ¬`reception_called` | — → `DOC.voucher` | — |
| `Z02.voucher.look.soaked` | `zoom:Z02` ∧ `reception_called` | — → `DOC.voucher`, титр `DOC.voucher.soaked` | — |
| `Z02.voucher.take` | `zoom:Z02` | — | — |
| `Z02.phone.look` | `zoom:Z02` | — | — |
| `Z02.phone.call` | `zoom:Z02` ∧ `voucher_read` ∧ ¬`reception_called` | A03_call_reception | `reception_called`, `knows_paper_soaks` |
| `Z02.phone.call.repeat` | `zoom:Z02` ∧ `reception_called` | — | `call.n` + 1 |
| `Z02.minibar.look` | `zoom:Z02` | — | — |
| `Z02.mineral.look` | `zoom:Z02` | — | — |
| `Z02.kombucha.look` | `zoom:Z02` | — | — |
| `Z02.lemonade.look` | `zoom:Z02` | — | — |
| `Z02.bottle.take` | `zoom:Z02`, взять бутылку ∧ ¬`shown(Z02.bottle.take)` | — (D5) | — |
| `Z02.bottle.take.repeat` | `zoom:Z02`, взять бутылку ∧ `shown(Z02.bottle.take)` | — | — |
| `Z02.plunger_bottle` | `zoom:Z02` ∧ `plunger_taken` ∧ `combo(вантуз, бутылка)` | — (D7) | — |
| `Z02.menu.look` | `zoom:Z02` ∧ ¬`has_menu_card` | — | — |
| `Z02.menu.take` | `zoom:Z02` ∧ ¬`has_menu_card` | A11_take_menu_card → `DOC.menu` | `has_menu_card`, `knows_assortment` |
| `PROBE.mineral` | `zoom:Z02` ∧ `foam_active` ∧ ¬`foam_class_closed` | A02_probe_mineral | `foam_class_closed`, `foam_swollen`, `knows_soap_grip` |
| `PROBE.kombucha` | `zoom:Z02` ∧ `foam_active` ∧ ¬`foam_class_closed` | A02b_probe_kombucha | то же |
| `PROBE.lemonade` | `zoom:Z02` ∧ `foam_active` ∧ ¬`foam_class_closed` | A02c_probe_lemonade | то же |
| `PROBE.juice` | `zoom:Z03` ∧ `breakfast_on_trolley` ∧ ¬`foam_class_closed` | A02d_probe_juice | то же |
| `PROBE.coffee` | `zoom:Z03` ∧ `breakfast_on_trolley` ∧ ¬`foam_class_closed` | A02e_probe_coffee | то же + `knows_hot_warning` |
| `PROBE.cistern` | `room:W1`, бачок ∧ ¬`foam_class_closed` | A02f_probe_cistern | то же |
| `PROBE.rule.known` | сразу после первой пробы ∧ `knows_foam_flow` | — | — |
| `PROBE.rule.unknown` | сразу после первой пробы ∧ ¬`knows_foam_flow` | — | — |
| `PROBE.repeat.1` | любая проба ∧ `foam_class_closed` ∧ `probe.n` = 0 | — (D3) | `probe.n` + 1 |
| `PROBE.repeat.2` | любая проба ∧ `foam_class_closed` ∧ `probe.n` = 1 | — | `probe.n` + 1 |
| `PROBE.repeat.3` | любая проба ∧ `foam_class_closed` ∧ `probe.n` ≥ 2 | — | `probe.n` + 1 |
| `Z03.trolley.look` | `zoom:Z03` ∧ ¬`stars_folded` | — | — |
| `Z03.trolley.look.work` | `zoom:Z03` ∧ `stars_folded` | — | — |
| `Z03.trolley.push` | `room:W1`, толкнуть к двери ∧ ¬`stars_folded` | — (D17) | — |
| `Z03.trolley.push.folded` | `room:W1`, толкнуть к двери ∧ `stars_folded` ∧ Лапидус не под тележкой | — | — |
| `Z03.stars.look` | `zoom:Z03` ∧ ¬`knows_stars_fold` | A05_inspect_stars | `knows_stars_fold`, `minus_four_stars_said` |
| `Z03.stars.look.again` | `zoom:Z03` ∧ `knows_stars_fold` ∧ ¬`stars_folded` | — | — |
| `Z03.stars.look.folded` | `zoom:Z03` ∧ `stars_folded` | — | — |
| `Z03.stars.pull` | `zoom:Z03` ∧ ¬`knows_stars_fold`, отломать | — (D18) | — |
| `Z03.stars.fold` | `zoom:Z03` ∧ `knows_stars_fold` ∧ ¬`stars_folded` | A06_fold_stars | `stars_folded`, `plate_revealed` |
| `Z03.plate.look` | `zoom:Z03` ∧ `plate_revealed` | — → `DOC.plate` | — |
| `Z03.skirt.look` | `zoom:Z03` ∧ ¬`knows_trolley_chamber` | — | — |
| `Z03.skirt.use` | `zoom:Z03` ∧ ¬`knows_trolley_chamber` | A04_try_skirt | `knows_trolley_chamber` |
| `Z03.skirt.use.again` | `zoom:Z03` ∧ `knows_trolley_chamber`, снять юбку | — | — |
| `Z03.skirt.look.after` | `zoom:Z03` ∧ `knows_trolley_chamber` | — | — |
| `Z03.pot.look` | `zoom:Z03` ∧ `breakfast_on_trolley` | A13_inspect_breakfast | `knows_hot_warning` |
| `Z03.cup.look` | `zoom:Z03` ∧ `breakfast_on_trolley` | — | — |
| `Z03.juice.look` | `zoom:Z03` ∧ `breakfast_on_trolley` | — | — |
| `Z03.cloche.look` | `zoom:Z03` ∧ `breakfast_on_trolley` | — | — |
| `Z03.cloche.use` | `zoom:Z03` ∧ `breakfast_on_trolley`, прикрыться | — (D16) | — |
| `Z03.napkin.look` | `zoom:Z03` ∧ `breakfast_on_trolley` | — | — |
| `Z03.napkin.use` | `zoom:Z03`, взять салфетку ∨ `combo(салфетка, пена)` | — (D8) | — |
| `Z03.porcelain.take` | `zoom:Z03`, взять кофейник или чашку | — (D5) | — |
| `Z03.under.no_peek` | залезть под тележку ∧ `knows_trolley_chamber` ∧ ¬`need_cover` | — (D21) | — |
| `Z03.under.no_wash` | залезть под тележку ∧ `need_cover` ∧ ¬`foam_class_closed` | — (D21) | — |
| `Z03.under.no_flow` | залезть под тележку ∧ `foam_class_closed` ∧ ¬`knows_foam_flow` | — | — |
| `Z03.under.no_call` | залезть под тележку ∧ `knows_foam_flow` ∧ ¬`reception_called` | — (D21) | — |
| `Z03.under.stars` | залезть под тележку ∧ остальные условия A08 ∧ ¬`stars_folded` (проверки идут в этом порядке: no_peek, no_wash, no_flow, no_call, stars) | — (D17) | — |
| `SEQ.peek.1_corridor` | выйти из W1 без тележки ∧ ¬`need_cover` ∧ `shock_done` — кадр 1 | A07_peek_lobby | — |
| `SEQ.peek.2_lift` | A07, кадр 2 | A07_peek_lobby | — |
| `SEQ.peek.3_lobby` | A07, кадр 3 | A07_peek_lobby | `crowd_seen`, `cascade_dry_seen`, `poster_seen`, `knows_bath_day`, `iz_folder_seen` |
| `SEQ.peek.4_waiter` | A07, кадр 4 | A07_peek_lobby | `knows_waiter_call` |
| `SEQ.peek.5_back` | A07, кадр 5 | A07_peek_lobby | `need_cover` |
| `SEQ.drive.1_under` | залезть под тележку ∧ все requires A08 (`stars_folded`, `knows_trolley_chamber`, `need_cover`, `reception_called`, `knows_bath_day`, `foam_class_closed`, `knows_foam_flow`) — кадр 0 | A08_drive_out | `trolley.pos` = `door` |
| `SEQ.drive.2_lift` | A08, кадр 1 | A08_drive_out | `trolley.pos` = `lift` |
| `SEQ.drive.3_lobby` | A08, кадр 2 | A08_drive_out | `trolley.pos` = `lobby` |
| `SEQ.drive.4_crowd` | A08, кадр 3 | A08_drive_out | `trolley_at_crowd`; `trolley.pos` = `crowd` |
| `SEQ.drive.again` | выезд из W1 под тележкой ∧ `trolley_at_crowd` (после возврата `W2.lift.use`) | — (AS11, H24) | `trolley.pos` = `crowd` |
| `W2.crowd.look` | `room:W2` ∧ `trolley_at_crowd` ∧ ¬`trolley_service_side` | — | — |
| `W2.crowd.push` | `room:W2` ∧ `trolley_at_crowd` ∧ ¬`trolley_service_side` ∧ ¬`shown(W2.crowd.push)` | — (D22) | — |
| `W2.crowd.push.again` | то же ∧ `shown(W2.crowd.push)` | — | — |
| `W2.board.look` | `room:W2` ∧ `trolley_at_crowd` ∧ ¬`trolley_service_side` | — | — |
| `W2.isolde.look` | `room:W2` ∧ `trolley_at_crowd` ∧ ¬`trolley_service_side` | — | — |
| `W2.poster.look` | `room:W2` | — → `DOC.bathday` | `poster_seen`, `knows_bath_day` |
| `W2.cascade.look` | `room:W2` | — | `cascade_dry_seen` |
| `W2.lift.use` | `room:W2` ∧ `trolley_at_crowd` ∧ ¬`trolley_service_side` | — | `trolley.pos` = `room` |
| `W2.getout.use` | `room:W2` ∧ ¬`trolley_service_side`, вылезти | — (D26) | — |
| `CHOICE.pass` | `menu:` у толпы ∧ `trolley_at_crowd` ∧ ¬`trolley_service_side` ∧ ¬`shown(CHOICE.pass)` | — (D23) | — |
| `CHOICE.pass.again` | то же ∧ `shown(CHOICE.pass)` | — | — |
| `CHOICE.wait` | `menu:` у толпы ∧ `trolley_at_crowd` ∧ ¬`trolley_service_side` | — (D24) | — |
| `CHOICE.guest` | `menu:` у толпы ∧ `trolley_at_crowd` ∧ ¬`trolley_service_side` | — (D25) | — |
| `SEQ.shout.1` | `menu:` крикнуть ∧ `trolley_at_crowd` ∧ `knows_waiter_call` — кадр 1 | A09_shout_hot | — |
| `SEQ.shout.2` | A09, кадр 2 | A09_shout_hot | — |
| `SEQ.shout.3` | A09, кадр 3 | A09_shout_hot | — |
| `SEQ.shout.4` | A09, кадр 4 | A09_shout_hot | `iz_rule3_seen` |
| `SEQ.shout.5` | A09, кадр 5 | A09_shout_hot | `trolley_service_side`; `trolley.pos` = `service` |
| `TALK.iz.open` | `trolley_service_side` ∧ `iz_formal` ∧ `iz_rule3_seen` ∧ `iz_folder_seen`, заговорить ∧ ¬`shock_report_known` | A10_talk_isolde (вход) | `shock_report_known` |
| `TALK.iz.clothes` | в разговоре A10, `menu:` одежда ∧ ¬`shown(TALK.iz.clothes)` | A10_talk_isolde | — |
| `TALK.iz.guest` | в разговоре A10, `menu:` «я гость» ∧ ¬`shown(TALK.iz.guest)` | A10_talk_isolde | — |
| `TALK.iz.repair` | в разговоре A10, `menu:` аварийная служба ∧ ¬`shown(TALK.iz.repair)` | A10_talk_isolde | — |
| `TALK.iz.exit` | в разговоре A10, `menu:` закончить | A10_talk_isolde (выход) | `iz_rules_all_shown`, `w3_open`, `w4_open` |
| `TALK.iz.again` | в разговоре A10, повтор темы с `shown(...)` | — | — |
| `END.act1` | после `TALK.iz.exit` (цель акта: `trolley_service_side`, `shock_report_known`, `iz_rules_all_shown`, `w3_open`, `w4_open`) | — | конец акта |
| `HINT.intro` | кнопка совета ∧ `hint.n` = 0 | — | `hint.n` = 1 |
| `HINT.cooldown` | кнопка совета ∧ `hint.lock` | — | — |
| `HINT.done` | кнопка совета ∧ открытых тем нет (цель акта достигнута) | — | — |
| `HINT.foam.1` | тема `foam` открыта: `foam_active` ∧ ¬`foam_class_closed`; `hint.level(foam)` = 0 | — | `hint.level(foam)` = 1, `hint.lock` |
| `HINT.foam.2` | тема `foam`; `hint.level(foam)` = 1 | — | `hint.level(foam)` = 2, `hint.lock` |
| `HINT.foam.3` | тема `foam`; `hint.level(foam)` ≥ 2 | — | `hint.level(foam)` = 3, `hint.lock` |
| `HINT.plunger.1` | тема `plunger`: `plunger_on_panel`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.plunger.2` | тема `plunger`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.plunger.3` | тема `plunger`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.call.1` | тема `call`: ¬`reception_called`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.call.2` | тема `call`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.call.3` | тема `call`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.peek.1` | тема `peek`: ¬`need_cover`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.peek.2` | тема `peek`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.peek.3` | тема `peek`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.skirt.1` | тема `skirt`: ¬`knows_trolley_chamber`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.skirt.2` | тема `skirt`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.skirt.3` | тема `skirt`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.stars.1` | тема `stars`: `knows_trolley_chamber` ∧ ¬`stars_folded`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.stars.2` | тема `stars`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.stars.3` | тема `stars`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.drive.1` | тема `drive`: все requires A08 ∧ ¬`trolley_at_crowd`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.drive.2` | тема `drive`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.drive.3` | тема `drive`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.crowd.1` | тема `crowd`: `trolley_at_crowd` ∧ ¬`trolley_service_side`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.crowd.2` | тема `crowd`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.crowd.3` | тема `crowd`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `DOC.voucher` | открыт из `Z02.voucher.look` / `Z02.voucher.look.soaked` | — | — |
| `DOC.voucher.soaked` | титр при открытии `DOC.voucher` ∧ `reception_called` | — | — |
| `DOC.menu` | открыт из `Z02.menu.take` / `INV.menu.look` | — | — |
| `DOC.pictograms` | открыт из `Z01.dispenser.look.full` | — | — |
| `DOC.bathday` | открыт из `W1.door.look` / `W2.poster.look` | — | — |
| `DOC.plate` | открыт из `Z03.plate.look` | — | — |
| `INV.plunger.look` | осмотр предмета в руках ∧ `plunger_taken` | — | — |
| `INV.menu.look` | осмотр предмета в руках ∧ `has_menu_card` | — → `DOC.menu` | — |
| `FB.plunger.1` | `combo(вантуз, не плоское)` без своего слота | — | — |
| `FB.plunger.2` | `combo(вантуз, плоское, но незачем)` без своего слота | — | — |
| `FB.menu.1` | `combo(меню, …)` без своего слота ∧ ¬`shown(FB.menu.1)` | — | — |
| `FB.menu.2` | `combo(меню, …)` без своего слота ∧ `shown(FB.menu.1)` | — | — |
| `FB.generic.1` | прочее `combo(a, b)` без своего слота: не тот материал или форма | — | — |
| `FB.generic.2` | прочее `combo(a, b)`: не тот адресат | — | — |
| `FB.generic.3` | прочее `combo(a, b)`: незачем | — | — |
| `UI.inventory` | всегда: подпись кнопки предметов в руках | — | — |

## Акт II «Старший по воде»

Граф: `acts/act2/ACT2_graph.json`, 23 действия, старт — 34 гарантированных флага финала Акта I (тележка за стойкой, `trolley_service_side`).

Приоритет тем Предка (по кратчайшему пути B01 → B15): `check` → `cause` → `map` → `align` → `journal` → `vitrine` → `seal` → `paint` → `witness` → `down`.

| Слот | Когда (флагами) | Действие графа | Ставит |
|---|---|---|---|
| `OPEN.counter` | старт акта: `trolley_service_side` (финал Акта I), кадр 1 | — | `trolley.pos` = `service` |
| `OPEN.requests` | старт акта, кадр 2: нормальный цикл P04 | — | — |
| `OPEN.pa` | старт акта, кадр 3 | — | — |
| `OPEN.anc` | один раз после `OPEN.pa` (по желанию реализации) | — | — |
| `Z04.look` | `zoom:Z04` | — | — |
| `Z04.pump.look` | `zoom:Z04` | — | — |
| `Z04.pump.use` | `zoom:Z04` ∧ `trolley_service_side` ∧ `cascade_dry_seen` ∧ ¬`cascade_pump_dry` | B01_pump_cascade | `cascade_pump_dry` |
| `Z04.pump.use.repeat` | `zoom:Z04` ∧ `cascade_pump_dry` | — (D1) | — |
| `Z04.folder.look` | `zoom:Z04` ∧ ¬`counter_notice_read` | — | — |
| `Z04.folder.take` | `zoom:Z04` ∧ ¬`counter_notice_read`, поднять папку | — (D27) | — |
| `Z04.map.look` | `zoom:Z04` ∧ ¬`has_hotel_map` | — | — |
| `Z04.map.take` | `zoom:Z04` ∧ ¬`has_hotel_map` | B04_take_hotel_map → `DOC.map_hotel` | `has_hotel_map` |
| `Z04.regulation.look` | `zoom:Z04` | B22_read_regulation → `DOC.regulation` | `regulation_cut_seen` |
| `Z04.regulation.take` | `zoom:Z04`, снять регламент | — (D24) | — |
| `Z04.drawer.look` | `zoom:Z04` ∧ ¬`knows_push_latch` | — | — |
| `Z04.drawer.open` | `zoom:Z04` ∧ `knows_push_latch`, ящик Изольды | — (D29) | — |
| `Z04.kefir.take` | `zoom:Z04` ∧ `kefir_in_drawer_seen`, взять кефир | — (D29) | — |
| `Z04.lowdrawer.open` | `zoom:Z04` ∧ `knows_push_latch` ∧ ¬`relic_r3` | R3_mug | `relic_r3` |
| `Z04.lowdrawer.again` | `zoom:Z04` ∧ `relic_r3` | — | — |
| `TALK.req.early` | заговорить о причине ∧ ¬(`cascade_pump_dry` ∧ `drums_same_time`) | — | — |
| `TALK.req.open` | заговорить о причине ∧ `cascade_pump_dry` ∧ `drums_same_time` ∧ `iz_formal` ∧ ¬`knows_supply_cut` | B03_merge_requests (вход) | — |
| `CHOICE.cause.three` | в B03, `menu:` «три поломки» | B03_merge_requests (D6) | — |
| `CHOICE.cause.empty` | в B03, `menu:` «вода кончилась» | B03_merge_requests (D7) | — |
| `CHOICE.cause.cut` | в B03, `menu:` «перекрыли на общей линии» | B03_merge_requests (выход) | `knows_supply_cut`, `requests_stapled`, `knows_push_latch`, `kefir_in_drawer_seen`, `knows_iz_stamp_mp` |
| `TALK.req.again` | заговорить о причине ∧ `knows_supply_cut` | — | — |
| `W3.enter` | `room:W3` ∧ `w3_open` ∧ ¬`shown(W3.enter)` | — | — |
| `W3.brand.look` | `room:W3`, табличка | — | — |
| `Z06.drums.look` | `zoom:Z06` ∧ `knows_bath_day` ∧ ¬`drums_same_time` | B02_inspect_drums | `drums_same_time`, `clothes_locked_seen` |
| `Z06.drum.restart` | `zoom:Z06`, запустить барабан | — (D2) | — |
| `Z06.hatch.open` | `zoom:Z06`, открыть люк ∧ ¬`shown(Z06.hatch.open)` | — (D3) | `clothes_locked_seen` |
| `Z06.hatch.open.repeat` | `zoom:Z06`, открыть люк ∧ `shown(Z06.hatch.open)` | — | — |
| `Z06.tank.probe` | `zoom:Z06`, облить голову из бака | — (D4) | `probe.n` + 1 |
| `Z07.cladding.look` | `zoom:Z07` ∧ `w3_open` | B24_inspect_cladding | `cladding_seen` |
| `Z07.cladding.use` | `zoom:Z07`, открыть панель | — | — |
| `Z08.cabinet.look` | `zoom:Z08` | — | — |
| `Z08.cabinet.open` | `zoom:Z08` ∧ ¬`relic_r2` | R2_postcard → `DOC.postcard` | `relic_r2` |
| `Z08.cabinet.again` | `zoom:Z08` ∧ `relic_r2` | — | — |
| `W4.enter` | `room:W4` ∧ `w4_open` ∧ ¬`shown(W4.enter)` | — | — |
| `W4.hatch.look` | `room:W4`, люк под стеклом | — | — |
| `W4.stairs.look` | `room:W4`, дверь «Служебное помещение» ∧ ¬`stairs_open` | — | — |
| `W4.stairs.locked` | `room:W4`, открыть дверь ∧ ¬`has_stairs_key` | — (D30) | — |
| `Z09.board.look` | `zoom:Z09` ∧ ¬`knows_plate_under_paint` | B11_inspect_board → `DOC.paint_act` | `knows_plate_under_paint`, `knows_paint_fresh`, `paint_act_read` |
| `Z09.paint.rub` | `zoom:Z09` ∧ `knows_plate_under_paint` ∧ ¬`name_revealed`, тереть пальцами | — (D20) | — |
| `Z09.paint.plunger` | `zoom:Z09` ∧ ¬`name_revealed` ∧ `combo(вантуз, краска)` | — (D22) | — |
| `Z09.paint.token` | `zoom:Z09` ∧ `relic_r1` ∧ ¬`name_revealed` ∧ `combo(жетон, краска)` | — (D23) | — |
| `Z09.paint.scrape` | `zoom:Z09` ∧ `has_menu_card` ∧ `knows_plate_under_paint` ∧ `knows_paint_fresh` ∧ `knows_paper_soaks` ∧ `combo(меню, краска)` | B12_scrape_plate → `DOC.plate_k` | `name_revealed`, `menu_smeared` |
| `Z09.plate.look` | `zoom:Z09` ∧ `name_revealed` | — → `DOC.plate_k` | — |
| `Z09.slot.look` | `zoom:Z09` | — | — |
| `Z09.slot.use` | `zoom:Z09` ∧ ¬`relic_r1` | R1_token → `DOC.token` | `relic_r1` |
| `Z10.table.look` | `zoom:Z10` | — | — |
| `Z10.paper.take` | `zoom:Z10`, унести бумагу | — (FB.paper) | — |
| `Z10.journal.read` | `zoom:Z10` ∧ ¬`journal_old_read` | B07_read_old_journal → `DOC.journal` | `journal_old_read` |
| `Z10.layoff.read` | `zoom:Z10` ∧ ¬`layoff_read` | B13_read_layoff → `DOC.layoff` | `layoff_read` |
| `Z10.memo.read` | `zoom:Z10` | B21_read_soviet_memo → `DOC.memo` | `memo_soviet_read` |
| `Z10.tube.open` | `zoom:Z10` ∧ ¬`shown(Z10.tube.open)` | — → `DOC.map_1908`, `DOC.photo` | `photo_seen` (в графе этот флаг ставит B05; движок ставит его при первом из двух) |
| `Z10.folder.open` | `zoom:Z10` | — → `DOC.map_soviet` | — |
| `Z10.films.lay` | `zoom:Z10` ∧ `w4_open` ∧ `has_hotel_map` ∧ ¬`overlay_by_frame` | B05_lay_films | `overlay_by_frame`, `knows_map_lies`, `photo_seen` |
| `Z10.films.dome` | `zoom:Z10` ∧ `overlay_by_frame` ∧ ¬`topology_known`, метка «купол» | — (D11) | — |
| `Z10.films.labels` | `zoom:Z10` ∧ `overlay_by_frame` ∧ ¬`topology_known`, метка «подписи» | — (D10) | — |
| `Z10.films.facade` | `zoom:Z10` ∧ `overlay_by_frame` ∧ ¬`topology_known`, метка «фасад» | — (D11) | — |
| `Z10.films.align` | `zoom:Z10` ∧ `overlay_by_frame` ∧ `knows_map_lies`, метки «источник» и «номер 317» | B06_align_source | `topology_known`, `knows_receiving_point`, `knows_office_by_source`, `knows_counter_on_line`, `knows_service_stairs` |
| `Z10.films.look` | `zoom:Z10` ∧ `topology_known` | — | — |
| `Z10.films.elsewhere` | `has_hotel_map` ∧ `combo(плёнка, стол или другая комната)` | — (D12) | — |
| `Z11.mirror.look` | `zoom:Z11` ∧ `w4_open` | B23_inspect_mirror | `mirror_seen` |
| `Z11.mirror.use` | `zoom:Z11`, снять или сдвинуть | — | — |
| `W2.exhibit.look` | `room:W2` ∧ `trolley_service_side` | — → `DOC.exhibit` | — |
| `SEQ.exhibit.go` | `room:W2` ∧ `trolley_service_side` ∧ `knows_trolley_chamber`, к экспонату под тележкой | — (BS13, H24) | `trolley.pos` = `exhibit` |
| `SEQ.exhibit.nocover` | `room:W2`, к экспонату без тележки | — (D17) | — |
| `Z05.vitrine.look` | `zoom:Z05` ∧ `trolley.pos` = `exhibit` ∧ ¬`vitrine_open` | — | — |
| `Z05.vitrine.pry` | `zoom:Z05` ∧ ¬`vitrine_open`, поддеть пальцами | — (D14) | — |
| `Z05.vitrine.plunger` | `zoom:Z05` ∧ ¬`vitrine_open` ∧ `combo(вантуз, дверца)` | — (D15) | — |
| `Z05.vitrine.smash` | `zoom:Z05` ∧ ¬`vitrine_open`, разбить | — (D16) | — |
| `Z05.vitrine.push` | `zoom:Z05` ∧ `knows_push_latch` ∧ ¬`vitrine_open`, нажать | B08_open_vitrine | `vitrine_open`, `meter_seal_seen` |
| `Z05.meter.look` | `zoom:Z05` ∧ `vitrine_open` | — | — |
| `Z05.seal.wipe` | `zoom:Z05` ∧ `vitrine_open`, стереть | — (D18) | — |
| `Z05.seal.plunger.early` | `zoom:Z05` ∧ `vitrine_open` ∧ `plunger_taken` ∧ ¬`journal_old_read` ∧ `combo(вантуз, пломба)` | — (D19) | — |
| `Z05.seal.plunger` | `zoom:Z05` ∧ `vitrine_open` ∧ `plunger_taken` ∧ `wet_ring_seen` ∧ `journal_old_read` ∧ `combo(вантуз, пломба)` | B09_compare_plunger | `seal_is_mark` |
| `SEQ.exhibit.back` | `room:W2` ∧ `trolley.pos` = `exhibit`, за стойку | — | `trolley.pos` = `service` |
| `TALK.iz.open` | заговорить с Изольдой (не о причине) ∧ `iz_formal` ∧ ¬`iz_admits_facts` | — | — |
| `TALK.iz.vitrine` | `menu:` ключ от витрины | — (D13) | — |
| `TALK.iz.stairs` | `menu:` ключ от лестницы ∧ ¬`has_stairs_key` | — (D28) | — |
| `TALK.iz.seal` | `menu:` пломба ∧ `meter_seal_seen` | — (D18) | — |
| `TALK.iz.plate` | `menu:` табличка ∧ `name_revealed` | — (D26) | — |
| `TALK.iz.signature` | `menu:` подпись ∧ `paint_act_read` ∧ `iz_formal` ∧ ¬`shown(TALK.iz.signature)` | B20_accuse_signature (D25) | `iz_defends_seen` |
| `TALK.iz.signature.again` | `menu:` подпись ∧ `shown(TALK.iz.signature)` | — | — |
| `TALK.iz.kefir` | `menu:` кефир ∧ `kefir_in_drawer_seen` | — (D29) | — |
| `TALK.iz.model.early` | `menu:` «изложить всё» ∧ не все requires B14 | — | — |
| `TALK.iz.layoff` | `menu:` «сантехника сократили, дело не передали» ∧ `knows_supply_cut` ∧ `topology_known` ∧ `photo_seen` ∧ `seal_is_mark` ∧ `name_revealed` ∧ `paint_act_read` ∧ `layoff_read` ∧ `trolley_service_side` ∧ `iz_formal` | B14_present_model (кадр 1) | `iz_admits_facts`, `knows_supplier_exists`, `knows_thursday_plumber`, `knows_handover_gap`, `knows_chalk_author` |
| `TALK.iz.folder` | B14, кадр 2 | B14_present_model → `DOC.notice_counter` | `counter_notice_read` |
| `TALK.iz.ladder` | B14, кадр 3 | B14_present_model | `iz_stepladder_minimized` |
| `TALK.iz.key` | B14, кадр 4 | B14_present_model | `has_stairs_key` |
| `TALK.iz.after` | заговорить с Изольдой ∧ `iz_admits_facts` | — | — |
| `TALK.iz.exit` | `menu:` закончить разговор | — | — |
| `SEQ.stairs.open` | `room:W4`, дверь ∧ `has_stairs_key` ∧ `topology_known` ∧ `iz_admits_facts` — кадр 1 | B15_descend | `stairs_open` |
| `Z12.enter` | B15, кадр 2: внизу лестницы | B15_descend | `knows_stairs_narrow` |
| `Z12.instr.look` | `zoom:Z12`, инструкция | — → `DOC.instr1908` | — |
| `Z12.door.look` | `zoom:Z12`, дверь | — → `DOC.notice_door` | `office_notice_read` |
| `Z12.door.knock` | `zoom:Z12`, постучать ∧ ¬`shown(Z12.door.knock)` | — (D32) | — |
| `Z12.door.use` | `zoom:Z12`, открыть | — (D32) | — |
| `Z12.seal.tear` | `zoom:Z12`, сорвать пломбу | — (D33) | — |
| `END.act2` | после `Z12.door.look` ∧ `Z12.door.knock` (цель акта: `midpoint_known`, `stairs_open`, `office_notice_read`, `iz_admits_facts`) | B15_descend (итог) | `midpoint_known` |
| `SEQ.w1.return` | `room:W2` ∧ `trolley_service_side` ∧ ¬`has_menu_card`, в номер под тележкой за меню | B10_take_menu (путь; само меню — слот `Z02.menu.take` Акта I) | `trolley.pos` = `room` |
| `W1.shower.act2` | `room:W1` в Акте II, лейка | — (D5) | — |
| `W2.cascade.look` | `room:W2` ∧ `trolley_service_side`, каскад | — | — |
| `W2.guests` | `room:W2`, фон при смене состояния вестибюля | — | — |
| `W2.pa.more` | `room:W2`, второе объявление акта (после `OPEN.pa`, один раз) | — | — |
| `W2.getout` | `room:W2`, вылезти | — | — |
| `HINT.done` | кнопка совета ∧ открытых тем нет | — | — |
| `HINT.check.1` | тема `check`: ¬(`cascade_pump_dry` ∧ `drums_same_time`); ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.check.2` | тема `check`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.check.3` | тема `check`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.cause.1` | тема `cause`: `cascade_pump_dry` ∧ `drums_same_time` ∧ ¬`knows_supply_cut`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.cause.2` | тема `cause`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.cause.3` | тема `cause`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.map.1` | тема `map`: ¬`overlay_by_frame`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.map.2` | тема `map`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.map.3` | тема `map`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.align.1` | тема `align`: `overlay_by_frame` ∧ ¬`topology_known`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.align.2` | тема `align`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.align.3` | тема `align`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.journal.1` | тема `journal`: ¬`journal_old_read`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.journal.2` | тема `journal`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.journal.3` | тема `journal`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.vitrine.1` | тема `vitrine`: `knows_push_latch` ∧ ¬`vitrine_open`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.vitrine.2` | тема `vitrine`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.vitrine.3` | тема `vitrine`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.seal.1` | тема `seal`: `vitrine_open` ∧ `journal_old_read` ∧ ¬`seal_is_mark`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.seal.2` | тема `seal`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.seal.3` | тема `seal`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.paint.1` | тема `paint`: `knows_plate_under_paint` ∧ ¬`name_revealed`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.paint.2` | тема `paint`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.paint.3` | тема `paint`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.witness.1` | тема `witness`: `knows_supply_cut` ∧ `topology_known` ∧ `seal_is_mark` ∧ `name_revealed` ∧ ¬`iz_admits_facts`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.witness.2` | тема `witness`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.witness.3` | тема `witness`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.down.1` | тема `down`: `has_stairs_key` ∧ ¬`stairs_open`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.down.2` | тема `down`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.down.3` | тема `down`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `DOC.notice_counter` | открыт из `TALK.iz.folder` | — | — |
| `DOC.notice_door` | открыт из `Z12.door.look` | — | — |
| `DOC.exhibit` | открыт из `W2.exhibit.look` | — | — |
| `DOC.journal` | открыт из `Z10.journal.read` | — | — |
| `DOC.paint_act` | открыт из `Z09.board.look` | — | — |
| `DOC.layoff` | открыт из `Z10.layoff.read` | — | — |
| `DOC.plate_k` | открыт из `Z09.paint.scrape` / `Z09.plate.look` | — | — |
| `DOC.regulation` | открыт из `Z04.regulation.look` | — | — |
| `DOC.memo` | открыт из `Z10.memo.read` | — | — |
| `DOC.instr1908` | открыт из `Z12.instr.look` | — | — |
| `DOC.map_hotel` | открыт из `Z04.map.take` / `INV.map.look` | — | — |
| `DOC.map_1908` | открыт из `Z10.tube.open` | — | — |
| `DOC.map_soviet` | открыт из `Z10.folder.open` | — | — |
| `DOC.photo` | открыт из `Z10.tube.open` | — | — |
| `DOC.postcard` | открыт из `Z08.cabinet.open` / `INV.postcard.look` | — | — |
| `DOC.token` | открыт из `Z09.slot.use` / `INV.token.look` | — | — |
| `INV.map.look` | предмет в руках ∧ `has_hotel_map` ∧ ¬`overlay_by_frame` | — → `DOC.map_hotel` | — |
| `INV.menu.painted` | предмет в руках ∧ `has_menu_card` ∧ `menu_smeared` | — | — |
| `INV.key.look` | предмет на столешнице ∧ `has_stairs_key` ∧ ¬`stairs_open` | — | — |
| `INV.token.look` | предмет в руках ∧ `relic_r1` | — → `DOC.token` | — |
| `INV.postcard.look` | предмет в руках ∧ `relic_r2` | — → `DOC.postcard` | — |
| `FB.films.1` | `combo(плёнка, …)` без своего слота ∧ ¬`shown(FB.films.1)` | — | — |
| `FB.films.2` | `combo(плёнка, …)` без своего слота ∧ `shown(FB.films.1)` | — | — |
| `FB.key.1` | `combo(ключ, не та дверь)` | — | — |
| `FB.paper.1` | унести бумагу отеля или старую бумагу (любой зум) | — | — |
| `FB.plunger.act2` | `combo(вантуз, …)` без своего слота в Акте II | — | — |

## Акт III «Улучшения номер три»

Граф: `acts/act3/ACT3_graph.json`, 30 действий, старт — 75 гарантированных флагов финала Акта II (Лапидус у двери конторы, тележка за стойкой).

Приоритет тем Предка (по кратчайшему пути C01 → C16): `order` → `lift` → `where` → `mirror` → `cabin` → `test` → `payer` → `load` → `down`.

Действия графа без своего слота в ТЗ Акта III — их озвучивают слоты Акта II, доступные и здесь: O10_read_memo (`Z10.memo.read`), O11_read_regulation (`Z04.regulation.look`), R1_token (`Z09.slot.use`), R2_postcard (`Z08.cabinet.open`), R3_mug (`Z04.lowdrawer.open`).

| Слот | Когда (флагами) | Действие графа | Ставит |
|---|---|---|---|
| `OPEN.door` | старт акта: `zoom:Z12` ∧ `stairs_open` ∧ `office_notice_read`, кадр 1 | — | — |
| `OPEN.pa` | старт акта, кадр 2 | — | — |
| `OPEN.anc` | один раз после `OPEN.pa` (по желанию реализации) | — | — |
| `Z12.instr.read` | `zoom:Z12` ∧ `knows_receiving_point` ∧ ¬`instr1908_read` | C01_read_order → `DOC.instr1908` | `instr1908_read`, `knows_order_trolley` |
| `Z12.door.knock.again` | `zoom:Z12`, постучать (в Акте III) | — (D2) | — |
| `SEQ.trolley.hall` | `room:W2` ∧ `trolley_service_side` ∧ `knows_order_trolley`, в зал с тележкой — кадр 1 | C02_trolley_stairs | `trolley_in_hall`; `trolley.pos` = `hall` |
| `W4.stairs.trolley` | `room:W4` ∧ `trolley_in_hall` ∧ `knows_stairs_narrow`, спустить тележку — кадр 2 | C02_trolley_stairs | `knows_lift_exists`; `trolley.pos` = `stairs` на кадр слота, затем `hall` (выкатил обратно — правка 08.10.2026) |
| `W4.stairs.carry` | `room:W4` ∧ `trolley_in_hall`, нести тележку | — (D1) | — |
| `Z10.photo.again` | `zoom:Z10` ∧ `knows_lift_exists` ∧ `photo_seen` ∧ ¬`knows_lift_in_hall` | C03_photo_floor | `knows_lift_in_hall` |
| `W4.lift.search` | (`room:W3` ∨ `room:W2`) ∧ `knows_lift_exists` ∧ ¬`knows_lift_in_hall`, искать лифт | — (D4) | — |
| `Z11.threshold.look` | `zoom:Z11` ∧ `knows_lift_exists` ∧ ¬`knows_door_behind_mirror` | C04_threshold | `knows_door_behind_mirror`, `knows_lift_in_hall`, `mirror_seen` |
| `Z11.mirror.look.again` | `zoom:Z11` ∧ `knows_door_behind_mirror` ∧ ¬`mirror_removed` | — | — |
| `Z11.mirror.press` | `zoom:Z11` ∧ `knows_door_behind_mirror` ∧ ¬`mirror_removed`, нажать | O01_mirror_hands (D5) | `mirror_tried` |
| `Z11.mirror.pull` | `zoom:Z11` ∧ `knows_door_behind_mirror` ∧ ¬`mirror_removed`, потянуть | O01_mirror_hands (D6) | `mirror_tried` |
| `Z11.mirror.menu` | `zoom:Z11` ∧ ¬`mirror_removed` ∧ `has_menu_card` ∧ `combo(меню, зеркало)` | — (D7) | — |
| `Z11.mirror.smash` | `zoom:Z11` ∧ ¬`mirror_removed`, разбить | — (D9) | — |
| `Z11.sticker.peel` | `zoom:Z11` ∧ ¬`mirror_removed`, отклеить | — (D10) | — |
| `TALK.iz.mirror` | `menu:` зеркало ∧ `knows_door_behind_mirror` ∧ `trolley_service_side` | O02_ask_mirror (D8) | `iz_mirror_design` |
| `Z11.mirror.plunger` | `zoom:Z11` ∧ `knows_lift_in_hall` ∧ `knows_door_behind_mirror` ∧ `plunger_taken` ∧ `knows_soap_grip` ∧ `combo(вантуз, зеркало)` | C05_plunger_mirror | `mirror_removed`, `lift_gate_seen` |
| `PA.mirror` | сразу после `Z11.mirror.plunger` | C05_plunger_mirror (кадр 2) | — |
| `Z11.gate.look` | `zoom:Z11` ∧ `lift_gate_seen` | — → `DOC.stencil`, `DOC.post` | — |
| `Z11.cabin.look` | `zoom:Z11` ∧ `mirror_removed` ∧ ¬`cabin_seen`, открыть решётку | C06_inspect_cabin → `DOC.sticker`, `DOC.chalk` | `cabin_seen`, `chalk_seen` |
| `Z11.cabin.paint` | `zoom:Z11` ∧ `cabin_seen`, банки | — → `DOC.paint_can` | — |
| `Z11.cabin.trolley.full` | `zoom:Z11` ∧ `cabin_seen` ∧ ¬`cabin_free` ∧ `trolley_in_hall`, вкатить | — (D11) | — |
| `Z11.switch.use` | `zoom:Z11` ∧ `cabin_seen`, рубильник | O03_touch_switch (D12) | `switch_tried` |
| `Z11.chalk.wipe` | `zoom:Z11` ∧ `chalk_seen`, стереть мел | — (D13) | — |
| `Z11.cabin.clear` | `zoom:Z11` ∧ `cabin_seen` ∧ `chalk_seen` ∧ `knows_chalk_author` ∧ ¬`cabin_free`, вынести | C07_clear_cabin | `cabin_free` |
| `PA.cabin` | сразу после `Z11.cabin.clear` | C07_clear_cabin (кадр 2) | — |
| `Z10.water.look` | `zoom:Z10`, стойка воды | — → `DOC.water_stand` | — |
| `Z10.water.carry` | `zoom:Z10`, взять бутылку в руки | — (D17) | — |
| `Z10.water.head` | `zoom:Z10`, облить голову | — (D20) | `probe.n` + 1 |
| `TALK.iz.kefir` | `menu:` кефир ∧ `knows_order_trolley` ∧ `trolley_service_side` ∧ ¬`kefir_ready` | O04_ask_kefir (D16) | `iz_kefir_refused` |
| `Z10.water.offer` | `zoom:Z10` ∧ `knows_order_trolley` ∧ `trolley_in_hall` ∧ `knows_assortment` ∧ ¬`offering_on_trolley` | C08_offering | `offering_on_trolley` |
| `Z11.lift.empty` | `zoom:Z11` ∧ `cabin_free` ∧ `trolley_in_hall` ∧ ¬`offering_on_trolley` ∧ ¬`payment_loaded`, отправить | — (D15) | — |
| `Z11.lift.ride.early` | `zoom:Z11` ∧ `lift_gate_seen` ∧ ¬`payment_in_hall`, встать в кабину | — (D14) | — |
| `SEQ.test.send` | `zoom:Z11` ∧ `cabin_free` ∧ `lift_gate_seen` ∧ `offering_on_trolley` ∧ `trolley_in_hall` ∧ ¬`test_run_done`, «Вниз» — кадр 1 | C09_test_run | `trolley.pos` = `receiving` |
| `SEQ.test.call` | C09, кадр 2: «Вызов» | C09_test_run → `DOC.note`, `DOC.tray_stamp` | `test_run_done`, `has_bill`, `breakfast_stamped`; `trolley.pos` = `hall` |
| `Z11.bill.read` | `zoom:Z11` ∧ `has_bill` ∧ ¬`bill_read` | C10_read_bill → `DOC.bill` | `kuh_note_read`, `bill_read`, `knows_kuh_name`, `knows_debt_balance`, `knows_secret_payer`, `lowest_point` |
| `Z11.wait.water` | `test_run_done` ∧ ¬`payment_delivered`, ждать | — (D19) | — |
| `SEQ.bill.counter` | `room:W4` ∧ `bill_read` ∧ `trolley_in_hall`, за стойку | C11_trolley_counter | `trolley_back_at_counter`; `trolley.pos` = `service` |
| `Z04.stamp.watch` | `zoom:Z04` ∧ `bill_read` ∧ ¬`knows_mp_habit` | C12_watch_stamp → `DOC.complaint` | `knows_mp_habit` |
| `TALK.iz.bill` | `menu:` отдать счёт ∧ `bill_read` ∧ ¬`bill_stamped` | O05_bill_direct (D21) | `iz_forwards_bill` |
| `TALK.iz.accuse` | `menu:` «это вы носили кефир» ∧ `knows_secret_payer` ∧ ¬`iz_confessed` | — (D22) | — |
| `TALK.iz.stamp` | `menu:` печать ∧ `bill_read` ∧ ¬`bill_stamped` | — (D23) | — |
| `Z04.bill.under` | `zoom:Z04` ∧ `knows_mp_habit` ∧ `bill_read` ∧ `knows_secret_payer` ∧ `combo(счёт, стопка жалоб)` — кадр 1 | C13_bill_under_stamp | `bill_stamped` |
| `TALK.iz.confess` | C13, кадр 2 | C13_bill_under_stamp | `iz_confessed`, `knows_payer_iz` |
| `SEQ.iz.payment` | C13, кадр 3 | C13_bill_under_stamp → `DOC.invoice` | `iz_sees_lapidus`, `kefir_ready`, `invoice_ready` |
| `Z04.kefir.take` | `zoom:Z04` ∧ `kefir_ready` ∧ ¬`payment_loaded`, взять бутылку | O06_take_bottle (D24) | `grip_refused_bottle` |
| `Z04.kefir.napkin` | `zoom:Z04` ∧ `kefir_ready` ∧ `combo(салфетка, кефир)` | — (D25) | — |
| `Z04.invoice.take` | `zoom:Z04` ∧ `invoice_ready` ∧ ¬`payment_loaded`, взять накладную | — (D26) | — |
| `TALK.iz.carry` | `menu:` отнести вниз ∧ `kefir_ready` | — (D27) | — |
| `SEQ.load` | `zoom:Z04` ∧ `kefir_ready` ∧ `invoice_ready` ∧ `trolley_back_at_counter`, подкатить тележку | C14_load_payment | `payment_loaded` |
| `SEQ.report` | `room:W2` ∧ `payment_loaded` ∧ `bill_stamped` ∧ `iz_confessed`, увезти от стойки | C15_leave_counter | `iz_reported_pa`, `payment_in_hall`; `trolley.pos` = `hall` |
| `Z12.door.payment` | `zoom:Z12` ∧ `payment_in_hall`, постучать | O07_walk_down (D29) | `door_still_closed` |
| `Z11.ride.standing` | `zoom:Z11` ∧ `payment_in_hall` ∧ `cabin_free`, встать рядом с тележкой | O08_ride_standing (D30) | `people_ban_read` |
| `Z11.send.alone` | `zoom:Z11` ∧ `payment_in_hall` ∧ `cabin_free`, отправить одну | O09_send_alone (D31) | `send_alone_refused` |
| `Z11.cabin.button` | `zoom:Z11` ∧ `cabin_seen`, искать кнопку внутри | — (D32) | — |
| `SEQ.ride` | `zoom:Z11` ∧ `payment_in_hall` ∧ `iz_reported_pa` ∧ `cabin_free` ∧ `lift_gate_seen` ∧ `iz_rule3_seen`, под тележку в кабине — кадр 1 | C16_ride_as_staff | `descended_as_staff`, `lap_hides_again`; `trolley.pos` = `cabin` |
| `SEQ.descent` | C16, кадр 2 | C16_ride_as_staff | `payment_delivered`, `in_receiving_point`; `trolley.pos` = `receiving` |
| `END.act3` | после `SEQ.descent` (цель акта: `in_receiving_point`, `payment_delivered`, `iz_reported_pa`, `iz_confessed`) | — | конец акта |
| `SEQ.counter.again` | переходы W2 ↔ W4 с тележкой после первого, кроме C11 и C15 | — (H24) | `trolley.pos` |
| `W2.guests` | `room:W2`, фон при смене состояния вестибюля | — | — |
| `W2.pa.more` | `room:W2`, ещё одно объявление (один раз, кроме `OPEN.pa`, `PA.mirror`, `PA.cabin`) | — | — |
| `W2.getout` | `room:W2`, вылезти | — | — |
| `W4.design.look` | `room:W4` ∧ `cabin_free`, куча «дизайна» | — | — |
| `Z11.mirror.after` | `zoom:Z11` ∧ `mirror_removed`, зеркало у стены | — | — |
| `HINT.done` | кнопка совета ∧ открытых тем нет | — | — |
| `HINT.order.1` | тема `order`: ¬`instr1908_read`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.order.2` | тема `order`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.order.3` | тема `order`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.lift.1` | тема `lift`: `instr1908_read` ∧ ¬`knows_lift_exists`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.lift.2` | тема `lift`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.lift.3` | тема `lift`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.where.1` | тема `where`: `knows_lift_exists` ∧ ¬(`knows_lift_in_hall` ∧ `knows_door_behind_mirror`); ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.where.2` | тема `where`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.where.3` | тема `where`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.mirror.1` | тема `mirror`: `knows_lift_in_hall` ∧ `knows_door_behind_mirror` ∧ ¬`mirror_removed`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.mirror.2` | тема `mirror`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.mirror.3` | тема `mirror`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.cabin.1` | тема `cabin`: `mirror_removed` ∧ ¬`cabin_free`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.cabin.2` | тема `cabin`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.cabin.3` | тема `cabin`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.test.1` | тема `test`: `cabin_free` ∧ ¬`test_run_done`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.test.2` | тема `test`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.test.3` | тема `test`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.payer.1` | тема `payer`: `bill_read` ∧ ¬`bill_stamped`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.payer.2` | тема `payer`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.payer.3` | тема `payer`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.load.1` | тема `load`: `kefir_ready` ∧ ¬`payment_loaded`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.load.2` | тема `load`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.load.3` | тема `load`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.down.1` | тема `down`: `payment_in_hall` ∧ ¬`in_receiving_point`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.down.2` | тема `down`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.down.3` | тема `down`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `DOC.stencil` | открыт из `Z11.gate.look` | — | — |
| `DOC.sticker` | открыт из `Z11.cabin.look` (наклейка) / `W4.design.look` | — | — |
| `DOC.chalk` | открыт из `Z11.cabin.look` (мел) | — | — |
| `DOC.post` | открыт из `Z11.gate.look` (пост) | — | — |
| `DOC.paint_can` | открыт из `Z11.cabin.paint` | — | — |
| `DOC.water_stand` | открыт из `Z10.water.look` | — | — |
| `DOC.note` | открыт из `SEQ.test.call` / `Z11.bill.read` | — | — |
| `DOC.bill` | открыт из `Z11.bill.read` / `INV.bill.look` | — | — |
| `DOC.tray_stamp` | открыт из `SEQ.test.call` (поднос) | — | — |
| `DOC.complaint` | открыт из `Z04.stamp.watch` | — | — |
| `DOC.invoice` | открыт из `SEQ.iz.payment` / `Z04.invoice.take` | — | — |
| `INV.bill.look` | предмет в руках ∧ `has_bill` | — → `DOC.bill` | — |
| `INV.plunger.act3` | предмет в руках ∧ `plunger_taken` (Акт III) | — | — |
| `FB.bill.1` | `combo(счёт, …)` без своего слота | — | — |
| `FB.plunger.act3` | `combo(вантуз, …)` без своего слота в Акте III | — | — |
| `FB.paper.act3` | унести бумагу отеля (любой зум) | — | — |

## Акт IV «Приёмка»

Граф: `acts/act4/ACT4_graph.json`, 15 действий, старт — 112 гарантированных флагов финала Акта III (кабина внизу, Лапидус под тележкой в W5).

Приоритет тем Предка (по кратчайшему пути E01 → E06): `out` → `hello` → `office` → `mark` → `valve`.

| Слот | Когда (флагами) | Действие графа | Ставит |
|---|---|---|---|
| `OPEN.arrive` | старт акта: `in_receiving_point` ∧ `lap_hides_again`, кадр 1 | — | — |
| `OPEN.steps` | старт акта, кадр 2 | — | — |
| `OPEN.anc` | один раз после `OPEN.steps` (по желанию реализации) | — | — |
| `SEQ.rollout` | `room:W5` ∧ `in_receiving_point` ∧ `lap_hides_again` ∧ `payment_delivered` ∧ `plate_revealed`, выкатить тележку — кадр 1 | E01_roll_out | — |
| `SEQ.goods` | E01, кадр 2 | E01_roll_out | `goods_accepted` |
| `SEQ.debt` | E01, кадр 3 | E01_roll_out | — |
| `SEQ.note_fix` | E01, кадр 4 | E01_roll_out → `DOC.note_fixed` | — |
| `SEQ.trolley_return` | E01, кадр 5 | E01_roll_out → `DOC.plate_mark` | `trolley_reinventoried` |
| `SEQ.wait` | E01, кадр 6 | E01_roll_out | `kuh_wants_hello` |
| `TALK.kuh.under` | `menu:` поздороваться из-под тележки ∧ `kuh_wants_hello` ∧ ¬`lap_out` | O01_report_from_under (D1) | `under_refused` |
| `W5.hand` | `room:W5` ∧ `kuh_wants_hello` ∧ ¬`lap_out`, высунуть руку | O01_report_from_under (D2) | `under_refused` |
| `W5.push_goods` | `room:W5` ∧ `goods_accepted` ∧ ¬`lap_out`, подтолкнуть груз | — (D3) | — |
| `W5.cover.skirt` | `room:W5` ∧ `kuh_wants_hello` ∧ ¬`lap_out`, обернуться юбкой | O02_cover_up (D4) | `cover_tried` |
| `W5.cover.map` | `room:W5` ∧ `kuh_wants_hello` ∧ ¬`lap_out` ∧ `has_hotel_map`, карта | O02_cover_up (D5) | `cover_tried` |
| `W5.cover.menu` | `room:W5` ∧ `kuh_wants_hello` ∧ ¬`lap_out` ∧ `has_menu_card`, меню | O02_cover_up (D6) | `cover_tried` |
| `W5.cover.napkin` | `room:W5` ∧ `kuh_wants_hello` ∧ ¬`lap_out` ∧ `breakfast_on_trolley`, салфетка | O02_cover_up (D7) | `cover_tried` |
| `W5.wait_more` | `room:W5` ∧ `kuh_wants_hello` ∧ ¬`lap_out`, ждать | — (D8) | — |
| `W5.door.early` | `room:W5` ∧ ¬`reported`, дверь на лестницу | — (D9) | — |
| `SEQ.come_out` | `room:W5` ∧ `kuh_wants_hello` ∧ ¬`lap_out`, вылезти и встать | E02_come_out | `lap_out` |
| `W5.sign.read` | `room:W5` ∧ `lap_out`, табличка | — → `DOC.reception_sign` | — |
| `SEQ.hello` | `room:W5` ∧ `lap_out` ∧ `knows_thursday_plumber` ∧ `instr1908_read` ∧ ¬`reported`, доложиться — кадр 1 | E03_report | — |
| `SEQ.report_line` | E03, кадр 2 | E03_report | `reported` |
| `SEQ.doors` | E03, кадр 3 | E03_report | — |
| `SEQ.office` | `room:W5` ∧ `reported` ∧ ¬`in_office`, войти в контору | E04_enter_office | `in_office` |
| `Z13.ledger.look` | `zoom:Z13` ∧ `in_office` | — → `DOC.ledger` | — |
| `Z13.valve.look` | `zoom:Z13` ∧ `in_office` ∧ ¬`marks_exchanged` | — → `DOC.seal_tag` | — |
| `Z13.speaker.look` | `zoom:Z13` ∧ `in_office` | — | — |
| `Z13.files.look` | `zoom:Z13` ∧ `in_office` | — | — |
| `Z13.mug.look` | `zoom:Z13` ∧ `in_office` | — | — |
| `Z13.photo.look` | `zoom:Z13` ∧ `in_office` | O03_look_photo → `DOC.photo_family` | `family_photo_seen` |
| `TALK.kuh.photo` | `menu:` родня ∧ `in_office` ∧ `family_photo_seen` | — | — |
| `TALK.kuh.plate` | `menu:` табличка ∧ `in_office` | — | — |
| `TALK.kuh.kefir` | `menu:` кефир ∧ `in_office` | — | — |
| `Z13.ledger.pen` | `zoom:Z13` ∧ `in_office` ∧ ¬`marks_exchanged`, ручка | O04_pen (D10) | `pen_slipped` |
| `Z13.ledger.thumb` | `zoom:Z13` ∧ `in_office` ∧ ¬`marks_exchanged`, палец | O05_thumb (D11) | `thumb_smeared` |
| `Z13.valve.sealed` | `zoom:Z13` ∧ `in_office` ∧ ¬`marks_exchanged`, задвижка | O06_valve_sealed (D12) | `valve_refused` |
| `Z13.plunger.mark` | `zoom:Z13` ∧ `in_office` ∧ `plunger_taken` ∧ `wet_ring_seen` ∧ `seal_is_mark` ∧ `combo(вантуз, журнал)` | E05_plunger_mark | `marks_exchanged` |
| `Z13.valve.turn` | `zoom:Z13` ∧ `marks_exchanged` ∧ `instr1908_read`, маховик | E06_open_valve | `water_restored` |
| `PA.final` | сразу после `Z13.valve.turn` | E06_open_valve (кадр 2) | — |
| `SEQ.finale` | после `PA.final` | E06_open_valve (кадр 3) | конец игры → эпилог по `relics` |
| `SEQ.upstairs` | `room:W6` ∧ `reported` ∧ ¬`water_restored`, выйти на лестницу (первый раз) | — (путь к R1–R3) | — |
| `Z09.token.act4` | `zoom:Z09` ∧ `reported` ∧ `w4_open` ∧ ¬`relic_r1` | R1_token | `relic_r1` |
| `Z08.postcard.act4` | `zoom:Z08` ∧ `reported` ∧ `w3_open` ∧ ¬`relic_r2` | R2_postcard | `relic_r2` |
| `Z04.mug.act4` | `zoom:Z04` ∧ `reported` ∧ `knows_push_latch` ∧ ¬`relic_r3` | R3_mug | `relic_r3` |
| `Z13.relics.look` | `zoom:Z13` ∧ `in_office` ∧ `relics` ≥ 1, вещи на столе | — | — |
| `EPI.0` | после `SEQ.finale` ∧ `relics` = 0 | — → `DOC.menu_new` | — |
| `EPI.1` | после `SEQ.finale` ∧ `relics` = 1 | — → `DOC.menu_new` | — |
| `EPI.2` | после `SEQ.finale` ∧ `relics` = 2 | — → `DOC.menu_new` | — |
| `EPI.3` | после `SEQ.finale` ∧ `relics` = 3 | — → `DOC.menu_new` | — |
| `HINT.done` | кнопка совета ∧ `water_restored` | — | — |
| `HINT.out.1` | тема `out`: `kuh_wants_hello` ∧ ¬`lap_out`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.out.2` | тема `out`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.out.3` | тема `out`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.hello.1` | тема `hello`: `lap_out` ∧ ¬`reported`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.hello.2` | тема `hello`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.hello.3` | тема `hello`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.office.1` | тема `office`: `reported` ∧ ¬`in_office`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.office.2` | тема `office`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.office.3` | тема `office`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.mark.1` | тема `mark`: `in_office` ∧ ¬`marks_exchanged`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.mark.2` | тема `mark`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.mark.3` | тема `mark`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `HINT.valve.1` | тема `valve`: `marks_exchanged` ∧ ¬`water_restored`; ступень 0 | — | ступень 1, `hint.lock` |
| `HINT.valve.2` | тема `valve`; ступень 1 | — | ступень 2, `hint.lock` |
| `HINT.valve.3` | тема `valve`; ступень ≥ 2 | — | ступень 3, `hint.lock` |
| `DOC.reception_sign` | открыт из `W5.sign.read` | — | — |
| `DOC.note_fixed` | открыт из `SEQ.note_fix` | — | — |
| `DOC.plate_mark` | открыт из `SEQ.trolley_return` | — | — |
| `DOC.ledger` | открыт из `Z13.ledger.look` / `Z13.plunger.mark` | — | — |
| `DOC.seal_tag` | открыт из `Z13.valve.look` | — | — |
| `DOC.photo_family` | открыт из `Z13.photo.look` | — | — |
| `DOC.menu_new` | открыт из `EPI.0` … `EPI.3` | — | — |
| `INV.plunger.act4` | предмет в руках ∧ `plunger_taken` (Акт IV) | — | — |
| `FB.plunger.act4` | `combo(вантуз, …)` без своего слота в Акте IV | — | — |
| `FB.kefir.head` | `combo(кефир или кружка, голова)` в W5 или W6 | — (D13) | — |
