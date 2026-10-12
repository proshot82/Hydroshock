# Звуковой пакет З4 — Акт IV и финальная вода (кандидаты, 12.10.2026)

В `assets/` ничего не перенесено — только после «да» автора. Слушать — `listen.html` (у каждого звука — что за момент в игре, что слышит игрок, чем продублирован) или страница-прослушка https://claude.ai/artifact/GTCKbVnotF69UPWMKW86uu.

**Из чего:** ElevenLabs Sound Effects (журнал `work/elevenlabs/log.jsonl`, исходники `raw/`); блип Кухтулху — синтез (`tools/audio/synth.py raw blip_kuh`); каскад финала — фонтан ElevenLabs + писк резиновой уточки (`duck_squeak_*`) на взлёте (решение автора: писк, без цитаты мелодии «Утиных историй»). Сборка — `build.py`, страница — `listen_gen.py`.

**Состав:** 11 эффектов §9.1 Акта IV (`sfx_wet_steps`, `sfx_wet_stamp`, `sfx_pen_scratch`, `sfx_door_clicks`, `sfx_pen_roll`, `sfx_soap_smear`, `sfx_seal_tear`, `sfx_valve_turn`, `sfx_building_exhale`, `sfx_pa_drown`, `sfx_drums_turn`) и три финальной воды (`sfx_fin_shower`, `sfx_fin_cascade`, `sfx_fin_spring`) по 3 варианта; `amb_below` ×3; `blip_kuh` a/b.

**Демо сцен** (из принятых `bgm_deep`, `bgm_below`, `sting_water`, `bgm_epilogue`):
- `demo_come_out_pen_1…3` — появление Кухтулху: тема «чудовище из глубины» обрывается, скрип пера (варианты 1–3), хабанера с начала;
- `demo_valve_1…3` — маховик → долгий выдох здания → поверх `sting_water`;
- `demo_finale_A/B/V` — ответ на вопрос о музыке финального монтажа: громкая связь тонет, четыре кадра монтажа (душ, каскад с уточкой, барабаны, источник); А — `bgm_epilogue` под монтажом, Б — без музыки, В — `bgm_below` под монтажом.

**Проверено машиной:** длина, пики, атаки; Whisper — речи в фоне низа и «громкая связь тонет» нет (в `sfx_pa_drown_1` — одна «фраза» на шуме с вероятностью «нет речи» 0,84, типичная ошибка распознавателя; проверить на слух).
