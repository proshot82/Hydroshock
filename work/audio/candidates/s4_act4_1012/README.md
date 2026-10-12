# Звуковой пакет З4 — Акт IV и финальная вода (кандидаты, 12.10.2026)

В `assets/` ничего не перенесено — только после «да» автора. Слушать — `listen.html` (у каждого звука — что за момент в игре, что слышит игрок, чем продублирован) или страница-прослушка https://claude.ai/artifact/GTCKbVnotF69UPWMKW86uu.

**Выбор автора 12.10.2026:** `sfx_wet_steps_2`, `sfx_wet_stamp_2`, `sfx_pen_scratch_1` (демо `demo_come_out_pen_1`), `sfx_pen_roll_3`, `sfx_soap_smear_2`, `sfx_seal_tear_1`, `sfx_valve_turn_2`, `sfx_building_exhale_3`, `sfx_pa_drown_3`, `sfx_fin_shower_3`, `sfx_fin_cascade_2`, `sfx_drums_turn_3`, `sfx_fin_spring_3`, `amb_below_3`, `blip_kuh_a` — финальные OGG в `final/` (`build.py --final`), ждут «да». **`sfx_door_clicks` — выбора нет, спросить.** Музыка финала: «хочется пободрее, больше духовых, игра же про трубы» → ред. 2 — `bgm_finale_a…d` (ElevenLabs Music: a диксиленд `music_v1`, b курортный духовой оркестр-полька, c биг-бэнд, d = a на `music_v2_5`; в b около 12 с тишины в середине), демо финала с выбранными звуками `demo_finale_brass_a…d` (`build.py --themes`). Кандидат на замену принятой `bgm_epilogue` (финал + эпилог, с первого кадра монтажа). **Автор: «ближе всего C, но тоже не вполне то»** → ред. 3 от c: `bgm_finale_c2` (тот же промпт, `music_v2_5`), `c3` (больше труб, фанфара, ~160 уд/мин, v2.5), `c4` (мультяшный джаз 1930-х, сурдины «уа-уа», v2.5), `c5` (уютнее, бальный зал, v1); демо `demo_finale_brass_c2…c5` (`build.py --themes c2 c3 c4 c5`).

**О моделях ElevenLabs Music:** все темы 06.10 и З1 сделаны `music_v1` — модель API по умолчанию (запрос без `model_id`). Music v2.5 вышла 11.09.2026 (по сообщениям прессы), в API — `music_v2_5`; пробовалась только в `bgm_deep_e` и `bgm_finale_d`. У v2/v2.5 — план композиции по кускам и привязка к уже сгенерированной песне (`conditioning_ref` по `song_id`).

**Из чего:** ElevenLabs Sound Effects (журнал `work/elevenlabs/log.jsonl`, исходники `raw/`); блип Кухтулху — синтез (`tools/audio/synth.py raw blip_kuh`); каскад финала — фонтан ElevenLabs + писк резиновой уточки (`duck_squeak_*`) на взлёте (решение автора: писк, без цитаты мелодии «Утиных историй»). Сборка — `build.py`, страница — `listen_gen.py`.

**Состав:** 11 эффектов §9.1 Акта IV (`sfx_wet_steps`, `sfx_wet_stamp`, `sfx_pen_scratch`, `sfx_door_clicks`, `sfx_pen_roll`, `sfx_soap_smear`, `sfx_seal_tear`, `sfx_valve_turn`, `sfx_building_exhale`, `sfx_pa_drown`, `sfx_drums_turn`) и три финальной воды (`sfx_fin_shower`, `sfx_fin_cascade`, `sfx_fin_spring`) по 3 варианта; `amb_below` ×3; `blip_kuh` a/b.

**Демо сцен** (из принятых `bgm_deep`, `bgm_below`, `sting_water`, `bgm_epilogue`):
- `demo_come_out_pen_1…3` — появление Кухтулху: тема «чудовище из глубины» обрывается, скрип пера (варианты 1–3), хабанера с начала;
- `demo_valve_1…3` — маховик → долгий выдох здания → поверх `sting_water`;
- `demo_finale_A/B/V` — ответ на вопрос о музыке финального монтажа: громкая связь тонет, четыре кадра монтажа (душ, каскад с уточкой, барабаны, источник); А — `bgm_epilogue` под монтажом, Б — без музыки, В — `bgm_below` под монтажом.

**Проверено машиной:** длина, пики, атаки; Whisper — речи в фоне низа и «громкая связь тонет» нет (в `sfx_pa_drown_1` — одна «фраза» на шуме с вероятностью «нет речи» 0,84, типичная ошибка распознавателя; проверить на слух).
