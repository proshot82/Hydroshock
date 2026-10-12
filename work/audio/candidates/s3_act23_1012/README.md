# Звуковой пакет З3 — Акты II–III (кандидаты, 12.10.2026)

**Выбор автора 12.10.2026:** `sfx_pump_dry_1`, `sfx_phone_ring_3`, `sfx_drum_beep_synth_a`, `sfx_latch_click_1`, `sfx_tag_fold_1`, `sfx_plunger_press_1`, `sfx_paint_scrape_2`, `sfx_token_drop_2`, `sfx_drawer_click_2`, `sfx_key_door_1`, `sfx_knock_b`, `sfx_trolley_jam_2`, `sfx_wheel_bump_3`, `sfx_board_lay_1`, `sfx_suction_glass_3`, `sfx_switch_1`, `sfx_grille_shut_2`, `sfx_lift_down_3`, `sfx_lift_up_1`, `sfx_stamp_2`, `sfx_bottle_catch_1`, `sfx_lobby_hush_a`, `sfx_descent_3`, `amb_laundry_2`, `amb_hall_1`. Готовые OGG (имена игры) — `final/` (`build.py --final`), 25 файлов; ждут «да» на перенос.

В `assets/` ничего не перенесено — только после «да» автора. Слушать — `listen.html` (там же у каждого звука — что за момент в игре, что слышит игрок, чем продублирован) или страница-прослушка https://claude.ai/artifact/QBU1V9Y5h4fYqrkbUywUh1.

**Из чего** (решения автора 12.10.2026, спека §9): органика и фоны — ElevenLabs Sound Effects (`tools/audio/eleven.py sfx`, журнал `work/elevenlabs/log.jsonl`, исходники `raw/`); писк табло ×3 — синтез (`tools/audio/synth.py raw sfx_drum_beep`); стук ×3 — собран из одного удара ElevenLabs (`knock_one_*`) с «долгой тишиной» после; «вестибюль затихает» (`sfx_lobby_hush_a`) — собран из принятого `assets/audio/amb_lobby.ogg` (ElevenLabs до настоящей тишины не доходит; в игре фон вестибюля в этот момент тоже гасится). Сборка листа — `build.py`, страницы — `listen_gen.py`.

**Громкость для прослушки:** эффекты моно −16 LUFS (пик ≤ −1,5 dBFS), фоны стерео −26 LUFS, склеены дважды (шов на 0:30); окончательный баланс — З5.

**Проверено машиной:** длина, пики, атаки; Whisper — речи в «вестибюле затихает» и фонах нет. Характер — на слух автора.

**Состав:** 21 эффект §9.1 по 3 варианта (`sfx_pump_dry` — без щелчка защиты, по решению автора; `sfx_grille_shut` — новый), `sfx_drum_beep` синтез a/b/c, `sfx_knock` a/b, `amb_laundry` ×3, `amb_hall` ×3. Слоты поздних правок получают те же файлы (спека §9.1, решение автора по п. 3).
